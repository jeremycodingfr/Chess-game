import pygame
import sys
import random

from const import *
from game import Game
from square import Square
from move import Move
from ai import AI


# Works even if your old const.py does not have the side-panel constants yet.
try:
    BOARD_SIZE
except NameError:
    BOARD_SIZE = 800
    PANEL_WIDTH = 300
    WIDTH = BOARD_SIZE + PANEL_WIDTH
    HEIGHT = 800
    SQSIZE = BOARD_SIZE // COLS


class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess AI')
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont('arial', 30, bold=True)
        self.result_font = pygame.font.SysFont('arial', 42, bold=True)
        self.heading_font = pygame.font.SysFont('arial', 20, bold=True)
        self.body_font = pygame.font.SysFont('arial', 17)
        self.small_font = pygame.font.SysFont('arial', 14)

        self.difficulties = ['Easy', 'Medium', 'Hard']
        self.difficulty_index = 1
        self.difficulty = self.difficulties[self.difficulty_index]

        # Right-side UI layout. Keep spacing stable so the panel does not break.
        self.difficulty_button = pygame.Rect(BOARD_SIZE + 25, 120, PANEL_WIDTH - 50, 36)
        self.resign_button = pygame.Rect(BOARD_SIZE + 25, HEIGHT - 132, PANEL_WIDTH - 50, 44)
        self.draw_offer_button = pygame.Rect(BOARD_SIZE + 25, HEIGHT - 78, PANEL_WIDTH - 50, 44)
        self.history_view_rect = pygame.Rect(BOARD_SIZE + 20, 310, PANEL_WIDTH - 40, HEIGHT - 500)
        self.history_row_height = 24
        self.history_scroll = 0
        self.needs_redraw = True

        button_width = 210
        button_height = 48
        self.play_again_button = pygame.Rect(
            (WIDTH - button_width) // 2,
            (HEIGHT // 2) + 95,
            button_width,
            button_height
        )

        self.start_new_game(randomise_colour=True)

    # ---------- setup ----------

    def start_new_game(self, randomise_colour=True, theme_idx=0):
        self.game = Game()
        if hasattr(self.game.config, 'themes') and self.game.config.themes:
            self.game.config.idx = theme_idx % len(self.game.config.themes)
            self.game.config.theme = self.game.config.themes[self.game.config.idx]

        self.move_history = []
        self.history_scroll = 0
        self.game_over = False
        self.result_title = ''
        self.result_message = ''
        self.result_detail = ''
        self.position_counts = {}

        self.human_color = random.choice(['white', 'black']) if randomise_colour else 'white'
        self.ai_color = 'black' if self.human_color == 'white' else 'white'
        self.ai = AI(color=self.ai_color, difficulty=self.difficulty)

        if self.human_color == 'white':
            self.status_message = 'Your turn. You are white.'
        else:
            self.status_message = 'You are black. AI goes first.'

        self.record_position()
        self.needs_redraw = True

    def reset_game(self):
        current_theme = self.game.config.idx if hasattr(self, 'game') else 0
        self.start_new_game(randomise_colour=True, theme_idx=current_theme)

    def cycle_difficulty(self):
        if self.game_over:
            return

        self.difficulty_index = (self.difficulty_index + 1) % len(self.difficulties)
        self.difficulty = self.difficulties[self.difficulty_index]
        self.ai = AI(color=self.ai_color, difficulty=self.difficulty)
        self.status_message = f'Difficulty changed to {self.difficulty}.'
        self.needs_redraw = True

    # ---------- board helpers ----------

    def inside_board(self, pos):
        x, y = pos
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

    def square_name(self, row, col):
        return f'{Square.get_alphacol(col)}{ROWS - row}'

    def other_color(self, color):
        return 'white' if color == 'black' else 'black'

    # ---------- repetition draw helpers ----------

    def get_position_key(self):
        board = self.game.board
        piece_letters = {
            'pawn': 'P',
            'knight': 'N',
            'bishop': 'B',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }

        layout = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = board.squares[row][col].piece
                if piece is None:
                    layout.append('__')
                else:
                    layout.append(f'{piece.color[0]}{piece_letters[piece.name]}')

        castling_rights = []
        for color, row in (('white', 7), ('black', 0)):
            king = board.squares[row][4].piece
            left_rook = board.squares[row][0].piece
            right_rook = board.squares[row][7].piece

            can_castle_left = (
                king is not None and king.name == 'king' and king.color == color and not king.moved and
                left_rook is not None and left_rook.name == 'rook' and left_rook.color == color and not left_rook.moved
            )
            can_castle_right = (
                king is not None and king.name == 'king' and king.color == color and not king.moved and
                right_rook is not None and right_rook.name == 'rook' and right_rook.color == color and not right_rook.moved
            )

            castling_rights.append(f'{color[0]}Q:{int(can_castle_left)}')
            castling_rights.append(f'{color[0]}K:{int(can_castle_right)}')

        en_passant_state = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = board.squares[row][col].piece
                if piece is not None and piece.name == 'pawn' and getattr(piece, 'en_passant', False):
                    en_passant_state.append(f'{piece.color[0]}{row}{col}')

        return (
            tuple(layout),
            self.game.next_player,
            tuple(castling_rights),
            tuple(en_passant_state)
        )

    def record_position(self):
        key = self.get_position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1
        return self.position_counts[key]

    def check_repetition_draw(self):
        if self.game_over:
            return True

        count = self.record_position()
        if count >= 3:
            self.finish_game(
                'Draw',
                'Draw by threefold repetition.',
                'The same position appeared 3 times.'
            )
            return True

        return False

    # ---------- move history ----------

    def move_text(self, piece, move, captured):
        piece_letters = {
            'pawn': '',
            'knight': 'N',
            'bishop': 'B',
            'rook': 'R',
            'queen': 'Q',
            'king': 'K'
        }
        start = self.square_name(move.initial.row, move.initial.col)
        end = self.square_name(move.final.row, move.final.col)
        sep = 'x' if captured else '-'
        text = f'{piece_letters[piece.name]}{start}{sep}{end}'

        if piece.name == 'pawn' and (move.final.row == 0 or move.final.row == 7):
            text += '=Q'

        return text

    def add_move_to_history(self, color, piece, move, captured):
        notation = self.move_text(piece, move, captured)
        self.move_history.append((color, notation))
        self.history_scroll = 0

    def get_move_pairs(self):
        pairs = []
        current_pair = None
        move_number = 1

        for color, notation in self.move_history:
            if color == 'white':
                current_pair = [move_number, notation, '']
                pairs.append(current_pair)
            else:
                if current_pair is None:
                    current_pair = [move_number, '', notation]
                    pairs.append(current_pair)
                else:
                    current_pair[2] = notation
                    move_number += 1
                    current_pair = None

        return pairs

    def get_history_max_scroll(self):
        pairs = self.get_move_pairs()
        visible_rows = max(1, (self.history_view_rect.height - 16) // self.history_row_height)
        return max(0, len(pairs) - visible_rows)

    def scroll_history(self, amount):
        old_scroll = self.history_scroll
        max_scroll = self.get_history_max_scroll()
        self.history_scroll = max(0, min(max_scroll, self.history_scroll + amount))
        if self.history_scroll != old_scroll:
            self.needs_redraw = True

    # ---------- result handling ----------

    def finish_game(self, title, message, detail=''):
        self.game.dragger.undrag_piece()
        self.result_title = title
        self.result_message = message
        self.result_detail = detail
        self.status_message = message
        self.game_over = True
        self.needs_redraw = True

    def check_game_state(self, color_to_move):
        state = self.game.board.get_game_state(color_to_move)

        if state == 'checkmate':
            winner = self.other_color(color_to_move)
            if winner == self.human_color:
                self.finish_game(
                    'You Win',
                    'Checkmate. You defeated the AI.',
                    f'You played {self.human_color.capitalize()}.'
                )
            else:
                self.finish_game(
                    'You Lose',
                    'Checkmate. The AI won.',
                    f'You played {self.human_color.capitalize()}.'
                )
            return True

        if state == 'stalemate':
            self.finish_game(
                'Stalemate',
                'No legal moves. The game is a draw.',
                f'{color_to_move.capitalize()} has no legal move.'
            )
            return True

        if state == 'check':
            if color_to_move == self.human_color:
                self.status_message = 'Check. Your king is under attack.'
            else:
                self.status_message = 'AI is in check.'
            self.needs_redraw = True

        return False

    # ---------- game actions ----------

    def ai_turn(self):
        game = self.game
        board = game.board

        self.status_message = f'AI thinking... {self.difficulty}'
        self.draw_screen()
        pygame.display.flip()

        ai_move = self.ai.choose_move(board)

        if ai_move is None:
            self.check_game_state(self.ai_color)
            if not self.game_over:
                self.finish_game('Draw', 'AI has no legal moves.', 'The game ended with no available move.')
            return

        ai_piece = board.squares[ai_move.initial.row][ai_move.initial.col].piece
        if ai_piece is None:
            self.finish_game('Draw', 'AI move failed.', 'Reset the game and try again.')
            return

        captured = board.squares[ai_move.final.row][ai_move.final.col].has_piece()

        self.add_move_to_history(self.ai_color, ai_piece, ai_move, captured)
        board.move(ai_piece, ai_move)
        board.set_true_en_passant(ai_piece)
        game.play_sound(captured)
        game.next_turn()

        if self.check_repetition_draw():
            self.needs_redraw = True
            return

        if not self.check_game_state(game.next_player):
            self.status_message = f'Your turn. You are {self.human_color}.'

        self.needs_redraw = True

    def resign(self):
        if self.game_over:
            return

        self.finish_game(
            'You Lose',
            f'You surrendered. {self.ai_color.capitalize()} wins.',
            'Press R or click Play Again to reset.'
        )

    def offer_draw(self):
        if self.game_over:
            return

        self.game.dragger.undrag_piece()

        if self.ai.accepts_draw(self.game.board):
            self.finish_game(
                'Draw Accepted',
                'The AI accepted your draw offer.',
                'The game ended by agreement.'
            )
        else:
            self.status_message = 'Draw rejected. Keep playing.'
            self.needs_redraw = True

    def handle_panel_click(self, pos):
        if self.difficulty_button.collidepoint(pos):
            self.cycle_difficulty()
            return True

        if self.resign_button.collidepoint(pos):
            self.resign()
            return True

        if self.draw_offer_button.collidepoint(pos):
            self.offer_draw()
            return True

        return False

    # ---------- colour and ui helpers ----------

    def to_rgb(self, color):
        pg_color = pygame.Color(color)
        return (pg_color.r, pg_color.g, pg_color.b)

    def clamp(self, value):
        return max(0, min(255, int(value)))

    def mix(self, color_a, color_b, weight_b):
        weight_a = 1 - weight_b
        return (
            self.clamp(color_a[0] * weight_a + color_b[0] * weight_b),
            self.clamp(color_a[1] * weight_a + color_b[1] * weight_b),
            self.clamp(color_a[2] * weight_a + color_b[2] * weight_b)
        )

    def ui_palette(self):
        theme = self.game.config.theme
        light = self.to_rgb(theme.bg.light)
        dark = self.to_rgb(theme.bg.dark)
        trace = self.to_rgb(theme.trace.dark)
        move_color = self.to_rgb(theme.moves.dark)

        panel_bg = self.mix(dark, (12, 16, 24), 0.50)
        card_bg = self.mix(dark, (255, 255, 255), 0.12)
        card_border = self.mix(trace, light, 0.20)
        muted_text = self.mix(light, (255, 255, 255), 0.30)
        line = self.mix(trace, (255, 255, 255), 0.15)
        button = self.mix(move_color, dark, 0.20)
        resign = self.mix((190, 60, 60), dark, 0.15)

        return {
            'panel_bg': panel_bg,
            'card_bg': card_bg,
            'card_border': card_border,
            'title': (245, 248, 255),
            'body': (235, 240, 250),
            'muted': muted_text,
            'line': line,
            'button': button,
            'resign': resign,
            'disabled': (95, 95, 95),
            'overlay': (0, 0, 0, 165)
        }

    def draw_text(self, surface, text, font, color, x, y):
        label = font.render(text, True, color)
        surface.blit(label, (x, y))

    def draw_centered_text(self, surface, text, font, color, center_x, y):
        label = font.render(text, True, color)
        rect = label.get_rect(center=(center_x, y))
        surface.blit(label, rect)

    def draw_wrapped_text(self, surface, text, font, color, rect, max_lines=2):
        words = text.split(' ')
        lines = []
        current = ''

        for word in words:
            test = word if current == '' else current + ' ' + word
            if font.size(test)[0] <= rect.width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        for i, line in enumerate(lines[:max_lines]):
            self.draw_text(surface, line, font, color, rect.x, rect.y + i * 21)

    def draw_button(self, surface, rect, text, bg_color, text_color=(255, 255, 255)):
        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), rect, width=2, border_radius=10)
        label = self.heading_font.render(text, True, text_color)
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)

    def draw_history_scrollbar(self, surface, palette, pairs_count, visible_rows):
        if pairs_count <= visible_rows:
            return

        track = pygame.Rect(self.history_view_rect.right - 9, self.history_view_rect.y + 8, 5, self.history_view_rect.height - 16)
        pygame.draw.rect(surface, self.mix(palette['card_bg'], (255, 255, 255), 0.15), track, border_radius=4)

        thumb_height = max(30, int(track.height * (visible_rows / pairs_count)))
        max_scroll = max(1, pairs_count - visible_rows)
        start_index = max_scroll - self.history_scroll
        scroll_ratio = start_index / max_scroll
        thumb_y = track.y + int((track.height - thumb_height) * scroll_ratio)

        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        pygame.draw.rect(surface, palette['line'], thumb, border_radius=4)

    def draw_panel(self, surface):
        panel_x = BOARD_SIZE
        palette = self.ui_palette()

        pygame.draw.rect(surface, palette['panel_bg'], (panel_x, 0, PANEL_WIDTH, HEIGHT))
        pygame.draw.line(surface, palette['line'], (panel_x, 0), (panel_x, HEIGHT), 3)

        self.draw_text(surface, 'Chess Engine AI', self.title_font, palette['title'], panel_x + 24, 24)
        self.draw_text(surface, f'You: {self.human_color.capitalize()}', self.body_font, palette['body'], panel_x + 26, 68)
        self.draw_text(surface, f'AI: {self.ai_color.capitalize()}', self.body_font, palette['body'], panel_x + 26, 92)

        difficulty_color = palette['button'] if not self.game_over else palette['disabled']
        self.draw_button(surface, self.difficulty_button, f'Difficulty: {self.difficulty}', difficulty_color)

        status_rect = pygame.Rect(panel_x + 20, 176, PANEL_WIDTH - 40, 68)
        pygame.draw.rect(surface, palette['card_bg'], status_rect, border_radius=10)
        pygame.draw.rect(surface, palette['card_border'], status_rect, width=1, border_radius=10)
        self.draw_text(surface, 'Status', self.small_font, palette['muted'], panel_x + 35, 187)
        text_rect = pygame.Rect(panel_x + 35, 209, PANEL_WIDTH - 70, 42)
        self.draw_wrapped_text(surface, self.status_message, self.body_font, palette['title'], text_rect, max_lines=2)

        self.draw_text(surface, 'Move History', self.heading_font, palette['title'], panel_x + 24, 274)
        pygame.draw.line(surface, palette['line'], (panel_x + 24, 302), (WIDTH - 24, 302), 2)

        pairs = self.get_move_pairs()
        visible_rows = max(1, (self.history_view_rect.height - 16) // self.history_row_height)
        max_scroll = max(0, len(pairs) - visible_rows)
        self.history_scroll = max(0, min(max_scroll, self.history_scroll))
        start_index = max_scroll - self.history_scroll
        visible_pairs = pairs[start_index:start_index + visible_rows]

        pygame.draw.rect(surface, self.mix(palette['card_bg'], (0, 0, 0), 0.10), self.history_view_rect, border_radius=8)
        pygame.draw.rect(surface, palette['card_border'], self.history_view_rect, width=1, border_radius=8)

        previous_clip = surface.get_clip()
        surface.set_clip(self.history_view_rect)

        for row_index, (index, white_move, black_move) in enumerate(visible_pairs):
            y = self.history_view_rect.y + 10 + (row_index * self.history_row_height)
            self.draw_text(surface, f'{index}.', self.small_font, palette['muted'], panel_x + 28, y)
            self.draw_text(surface, white_move, self.small_font, palette['title'], panel_x + 62, y)
            self.draw_text(surface, black_move, self.small_font, palette['body'], panel_x + 155, y)

        surface.set_clip(previous_clip)
        self.draw_history_scrollbar(surface, palette, len(pairs), visible_rows)

        self.draw_text(surface, 'Click difficulty to change AI', self.small_font, palette['muted'], panel_x + 25, HEIGHT - 214)
        self.draw_text(surface, 'Mouse wheel: scroll moves', self.small_font, palette['muted'], panel_x + 25, HEIGHT - 194)
        self.draw_text(surface, 'Controls: T theme   R reset', self.small_font, palette['muted'], panel_x + 25, HEIGHT - 172)

        resign_color = palette['resign'] if not self.game_over else palette['disabled']
        draw_color = palette['button'] if not self.game_over else palette['disabled']
        self.draw_button(surface, self.resign_button, 'Surrender', resign_color)
        self.draw_button(surface, self.draw_offer_button, 'Ask for Draw', draw_color)

    def draw_result_overlay(self, surface):
        if not self.game_over:
            return

        palette = self.ui_palette()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(palette['overlay'])
        surface.blit(overlay, (0, 0))

        card_width = 500
        card_height = 310
        card = pygame.Rect((WIDTH - card_width) // 2, (HEIGHT - card_height) // 2, card_width, card_height)
        pygame.draw.rect(surface, palette['card_bg'], card, border_radius=18)
        pygame.draw.rect(surface, palette['card_border'], card, width=3, border_radius=18)

        center_x = card.centerx
        self.draw_centered_text(surface, 'Game Over', self.heading_font, palette['muted'], center_x, card.y + 42)
        self.draw_centered_text(surface, self.result_title, self.result_font, palette['title'], center_x, card.y + 92)
        self.draw_centered_text(surface, self.result_message, self.body_font, palette['body'], center_x, card.y + 144)

        if self.result_detail:
            self.draw_centered_text(surface, self.result_detail, self.small_font, palette['muted'], center_x, card.y + 174)

        self.draw_centered_text(surface, 'Press R to reset or click Play Again.', self.small_font, palette['muted'], center_x, card.y + 214)
        self.draw_button(surface, self.play_again_button, 'Play Again', palette['button'])

    def draw_screen(self):
        game = self.game
        screen = self.screen
        dragger = game.dragger

        game.show_bg(screen)
        game.show_last_move(screen)
        game.show_moves(screen)
        game.show_pieces(screen)
        game.show_hover(screen)
        self.draw_panel(screen)

        if dragger.dragging:
            dragger.update_blit(screen)

        self.draw_result_overlay(screen)

    # ---------- event helpers ----------

    def try_start_drag(self, pos):
        game = self.game
        board = game.board
        dragger = game.dragger

        if self.game_over or not self.inside_board(pos):
            return

        dragger.update_mouse(pos)
        clicked_row = dragger.mouseY // SQSIZE
        clicked_col = dragger.mouseX // SQSIZE

        if board.squares[clicked_row][clicked_col].has_piece():
            piece = board.squares[clicked_row][clicked_col].piece

            if piece.color == game.next_player and game.next_player == self.human_color:
                board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                dragger.save_initial(pos)
                dragger.drag_piece(piece)
                self.needs_redraw = True

    def handle_mouse_motion(self, pos):
        game = self.game
        dragger = game.dragger
        old_hover = game.hovered_sqr

        if self.inside_board(pos):
            motion_row = pos[1] // SQSIZE
            motion_col = pos[0] // SQSIZE
            game.set_hover(motion_row, motion_col)
        else:
            game.hovered_sqr = None

        old_pos = None if old_hover is None else (old_hover.row, old_hover.col)
        new_hover = game.hovered_sqr
        new_pos = None if new_hover is None else (new_hover.row, new_hover.col)

        if old_pos != new_pos or dragger.dragging:
            self.needs_redraw = True

        if dragger.dragging:
            dragger.update_mouse(pos)

    def release_drag(self, pos):
        game = self.game
        board = game.board
        dragger = game.dragger
        human_moved = False

        if dragger.dragging and self.inside_board(pos) and not self.game_over:
            dragger.update_mouse(pos)
            released_row = dragger.mouseY // SQSIZE
            released_col = dragger.mouseX // SQSIZE

            initial = Square(dragger.initial_row, dragger.initial_col)
            final = Square(released_row, released_col)
            move = Move(initial, final)

            if board.valid_move(dragger.piece, move):
                captured = board.squares[released_row][released_col].has_piece()
                moved_piece = dragger.piece
                self.add_move_to_history(self.human_color, moved_piece, move, captured)
                board.move(moved_piece, move)
                board.set_true_en_passant(moved_piece)
                game.play_sound(captured)
                game.next_turn()
                human_moved = True

        if dragger.dragging:
            dragger.undrag_piece()
            self.needs_redraw = True

        return human_moved

    # ---------- main loop ----------

    def mainloop(self):
        while True:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEWHEEL:
                    if self.history_view_rect.collidepoint(pygame.mouse.get_pos()):
                        self.scroll_history(event.y)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_over and self.play_again_button.collidepoint(event.pos):
                        self.reset_game()
                        continue

                    if event.button == 4:
                        if self.history_view_rect.collidepoint(event.pos):
                            self.scroll_history(1)
                        continue

                    if event.button == 5:
                        if self.history_view_rect.collidepoint(event.pos):
                            self.scroll_history(-1)
                        continue

                    if self.handle_panel_click(event.pos):
                        continue

                    self.try_start_drag(event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    human_moved = self.release_drag(event.pos)
                    if human_moved:
                        if not self.check_repetition_draw():
                            self.check_game_state(self.game.next_player)
                        self.needs_redraw = True

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        self.game.change_theme()
                        self.needs_redraw = True

                    elif event.key == pygame.K_r:
                        self.reset_game()

            if not self.game_over and not self.game.dragger.dragging and self.game.next_player == self.ai_color:
                self.ai_turn()

            if self.needs_redraw or self.game.dragger.dragging:
                self.draw_screen()
                pygame.display.flip()
                self.needs_redraw = False


main = Main()
main.mainloop()
