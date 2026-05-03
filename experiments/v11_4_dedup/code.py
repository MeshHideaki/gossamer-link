import numpy as np
import random

NUM_ROLES = 3
MAX_CONNECTIONS = 4
SEARCH_K = 5
ESSENCE_SLOTS = 3

class Node:
    def __init__(self, id, dim=8):
        self.id = id
        self.essences = [self._normalize(np.random.randn(dim)) for _ in range(ESSENCE_SLOTS)]
        self.trust = 0.5
        self.role = np.random.randint(0, NUM_ROLES)
        self.connections = set()
        self.in_deg = 0

    def _normalize(self, x):
        return x / (np.linalg.norm(x) + 1e-8)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

def essence_similarity(node_a, node_b):
    return max(
        cosine_similarity(ea, eb)
        for ea in node_a.essences
        for eb in node_b.essences
    )

# ===== 改良：重複排除（安定補完付き）=====
def global_dedup(nodes):
    all_vectors = []

    for node in nodes:
        new_ess = []

        for e in node.essences:
            duplicate = False
            for existing in all_vectors:
                if cosine_similarity(e, existing) > 0.9:
                    duplicate = True
                    break

            if not duplicate:
                new_ess.append(e)
                all_vectors.append(e)

        # ★ 改良：ランダム補充を廃止し、近傍平均で補完
        while len(new_ess) < ESSENCE_SLOTS:
            if all_vectors:
                base = random.choice(all_vectors)
                noise = np.random.randn(len(base)) * 0.02
                new_vec = base + noise
                new_vec = new_vec / (np.linalg.norm(new_vec) + 1e-8)
                new_ess.append(new_vec)
            else:
                new_ess.append(node._normalize(np.random.randn(len(node.essences[0]))))

        node.essences = new_ess[:ESSENCE_SLOTS]

# ===== 検索 =====
def search_nodes(node, nodes):
    candidates = [n for n in nodes if n.id != node.id]

    scored = []
    for n in candidates:
        sim = essence_similarity(node, n)
        score = 0.6 * n.trust + 0.4 * sim
        scored.append((score, n))

    scored.sort(reverse=True, key=lambda x: x[0])

    selected = []
    for _, n in scored:
        if len(selected) >= SEARCH_K:
            break
        if all(essence_similarity(n, s) < 0.8 for s in selected):
            selected.append(n)

    while len(selected) < SEARCH_K:
        cand = random.choice(candidates)
        if cand not in selected:
            selected.append(cand)

    return selected

def compress_essences(node):
    new_ess = []
    for e in node.essences:
        if all(cosine_similarity(e, ne) < 0.85 for ne in new_ess):
            new_ess.append(e)

    while len(new_ess) < ESSENCE_SLOTS:
        base = random.choice(new_ess) if new_ess else np.random.randn(len(node.essences[0]))
        noise = np.random.randn(len(base)) * 0.02
        vec = base + noise
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        new_ess.append(vec)

    node.essences = new_ess[:ESSENCE_SLOTS]

def enforce_structure(node):
    for i in range(len(node.essences)):
        for j in range(i+1, len(node.essences)):
            sim = cosine_similarity(node.essences[i], node.essences[j])
            if sim > 0.75:
                diff = node.essences[i] - node.essences[j]
                node.essences[i] += 0.05 * diff
                node.essences[j] -= 0.05 * diff
                node.essences[i] /= (np.linalg.norm(node.essences[i]) + 1e-8)
                node.essences[j] /= (np.linalg.norm(node.essences[j]) + 1e-8)

def update_connections(nodes):
    for n in nodes:
        n.in_deg = 0

    incoming = {n.id: 0 for n in nodes}

    for node in nodes:
        targets = search_nodes(node, nodes)[:MAX_CONNECTIONS]
        node.connections = set([n.id for n in targets])

        for t in node.connections:
            incoming[t] += 1
            nodes[t].in_deg += 1

    for node in nodes:
        adjusted = set()
        for t in node.connections:
            penalty = incoming[t] / len(nodes)
            if random.random() > penalty:
                adjusted.add(t)

        while len(adjusted) < MAX_CONNECTIONS:
            cand = [n.id for n in nodes if n.id != node.id and n.id not in adjusted]
            if not cand:
                break
            adjusted.add(random.choice(cand))

        node.connections = adjusted

def get_neighbors(node, nodes):
    return [nodes[i] for i in node.connections]

def update_trust(nodes, neighbors_dict):
    scores = []

    for node in nodes:
        neighbors = neighbors_dict[node.id]
        sims = [essence_similarity(node, n) for n in neighbors] if neighbors else [0.5]
        scores.append(np.mean(sims))

    scores = np.array(scores)
    rel = scores - np.mean(scores)
    rel /= (np.std(rel) + 1e-8)

    for i, node in enumerate(nodes):
        node.trust = float(np.clip(
            0.6 * node.trust +
            0.4 * (0.5 + 0.3 * rel[i]),
            0.05, 1.0
        ))

def propagate(node, neighbors):
    if not neighbors:
        return

    for n in neighbors:
        for i in range(len(n.essences)):
            src = random.choice(node.essences)
            sim = cosine_similarity(n.essences[i], src)

            if sim < 0.6:
                n.essences[i] += 0.05 * (src - n.essences[i])
            elif sim > 0.85:
                n.essences[i] -= 0.05 * (src - n.essences[i])

            n.essences[i] /= (np.linalg.norm(n.essences[i]) + 1e-8)

def step(nodes):
    update_connections(nodes)
    neighbors_dict = {n.id: get_neighbors(n, nodes) for n in nodes}
    update_trust(nodes, neighbors_dict)

    for node in nodes:
        propagate(node, neighbors_dict[node.id])
        enforce_structure(node)
        compress_essences(node)

    global_dedup(nodes)

nodes = [Node(i) for i in range(10)]

for _ in range(400):
    step(nodes)

all_ess = []
for n in nodes:
    all_ess.extend(n.essences)

essences = np.array(all_ess)
variances = np.var(essences, axis=0)

print("平均分散:", float(np.mean(variances)))
print("信頼スコア:", [round(n.trust, 3) for n in nodes])
print("役割:", [n.role for n in nodes])
print("接続:", [list(n.connections) for n in nodes])
