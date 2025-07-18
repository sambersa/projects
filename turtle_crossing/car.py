from player import Turtle
import random

COLORS = ["blue", "red", "orange", "green", "purple", "yellow", "pink", "cyan"]
SPEED = [5, 8, 11, 14, 17, 20, 23, 25, 27]

class Car(Turtle):
    def __init__(self, lanes):
        Turtle.__init__(self)
        self.penup()
        self.shape("square")
        self.color(random.choice(COLORS))
        self.shapesize(stretch_wid=1, stretch_len=3)
        self.speed("fastest")
        self.move_speed = random.choice(SPEED)
        self.lanes = lanes

    def move(self):
        self.backward(self.move_speed)

    def reset_position(self):
        self.goto(400, random.choice(self.lanes))
