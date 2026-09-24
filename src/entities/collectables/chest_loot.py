"""Chest loot table for the interactable chest tile.

Weighted random roll: every chest drop is one of coins, score, full
weapon refill, or heal. Reroll on demand for tests.
"""

import random


# (kind, value, weight). `value` is None for refill (player.reload_weapon
# takes no argument).
CHEST_LOOT_TABLE = (
    ("coins", 5, 50),
    ("score", 200, 25),
    ("refill", None, 15),
    ("heal", 30, 10),
)


def roll_chest_loot():
    """Return one (kind, value) entry sampled by weight.

    `kind` is one of "coins" / "score" / "refill" / "heal".
    `value` is the integer amount for coins/score/heal, or None for refill.
    """
    total = sum(weight for _, _, weight in CHEST_LOOT_TABLE)
    roll = random.randint(1, total)
    cumulative = 0
    for kind, value, weight in CHEST_LOOT_TABLE:
        cumulative += weight
        if roll <= cumulative:
            return (kind, value)
    # Defensive fallback (the loop always returns; this is just to keep
    # linters quiet about the implicit return on an empty table).
    return CHEST_LOOT_TABLE[0][:2]