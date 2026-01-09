"""Fingerprint Matching Utilities"""


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance (number of insertions, deletions, substitutions)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def calculate_similarity(fp1: str, fp2: str) -> float:
    """
    Calculate similarity between two fingerprints using Levenshtein distance
    
    Args:
        fp1: First fingerprint
        fp2: Second fingerprint
        
    Returns:
        Similarity score between 0.0 (completely different) and 1.0 (identical)
    """
    if not fp1 or not fp2:
        return 0.0
    
    if fp1 == fp2:
        return 1.0
    
    # Calculate edit distance
    distance = levenshtein_distance(fp1, fp2)
    max_len = max(len(fp1), len(fp2))
    
    # Convert to similarity score (1.0 = identical, 0.0 = completely different)
    similarity = 1.0 - (distance / max_len)
    
    return similarity
