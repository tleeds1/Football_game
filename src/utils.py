import math


def distance(p1, p2):
    """Calculate distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
    
    
def normalize(x, y):
    """Normalize a vector."""
    length = math.sqrt(x * x + y * y)
    if length > 0:
        return (x / length, y / length)
    return (0, 0)
    
    
def clamp(value, min_val, max_val):
    """Clamp a value between min and max."""
    return max(min_val, min(value, max_val))
