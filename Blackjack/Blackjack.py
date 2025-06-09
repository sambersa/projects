import random


def deal_card():
    cards = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
    card = random.choice(cards)
    return card

def calculate_score(cards):
    if sum(cards) == 21 and len(cards) == 2:
        return 0
    while 11 in cards and sum(cards) > 21:
        cards.remove(11)
        cards.append(1)
    return sum(cards)

def compare(u_score, c_score):
    if u_score == c_score:
        return "Draw"
    elif c_score == 0:
        return "Lose, opponent has blackjack"
    elif u_score == 0:
        return "You win. You have blackjack"
    elif u_score > 21:
        return "Bust, you went over 21"
    elif c_score > 21:
        return "Bust, opponent went over 21"
    elif u_score > c_score:
        return "You win!"
    else:
        return "You lose!"


def play_game():
    user_cards = []
    computer_cards = []
    game_over = False

    for _ in range(2):
        user_cards.append(deal_card())
        computer_cards.append(deal_card())

    while not game_over:
        user_score = calculate_score(user_cards)
        computer_score = calculate_score(computer_cards)

        print(f"Your current hand is: {user_cards}, current score is: {user_score}\n")
        print(f"Computer's first card is: {computer_cards[0]}\n")

        if user_score == 0 or computer_score == 0 or user_score > 21:
            game_over = True
        else:
            user_deal = input("Type 'y' to get another card, type 'n' to pass: \n")
            if user_deal == "y":
                user_cards.append(deal_card())
            else:
                game_over = True

    while computer_score != 0 and computer_score < 17:
        computer_cards.append(deal_card())
        computer_score = calculate_score(computer_cards)

    print(f"Your final hand is: {user_cards}, final score is: {user_score}\n")
    print(f"Computer's final hand is: {computer_cards}, final score is: {computer_score}\n")
    print(compare(user_score, computer_score))

while input("Do you want to play a game of Blackjack? Type 'y' or 'n': \n") == 'y'.lower():
    play_game()






