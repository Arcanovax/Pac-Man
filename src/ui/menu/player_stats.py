class Player_Stats():
    def __init__(self, score, level, lives):
        self.lives = lives
        self.score = score
        self.level = level

    def update(self, var, value):
        setattr(self, var, value)
