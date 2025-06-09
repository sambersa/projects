Higher Lower Game 🎯
A simple command-line implementation of the classic "Higher or Lower" guessing game written in Python. Test your knowledge of celebrity social media followers!
🎮 Features

Celebrity Comparison Game: Compare follower counts between famous personalities
Interactive Gameplay: User-friendly prompts guide you through each round
Score Tracking: Keep track of your consecutive correct guesses
Dynamic Content: Celebrities are randomly selected for each comparison
Robust Input Handling: Validates user input and handles invalid entries gracefully
Edge Case Management: Handles tied follower counts and ensures fair gameplay

🎲 Game Rules

You're presented with two celebrities (A and B) with their descriptions and countries
Guess which celebrity has more followers by typing 'A' or 'B'
If correct, your score increases and you continue with a new comparison
If wrong, the game ends and displays your final score
The goal is to achieve the highest consecutive score possible!

▶️ How to Play

Run the script:
bashpython higher_lower.py

Read the comparison:

Celebrity A: Name, description, and country
Celebrity B: Name, description, and country


Make your guess:

Type 'A' if you think Celebrity A has more followers
Type 'B' if you think Celebrity B has more followers


Continue playing:

Correct guesses advance you to the next round
Wrong guesses end the game and show your final score



📁 Project Structure
higher-lower-game/
├── higher_lower.py    # Main game logic
├── game_data.py       # Celebrity data (follower counts, descriptions)
└── README.md          # Project documentation
💡 Tech Stack

Python 3
Standard Library:

random - For celebrity selection and tie-breaking
Built-in functions for user input and game flow



🧠 Concepts Demonstrated

Function Organization: Clean separation of concerns with dedicated functions
Game Loop Logic: Continuous gameplay until failure condition
Input Validation: Robust handling of user input with error checking
Conditional Logic: Complex decision trees for game outcomes
Random Selection: Dynamic content generation for replayability
Data Structure Manipulation: Working with dictionaries and lists
User Experience Design: Clear prompts and feedback system

🚀 Getting Started

Clone the repository:
bashgit clone https://github.com/yourusername/higher-lower-game.git
cd higher-lower-game

Ensure you have the game_data.py file with celebrity information
Run the game:
bashpython higher_lower.py


🎯 Example Gameplay
Compare A: Cristiano Ronaldo, a Footballer, from Portugal

Against B: Ariana Grande, a Musician and actress, from United States

Who has more followers? Type 'A' or 'B': A
Correct! Your score is 1

Compare A: Cristiano Ronaldo, a Footballer, from Portugal

Against B: Kim Kardashian, a Reality TV personality, from United States

Who has more followers? Type 'A' or 'B': B
Wrong! Game over
🔧 Customization
Want to add your own celebrities or modify the game? Simply update the game_data.py file with your own data structure following this format:
pythondata = [
    {
        'name': 'Celebrity Name',
        'follower_count': 000,  # in millions
        'description': 'Brief description',
        'country': 'Country name'
    },
    # Add more celebrities...
]
📈 Future Enhancements

Add difficulty levels with different celebrity categories
Implement a leaderboard system
Add more detailed statistics tracking
Create a GUI version using tkinter or pygame
Add multiplayer functionality


Built with Python
