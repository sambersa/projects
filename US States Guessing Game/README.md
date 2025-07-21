🗺️ U.S. States Game – A U.S. Geography Quiz Game in Python
🎯 Features
A fun and educational U.S. geography quiz game built with Python’s turtle and pandas modules. Players test their knowledge of the 50 U.S. states by entering state names, which are then labeled on a blank U.S. map. It's an engaging way to learn state locations while practicing Python programming.



🕹️ Gameplay
A blank U.S. map is displayed on the screen.

Players are prompted to guess the name of a U.S. state.

Correct guesses appear on the map at the correct location.

The game tracks how many states you've correctly guessed.

Type "Exit" to end the game early and receive a list of the states you missed in a CSV file.



🧱 Core Components
Turtle Graphics: Used to display the map and draw state names.

Pandas: Handles the CSV data of all 50 states and their coordinates.

CSV Output: At the end of the game (or on exit), a states_to_learn.csv file is created with all the states the user missed.



▶️ How to Play
Make sure Python is installed:

Run the main script:


python main.py
1. Guess as many U.S. states as you can!
2. If you want to stop early, type Exit in the input box.
3. Check the states_to_learn.csv file to study the states you missed.

📂 File Structure
.
├── main.py               # Main game script
├── 50_states.csv         # CSV with state names and (x, y) coordinates
├── blank_states_img.gif  # U.S. map image used for the background
└── states_to_learn.csv   # Generated file with unguessed states



📚 Learning Goals
Practice Object-Oriented Programming (OOP) in Python (can be extended with classes).

Use turtle graphics for basic GUI and drawing.

Work with pandas to manage tabular data.

Implement a game loop with user input and real-time updates.

Learn CSV file generation and dynamic feedback.



