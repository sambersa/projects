from turtle import Turtle

class Collision(Turtle):
    def __init__(self):
        super().__init__()

    def check_wall_collision(ball, screen_height):
        if ball.ycor() > screen_height / 2 - 10 or ball.ycor() < -screen_height / 2 + 10:
            ball.setheading(-ball.heading())

    def check_paddle_collision(ball, paddle):
        if ball.distance(paddle) < 20 and abs(ball.xcor() - paddle.xcor()) < 20:
            ball.setheading(180 - ball.heading())