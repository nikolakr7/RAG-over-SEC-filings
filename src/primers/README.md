# Embeddings primer (Phase 2, step 1)

Data is ready: `data/primer/embeddings.npy` (20 x 1536 float32) and
`data/primer/sentences.json` (id, group, text; row i of the matrix is
sentence i). Regenerate anytime with
`python src/primers/embed_primer_sentences.py` (564 tokens, ~$0.00001).

## The exercise (write it yourself: numpy only, no sklearn/scipy)

Create `src/primers/similarity_lab.py` that does, in order:

1. Load both files.
2. `cosine(a, b)` and `l2(a, b)` from the raw formulas:
   cosine = dot(a, b) / (norm(a) * norm(b)); l2 = norm(a - b).
   Write them yourself from `np.dot` / `np.linalg.norm`.
3. Print the norm of every vector. (Prediction 4 becomes obvious here.
   What does this imply about cosine vs the plain dot product?)
4. Build the 20x20 cosine matrix. Loops are fine first; then, if you
   want, redo it as one matrix multiplication and check they agree.
5. For each sentence, print its top-3 neighbors (excluding itself) with
   scores, labeled by id so the groups are visible.
6. Verify metric equivalence: for a few anchor sentences, rank all 19
   others by cosine (descending) and by L2 (ascending) and assert the
   orderings are identical. Then verify the formula behind it:
   l2(a, b)^2 is approximately 2 - 2 * cosine(a, b) for unit vectors.
7. Answer the five predictions with real numbers:
   P1  cosine(A1, A2): the near-duplicate auditor sign-offs
   P2  cosine(B1, B2) vs cosine(C1, C2): paraphrase vs negation
   P3  cosine(D1, D2) vs P1: the Merck keyword trap vs true near-dups
   P4  double one vector: cosine unchanged? L2 changed how?
   P5  typical cosine between unrelated pairs (say A1 vs H2, E3 vs H3):
       near 0, ~0.5, or negative?

## Questions to answer in your notes when done

- Where did the negation pair C1/C2 rank among ALL pairs? What does
  that mean for a benchmark question whose answer hinges on "did NOT
  meet its primary endpoint"?
- Did D1/D2 (shared "Merck", different meaning) score above or below
  B1/B2 (same meaning, different words)? Which behavior do you WANT
  from a retriever, and which did you get?
- Look at the single highest off-diagonal pair in the whole matrix. Is
  it the pair you would have predicted?
- Why does the answer to P5 matter when you later pick a similarity
  threshold or interpret pgvector scores?

When your numbers are in, we compare them against the predictions you
wrote down, and then move to chunking.
