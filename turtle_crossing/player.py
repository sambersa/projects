from turtle import Turtle

class Player(Turtle):
    def __init__(self):
        super().__init__()
        self.shape("turtle")
        self.color("green")
        self.penup()
        self.shapesize(1.5)
        self.goto(x=0, y=-280)
        self.setheading(90)

    def move_up(self):
        if self.ycor() < 250:
            self.sety(self.ycor() + 20)

    def move_down(self):
        if self.ycor() < 250:
            self.sety(self.ycor() - 20)

    def reset_position(self):
        self.goto(x=0, y=-280)
