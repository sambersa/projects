from turtle import Turtle
import random

ANGLES = (45, 55, 65, 135, 225, 315)

class Ball(Turtle):
    def __init__(self):
        super().__init__()
        self.shape("circle")
        self.color("white")
        self.penup()
        self.reset_direction()

    def reset_direction(self):
        self.goto(0, 0)
        #Random angle: ball will either head left or right

        angle = random.choice(ANGLES)
        self.setheading(angle)
        self.move_speed = 14

    def move_ball(self):
        self.forward(self.move_speed)
