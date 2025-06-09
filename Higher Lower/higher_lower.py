from game_data import data
import random

def get_random_celebrity():
    return random.choice(data)

def get_user_choice():
    while True:
        guess = input("Who has more followers? Type 'A' or 'B': ").upper()
        if guess in ['A', 'B']:
            return guess
        print("Please enter a valid input of: 'A' or 'B'.")

def display_comparison(celeb_A, celeb_B):
    print(f"Compare A: {celeb_A['name']}, a {celeb_A['description']}, from {celeb_A['country']}\n")
    print(f"Against B: {celeb_B['name']}, a {celeb_B['description']}, from {celeb_B['country']}\n")

def determine_winner(celeb_A, celeb_B):
    if celeb_A['follower_count'] > celeb_B['follower_count']:
        return 'A'
    elif celeb_A['follower_count'] < celeb_B['follower_count']:
        return 'B'
    else:
        return random.choice(['A', 'B'])

def replace_loser(celeb_A, celeb_B, correct_answer):
    if correct_answer == 'A':
        celeb_B = get_random_celebrity()
    else:
        celeb_A = get_random_celebrity()
    return celeb_A, celeb_B

def higher_lower():

    game_over = False
    score = 0

    celeb_A = get_random_celebrity()
    celeb_B = get_random_celebrity()

    while not game_over:
        display_comparison(celeb_A, celeb_B)
        guess = get_user_choice()
        correct_answer = determine_winner(celeb_A, celeb_B)

        if guess == correct_answer:
            score += 1
            print(f"Correct! Your score is {score}")

            celeb_A, celeb_B = replace_loser(celeb_A, celeb_B, correct_answer)
        else:
            print("Wrong! Game over")
            game_over = True

higher_lower()



