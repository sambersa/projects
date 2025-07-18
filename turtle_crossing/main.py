from turtle import Screen
from player import Player
from car import Car
from scoreboard import Scoreboard
import random
import time

screen = Screen()
screen.title("Turtle Crossing")

def main():
    screen.clear()
    screen.setup(width=800, height=600)
    screen.bgcolor("white")
    screen.tracer(0)
    screen.listen()

    lanes = [-200, -150, -100, -50, 0, 50, 100, 150, 200, 250]
    random.shuffle(lanes)

    player = Player()
    scoreboard = Scoreboard()
    cars = []

    for i in range(10):
        car = Car(lanes)
        car.goto(x=400, y=lanes[i])
        cars.append(car)

    def increase_cars_speed():
        for car in cars:
            car.move_speed += 3

    screen.onkey(player.move_up, "Up")
    screen.onkey(player.move_down, "Down")

    game_is_on = True

    while game_is_on:
        time.sleep(0.07)

        for car in cars:
            car.move()
            if car.xcor() < -420:
                car.reset_position()

        if player.ycor() > 250:
            player.reset_position()
            scoreboard.increase_score()
            increase_cars_speed()

        for car in cars:
            if player.distance(car) < 30:
                game_is_on = False
                screen.update()
                scoreboard.game_over()
                screen.onkey(main, "r")  # Press r key to restart


        screen.update()

main()
screen.mainloop()
