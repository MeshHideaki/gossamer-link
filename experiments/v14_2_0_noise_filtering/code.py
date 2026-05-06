# v14.2.0 noise filtering layer
# EMA smoothing + spike suppression + signal preservation

import numpy as np
import hashlib
import random

# ============================================
# constants
# ============================================

NUM_ROLES = 3
MAX_CONNECTIONS = 4
SEARCH_K = 5
ESSENCE_SLOTS = 3

POW_DIFFICULTY = 2

TRUST_DECAY = 0.02

MIN_TRUST = 0.05
MAX_TRUST = 0.95

ANOMALY_Z = 1.1
ANOMALY_WEIGHT = 0.25

TARGET_VAR_MAX = 0.06
UPDATE_SCALE = 0.5

INPUT_DIM = 8
EPS = 1e-8

# v14.2.0
EMA_ALPHA = 0.18
SPIKE_THRESHOLD = 2.2
SPIKE_SUPPRESSION = 0.35

# ============================================
# preprocessor
# ============================================

class HumanPreprocessor:

    def preprocess(self, raw_input):

        x = np.array(raw_input, dtype=np.float64)

        if x.shape != (INPUT_DIM,):

            padded = np.zeros(INPUT_DIM)

            usable = min(len(x), INPUT_DIM)

            padded[:usable] = x[:usable]

            x = padded

        x = np.nan_to_num(
            x,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        norm = np.linalg.norm(x)

        if norm < EPS:

            x = np.zeros(INPUT_DIM)
            x[0] = 1.0

            norm = np.linalg.norm(x)

        x = x / (norm + EPS)

        return x


# ============================================
# noise filter
# ============================================

class NoiseFilter:

    def __init__(self):

        self.ema_state = np.zeros(INPUT_DIM)

    def filter(self, x):

        x = np.array(x, dtype=np.float64)

        deviation = np.linalg.norm(
            x - self.ema_state
        )

        spike_detected = (
            deviation > SPIKE_THRESHOLD
        )

        filtered = (
            EMA_ALPHA * x
            + (1.0 - EMA_ALPHA)
            * self.ema_state
        )

        if spike_detected:

            filtered = (
                SPIKE_SUPPRESSION * filtered
                + (1.0 - SPIKE_SUPPRESSION)
                * self.ema_state
            )

        self.ema_state = filtered.copy()

        norm = np.linalg.norm(filtered)

        if norm < EPS:
            norm = 1.0

        filtered /= norm

        return filtered, spike_detected


# ============================================
# node
# ============================================

class Node:

    def __init__(self, id, dim=8):

        self.id = id

        self.essences = np.random.randn(
            ESSENCE_SLOTS,
            dim
        )

        self.essences /= (
            np.linalg.norm(
                self.essences,
                axis=1,
                keepdims=True
            ) + EPS
        )

        self.trust = 0.5

        self.role = np.random.randint(
            0,
            NUM_ROLES
        )

        self.connections = set()

        self.age = 1

        self.nonce = 0

        self.anomaly_score = 0.0
        self.is_anomaly = False


# ============================================
# utility
# ============================================

def compute_hash(val):

    return hashlib.sha256(
        str(val).encode()
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

    return np.max(
        np.dot(a, b.T)
    )


# ============================================
# anomaly detection
# ============================================

def detect_anomaly(nodes):

    vals = np.array([
        n.trust for n in nodes
    ])

    mean = np.mean(vals)

    std = np.std(vals) + EPS

    for i, n in enumerate(nodes):

        z = abs(
            (vals[i] - mean) / std
        )

        n.anomaly_score = float(z)

        n.is_anomaly = (
            z > ANOMALY_Z
        )


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
                sim(n.essences, nb.essences)
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
        ranks / (len(nodes) - 1 + EPS)
    )

    target = (
        MIN_TRUST
        + (MAX_TRUST - MIN_TRUST)
        * target
    )

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

            + 0.55
            * (target[i] - n.trust)

            + 0.12
            * (n.trust - mean_trust)
        )

        new_trust *= anomaly_scale

        if new_trust <= MIN_TRUST:

            new_trust = (
                MIN_TRUST
                + 0.02 * random.random()
            )

        n.trust = float(
            np.clip(
                new_trust,
                MIN_TRUST,
                MAX_TRUST
            )
        )


# ============================================
# essence update
# ============================================

def update_essences(nodes):

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

            sim_val = np.dot(
                node.essences[i],
                src
            )

            if sim_val < 0.6:

                node.essences[i] += (
                    UPDATE_SCALE
                    * 0.08
                    * (
                        src
                        - node.essences[i]
                    )
                )

            elif sim_val > 0.85:

                node.essences[i] -= (
                    UPDATE_SCALE
                    * 0.04
                    * (
                        src
                        - node.essences[i]
                    )
                )

            node.essences[i] /= (
                np.linalg.norm(
                    node.essences[i]
                ) + EPS
            )


# ============================================
# variance clamp
# ============================================

def clamp_variance(nodes):

    all_vecs = np.array([
        e
        for n in nodes
        for e in n.essences
    ])

    var = np.var(
        all_vecs,
        axis=0
    )

    mean_var = np.mean(var)

    if mean_var > TARGET_VAR_MAX:

        scale = np.sqrt(
            TARGET_VAR_MAX
            / (mean_var + EPS)
        )

        for n in nodes:
            n.essences *= scale


# ============================================
# network step
# ============================================

def step(nodes):

    for n in nodes:

        n.age += 1

        mine_pow(n)

    detect_anomaly(nodes)

    for node in nodes:

        candidates = [
            n for n in nodes
            if n.id != node.id
        ]

        scored = []

        for c in candidates:

            s = sim(
                node.essences,
                c.essences
            )

            score = (
                0.6 * c.trust
                + 0.4 * s
            )

            scored.append(
                (score, c)
            )

        scored.sort(
            reverse=True,
            key=lambda x: x[0]
        )

        selected = []

        for _, c in scored:

            if len(selected) >= SEARCH_K:
                break

            if all(
                sim(
                    c.essences,
                    s.essences
                ) < 0.7
                for s in selected
            ):
                selected.append(c)

        while len(selected) < SEARCH_K:

            c = random.choice(
                candidates
            )

            if c not in selected:
                selected.append(c)

        node.connections = {
            c.id
            for c in selected[
                :MAX_CONNECTIONS
            ]
        }

    update_trust(nodes)

    update_essences(nodes)

    clamp_variance(nodes)


# ============================================
# validation
# ============================================

pre = HumanPreprocessor()

noise_filter = NoiseFilter()

# sustained signal
base_signal = np.array([
    0.6,
    -0.4,
    0.8,
    0.3,
    -0.2,
    0.5,
    0.1,
    -0.6
])

# spam spikes
spike_signal = np.array([
    12.0,
    -15.0,
    20.0,
    -18.0,
    16.0,
    -14.0,
    13.0,
    -17.0
])

raw_history = []
filtered_history = []

spike_before = []
spike_after = []

for t in range(120):

    signal = base_signal.copy()

    signal += (
        np.random.randn(INPUT_DIM)
        * 0.12
    )

    if t % 15 == 0:
        signal += spike_signal

    processed = pre.preprocess(signal)

    filtered, spike = noise_filter.filter(
        processed
    )

    raw_history.append(processed)
    filtered_history.append(filtered)

    spike_before.append(
        np.linalg.norm(processed)
    )

    spike_after.append(
        np.linalg.norm(filtered)
    )

raw_history = np.array(raw_history)
filtered_history = np.array(filtered_history)

# ============================================
# metrics
# ============================================

signal_delta_raw = np.mean(
    np.linalg.norm(
        raw_history[1:] - raw_history[:-1],
        axis=1
    )
)

signal_delta_filtered = np.mean(
    np.linalg.norm(
        filtered_history[1:]
        - filtered_history[:-1],
        axis=1
    )
)

spike_reduction_ratio = float(
    1.0
    - (
        signal_delta_filtered
        / (signal_delta_raw + EPS)
    )
)

signal_preservation_ratio = float(
    np.mean(
        np.sum(
            raw_history
            * filtered_history,
            axis=1
        )
    )
)

# ============================================
# network execution
# ============================================

nodes = [
    Node(i)
    for i in range(10)
]

for t in range(400):
    step(nodes)

essences = np.array([
    e
    for n in nodes
    for e in n.essences
])

variances = np.var(
    essences,
    axis=0
)

mean_variance = float(
    np.mean(variances)
)

# ============================================
# validation
# ============================================

achieved = True

if not (
    0.02 <= mean_variance <= 0.06
):
    achieved = False

if spike_reduction_ratio <= 0.5:
    achieved = False

if signal_preservation_ratio <= 0.6:
    achieved = False

# ============================================
# output
# ============================================

print("metrics")

print(
    "mean_variance:",
    round(mean_variance, 6)
)

print(
    "spike_reduction_ratio:",
    round(
        spike_reduction_ratio,
        6
    )
)

print(
    "signal_preservation_ratio:",
    round(
        signal_preservation_ratio,
        6
    )
)

print(
    "validation_result:",
    achieved
)

print(
    "final_result:",
    "achieved"
    if achieved
    else "not achieved"
)
