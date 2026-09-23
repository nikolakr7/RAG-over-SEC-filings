# 1: Loading the files
import json
import numpy as np

emb = np.load("data/primer/embeddings.npy")  # shape (20, 1536)
sentences = json.loads(open("data/primer/sentences.json", encoding="utf-8").read())


# 2: Computing similarity and L2 distance
def cosine(a, b):
    """Compute the cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def l2(a, b):
    """Compute the L2 distance between two vectors."""
    return np.linalg.norm(a - b)


# 3: Displaying the L2 norm of each embedding
# 6 decimals: the vectors are only APPROXIMATELY unit length (float32 +
# API rounding), and that epsilon is what makes the step-6 identity
# hold only to ~3-4 decimals.
for i in range(20):
    print(sentences[i]["id"], f"{np.linalg.norm(emb[i]):.6f}")

norms = np.linalg.norm(emb, axis=1)
worst = np.argsort(np.abs(norms - 1))[::-1][:3]
print("rows furthest from unit length:",
      [(sentences[i]["id"], f"{norms[i]:.6f}") for i in worst])

# 4: building the 20x20 similarity matrix
M = np.zeros((20, 20))
for i in range(20):
    for j in range(20):
        M[i, j] = cosine(emb[i], emb[j])

# print(np.round(M, 2))          # whole table, 2 decimals

# 5: Top 3 neighbours
for i in range(20):
    # get the indices of the top 3 neighbours (excluding itself)
    top3 = np.argsort(M[i])[::-1][1:4]
    # print(f"Top 3 neighbours for {sentences[i]['id']}:")
    # for j in top3:
    # print(f"  {sentences[j]['id']} (similarity: {M[i, j]:.2f})")

# 6: metric equivalence: cosine and L2 must produce the same rankings
anchors = [0, 8, 17]  # A1, D2, H2 (index 8 is D2; earlier comment said D1, trust the data not the comment)

for i in anchors:
    cos_row = np.array([cosine(emb[i], emb[j]) for j in range(20)])
    l2_row = np.array([l2(emb[i], emb[j]) for j in range(20)])

    order_cos = np.argsort(cos_row)[::-1][1:]  # biggest similarity first, skip self
    order_l2 = np.argsort(l2_row)[1:]  # smallest distance first, skip self

    print(
        sentences[i]["id"], "rankings identical:", np.array_equal(order_cos, order_l2)
    )

# the formula behind it: for unit vectors, l2^2 == 2 - 2*cosine.
# Vectors are unit length only to ~1e-4 (see step 3), so the identity
# holds to the same order; atol=1e-3 is the tolerance that matches the
# data's actual precision. np.isclose's DEFAULT (rtol=1e-5) is stricter
# than the data and printed match=False on every pair -- the formula was
# fine, the tolerance was an unexamined opinion.
for i, j in [(0, 1), (3, 4), (5, 6), (8, 9)]:
    lhs = l2(emb[i], emb[j]) ** 2
    rhs = 2 - 2 * cosine(emb[i], emb[j])
    print(
        f"{sentences[i]['id']}-{sentences[j]['id']}: "
        f"l2^2={lhs:.6f}  2-2cos={rhs:.6f}  "
        f"match={np.isclose(lhs, rhs, atol=1e-3)}  "
        f"norms={np.linalg.norm(emb[i]):.6f}/{np.linalg.norm(emb[j]):.6f}"
    )

# 7 / P4: double a vector's length and watch which metric cares
v = 2 * emb[0]
print("cosine(A1, A2) original:", round(cosine(emb[0], emb[1]), 6))
print("cosine(2*A1, A2)       :", round(cosine(v, emb[1]), 6))
print("l2(A1, A2) original    :", round(l2(emb[0], emb[1]), 6))
print("l2(2*A1, A2)           :", round(l2(v, emb[1]), 6))
print(
    "l2^2 =",
    round(l2(v, emb[1]) ** 2, 4),
    "  2-2cos =",
    round(2 - 2 * cosine(v, emb[1]), 4),
)
