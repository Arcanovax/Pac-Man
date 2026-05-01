class Player_Stats():
    """Simple container for player statistics used by the menu.

    Stores `score`, `level` and `lives` and exposes a generic `update`
    method to set attributes dynamically.
    """
    def __init__(self, score: int, level: int, lives: int):
        self.lives = lives
        self.score = score
        self.level = level

    def update(self, var: str, value: int) -> None:
        """Update an attribute on the stats object by name."""
        setattr(self, var, value)
