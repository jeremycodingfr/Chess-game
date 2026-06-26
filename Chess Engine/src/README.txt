
Chess Engine AI UI - Legal Move Fix

Run with:
python main.py

Controls:
- Drag white pieces to move
- T changes board theme
- R resets the game
- Surrender ends the game
- Ask for Draw offers a draw to the AI

Fixes in this version:
- The king cannot capture a protected queen or any protected piece.
- All legal responses to check are tested correctly.
- A knight can capture a checking knight if the king becomes safe.
- King movement checks enemy attacks directly.
- Enemy kings cannot be captured as normal pieces.
- Castling checks current, passing, and landing squares.
