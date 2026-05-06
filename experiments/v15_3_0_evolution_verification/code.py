# v15.3.0 evolution verification (final MVP verification)

import numpy as np
import hashlib
import random

# ============================================
# reproducibility
# ============================================

SEED = 77
np.random.seed(SEED)
random.seed(SEED)

# ============================================
# constants
# ============================================

NODE_COUNT = 12
DIM = 8

STEP_COUNT = 1200

MAX_CONNECTIONS = 4
SEARCH_K = 5

ESSENCE_SLOTS = 3

TRUST_DECAY = 0.02

POW_DIFFICULTY = 2

ANOMALY_Z = 1.2
ANOMALY_WEIGHT = 0.02

HUMAN_FEEDBACK_WEIGHT = 0.02

UPDATE_SCALE = 0.055

EMA_ALPHA = 0.16

TARGET_VAR_MIN = 0.02
TARGET_VAR_MAX = 0.06

# ============================================
# node
# ============================================

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

        self.trust = np.random.uniform(
            0.35,
            0.65
        )

        self.connections = set()

        self.prev_connections = set()

        self.age = 1
        self.nonce = 0

        self.anomaly_score = 0.0
        self.is_anomaly = False

        self.eval_memory = np.zeros(DIM)

# ============================================
# utilities
# ============================================

def normalize(v):
    return v / (np.linalg.norm(v) + 1e-8)

def compute_hash(v):
    return hashlib.sha256(
        str(v).encode()
    ).hexdigest()

def valid_pow(node):
    return compute_hash(
        (node.id, node.nonce)
    ).startswith(
        "0" * POW_DIFFICULTY
    )

def mine_pow(node):

    if valid_pow(node):
        return

    while not valid_pow(node):
        node.nonce += 1

def sim(a, b):
    return np.max(np.dot(a, b.T))

# ============================================
# preprocess
# ============================================

def preprocess(text):

    vec = np.zeros(DIM)

    if len(text) == 0:
        return normalize(vec + 1e-8)

    for i, ch in enumerate(text):

        idx = i % DIM

        vec[idx] += (
            (ord(ch) % 97) / 96.0
        )

    return normalize(vec)

# ============================================
# anomaly detection
# ============================================

def detect_anomaly(nodes):

    vals = np.array([
        n.trust for n in nodes
    ])

    mean = np.mean(vals)
    std = np.std(vals) + 1e-8

    for i, n in enumerate(nodes):

        z = abs(
            (vals[i] - mean) / std
        )

        n.anomaly_score = float(z)

        n.is_anomaly = z > ANOMALY_Z

# ============================================
# trust update
# ============================================

def update_trust(nodes):

    scores = []

    for n in nodes:

        neighbors = [
            nodes[i]
            for i in n.connections
        ]

        if neighbors:

            sims = [
                sim(
                    n.essences,
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
        ranks / (len(nodes) - 1 + 1e-8)
    )

    target = 0.05 + 0.90 * target

    mean_trust = np.mean([
        n.trust for n in nodes
    ])

    for i, n in enumerate(nodes):

        anomaly_scale = (
            1.0
            - ANOMALY_WEIGHT
            * (
                n.anomaly_score
                / (1.0 + n.anomaly_score)
            )
        )

        new_trust = (
            (1.0 - TRUST_DECAY)
            * n.trust
            + 0.34
            * (target[i] - n.trust)
            + 0.09
            * (n.trust - mean_trust)
        )

        new_trust *= anomaly_scale

        n.trust = float(
            np.clip(
                new_trust,
                0.05,
                0.95
            )
        )

# ============================================
# essence evolution
# ============================================

def evolve_essences(
    nodes,
    human_vector
):

    for node in nodes:

        neighbors = [
            nodes[i]
            for i in node.connections
        ]

        if not neighbors:
            continue

        node.eval_memory = (
            (1.0 - EMA_ALPHA)
            * node.eval_memory
            + EMA_ALPHA
            * human_vector
        )

        for i in range(ESSENCE_SLOTS):

            src_node = random.choice(
                neighbors
            )

            src = src_node.essences[
                random.randrange(
                    ESSENCE_SLOTS
                )
            ]

            influence = (
                (1.0 - HUMAN_FEEDBACK_WEIGHT)
                * src
                + HUMAN_FEEDBACK_WEIGHT
                * node.eval_memory
            )

            influence = normalize(influence)

            similarity = np.dot(
                node.essences[i],
                influence
            )

            if similarity < 0.6:

                node.essences[i] += (
                    UPDATE_SCALE
                    * (
                        influence
                        - node.essences[i]
                    )
                )

            elif similarity > 0.85:

                node.essences[i] -= (
                    UPDATE_SCALE
                    * 0.5
                    * (
                        influence
                        - node.essences[i]
                    )
                )

            node.essences[i] = normalize(
                node.essences[i]
            )

# ============================================
# rewiring
# ============================================

def rewire(nodes):

    rewired = 0
    total = 0

    for node in nodes:

        node.prev_connections = set(
            node.connections
        )

        candidates = [
            n for n in nodes
            if n.id != node.id
        ]

        scored = []

        for cand in candidates:

            s = sim(
                node.essences,
                cand.essences
            )

            score = (
                0.6 * cand.trust
                + 0.4 * s
            )

            if cand.is_anomaly:
                score *= 0.92

            scored.append(
                (score, cand)
            )

        scored.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        selected = []

        for _, cand in scored:

            if len(selected) >= SEARCH_K:
                break

            if all(
                sim(
                    cand.essences,
                    s.essences
                ) < 0.78
                for s in selected
            ):
                selected.append(cand)

        while len(selected) < SEARCH_K:

            c = random.choice(
                candidates
            )

            if c not in selected:
                selected.append(c)

        node.connections = set(
            c.id
            for c in selected[:MAX_CONNECTIONS]
        )

        rewired += len(
            node.connections.symmetric_difference(
                node.prev_connections
            )
        )

        total += MAX_CONNECTIONS

    return rewired / (total + 1e-8)

# ============================================
# variance regulation
# ============================================

def regulate_variance(nodes):

    all_vecs = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    variances = np.var(
        all_vecs,
        axis=0
    )

    mean_var = float(
        np.mean(variances)
    )

    if mean_var > TARGET_VAR_MAX:

        scale = np.sqrt(
            TARGET_VAR_MAX
            / (mean_var + 1e-8)
        )

        for n in nodes:
            n.essences *= scale

    elif mean_var < TARGET_VAR_MIN:

        for n in nodes:

            noise = (
                np.random.randn(
                    ESSENCE_SLOTS,
                    DIM
                ) * 0.02
            )

            n.essences += noise

            n.essences /= (
                np.linalg.norm(
                    n.essences,
                    axis=1,
                    keepdims=True
                ) + 1e-8
            )

# ============================================
# disturbance injection
# ============================================

def inject_disturbance(
    nodes,
    step
):

    # random spike

    if step == 400:

        for n in random.sample(
            nodes,
            3
        ):

            n.trust = np.clip(
                n.trust
                + np.random.uniform(
                    -0.25,
                    0.25
                ),
                0.05,
                0.95
            )

    # anomaly injection

    if step == 700:

        target = random.choice(nodes)

        target.essences += (
            np.random.randn(
                ESSENCE_SLOTS,
                DIM
            ) * 0.8
        )

        target.essences /= (
            np.linalg.norm(
                target.essences,
                axis=1,
                keepdims=True
            ) + 1e-8
        )

    # connection disruption

    if step == 900:

        for n in random.sample(
            nodes,
            4
        ):
            n.connections = set()

# ============================================
# metrics
# ============================================

def compute_metrics(
    nodes,
    rewiring_history
):

    essences = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    mean_variance = float(
        np.mean(
            np.var(
                essences,
                axis=0
            )
        )
    )

    trusts = np.array([
        n.trust for n in nodes
    ])

    trust_range = float(
        np.max(trusts)
        - np.min(trusts)
    )

    trust_saturation = bool(
        np.any(trusts >= 0.999)
        or np.std(trusts) < 0.01
    )

    conn_vectors = []

    for n in nodes:

        vec = np.zeros(NODE_COUNT)

        for c in n.connections:
            vec[c] = 1.0

        conn_vectors.append(vec)

    conn_vectors = np.array(
        conn_vectors
    )

    structural_diversity = float(
        np.mean(
            np.var(
                conn_vectors,
                axis=0
            )
        )
    )

    in_deg = np.zeros(NODE_COUNT)

    for n in nodes:
        for c in n.connections:
            in_deg[c] += 1

    dominance_ratio = float(
        np.max(in_deg)
        / np.sum(in_deg)
    )

    rewiring_rate = float(
        np.mean(rewiring_history)
    )

    validation = (
        (0.02 <= mean_variance <= 0.06)
        and (trust_range >= 0.20)
        and (structural_diversity >= 0.10)
        and (dominance_ratio < 0.50)
        and (rewiring_rate >= 0.20)
        and (not trust_saturation)
    )

    return {
        "mean_variance": round(
            mean_variance,
            6
        ),
        "trust_range": round(
            trust_range,
            6
        ),
        "structural_diversity": round(
            structural_diversity,
            6
        ),
        "dominance_ratio": round(
            dominance_ratio,
            6
        ),
        "rewiring_rate": round(
            rewiring_rate,
            6
        ),
        "trust_saturation": (
            trust_saturation
        ),
        "validation_result": (
            validation
        ),
        "final_result": (
            "achieved"
            if validation
            else "not achieved"
        )
    }

# ============================================
# stimuli
# ============================================

stimuli = {
    "Stimulus A":
        "aggressive convergence attack pressure",

    "Stimulus B":
        "evasive divergence isolation drift",

    "Stimulus C":
        "mixed adaptive cooperative conflict"
}

# ============================================
# run
# ============================================

overall = True

for stimulus_name, text in stimuli.items():

    nodes = [
        Node(i)
        for i in range(NODE_COUNT)
    ]

    rewiring_history = []

    for step in range(STEP_COUNT):

        for n in nodes:
            n.age += 1
            mine_pow(n)

        # input
        human_vector = preprocess(text)

        # anomaly detection
        detect_anomaly(nodes)

        # trust update
        update_trust(nodes)

        # essence evolution
        evolve_essences(
            nodes,
            human_vector
        )

        # rewiring
        rewiring_rate = rewire(nodes)

        rewiring_history.append(
            rewiring_rate
        )

        # disturbance test
        inject_disturbance(
            nodes,
            step
        )

        # variance regulation
        regulate_variance(nodes)

    metrics = compute_metrics(
        nodes,
        rewiring_history
    )

    print("metrics")
    print(
        "stimulus:",
        stimulus_name
    )

    for k, v in metrics.items():
        print(f"{k}: {v}")

    print()

    overall &= metrics[
        "validation_result"
    ]

print(
    "overall_final_result:",
    (
        "achieved"
        if overall
        else "not achieved"
    )
)
