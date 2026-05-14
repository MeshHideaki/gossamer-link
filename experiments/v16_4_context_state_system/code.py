# v16.4.1 context state system
# deterministic context rotation fix
# environment conditioned topology verification
# triple execution validation required

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

# =========================================================
# context states
# =========================================================

CONTEXTS = [
    "sparse_mode",
    "hostile_mode",
    "cooperative_mode",
    "unstable_mode"
]

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

        self.last_active = 0

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
# anomaly detection
# =========================================================

def detect_anomaly(nodes):

    trust_values = np.array([
        n.trust for n in nodes
    ])

    mean = np.mean(trust_values)

    std = np.std(trust_values) + 1e-8

    for i, node in enumerate(nodes):

        z = abs(
            (trust_values[i] - mean) / std
        )

        node.anomaly_score = float(z)

        node.is_anomaly = z > ANOMALY_Z

# =========================================================
# trust update
# =========================================================

def update_trust(nodes, context_state):

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
        + (MAX_TRUST - MIN_TRUST)
        * (ranks / (len(nodes) - 1 + 1e-8))
    )

    mean_trust = np.mean([
        n.trust for n in nodes
    ])

    context_modifier = {

        "sparse_mode": 0.45,
        "hostile_mode": 0.40,
        "cooperative_mode": 0.60,
        "unstable_mode": 0.50

    }

    influence = context_modifier[context_state]

    for i, node in enumerate(nodes):

        anomaly_scale = (
            1.0
            - 0.18
            * (
                node.anomaly_score
                / (1.0 + node.anomaly_score)
            )
        )

        new_trust = (
            (1 - TRUST_DECAY) * node.trust
            + influence * (target[i] - node.trust)
            + 0.10 * (node.trust - mean_trust)
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

def propagate_essences(nodes, context_state):

    context_scale = {

        "sparse_mode": 0.03,
        "hostile_mode": 0.08,
        "cooperative_mode": 0.05,
        "unstable_mode": 0.10

    }

    local_scale = context_scale[context_state]

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
                    local_scale
                    * (
                        src
                        - node.essences[i]
                    )
                )

            elif sim > 0.85:

                node.essences[i] -= (
                    local_scale
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

def rewire(nodes, context_state):

    previous = {
        n.id: copy.deepcopy(n.connections)
        for n in nodes
    }

    density_limit = {

        "sparse_mode": 2,
        "hostile_mode": 3,
        "cooperative_mode": 4,
        "unstable_mode": 4

    }

    allowed_connections = density_limit[
        context_state
    ]

    rewiring_change = 0

    for node in nodes:

        candidates = [
            n for n in nodes
            if n.id != node.id
        ]

        scored = []

        for c in candidates:

            sim = similarity(
                node.essences,
                c.essences
            )

            score = (
                0.55 * c.trust
                + 0.45 * sim
            )

            if context_state == "hostile_mode":

                score -= (
                    0.10 * c.anomaly_score
                )

            elif context_state == "cooperative_mode":

                score += (
                    0.08 * len(c.connections)
                )

            elif context_state == "unstable_mode":

                score += random.uniform(
                    -0.15,
                    0.15
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

        node.connections = set(
            c.id
            for c in selected[:allowed_connections]
        )

        overlap = len(
            previous[node.id]
            & node.connections
        )

        if overlap >= max(
            1,
            allowed_connections - 1
        ):

            node.persistence_counter += 1

        rewiring_change += len(
            previous[node.id]
            ^ node.connections
        )

    return rewiring_change

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
            / (mean_variance + 1e-8)
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
# global memory
# =========================================================

context_memory = {}

successful_topology_memory = []

topology_history = []

cause_memory = []

collapse_events = 0

context_switch_count = 0

context_reuse_count = 0

successful_context_recovery = 0

# =========================================================
# topology metrics
# =========================================================

def topology_density(nodes):

    total_possible = (
        NODE_COUNT
        * (NODE_COUNT - 1)
    )

    active = sum(
        len(n.connections)
        for n in nodes
    )

    return active / (total_possible + 1e-8)

def cluster_pattern(nodes):

    return sorted([
        len(n.connections)
        for n in nodes
    ])

# =========================================================
# topology history
# =========================================================

def record_topology(
    nodes,
    step,
    context_state
):

    global collapse_events

    degree_distribution = [
        len(n.connections)
        for n in nodes
    ]

    topology_history.append({

        "step": step,

        "context": context_state,

        "connections": [
            sorted(list(n.connections))
            for n in nodes
        ],

        "degree_distribution":
        degree_distribution,

        "trust_distribution": [
            round(n.trust, 3)
            for n in nodes
        ],

        "persistence": [
            n.persistence_counter
            for n in nodes
        ]
    })

    if min(degree_distribution) <= 1:

        collapse_events += 1

# =========================================================
# causal memory
# =========================================================

def record_cause_memory(
    nodes,
    step,
    context_state,
    rewiring_change
):

    density = topology_density(nodes)

    event = []

    if rewiring_change > 10:
        event.append("rewiring")

    if any(n.is_anomaly for n in nodes):
        event.append("anomaly_detection")

    if density < 0.20:
        event.append("collapse")

    if np.std([
        n.trust for n in nodes
    ]) > 0.15:
        event.append("trust_shift")

    if np.mean([
        n.persistence_counter
        for n in nodes
    ]) > 10:
        event.append("persistence_gain")

    if len(event) == 0:
        event.append("stable_transition")

    cause_memory.append({

        "step": step,

        "context": context_state,

        "cause_event": event,

        "effect_topology": {

            "degree_distribution": [
                len(n.connections)
                for n in nodes
            ],

            "active_connections": [
                sorted(list(n.connections))
                for n in nodes
            ],

            "topology_density": density,

            "cluster_pattern":
            cluster_pattern(nodes)
        },

        "survival_delta": {

            "trust_stability":
            float(np.std([
                n.trust for n in nodes
            ])),

            "persistence_increase":
            float(np.mean([
                n.persistence_counter
                for n in nodes
            ])),

            "variance_stability":
            float(np.mean(np.var(
                np.array([
                    e
                    for n in nodes
                    for e in n.essences
                ]),
                axis=0
            )))
        }
    })

# =========================================================
# successful topology
# =========================================================

def save_successful_topology(
    nodes,
    context_state
):

    density = topology_density(nodes)

    if 0.20 <= density <= 0.45:

        successful_topology_memory.append({

            "context": context_state,

            "connections": [
                copy.deepcopy(n.connections)
                for n in nodes
            ],

            "trust_distribution": [
                n.trust for n in nodes
            ],

            "persistence": [
                n.persistence_counter
                for n in nodes
            ],

            "topology_density": density,

            "cluster_pattern":
            cluster_pattern(nodes)
        })

# =========================================================
# context reactivation
# =========================================================

def context_reactivation(
    nodes,
    context_state
):

    global context_reuse_count
    global successful_context_recovery

    if context_state not in context_memory:
        return

    if random.random() < 0.15:

        memory = context_memory[
            context_state
        ]

        restored = memory["connections"]

        for i, node in enumerate(nodes):

            node.connections = set(
                list(restored[i])[:MAX_CONNECTIONS]
            )

            node.persistence_counter += 1

        context_reuse_count += 1

        successful_context_recovery += 1

# =========================================================
# context memory update
# =========================================================

def update_context_memory(
    nodes,
    context_state
):

    context_memory[context_state] = {

        "connections": [
            copy.deepcopy(n.connections)
            for n in nodes
        ],

        "trust_profile": [
            n.trust for n in nodes
        ],

        "cluster_pattern":
        cluster_pattern(nodes),

        "rewiring_preference":
        topology_density(nodes)
    }

# =========================================================
# metrics
# =========================================================

def compute_metrics(nodes):

    all_vectors = np.array([

        e

        for n in nodes

        for e in n.essences

    ])

    mean_variance = float(
        np.mean(np.var(
            all_vectors,
            axis=0
        ))
    )

    trust_values = [
        n.trust for n in nodes
    ]

    patterns = {

        tuple(sorted(list(n.connections)))

        for n in nodes

    }

    average_persistence = np.mean([

        min(n.persistence_counter, 80)

        for n in nodes

    ])

    return {

        "history_length":
        len(topology_history),

        "cause_memory_length":
        len(cause_memory),

        "successful_memory_count":
        len(successful_topology_memory),

        "context_switch_count":
        context_switch_count,

        "unique_context_count":
        len(context_memory),

        "context_reuse_count":
        context_reuse_count,

        "successful_context_recovery":
        successful_context_recovery,

        "context_integrity":
        len(context_memory) >= 4,

        "historical_adaptation":
        context_reuse_count > 0,

        "structural_diversity":
        round(
            float(len(patterns) / NODE_COUNT),
            6
        ),

        "average_persistence":
        round(
            float(average_persistence),
            6
        ),

        "simulation_stability":
        0.02 <= mean_variance <= 0.06,

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
# validation
# =========================================================

def validate(metrics):

    return (

        metrics["history_length"] >= 120

        and metrics["cause_memory_length"] >= 120

        and metrics["successful_memory_count"] >= 10

        and metrics["context_switch_count"] >= 4

        and metrics["unique_context_count"] >= 4

        and metrics["context_reuse_count"] >= 1

        and metrics["successful_context_recovery"] >= 1

        and metrics["context_integrity"] is True

        and metrics["historical_adaptation"] is True

        and metrics["structural_diversity"] >= 0.35

        and 5.0 <= metrics["average_persistence"] <= 80.0

        and metrics["simulation_stability"] is True

        and 0.02 <= metrics["mean_variance"] <= 0.06

        and 0.15 <= metrics["trust_range"] <= 0.85

    )

# =========================================================
# simulation
# =========================================================

def run_simulation(run_id):

    global topology_history
    global cause_memory
    global collapse_events

    global successful_topology_memory

    global context_memory

    global context_switch_count
    global context_reuse_count
    global successful_context_recovery

    topology_history = []

    cause_memory = []

    collapse_events = 0

    successful_topology_memory = []

    context_memory = {}

    context_switch_count = 0

    context_reuse_count = 0

    successful_context_recovery = 0

    current_seed = BASE_SEED + run_id

    random.seed(current_seed)

    np.random.seed(current_seed)

    nodes = [
        Node(i)
        for i in range(NODE_COUNT)
    ]

    current_context = CONTEXTS[0]

    # initial registration

    update_context_memory(
        nodes,
        current_context
    )

    for step in range(STEP_COUNT):

        # deterministic rotation fix

        if step % 150 == 0 and step > 0:

            context_index = (
                (step // 150)
                % len(CONTEXTS)
            )

            current_context = CONTEXTS[
                context_index
            ]

            context_switch_count += 1

        for n in nodes:

            n.age += 1

            mine_pow(n)

        detect_anomaly(nodes)

        update_trust(
            nodes,
            current_context
        )

        propagate_essences(
            nodes,
            current_context
        )

        rewiring_change = rewire(
            nodes,
            current_context
        )

        regulate_variance(nodes)

        context_reactivation(
            nodes,
            current_context
        )

        update_context_memory(
            nodes,
            current_context
        )

        save_successful_topology(
            nodes,
            current_context
        )

        if step % HISTORY_INTERVAL == 0:

            record_topology(
                nodes,
                step,
                current_context
            )

            record_cause_memory(
                nodes,
                step,
                current_context,
                rewiring_change
            )

    metrics = compute_metrics(nodes)

    result = validate(metrics)

    print(f"\n--- RUN #{run_id + 1} ---")

    ordered_keys = [

        "history_length",
        "cause_memory_length",
        "successful_memory_count",
        "context_switch_count",
        "unique_context_count",
        "context_reuse_count",
        "successful_context_recovery",
        "context_integrity",
        "historical_adaptation",
        "structural_diversity",
        "average_persistence",
        "simulation_stability",
        "mean_variance",
        "trust_range"

    ]

    for k in ordered_keys:

        print(f"{k}: {metrics[k]}")

    print(
        "validation_result:",
        result
    )

    return result

# =========================================================
# triple execution
# =========================================================

results = []

for run_id in range(3):

    results.append(
        run_simulation(run_id)
    )

print("\nfinal_result:")

if all(results):

    print("ACHIEVED")

else:

    print("NOT ACHIEVED")
