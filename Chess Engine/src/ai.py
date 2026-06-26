
import copy
import random

from const import ROWS, COLS
from move import Move
from square import Square
from piece import King


class AI:
    def __init__(self, color='black', difficulty='Medium', depth=None, max_search_moves=14):
        self.color = color
        self.opponent_color = 'white' if color == 'black' else 'black'
        self.max_search_moves = max_search_moves
        self.piece_scores = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }
        self.set_difficulty(difficulty, depth)

    def set_difficulty(self, difficulty, depth=None):
        difficulty = str(difficulty).capitalize()
        if difficulty not in ['Easy', 'Medium', 'Hard']:
            difficulty = 'Medium'

        self.difficulty = difficulty

        if depth is not None:
            self.depth = depth
        elif difficulty == 'Hard':
            self.depth = 2
        else:
            self.depth = 1

        self.max_search_moves = 16 if difficulty == 'Hard' else 14

    def choose_move(self, board):
        moves = self.get_all_moves(board, self.color)

        if not moves:
            return None

        if self.difficulty == 'Easy':
            return random.choice(moves)

        opening_move = self.choose_opening_move(board, moves)
        if opening_move is not None:
            return opening_move

        if self.difficulty == 'Medium' or self.depth <= 1:
            return self.choose_fast_move(board, moves)

        return self.choose_minimax_move(board, moves)

    # ---------- difficulty logic ----------

    def choose_minimax_move(self, board, moves):
        ordered_moves = self.order_moves(board, moves, self.color)
        ordered_moves = ordered_moves[:self.max_search_moves]

        best_score = float('inf') if self.color == 'black' else float('-inf')
        best_moves = []

        for move in ordered_moves:
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

        return random.choice(best_moves) if best_moves else self.choose_fast_move(board, moves)

    # ---------- opening variety ----------

    def own_moved_piece_count(self, board):
        count = 0
        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]
                if square.has_team_piece(self.color) and square.piece.moved:
                    count += 1
        return count

    def choose_opening_move(self, board, moves):
        # First AI move: prefer random pawn openings so it does not always use the knight first.
        if self.own_moved_piece_count(board) > 0:
            return None

        if self.color == 'white':
            preferred = [
                ((6, 4), (4, 4)),  # e2-e4
                ((6, 3), (4, 3)),  # d2-d4
                ((6, 2), (4, 2)),  # c2-c4
                ((6, 6), (5, 6)),  # g2-g3
                ((6, 1), (5, 1)),  # b2-b3
            ]
        else:
            preferred = [
                ((1, 4), (3, 4)),  # e7-e5
                ((1, 3), (3, 3)),  # d7-d5
                ((1, 2), (3, 2)),  # c7-c5
                ((1, 6), (2, 6)),  # g7-g6
                ((1, 1), (2, 1)),  # b7-b6
            ]

        legal_by_coords = {
            ((move.initial.row, move.initial.col), (move.final.row, move.final.col)): move
            for move in moves
        }

        candidates = []
        for coords in preferred:
            move = legal_by_coords.get(coords)
            if move is not None:
                candidates.append(move)

        if candidates:
            return random.choice(candidates)

        pawn_moves = []
        for move in moves:
            piece = board.squares[move.initial.row][move.initial.col].piece
            if piece is not None and piece.name == 'pawn':
                pawn_moves.append(move)

        return random.choice(pawn_moves) if pawn_moves else None

    # ---------- search ----------

    def choose_fast_move(self, board, moves):
        scored_moves = []

        for move in moves:
            score = self.quick_score(board, move, self.color)
            scored_moves.append((score, move))

        best_score = max(score for score, move in scored_moves)
        best_moves = [move for score, move in scored_moves if score == best_score]
        return random.choice(best_moves)

    def minimax(self, board, depth, turn_color, alpha, beta):
        if depth == 0:
            return self.evaluate(board)

        moves = self.get_all_moves(board, turn_color)

        if not moves:
            return self.evaluate(board)

        moves = self.order_moves(board, moves, turn_color)
        moves = moves[:self.max_search_moves]

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
        # Positive score means white is better. Negative score means black is better.
        score = 0

        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]

                if square.has_piece():
                    piece = square.piece
                    score += piece.value

                    if not isinstance(piece, King):
                        centre_distance = abs(3.5 - row) + abs(3.5 - col)
                        centre_bonus = (3.5 - centre_distance) * 0.05
                        score += centre_bonus if piece.color == 'white' else -centre_bonus

        return score

    def quick_score(self, board, move, color):
        piece = board.squares[move.initial.row][move.initial.col].piece
        target = board.squares[move.final.row][move.final.col].piece

        if piece is None:
            return -999999

        score = random.uniform(0, 0.25)

        # Captures. Favour winning material and good trades.
        if target is not None:
            captured_value = self.piece_scores.get(target.name, 0)
            attacker_value = self.piece_scores.get(piece.name, 0)
            score += captured_value * 10 - attacker_value

        # Centre control.
        centre_distance = abs(3.5 - move.final.row) + abs(3.5 - move.final.col)
        score += (7 - centre_distance) * 8

        # Promotion.
        if piece.name == 'pawn' and (move.final.row == 0 or move.final.row == 7):
            score += 850

        # Develop bishops slightly more than knights so knight moves are not over-forced.
        if piece.name == 'bishop':
            if color == 'white' and move.initial.row == 7:
                score += 30
            elif color == 'black' and move.initial.row == 0:
                score += 30

        if piece.name == 'knight':
            if color == 'white' and move.initial.row == 7:
                score += 12
            elif color == 'black' and move.initial.row == 0:
                score += 12

        # Early pawn play gives more varied openings.
        if piece.name == 'pawn' and self.own_moved_piece_count(board) <= 2:
            if move.initial.col in [2, 3, 4, 6, 1]:
                score += 20
            if abs(move.final.row - move.initial.row) == 2:
                score += 8

        # Keep the king safer in the opening.
        if piece.name == 'king' and abs(move.final.col - move.initial.col) != 2:
            score -= 20

        return score

    def order_moves(self, board, moves, color):
        return sorted(moves, key=lambda move: self.quick_score(board, move, color), reverse=True)

    def accepts_draw(self, board):
        score = self.evaluate(board)

        # The black AI accepts a draw when the position is equal or bad for black.
        if self.color == 'black':
            return score >= -1.5

        return score <= 1.5

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
