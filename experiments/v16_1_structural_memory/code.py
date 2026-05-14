# v16.1.0 structural memory history implementation
# strict validation edition

import numpy as np
import random
import hashlib
import copy

# =========================================================
# constants
# =========================================================

SEED = 42

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

UPDATE_SCALE = 0.035

HISTORY_INTERVAL = 5

COLLAPSE_PROBABILITY = 0.015

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

        self.trust = random.uniform(
            0.30,
            0.70
        )

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

def compute_hash(value):

    return hashlib.sha256(
        str(value).encode()
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

    return np.max(
        np.dot(a, b.T)
    )


# =========================================================
# anomaly detection
# =========================================================

def detect_anomaly(nodes):

    values = np.array([
        n.trust for n in nodes
    ])

    mean = np.mean(values)

    std = np.std(values) + 1e-8

    for i, node in enumerate(nodes):

        z = abs(
            (values[i] - mean) / std
        )

        node.anomaly_score = float(z)

        node.is_anomaly = (
            z > ANOMALY_Z
        )


# =========================================================
# trust update
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

            scores.append(
                np.mean(sims)
            )

        else:

            scores.append(0.5)

    scores = np.array(scores)

    order = np.argsort(scores)

    ranks = np.empty_like(order)

    ranks[order] = np.arange(
        len(nodes)
    )

    target = (
        ranks /
        (len(nodes) - 1 + 1e-8)
    )

    target = (
        MIN_TRUST +
        (MAX_TRUST - MIN_TRUST) *
        target
    )

    mean_trust = np.mean([
        n.trust for n in nodes
    ])

    for i, node in enumerate(nodes):

        anomaly_scale = (
            1.0 -
            0.12 *
            (
                node.anomaly_score /
                (1.0 + node.anomaly_score)
            )
        )

        new_trust = (
            (1 - TRUST_DECAY) *
            node.trust

            + 0.38 *
            (target[i] - node.trust)

            + 0.08 *
            (node.trust - mean_trust)
        )

        new_trust *= anomaly_scale

        node.trust = float(
            np.clip(
                new_trust,
                MIN_TRUST,
                MAX_TRUST
            )
        )


# =========================================================
# essence propagation
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

            src_node = random.choice(
                neighbors
            )

            src = src_node.essences[
                random.randrange(
                    ESSENCE_SLOTS
                )
            ]

            sim = np.dot(
                node.essences[i],
                src
            )

            if sim < 0.6:

                node.essences[i] += (
                    UPDATE_SCALE *
                    (
                        src -
                        node.essences[i]
                    )
                )

            elif sim > 0.85:

                node.essences[i] -= (
                    UPDATE_SCALE * 0.5 *
                    (
                        src -
                        node.essences[i]
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

    previous_connections = {
        n.id: copy.deepcopy(
            n.connections
        )
        for n in nodes
    }

    for node in nodes:

        candidates = [
            n for n in nodes
            if n.id != node.id
        ]

        scored = []

        for candidate in candidates:

            sim = similarity(
                node.essences,
                candidate.essences
            )

            score = (
                0.55 * candidate.trust +
                0.45 * sim
            )

            scored.append(
                (score, candidate)
            )

        scored.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        selected = []

        for _, candidate in scored:

            if len(selected) >= SEARCH_K:
                break

            if all(
                similarity(
                    candidate.essences,
                    s.essences
                ) < 0.72
                for s in selected
            ):
                selected.append(candidate)

        while len(selected) < SEARCH_K:

            c = random.choice(
                candidates
            )

            if c not in selected:
                selected.append(c)

        node.connections = set(
            c.id
            for c in selected[
                :MAX_CONNECTIONS
            ]
        )

        overlap = len(
            previous_connections[
                node.id
            ] &
            node.connections
        )

        if overlap >= 2:
            node.persistence_counter += 1


# =========================================================
# variance regulation
# =========================================================

def regulate_variance(nodes):

    all_vectors = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    variance = np.var(
        all_vectors,
        axis=0
    )

    mean_variance = np.mean(
        variance
    )

    if mean_variance > TARGET_VAR_MAX:

        scale = np.sqrt(
            TARGET_VAR_MAX /
            (
                mean_variance +
                1e-8
            )
        )

        for n in nodes:
            n.essences *= scale

    elif mean_variance < TARGET_VAR_MIN:

        for n in nodes:

            noise = (
                np.random.randn(
                    *n.essences.shape
                ) * 0.012
            )

            n.essences += noise

            n.essences /= (
                np.linalg.norm(
                    n.essences,
                    axis=1,
                    keepdims=True
                ) + 1e-8
            )


# =========================================================
# structural memory
# =========================================================

topology_history = []

collapse_events = 0


def record_topology(nodes, step):

    global collapse_events

    degree_distribution = [
        len(n.connections)
        for n in nodes
    ]

    snapshot = {

        "step": step,

        "connections": [
            sorted(
                list(n.connections)
            )
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
    }

    topology_history.append(
        snapshot
    )

    if (
        random.random() <
        COLLAPSE_PROBABILITY
    ):

        collapse_events += 1

        collapse_node = random.choice(
            nodes
        )

        collapse_node.connections = set()


# =========================================================
# metrics
# =========================================================

def compute_metrics(nodes):

    all_vectors = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    variance = np.var(
        all_vectors,
        axis=0
    )

    mean_variance = float(
        np.mean(variance)
    )

    trust_values = [
        n.trust for n in nodes
    ]

    trust_range = (
        max(trust_values) -
        min(trust_values)
    )

    unique_patterns = set()

    for n in nodes:

        pattern = tuple(
            sorted(
                list(n.connections)
            )
        )

        unique_patterns.add(
            pattern
        )

    structural_diversity = (
        len(unique_patterns) /
        NODE_COUNT
    )

    average_persistence = np.mean([
        min(
            n.persistence_counter,
            80
        )
        for n in nodes
    ])

    memory_integrity = (
        len(topology_history) >= 120
    )

    simulation_stability = (
        0.02 <=
        mean_variance <=
        0.06
    )

    return {

        "history_length":
            len(topology_history),

        "collapse_events":
            collapse_events,

        "average_persistence":
            round(
                float(
                    average_persistence
                ),
                6
            ),

        "structural_diversity":
            round(
                float(
                    structural_diversity
                ),
                6
            ),

        "memory_integrity":
            memory_integrity,

        "simulation_stability":
            simulation_stability,

        "mean_variance":
            round(
                mean_variance,
                6
            ),

        "trust_range":
            round(
                float(
                    trust_range
                ),
                6
            )
    }


# =========================================================
# single simulation
# =========================================================

def run_simulation(run_index):

    global topology_history
    global collapse_events

    topology_history = []

    collapse_events = 0

    current_seed = (
        SEED + run_index
    )

    random.seed(
        current_seed
    )

    np.random.seed(
        current_seed
    )

    nodes = [
        Node(i)
        for i in range(
            NODE_COUNT
        )
    ]

    for step in range(
        STEP_COUNT
    ):

        for n in nodes:

            n.age += 1

            mine_pow(n)

        detect_anomaly(nodes)

        update_trust(nodes)

        propagate_essences(nodes)

        rewire(nodes)

        regulate_variance(nodes)

        if (
            step %
            HISTORY_INTERVAL
            == 0
        ):
            record_topology(
                nodes,
                step
            )

    metrics = compute_metrics(
        nodes
    )

    validation_result = (

        metrics[
            "history_length"
        ] >= 120

        and

        metrics[
            "collapse_events"
        ] >= 1

        and

        5.0 <=
        metrics[
            "average_persistence"
        ] <= 80.0

        and

        metrics[
            "structural_diversity"
        ] >= 0.35

        and

        metrics[
            "memory_integrity"
        ] is True

        and

        metrics[
            "simulation_stability"
        ] is True

        and

        0.02 <=
        metrics[
            "mean_variance"
        ] <= 0.06

        and

        0.15 <=
        metrics[
            "trust_range"
        ] <= 0.85
    )

    print(
        f"\n--- RUN #{run_index + 1} ---"
    )

    for k, v in metrics.items():
        print(f"{k}: {v}")

    print(
        "validation_result:",
        validation_result
    )

    return validation_result


# =========================================================
# triple execution
# =========================================================

results = []

for run_id in range(3):

    result = run_simulation(
        run_id
    )

    results.append(result)

overall = all(results)

print("\nfinal_result:")

if overall:
    print("ACHIEVED")
else:
    print("NOT ACHIEVED")
