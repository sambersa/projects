from turtle import Turtle


class Scoreboard(Turtle):

    def __init__(self):
        super().__init__()
        self.color("white")
        self.penup()
        self.hideturtle()
        self.score_left = 0
        self.score_right = 0
        self.update_score()

    def update_score(self):
        self.clear()
        self.goto(-250, 260)
        self.write(f"Player One: {self.score_left}", font=("Courier", 12, "normal"))
        self.goto(120, 260)
        self.write(f"Player Two: {self.score_right}", font=("Courier", 12, "normal"))

    def left_scores(self):
        self.score_left += 1
        self.update_score()

    def right_scores(self):
        self.score_right += 1
        self.update_score()

    def reset(self):
        self.score_left = 0
        self.score_right = 0
        self.update_score()

    def game_over(self):
        self.goto(0, 0)
        self.write("Game Over", align="center", font=("Courier", 24, "normal"))