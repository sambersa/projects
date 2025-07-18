from turtle import Turtle

class Scoreboard(Turtle):

    def __init__(self):
        super().__init__()
        self.color("black")
        self.penup()
        self.hideturtle()
        self.score = 0
        self.update_score()

    def update_score(self):
        self.clear()
        self.goto(-250, 260)
        self.write(f"Score: {self.score}", font=("Courier", 12, "normal"))

    def increase_score(self):
        self.score += 1
        self.update_score()

    def reset(self):
        self.score = 0
        self.update_score()

    def game_over(self):
        self.clear()
        self.goto(0, 0)
        self.write("Game Over", align="center", font=("Courier", 24, "normal"))
        self.goto(0, -30)
        self.write(f"Your score was {self.score}", align="center", font=("Courier", 24, "normal"))
        self.goto(0, -60)
        self.write("Press 'R' to restart", align="center", font=("Courier", 14, "normal"))

