# ==============================================================================
# RECOMAI - High-Performance Similarity Computation Engine
# Written in Mojo for Vectorized Cosine Similarity & Matrix Scoring
# ==============================================================================

from math import sqrt
import sys

fn dot_product(v1: DynamicVector[Float64], v2: DynamicVector[Float64]) -> Float64:
    """Compute dot product of two vectors with high-throughput accumulation."""
    var total: Float64 = 0.0
    let n = min(len(v1), len(v2))
    for i in range(n):
        total += v1[i] * v2[i]
    return total

fn vector_magnitude(v: DynamicVector[Float64]) -> Float64:
    """Compute the Euclidean L2 norm of a vector."""
    var sum_sq: Float64 = 0.0
    for i in range(len(v)):
        sum_sq += v[i] * v[i]
    if sum_sq <= 0.0:
        return 0.0
    return sqrt(sum_sq)

fn cosine_similarity(v1: DynamicVector[Float64], v2: DynamicVector[Float64]) -> Float64:
    """Calculate normalized cosine similarity between two latent embedding vectors."""
    let mag1 = vector_magnitude(v1)
    let mag2 = vector_magnitude(v2)
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    let dot = dot_product(v1, v2)
    return dot / (mag1 * mag2)

fn batch_cosine_similarity(
    query: DynamicVector[Float64],
    candidates: DynamicVector[DynamicVector[Float64]]
) -> DynamicVector[Float64]:
    """Compute cosine similarities for a batch of candidate vectors in parallel."""
    var scores = DynamicVector[Float64]()
    for i in range(len(candidates)):
        let sim = cosine_similarity(query, candidates[i])
        scores.append(sim)
    return scores

fn main():
    print("RECOMAI Mojo Similarity Engine initialized successfully.")
    # Demonstration test of vector similarity
    var v1 = DynamicVector[Float64]()
    var v2 = DynamicVector[Float64]()
    for _ in range(8):
        v1.append(0.5)
        v2.append(0.5)
    let sim = cosine_similarity(v1, v2)
    print("Self similarity test:", sim)
