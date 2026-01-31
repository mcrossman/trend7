# Core algorithms and utilities


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    k: int = 60
) -> dict[str, float]:
    """
    Reciprocal Rank Fusion (RRF) for combining multiple rankings.
    
    RRF score = sum(1 / (k + rank)) for each ranking
    
    Args:
        rankings: List of rankings, each a list of item IDs in order
        k: Constant to prevent high rankings from dominating (default: 60)
    
    Returns:
        Dictionary mapping item IDs to their RRF scores
    """
    scores: dict[str, float] = {}
    
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            if item_id not in scores:
                scores[item_id] = 0.0
            scores[item_id] += 1.0 / (k + rank)
    
    return scores


def calculate_similarity(
    vec1: list[float],
    vec2: list[float]
) -> float:
    """
    Calculate cosine similarity between two vectors.
    """
    import math
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)
