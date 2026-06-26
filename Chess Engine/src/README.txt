Chess Engine Application

A Python and Pygame chess game where the player can play against an AI opponent. The game includes a visual chessboard, legal move checking, AI difficulty levels, move history, draw options, surrender, and end-game result screens.

Features

* Play against an AI opponent
* Three difficulty levels: Easy, Medium, and Hard
* Legal move validation for all chess pieces
* Check, checkmate, and stalemate detection
* Draw by repeated position
* Surrender option
* Ask for draw option
* Move history panel with scrolling
* Random player colour on reset
* Theme-changing board and UI
* Win, lose, draw, and stalemate result screens

AI Difficulty

Easy:
The AI chooses a random legal move.

Medium:
The AI chooses stronger moves based on captures, piece value, centre control, and promotion chances.

Hard:
The AI uses minimax with alpha-beta pruning to search for stronger moves.

Controls

Move pieces:
Click and drag a piece to a legal square.

Change theme:
Press T.

Reset game:
Press R.

Scroll move history:
Use the mouse wheel over the move history panel.

Change difficulty:
Click the Difficulty button on the right-side panel.

Surrender:
Click the Surrender button.

Ask for draw:
Click the Ask for Draw button.

How to Run

1. Open the project folder in Visual Studio Code.
2. Make sure the assets folder is in the same folder as main.py.
3. Install Pygame if needed:

pip install pygame

4. Run the game:

python main.py

Main Files

main.py:
Runs the game loop, user interface, buttons, move history, reset system, and result screens.

board.py:
Handles the chessboard, legal moves, check, checkmate, stalemate, castling, promotion, and en passant.

ai.py:
Controls the AI opponent and difficulty levels.

piece.py:
Contains the chess piece classes.

move.py:
Stores move information.

square.py:
Stores board square information.

game.py:
Handles the board display, themes, turns, sounds, and game reset.

dragger.py:
Handles piece dragging with the mouse.

Requirements

* Python 3
* Pygame
* Visual Studio Code or another Python editor

Future Improvements

* Undo move
* Save and load game
* Stronger opening book
* Timer system
* Online multiplayer
  ::: 
