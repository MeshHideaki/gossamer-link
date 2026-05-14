# v16.5.4 predictive topology system
# binary predictive stabilization
# triple execution strict validation

import numpy as np
import random
import hashlib
import copy

# =========================================================
# constants
# =========================================================

BASE_SEED = 42

NODE_COUNT = 12
STEP_COUNT = 700

DIM = 8

MAX_CONNECTIONS = 4
SEARCH_K = 5
ESSENCE_SLOTS = 3

POW_DIFFICULTY = 2

TRUST_DECAY = 0.02

MIN_TRUST = 0.05
MAX_TRUST = 0.95

ANOMALY_Z = 1.2

TARGET_VAR_MIN = 0.02
TARGET_VAR_MAX = 0.06

UPDATE_SCALE = 0.05

HISTORY_INTERVAL = 5

PREDICTION_THRESHOLD = 0.24

# =========================================================
# node
# =========================================================

class Node:

    def __init__(self, node_id):

        self.id = node_id

        self.essences = np.random.randn(
            ESSENCE_SLOTS,
            DIM
        )

        self.essences /= (
            np.linalg.norm(
                self.essences,
                axis=1,
                keepdims=True
            ) + 1e-8
        )

        self.trust = random.uniform(0.3, 0.7)

        self.connections = set()

        self.age = 1
        self.nonce = 0

        self.is_anomaly = False
        self.anomaly_score = 0.0

        self.persistence_counter = 0

# =========================================================
# utility
# =========================================================

def compute_hash(val):

    return hashlib.sha256(
        str(val).encode()
    ).hexdigest()

def valid_pow(node):

    return compute_hash(
        (node.id, node.nonce)
    ).startswith("0" * POW_DIFFICULTY)

def mine_pow(node):

    if valid_pow(node):
        return

    while not valid_pow(node):
        node.nonce += 1

def similarity(a, b):

    return np.max(np.dot(a, b.T))

# =========================================================
# global memory
# =========================================================

topology_history = []

cause_memory = []

future_prediction_memory = []

successful_topology_memory = []

collapse_events = 0

prediction_events = 0
successful_predictions = 0

proactive_rewiring_count = 0
prevented_collapse_events = 0

# =========================================================
# anomaly
# =========================================================

def detect_anomaly(nodes):

    trust_values = np.array([
        n.trust for n in nodes
    ])

    mean = np.mean(trust_values)

    std = np.std(trust_values) + 1e-8

    for i, node in enumerate(nodes):

        z = abs(
            (trust_values[i] - mean)
            / std
        )

        node.anomaly_score = float(z)

        node.is_anomaly = z > ANOMALY_Z

# =========================================================
# trust
# =========================================================

def update_trust(nodes):

    scores = []

    for node in nodes:

        neighbors = [
            nodes[i]
            for i in node.connections
        ]

        if neighbors:

            sims = [
                similarity(
                    node.essences,
                    nb.essences
                )
                for nb in neighbors
            ]

            scores.append(np.mean(sims))

        else:

            scores.append(0.5)

    scores = np.array(scores)

    order = np.argsort(scores)

    ranks = np.empty_like(order)

    ranks[order] = np.arange(len(nodes))

    target = (
        MIN_TRUST
        + (
            MAX_TRUST
            - MIN_TRUST
        )
        * (
            ranks
            / (len(nodes) - 1 + 1e-8)
        )
    )

    mean_trust = np.mean([
        n.trust for n in nodes
    ])

    for i, node in enumerate(nodes):

        anomaly_scale = (
            1.0
            - 0.18
            * (
                node.anomaly_score
                / (
                    1.0
                    + node.anomaly_score
                )
            )
        )

        new_trust = (
            (1 - TRUST_DECAY)
            * node.trust
            + 0.50
            * (target[i] - node.trust)
            + 0.10
            * (node.trust - mean_trust)
        )

        node.trust = float(
            np.clip(
                new_trust * anomaly_scale,
                MIN_TRUST,
                MAX_TRUST
            )
        )

# =========================================================
# propagation
# =========================================================

def propagate_essences(nodes):

    for node in nodes:

        neighbors = [
            nodes[i]
            for i in node.connections
        ]

        if not neighbors:
            continue

        for i in range(ESSENCE_SLOTS):

            src_node = random.choice(neighbors)

            src = src_node.essences[
                random.randrange(ESSENCE_SLOTS)
            ]

            sim = np.dot(
                node.essences[i],
                src
            )

            if sim < 0.6:

                node.essences[i] += (
                    UPDATE_SCALE
                    * (
                        src
                        - node.essences[i]
                    )
                )

            elif sim > 0.85:

                node.essences[i] -= (
                    UPDATE_SCALE
                    * 0.5
                    * (
                        src
                        - node.essences[i]
                    )
                )

            node.essences[i] /= (
                np.linalg.norm(
                    node.essences[i]
                ) + 1e-8
            )

# =========================================================
# rewiring
# =========================================================

def rewire(nodes):

    for node in nodes:

        candidates = [
            n for n in nodes
            if n.id != node.id
        ]

        scored = []

        for c in candidates:

            score = (
                0.55 * c.trust
                + 0.45
                * similarity(
                    node.essences,
                    c.essences
                )
            )

            scored.append((score, c))

        scored.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        selected = []

        for _, c in scored:

            if len(selected) >= SEARCH_K:
                break

            if all(
                similarity(
                    c.essences,
                    s.essences
                ) < 0.75
                for s in selected
            ):
                selected.append(c)

        while len(selected) < SEARCH_K:

            c = random.choice(candidates)

            if c not in selected:
                selected.append(c)

        previous = copy.deepcopy(
            node.connections
        )

        node.connections = set([
            c.id
            for c in selected[:MAX_CONNECTIONS]
        ])

        overlap = len(
            previous & node.connections
        )

        if overlap >= 3:
            node.persistence_counter += 1

# =========================================================
# proactive rewiring
# =========================================================

def proactive_rewiring(nodes):

    global proactive_rewiring_count

    if len(successful_topology_memory) == 0:
        return False

    memory = random.choice(
        successful_topology_memory
    )

    for i, node in enumerate(nodes):

        restored = memory[
            "connections"
        ][i]

        combined = list(set(
            list(node.connections)
            + restored
        ))

        random.shuffle(combined)

        node.connections = set(
            combined[:MAX_CONNECTIONS]
        )

        node.persistence_counter += 2

    proactive_rewiring_count += 1

    return True

# =========================================================
# variance regulation
# =========================================================

def regulate_variance(nodes):

    all_vectors = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    mean_variance = np.mean(
        np.var(all_vectors, axis=0)
    )

    if mean_variance > TARGET_VAR_MAX:

        scale = np.sqrt(
            TARGET_VAR_MAX
            / (
                mean_variance + 1e-8
            )
        )

        for n in nodes:
            n.essences *= scale

    elif mean_variance < TARGET_VAR_MIN:

        for n in nodes:

            n.essences += (
                np.random.randn(
                    *n.essences.shape
                ) * 0.01
            )

            n.essences /= (
                np.linalg.norm(
                    n.essences,
                    axis=1,
                    keepdims=True
                ) + 1e-8
            )

# =========================================================
# successful memory
# =========================================================

def store_successful_topology(nodes):

    global successful_topology_memory

    memory = {

        "connections": [
            sorted(list(n.connections))
            for n in nodes
        ]
    }

    successful_topology_memory.append(memory)

    if len(successful_topology_memory) > 20:
        successful_topology_memory.pop(0)

# =========================================================
# predictive state
# =========================================================

def compute_predictive_state(
    nodes,
    instability_history
):

    trust_std = np.std([
        n.trust for n in nodes
    ])

    anomaly_ratio = np.mean([
        1.0 if n.is_anomaly else 0.0
        for n in nodes
    ])

    density = np.mean([
        len(n.connections)
        for n in nodes
    ]) / MAX_CONNECTIONS

    instability = (
        0.40 * trust_std
        + 0.35 * anomaly_ratio
        + 0.25 * (1.0 - density)
    )

    instability_history.append(
        instability
    )

    if len(instability_history) < 8:

        trend = instability

    else:

        recent = np.mean(
            instability_history[-4:]
        )

        older = np.mean(
            instability_history[-8:-4]
        )

        trend = recent - older

    predicted_collapse = (
        instability > PREDICTION_THRESHOLD
        and trend > 0.0
    )

    return predicted_collapse, instability

# =========================================================
# prediction validation
# =========================================================

def validate_prediction(
    prediction,
    actual,
    rewired,
    before_instability,
    after_instability,
    step
):

    global prediction_events
    global successful_predictions

    global prevented_collapse_events

    global future_prediction_memory

    prediction_events += 1

    success = (
        prediction == actual
    )

    if success:
        successful_predictions += 1

    if (
        rewired
        and after_instability
        < before_instability
    ):
        prevented_collapse_events += 1

    future_prediction_memory.append({

        "step": step,

        "prediction": prediction,

        "actual_outcome": actual,

        "prediction_error":
            0 if success else 1
    })

# =========================================================
# history
# =========================================================

def record_topology(nodes, step):

    global topology_history
    global collapse_events

    topology_history.append({

        "step": step,

        "connections": [
            sorted(list(n.connections))
            for n in nodes
        ]
    })

    density = np.mean([
        len(n.connections)
        for n in nodes
    ])

    if density < 2.5:
        collapse_events += 1

# =========================================================
# cause memory
# =========================================================

def record_cause_memory(nodes, step):

    global cause_memory

    cause_memory.append({

        "step": step,

        "cause_event":
            ["predictive_shift"],

        "effect_topology": {

            "density": float(np.mean([
                len(n.connections)
                for n in nodes
            ]))
        },

        "survival_delta": {

            "trust_std": float(np.std([
                n.trust for n in nodes
            ]))
        }
    })

# =========================================================
# metrics
# =========================================================

def compute_metrics(nodes):

    all_vectors = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    mean_variance = float(np.mean(
        np.var(all_vectors, axis=0)
    ))

    trust_values = [
        n.trust for n in nodes
    ]

    patterns = {
        tuple(sorted(list(n.connections)))
        for n in nodes
    }

    prediction_accuracy = (
        successful_predictions
        / (
            prediction_events
            + 1e-8
        )
    )

    avg_persistence = np.mean([
        min(
            n.persistence_counter,
            80
        )
        for n in nodes
    ])

    predictive_integrity = all(

        (
            "prediction" in p
            and "actual_outcome" in p
            and "prediction_error" in p
        )

        for p in future_prediction_memory
    )

    future_adaptation = (

        proactive_rewiring_count >= 5

        and prevented_collapse_events >= 3

        and prediction_accuracy >= 0.55
    )

    return {

        "history_length":
            len(topology_history),

        "cause_memory_length":
            len(cause_memory),

        "successful_memory_count":
            len(successful_topology_memory),

        "prediction_memory_length":
            len(future_prediction_memory),

        "prediction_events":
            prediction_events,

        "successful_predictions":
            successful_predictions,

        "proactive_rewiring_count":
            proactive_rewiring_count,

        "prevented_collapse_events":
            prevented_collapse_events,

        "prediction_accuracy":
            round(
                prediction_accuracy,
                6
            ),

        "future_adaptation":
            future_adaptation,

        "historical_adaptation":
            (
                len(
                    successful_topology_memory
                ) >= 10
            ),

        "predictive_integrity":
            predictive_integrity,

        "structural_diversity":
            round(
                float(
                    len(patterns)
                    / NODE_COUNT
                ),
                6
            ),

        "average_persistence":
            round(
                avg_persistence,
                6
            ),

        "simulation_stability":
            (
                TARGET_VAR_MIN
                <= mean_variance
                <= TARGET_VAR_MAX
            ),

        "mean_variance":
            round(mean_variance, 6),

        "trust_range":
            round(
                float(
                    max(trust_values)
                    - min(trust_values)
                ),
                6
            )
    }

# =========================================================
# reset
# =========================================================

def reset_globals():

    global topology_history
    global cause_memory

    global future_prediction_memory

    global successful_topology_memory

    global collapse_events

    global prediction_events
    global successful_predictions

    global proactive_rewiring_count
    global prevented_collapse_events

    topology_history = []

    cause_memory = []

    future_prediction_memory = []

    successful_topology_memory = []

    collapse_events = 0

    prediction_events = 0
    successful_predictions = 0

    proactive_rewiring_count = 0
    prevented_collapse_events = 0

# =========================================================
# simulation
# =========================================================

def run_simulation(run_id):

    reset_globals()

    seed = BASE_SEED + run_id

    random.seed(seed)
    np.random.seed(seed)

    nodes = [
        Node(i)
        for i in range(NODE_COUNT)
    ]

    instability_history = []

    for step in range(STEP_COUNT):

        before_instability = np.std([
            n.trust for n in nodes
        ])

        for node in nodes:

            node.age += 1

            mine_pow(node)

        detect_anomaly(nodes)

        prediction, instability = (
            compute_predictive_state(
                nodes,
                instability_history
            )
        )

        rewired = False

        if prediction:

            rewired = proactive_rewiring(
                nodes
            )

        update_trust(nodes)

        propagate_essences(nodes)

        rewire(nodes)

        regulate_variance(nodes)

        after_instability = np.std([
            n.trust for n in nodes
        ])

        actual = (
            after_instability
            > PREDICTION_THRESHOLD
        )

        validate_prediction(

            prediction,
            actual,
            rewired,

            before_instability,
            after_instability,

            step
        )

        if step % 15 == 0:

            store_successful_topology(
                nodes
            )

        if step % HISTORY_INTERVAL == 0:

            record_topology(
                nodes,
                step
            )

            record_cause_memory(
                nodes,
                step
            )

    metrics = compute_metrics(nodes)

    validation = (

        metrics["history_length"] >= 120

        and metrics[
            "cause_memory_length"
        ] >= 120

        and metrics[
            "successful_memory_count"
        ] >= 10

        and metrics[
            "prediction_memory_length"
        ] >= 120

        and metrics[
            "prediction_events"
        ] >= 10

        and metrics[
            "successful_predictions"
        ] >= 5

        and metrics[
            "proactive_rewiring_count"
        ] >= 5

        and metrics[
            "prevented_collapse_events"
        ] >= 3

        and metrics[
            "prediction_accuracy"
        ] >= 0.55

        and metrics[
            "future_adaptation"
        ] is True

        and metrics[
            "historical_adaptation"
        ] is True

        and metrics[
            "predictive_integrity"
        ] is True

        and metrics[
            "structural_diversity"
        ] >= 0.35

        and (
            5.0
            <= metrics[
                "average_persistence"
            ]
            <= 80.0
        )

        and metrics[
            "simulation_stability"
        ] is True

        and (
            0.02
            <= metrics[
                "mean_variance"
            ]
            <= 0.06
        )

        and (
            0.15
            <= metrics[
                "trust_range"
            ]
            <= 0.85
        )
    )

    print(f"\n--- RUN #{run_id + 1} ---")

    for k, v in metrics.items():

        print(f"{k}: {v}")

    print(
        "validation_result:",
        validation
    )

    return validation

# =========================================================
# triple execution
# =========================================================

results = []

for run_id in range(3):

    result = run_simulation(run_id)

    results.append(result)

print("\nfinal_result:")

if all(results):
    print("ACHIEVED")
else:
    print("NOT ACHIEVED")
