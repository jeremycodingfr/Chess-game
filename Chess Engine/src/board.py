from const import *
from square import Square
from piece import *
from move import Move
from sound import Sound
import copy
import os


class Board:

    def __init__(self):
        self.squares = [[0, 0, 0, 0, 0, 0, 0, 0] for col in range(COLS)]
        self.last_move = None
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    # ---------- movement ----------

    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final

        en_passant_empty = self.squares[final.row][final.col].isempty()

        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            diff = final.col - initial.col

            # en passant capture
            if diff != 0 and en_passant_empty:
                self.squares[initial.row][final.col].piece = None
                self.squares[final.row][final.col].piece = piece
                if not testing:
                    sound = Sound(os.path.join('assets/sounds/capture.wav'))
                    sound.play()

            # pawn promotion
            else:
                self.check_promotion(piece, final)

        # king castling
        if isinstance(piece, King):
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook = piece.left_rook if diff < 0 else piece.right_rook
                if rook is not None and rook.moves:
                    self.move(rook, rook.moves[-1])

        piece.moved = True
        piece.clear_moves()
        self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        for row in range(ROWS):
            for col in range(COLS):
                current_piece = self.squares[row][col].piece
                if isinstance(current_piece, Pawn):
                    current_piece.en_passant = False

        if not isinstance(piece, Pawn) or self.last_move is None:
            return

        moved_two_squares = abs(self.last_move.final.row - self.last_move.initial.row) == 2
        piece.en_passant = moved_two_squares

    # ---------- check / mate helpers ----------

    def opponent(self, color):
        return 'white' if color == 'black' else 'black'

    def find_king(self, color):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    return row, col
        return None

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if king_pos is None:
            return True

        king_row, king_col = king_pos
        return self.is_square_attacked(king_row, king_col, self.opponent(color))

    def is_square_attacked(self, row, col, by_color):
        # Pawn attacks
        pawn_dir = -1 if by_color == 'white' else 1
        pawn_row = row - pawn_dir
        for pawn_col in (col - 1, col + 1):
            if Square.in_range(pawn_row, pawn_col):
                piece = self.squares[pawn_row][pawn_col].piece
                if isinstance(piece, Pawn) and piece.color == by_color:
                    return True

        # Knight attacks
        knight_moves = [
            (-2, 1), (-1, 2), (1, 2), (2, 1),
            (2, -1), (1, -2), (-1, -2), (-2, -1)
        ]
        for row_offset, col_offset in knight_moves:
            check_row = row + row_offset
            check_col = col + col_offset
            if Square.in_range(check_row, check_col):
                piece = self.squares[check_row][check_col].piece
                if isinstance(piece, Knight) and piece.color == by_color:
                    return True

        # King attacks
        for row_offset in (-1, 0, 1):
            for col_offset in (-1, 0, 1):
                if row_offset == 0 and col_offset == 0:
                    continue
                check_row = row + row_offset
                check_col = col + col_offset
                if Square.in_range(check_row, check_col):
                    piece = self.squares[check_row][check_col].piece
                    if isinstance(piece, King) and piece.color == by_color:
                        return True

        # Bishop / queen diagonal attacks
        diagonal_dirs = [(-1, 1), (-1, -1), (1, 1), (1, -1)]
        for row_dir, col_dir in diagonal_dirs:
            check_row = row + row_dir
            check_col = col + col_dir
            while Square.in_range(check_row, check_col):
                piece = self.squares[check_row][check_col].piece
                if piece is not None:
                    if piece.color == by_color and (isinstance(piece, Bishop) or isinstance(piece, Queen)):
                        return True
                    break
                check_row += row_dir
                check_col += col_dir

        # Rook / queen straight attacks
        straight_dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        for row_dir, col_dir in straight_dirs:
            check_row = row + row_dir
            check_col = col + col_dir
            while Square.in_range(check_row, check_col):
                piece = self.squares[check_row][check_col].piece
                if piece is not None:
                    if piece.color == by_color and (isinstance(piece, Rook) or isinstance(piece, Queen)):
                        return True
                    break
                check_row += row_dir
                check_col += col_dir

        return False

    def in_check(self, piece, move):
        temp_board = copy.deepcopy(self)
        temp_piece = temp_board.squares[move.initial.row][move.initial.col].piece

        if temp_piece is None:
            return True

        temp_board.move(temp_piece, move, testing=True)
        return temp_board.is_in_check(piece.color)

    def has_legal_moves(self, color):
        for row in range(ROWS):
            for col in range(COLS):
                square = self.squares[row][col]
                if square.has_team_piece(color):
                    piece = square.piece
                    self.calc_moves(piece, row, col, bool=True)
                    has_moves = len(piece.moves) > 0
                    piece.clear_moves()
                    if has_moves:
                        return True
        return False

    def get_all_legal_moves(self, color):
        moves = []
        for row in range(ROWS):
            for col in range(COLS):
                square = self.squares[row][col]
                if square.has_team_piece(color):
                    piece = square.piece
                    self.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        initial = Square(move.initial.row, move.initial.col)
                        final = Square(move.final.row, move.final.col)
                        moves.append(Move(initial, final))
                    piece.clear_moves()
        return moves

    def get_game_state(self, color):
        in_check = self.is_in_check(color)
        has_moves = self.has_legal_moves(color)

        if has_moves:
            return 'check' if in_check else 'playing'

        return 'checkmate' if in_check else 'stalemate'

    # ---------- move generation ----------

    def add_if_legal(self, piece, move, check_king=True):
        if check_king:
            if not self.in_check(piece, move):
                piece.add_move(move)
        else:
            piece.add_move(move)

    def calc_moves(self, piece, row, col, bool=True):
        '''Calculate all legal moves for one piece.'''
        piece.clear_moves()

        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))

            for possible_move_row in range(start, end, piece.dir):
                if not Square.in_range(possible_move_row):
                    break

                if self.squares[possible_move_row][col].isempty():
                    initial = Square(row, col)
                    final = Square(possible_move_row, col)
                    move = Move(initial, final)
                    self.add_if_legal(piece, move, bool)
                else:
                    break

            possible_move_row = row + piece.dir
            for possible_move_col in (col - 1, col + 1):
                if Square.in_range(possible_move_row, possible_move_col):
                    target_piece = self.squares[possible_move_row][possible_move_col].piece
                    if target_piece is not None and target_piece.color != piece.color:
                        if bool and isinstance(target_piece, King):
                            continue
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col, target_piece)
                        move = Move(initial, final)
                        self.add_if_legal(piece, move, bool)

            # en passant
            row_for_en_passant = 3 if piece.color == 'white' else 4
            final_row = 2 if piece.color == 'white' else 5

            if row == row_for_en_passant:
                for side_col in (col - 1, col + 1):
                    if Square.in_range(side_col):
                        side_piece = self.squares[row][side_col].piece
                        if isinstance(side_piece, Pawn) and side_piece.color != piece.color and side_piece.en_passant:
                            initial = Square(row, col)
                            final = Square(final_row, side_col, side_piece)
                            move = Move(initial, final)
                            self.add_if_legal(piece, move, bool)

        def knight_moves():
            possible_moves = [
                (row - 2, col + 1),
                (row - 1, col + 2),
                (row + 1, col + 2),
                (row + 2, col + 1),
                (row + 2, col - 1),
                (row + 1, col - 2),
                (row - 1, col - 2),
                (row - 2, col - 1),
            ]

            for possible_move_row, possible_move_col in possible_moves:
                if Square.in_range(possible_move_row, possible_move_col):
                    target_piece = self.squares[possible_move_row][possible_move_col].piece
                    if target_piece is None or target_piece.color != piece.color:
                        if bool and isinstance(target_piece, King):
                            continue
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col, target_piece)
                        move = Move(initial, final)
                        self.add_if_legal(piece, move, bool)

        def straightline_moves(increments):
            for row_incr, col_incr in increments:
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr

                while Square.in_range(possible_move_row, possible_move_col):
                    target_piece = self.squares[possible_move_row][possible_move_col].piece
                    initial = Square(row, col)
                    final = Square(possible_move_row, possible_move_col, target_piece)
                    move = Move(initial, final)

                    if target_piece is None:
                        self.add_if_legal(piece, move, bool)

                    elif target_piece.color != piece.color:
                        if not (bool and isinstance(target_piece, King)):
                            self.add_if_legal(piece, move, bool)
                        break

                    else:
                        break

                    possible_move_row += row_incr
                    possible_move_col += col_incr

        def king_moves():
            adjacent_squares = [
                (row - 1, col),
                (row - 1, col + 1),
                (row, col + 1),
                (row + 1, col + 1),
                (row + 1, col),
                (row + 1, col - 1),
                (row, col - 1),
                (row - 1, col - 1),
            ]

            for possible_move_row, possible_move_col in adjacent_squares:
                if Square.in_range(possible_move_row, possible_move_col):
                    target_piece = self.squares[possible_move_row][possible_move_col].piece
                    if target_piece is None or target_piece.color != piece.color:
                        if bool and isinstance(target_piece, King):
                            continue
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col, target_piece)
                        move = Move(initial, final)
                        self.add_if_legal(piece, move, bool)

            if not bool:
                return

            # Castling: king cannot be in check, pass through check, or land in check.
            if piece.moved or self.is_in_check(piece.color):
                return

            enemy_color = self.opponent(piece.color)

            # Queen-side castling
            left_rook = self.squares[row][0].piece
            if isinstance(left_rook, Rook) and left_rook.color == piece.color and not left_rook.moved:
                if self.squares[row][1].isempty() and self.squares[row][2].isempty() and self.squares[row][3].isempty():
                    if not self.is_square_attacked(row, 3, enemy_color) and not self.is_square_attacked(row, 2, enemy_color):
                        piece.left_rook = left_rook
                        left_rook.add_move(Move(Square(row, 0), Square(row, 3)))
                        piece.add_move(Move(Square(row, col), Square(row, 2)))

            # King-side castling
            right_rook = self.squares[row][7].piece
            if isinstance(right_rook, Rook) and right_rook.color == piece.color and not right_rook.moved:
                if self.squares[row][5].isempty() and self.squares[row][6].isempty():
                    if not self.is_square_attacked(row, 5, enemy_color) and not self.is_square_attacked(row, 6, enemy_color):
                        piece.right_rook = right_rook
                        right_rook.add_move(Move(Square(row, 7), Square(row, 5)))
                        piece.add_move(Move(Square(row, col), Square(row, 6)))

        if isinstance(piece, Pawn):
            pawn_moves()
        elif isinstance(piece, Knight):
            knight_moves()
        elif isinstance(piece, Bishop):
            straightline_moves([(-1, 1), (-1, -1), (1, 1), (1, -1)])
        elif isinstance(piece, Rook):
            straightline_moves([(-1, 0), (0, 1), (1, 0), (0, -1)])
        elif isinstance(piece, Queen):
            straightline_moves([
                (-1, 1), (-1, -1), (1, 1), (1, -1),
                (-1, 0), (0, 1), (1, 0), (0, -1)
            ])
        elif isinstance(piece, King):
            king_moves()

    # ---------- board setup ----------

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        self.squares[row_other][3] = Square(row_other, 3, Queen(color))
        self.squares[row_other][4] = Square(row_other, 4, King(color))
