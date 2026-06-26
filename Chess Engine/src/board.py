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
                self.squares[initial.row][initial.col + diff].piece = None
                self.squares[final.row][final.col].piece = piece
                if not testing:
                    sound = Sound(os.path.join('assets/sounds/capture.wav'))
                    sound.play()
            else:
                self.check_promotion(piece, final)

        # king castling
        if isinstance(piece, King):
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook_initial_col = 0 if diff < 0 else 7
                rook_final_col = 3 if diff < 0 else 5
                rook = piece.left_rook if diff < 0 else piece.right_rook

                if rook is None:
                    rook = self.squares[initial.row][rook_initial_col].piece

                if rook is not None:
                    rook_move = Move(
                        Square(initial.row, rook_initial_col),
                        Square(initial.row, rook_final_col)
                    )
                    self.move(rook, rook_move, testing)

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
                p = self.squares[row][col].piece
                if isinstance(p, Pawn):
                    p.en_passant = False

        if isinstance(piece, Pawn) and self.last_move:
            moved_two_squares = abs(self.last_move.final.row - self.last_move.initial.row) == 2
            piece.en_passant = moved_two_squares

    # ---------- check and legality helpers ----------

    def enemy_color(self, color):
        return 'white' if color == 'black' else 'black'

    def find_king(self, color):
        for row in range(ROWS):
            for col in range(COLS):
                square = self.squares[row][col]
                if square.has_piece():
                    piece = square.piece
                    if isinstance(piece, King) and piece.color == color:
                        return row, col
        return None

    def is_square_attacked(self, row, col, attacker_color):
        # Pawn attacks
        pawn_dir = -1 if attacker_color == 'white' else 1
        pawn_row = row - pawn_dir
        for pawn_col in (col - 1, col + 1):
            if Square.in_range(pawn_row, pawn_col):
                piece = self.squares[pawn_row][pawn_col].piece
                if isinstance(piece, Pawn) and piece.color == attacker_color:
                    return True

        # Knight attacks
        knight_moves = [
            (row - 2, col + 1), (row - 1, col + 2),
            (row + 1, col + 2), (row + 2, col + 1),
            (row + 2, col - 1), (row + 1, col - 2),
            (row - 1, col - 2), (row - 2, col - 1),
        ]
        for r, c in knight_moves:
            if Square.in_range(r, c):
                piece = self.squares[r][c].piece
                if isinstance(piece, Knight) and piece.color == attacker_color:
                    return True

        # Rook and queen attacks
        straight_dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        for row_step, col_step in straight_dirs:
            r = row + row_step
            c = col + col_step
            while Square.in_range(r, c):
                square = self.squares[r][c]
                if square.has_piece():
                    piece = square.piece
                    if piece.color == attacker_color and (isinstance(piece, Rook) or isinstance(piece, Queen)):
                        return True
                    break
                r += row_step
                c += col_step

        # Bishop and queen attacks
        diagonal_dirs = [(-1, 1), (-1, -1), (1, 1), (1, -1)]
        for row_step, col_step in diagonal_dirs:
            r = row + row_step
            c = col + col_step
            while Square.in_range(r, c):
                square = self.squares[r][c]
                if square.has_piece():
                    piece = square.piece
                    if piece.color == attacker_color and (isinstance(piece, Bishop) or isinstance(piece, Queen)):
                        return True
                    break
                r += row_step
                c += col_step

        # King attacks
        king_dirs = [
            (-1, 0), (-1, 1), (0, 1), (1, 1),
            (1, 0), (1, -1), (0, -1), (-1, -1),
        ]
        for row_step, col_step in king_dirs:
            r = row + row_step
            c = col + col_step
            if Square.in_range(r, c):
                piece = self.squares[r][c].piece
                if isinstance(piece, King) and piece.color == attacker_color:
                    return True

        return False

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if king_pos is None:
            return True

        king_row, king_col = king_pos
        return self.is_square_attacked(king_row, king_col, self.enemy_color(color))

    def move_leaves_king_in_check(self, piece, move):
        temp_board = copy.deepcopy(self)
        temp_piece = temp_board.squares[move.initial.row][move.initial.col].piece

        if temp_piece is None:
            return True

        temp_board.move(temp_piece, move, testing=True)
        return temp_board.is_in_check(piece.color)

    def in_check(self, piece, move):
        # Kept for compatibility with the rest of the project.
        return self.move_leaves_king_in_check(piece, move)

    def _enemy_king_on_square(self, piece, row, col):
        target = self.squares[row][col].piece
        return isinstance(target, King) and target.color != piece.color

    def _try_add_move(self, piece, move, validate=True):
        if self._enemy_king_on_square(piece, move.final.row, move.final.col):
            return

        if validate:
            if not self.move_leaves_king_in_check(piece, move):
                piece.add_move(move)
        else:
            piece.add_move(move)

    def calc_moves(self, piece, row, col, bool=True):
        '''Calculate all legal moves for a piece on a square.'''
        piece.clear_moves()

        def pawn_moves():
            steps = 1 if piece.moved else 2

            # vertical moves
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))
            for possible_move_row in range(start, end, piece.dir):
                if not Square.in_range(possible_move_row):
                    break

                if self.squares[possible_move_row][col].isempty():
                    initial = Square(row, col)
                    final = Square(possible_move_row, col)
                    move = Move(initial, final)
                    self._try_add_move(piece, move, bool)
                else:
                    break

            # diagonal captures
            possible_move_row = row + piece.dir
            for possible_move_col in (col - 1, col + 1):
                if Square.in_range(possible_move_row, possible_move_col):
                    target = self.squares[possible_move_row][possible_move_col]
                    if target.has_enemy_piece(piece.color) and not isinstance(target.piece, King):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col, target.piece)
                        move = Move(initial, final)
                        self._try_add_move(piece, move, bool)

            # en passant
            r = 3 if piece.color == 'white' else 4
            fr = 2 if piece.color == 'white' else 5

            for side_col in (col - 1, col + 1):
                if Square.in_range(side_col) and row == r:
                    side_piece = self.squares[row][side_col].piece
                    if isinstance(side_piece, Pawn) and side_piece.color != piece.color and side_piece.en_passant:
                        initial = Square(row, col)
                        final = Square(fr, side_col, side_piece)
                        move = Move(initial, final)
                        self._try_add_move(piece, move, bool)

        def knight_moves():
            possible_moves = [
                (row - 2, col + 1), (row - 1, col + 2),
                (row + 1, col + 2), (row + 2, col + 1),
                (row + 2, col - 1), (row + 1, col - 2),
                (row - 1, col - 2), (row - 2, col - 1),
            ]

            for possible_move_row, possible_move_col in possible_moves:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        self._try_add_move(piece, move, bool)

        def straightline_moves(incrs):
            for row_incr, col_incr in incrs:
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr

                while Square.in_range(possible_move_row, possible_move_col):
                    initial = Square(row, col)
                    final_piece = self.squares[possible_move_row][possible_move_col].piece
                    final = Square(possible_move_row, possible_move_col, final_piece)
                    move = Move(initial, final)

                    if self.squares[possible_move_row][possible_move_col].isempty():
                        self._try_add_move(piece, move, bool)

                    elif self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                        self._try_add_move(piece, move, bool)
                        break

                    elif self.squares[possible_move_row][possible_move_col].has_team_piece(piece.color):
                        break

                    possible_move_row += row_incr
                    possible_move_col += col_incr

        def king_moves():
            adjs = [
                (row - 1, col), (row - 1, col + 1),
                (row, col + 1), (row + 1, col + 1),
                (row + 1, col), (row + 1, col - 1),
                (row, col - 1), (row - 1, col - 1),
            ]

            # normal king moves
            for possible_move_row, possible_move_col in adjs:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        self._try_add_move(piece, move, bool)

            # castling
            if piece.moved:
                return

            enemy = self.enemy_color(piece.color)
            if bool and self.is_in_check(piece.color):
                return

            # queen side castle
            left_rook = self.squares[row][0].piece
            if isinstance(left_rook, Rook) and not left_rook.moved:
                if self.squares[row][1].isempty() and self.squares[row][2].isempty() and self.squares[row][3].isempty():
                    safe_to_castle = True
                    if bool:
                        safe_to_castle = not self.is_square_attacked(row, 3, enemy) and not self.is_square_attacked(row, 2, enemy)

                    if safe_to_castle:
                        piece.left_rook = left_rook
                        moveR = Move(Square(row, 0), Square(row, 3))
                        moveK = Move(Square(row, col), Square(row, 2))
                        left_rook.add_move(moveR)
                        piece.add_move(moveK)

            # king side castle
            right_rook = self.squares[row][7].piece
            if isinstance(right_rook, Rook) and not right_rook.moved:
                if self.squares[row][5].isempty() and self.squares[row][6].isempty():
                    safe_to_castle = True
                    if bool:
                        safe_to_castle = not self.is_square_attacked(row, 5, enemy) and not self.is_square_attacked(row, 6, enemy)

                    if safe_to_castle:
                        piece.right_rook = right_rook
                        moveR = Move(Square(row, 7), Square(row, 5))
                        moveK = Move(Square(row, col), Square(row, 6))
                        right_rook.add_move(moveR)
                        piece.add_move(moveK)

        if isinstance(piece, Pawn):
            pawn_moves()

        elif isinstance(piece, Knight):
            knight_moves()

        elif isinstance(piece, Bishop):
            straightline_moves([
                (-1, 1), (-1, -1),
                (1, 1), (1, -1),
            ])

        elif isinstance(piece, Rook):
            straightline_moves([
                (-1, 0), (0, 1),
                (1, 0), (0, -1),
            ])

        elif isinstance(piece, Queen):
            straightline_moves([
                (-1, 1), (-1, -1),
                (1, 1), (1, -1),
                (-1, 0), (0, 1),
                (1, 0), (0, -1),
            ])

        elif isinstance(piece, King):
            king_moves()

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        # pawns
        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        # knights
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        # bishops
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        # rooks
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        # queen
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))

        # king
        self.squares[row_other][4] = Square(row_other, 4, King(color))
