def cook_time_seconds(cook_speed: int) -> int:
    """Время на 1 патоген в секундах. cook_speed 0..100 → 3600..30."""
    if cook_speed < 0:
        cook_speed = 0
    if cook_speed > 100:
        cook_speed = 100
    return int(3600 - 3570 * (cook_speed / 100))
