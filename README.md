# Chess Engine Application

A Python chess game built with Pygame. The player can play against an AI opponent with legal move checking, different AI difficulty levels, move history, draw options, surrender, and end-game result screens.

## Features

* Play against an AI opponent
* Three difficulty levels: Easy, Medium, and Hard
* Legal move validation for all chess pieces
* Check, checkmate, and stalemate detection
* Draw by repeated position
* Surrender option
* Ask for draw option
* Scrollable move history panel
* Random player colour on reset
* Theme-changing board and UI
* Win, lose, draw, and stalemate screens

## AI Difficulty Levels

### Easy

The AI chooses a random legal move.

### Medium

The AI evaluates moves using captures, piece value, centre control, and promotion chances.

### Hard

The AI uses minimax with alpha-beta pruning to search for stronger moves.

## Technologies Used

* Python
* Pygame
* Visual Studio Code

## How to Run

1. Clone or download this repository.

2. Open the project folder in Visual Studio Code.

3. Install Pygame:

```bash
pip install pygame
```

4. Run the game:

```bash
python main.py
```

Make sure the `assets` folder is in the same project directory as `main.py`.

## Controls

| Action              | Control                             |
| ------------------- | ----------------------------------- |
| Move piece          | Click and drag                      |
| Change theme        | Press T                             |
| Reset game          | Press R                             |
| Scroll move history | Mouse wheel over move history panel |
| Change difficulty   | Click Difficulty                    |
| Surrender           | Click Surrender                     |
| Ask for draw        | Click Ask for Draw                  |

## Main Files

| File         | Purpose                                                                               |
| ------------ | ------------------------------------------------------------------------------------- |
| `main.py`    | Runs the game loop, UI, buttons, move history, reset system, and result screens       |
| `board.py`   | Handles legal moves, check, checkmate, stalemate, castling, promotion, and en passant |
| `ai.py`      | Controls AI decisions and difficulty levels                                           |
| `piece.py`   | Contains the chess piece classes                                                      |
| `move.py`    | Stores move information                                                               |
| `square.py`  | Stores board square information                                                       |
| `game.py`    | Handles board display, turns, themes, sounds, and reset                               |
| `dragger.py` | Handles piece dragging with the mouse                                                 |

## Game Rules Included

The chess engine supports normal chess movement and several special rules, including castling, pawn promotion, en passant, check detection, checkmate, stalemate, and draw by repeated positions.

## Future Improvements

* Undo move
* Save and load game
* Larger opening book
* Online multiplayer
* Web or PWA deployment

## Author

Created by Jeremy Nguyen.
