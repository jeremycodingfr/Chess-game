import copy
import random

from const import ROWS, COLS
from move import Move
from square import Square
from piece import King


class AI:
    def __init__(self, color='black', depth=2):
        self.color = color
        self.depth = depth
        self.opponent_color = 'white' if color == 'black' else 'black'

    def choose_move(self, board):
        moves = self.get_all_moves(board, self.color)

        if not moves:
            return None

        best_score = float('inf') if self.color == 'black' else float('-inf')
        best_moves = []

        for move in moves:
            temp_board = copy.deepcopy(board)
            self.make_move(temp_board, move)

            score = self.minimax(
                temp_board,
                self.depth - 1,
                self.opponent_color,
                float('-inf'),
                float('inf')
            )

            if self.color == 'black':
                if score < best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            else:
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)

        return random.choice(best_moves)

    def minimax(self, board, depth, turn_color, alpha, beta):
        if depth == 0:
            return self.evaluate(board)

        moves = self.get_all_moves(board, turn_color)

        if not moves:
            return self.evaluate(board)

        if turn_color == 'white':
            max_score = float('-inf')

            for move in moves:
                temp_board = copy.deepcopy(board)
                self.make_move(temp_board, move)
                score = self.minimax(temp_board, depth - 1, 'black', alpha, beta)
                max_score = max(max_score, score)
                alpha = max(alpha, score)

                if beta <= alpha:
                    break

            return max_score

        min_score = float('inf')

        for move in moves:
            temp_board = copy.deepcopy(board)
            self.make_move(temp_board, move)
            score = self.minimax(temp_board, depth - 1, 'white', alpha, beta)
            min_score = min(min_score, score)
            beta = min(beta, score)

            if beta <= alpha:
                break

        return min_score

    def evaluate(self, board):
        score = 0

        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]

                if square.has_piece():
                    piece = square.piece
                    score += piece.value

                    # Small positional score: pieces closer to the centre are slightly better.
                    if not isinstance(piece, King):
                        centre_distance = abs(3.5 - row) + abs(3.5 - col)
                        centre_bonus = (3.5 - centre_distance) * 0.05
                        score += centre_bonus if piece.color == 'white' else -centre_bonus

        return score

    def get_all_moves(self, board, color):
        moves = []
        self.clear_all_moves(board)

        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]

                if square.has_team_piece(color):
                    piece = square.piece
                    board.calc_moves(piece, row, col, bool=True)

                    for move in piece.moves:
                        initial = Square(move.initial.row, move.initial.col)
                        final = Square(move.final.row, move.final.col)
                        moves.append(Move(initial, final))

                    piece.clear_moves()

        return moves

    def make_move(self, board, move):
        piece = board.squares[move.initial.row][move.initial.col].piece

        if piece is None:
            return

        board.move(piece, move, testing=True)
        board.set_true_en_passant(piece)

    def clear_all_moves(self, board):
        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]

                if square.has_piece():
                    square.piece.clear_moves()
