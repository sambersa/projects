MENU = {
    "espresso": {
        "ingredients": {
            "water": 50,
            "coffee": 18,
        },
        "cost": 1.5,
    },
    "latte": {
        "ingredients": {
            "water": 200,
            "milk": 150,
            "coffee": 24,
        },
        "cost": 2.5,
    },
    "cappuccino": {
        "ingredients": {
            "water": 250,
            "milk": 100,
            "coffee": 24,
        },
        "cost": 3.0,
    }
}

resources = {
    "water": 300,
    "milk": 200,
    "coffee": 100,
}

profit = 0

def sufficient_resources(order_ingredients):
    """Make a for loop to check if the order ingredients are greater than availabile resources"""
    for items in order_ingredients:
        if order_ingredients[items] >= resources[items]:
            print(f"Sorry there isn't enough {items}")
            return False
    return True

def process_coins():
    """Create a variable "total" and ask for each coin and multiply accordinlgy and then return the value"""
    print("Please insert coins: ")
    total = int(input("How many quarters?: ")) * 0.25
    total += int(input("How many dimes?: ")) * 0.1
    total += int(input("How many nickels?: ")) * 0.05
    total += int(input("How many pennies?: ")) * 0.01
    return total

def transaction_success(money_received, drink_cost):
    """Check if money received from user is enough for drink, if it is return change and add profit to machine "profit" variable, profit should be += drink_cost, if not enough, print it"""
    if money_received >= drink_cost:
        change = round(money_received - drink_cost, 2)
        print(f"Your change is ${change}")
        global profit
        profit += drink_cost
        return True
    else:
        print("Not enough money, sorry.")
        return False


def make_coffee(drink_name, order_ingredients):
    """Deduct the required ingredients from the resources with a for loop, deduct from the resources dict and deduct with order ingredients from the item (Drink) itself"""
    for items in order_ingredients:
        resources[items] -= order_ingredients[items]
    print(f"Here's your {drink_name}")

is_on = True

"""Ask user for input, choices: off, report and else if choice is in menu, assign it to a variable, then check if sufficient resources, check if transaction success (payment etc), finally make coffee"""

while is_on:
    choice = input("What would you like? Espresso/Latte/Cappuccino: ").lower()
    if choice == "off":
        is_on = False
    elif choice == "report":
        print(f"Available Water: {resources['water']}ml")
        print(f"Available Milk: {resources['milk']}ml")
        print(f"Available Coffee: {resources['coffee']}g")
        print(f"Money: ${profit}")
    else:
        drink = MENU[choice]
        if sufficient_resources(drink["ingredients"]):
            payment = process_coins()
            if transaction_success(payment, drink["cost"]):
                make_coffee(choice, drink["ingredients"])








