from turtle import Screen
from paddle import Paddle
from ball import Ball
from scoreboard import Scoreboard
import time

screen = Screen()
screen.setup(800, 600)
screen.bgcolor("black")
screen.tracer(0)

paddle_1 = Paddle(position=(-285, 0))
paddle_2 = Paddle(position=(275, 0))
ball = Ball()
scoreboard = Scoreboard()


screen.listen()
screen.onkey(paddle_1.move_up, "w")
screen.onkey(paddle_1.move_down, "s")
screen.onkey(paddle_2.move_up, "Up")
screen.onkey(paddle_2.move_down, "Down")

def check_wall_collision(ball, screen_height):
    if ball.ycor() > screen_height / 2 - 10:
        # Bounce downwards
        ball.sety(screen_height / 2 - 10)
        ball.setheading(-ball.heading())
    elif ball.ycor() < -screen_height / 2 + 10:
        # Bounce upwards
        ball.sety(-screen_height / 2 + 10)
        ball.setheading(-ball.heading())

def check_paddle_collision(ball, paddle):
    if ball.distance(paddle) < 50 and abs(ball.xcor() - paddle.xcor()) < 20:
        ball.setheading(180 - ball.heading())

def check_score(ball, screen_width):
    if ball.xcor() > screen_width / 2 - 10:
        scoreboard.left_scores()
        ball.reset_direction()
    elif ball.xcor() < -screen_width / 2 + 10:
        scoreboard.right_scores()
        ball.reset_direction()


game_is_on = True
while game_is_on:
    screen.update()
    time.sleep(0.04)
    ball.move_ball()

    # Detect collision with paddle
    check_wall_collision(ball, screen.window_height())
    check_paddle_collision(ball, paddle_1)
    check_paddle_collision(ball, paddle_2)

    # Check score
    check_score(ball, screen.window_width())

    if scoreboard.score_left == 3 or scoreboard.score_right == 3:
        game_is_on = False
        scoreboard.game_over()
        ball.color("black")

screen.update()
screen.exitonclick()