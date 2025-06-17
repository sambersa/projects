from menu import Menu
from coffee_maker import CoffeeMaker
from money_machine import MoneyMachine

"""Prompt User by asking what would you like espresso, latte, cappuccino"""

coffee_maker = CoffeeMaker()
menu = Menu()
money = MoneyMachine()
is_on = True

while is_on:
    choice = input("What would you like? Espresso/Latte/Cappuccino: ").lower()
    if choice == "off":
        is_on = False
    elif choice == "report":
        coffee_maker.report()
        money.report()
    else:
        drink = menu.find_drink(choice)
        if drink:
            print(f"Your drink is {drink.name}, which costs ${drink.cost}")
        if coffee_maker.is_resource_sufficient(drink):
            if money.make_payment(drink.cost):
                coffee_maker.make_coffee(drink)
        else:
            print("Sorry, that item is not available.")




