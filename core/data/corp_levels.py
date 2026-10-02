"""Уровни корпорации."""

MAX_CORP_LEVEL = 5

# level_to: {infected, resources, reward_type, reward_value}
# reward_type: 'resources' | 'exp' | 'epicoins'
CORP_LEVELS: dict[int, dict] = {
    1: {'infected': 20_000,   'resources': 250_000_000,   'reward': ('resources', 300_000)},
    2: {'infected': 35_000,   'resources': 400_000_000,   'reward': ('exp', 5)},
    3: {'infected': 50_000,   'resources': 750_000_000,   'reward': ('epicoins', 1000)},
    4: {'infected': 75_000,   'resources': 1_000_000_000, 'reward': ('exp', 5)},
    5: {'infected': 150_000,  'resources': 2_000_000_000, 'reward': ('exp', 10)},
}


def exp_bonus_for_level(level: int) -> int:
    """Суммарный % бонуса к опыту при заражении. Макс 20%."""
    total = 0
    if level >= 2:
        total += 5
    if level >= 4:
        total += 5
    if level >= 5:
        total += 10
    return min(total, 20)
