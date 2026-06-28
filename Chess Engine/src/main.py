
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

        # Professional UI fonts. These use common system fallbacks.
        self.title_font = pygame.font.SysFont('arial', 28, bold=True)
        self.result_font = pygame.font.SysFont('arial', 42, bold=True)
        self.heading_font = pygame.font.SysFont('arial', 18, bold=True)
        self.body_font = pygame.font.SysFont('arial', 15)
        self.body_bold_font = pygame.font.SysFont('arial', 15, bold=True)
        self.button_font = pygame.font.SysFont('arial', 15, bold=True)
        self.small_font = pygame.font.SysFont('arial', 12)
        self.tiny_font = pygame.font.SysFont('arial', 11)

        self.difficulties = ['Easy', 'Medium', 'Hard']
        self.difficulty_index = 1
        self.difficulty = self.difficulties[self.difficulty_index]

        # Right-side UI layout. Kept compact so it fits beside the 800px board.
        self.panel_margin = 22
        self.panel_inner_width = PANEL_WIDTH - (self.panel_margin * 2)
        panel_x = BOARD_SIZE + self.panel_margin

        self.difficulty_button = pygame.Rect(panel_x, 154, self.panel_inner_width, 40)
        self.history_view_rect = pygame.Rect(panel_x, 340, self.panel_inner_width, 250)
        self.resign_button = pygame.Rect(panel_x, HEIGHT - 124, self.panel_inner_width, 42)
        self.draw_offer_button = pygame.Rect(panel_x, HEIGHT - 70, self.panel_inner_width, 42)

        self.history_row_height = 25
        self.history_scroll = 0
        self.needs_redraw = True

        button_width = 220
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
        visible_rows = max(1, (self.history_view_rect.height - 32) // self.history_row_height)
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

        panel_bg = self.mix(dark, (13, 17, 28), 0.68)
        panel_bg_2 = self.mix(panel_bg, (255, 255, 255), 0.04)
        card_bg = self.mix(panel_bg, (255, 255, 255), 0.08)
        card_bg_hover = self.mix(card_bg, (255, 255, 255), 0.07)
        card_border = self.mix(trace, (255, 255, 255), 0.25)
        accent = self.mix(move_color, (255, 255, 255), 0.08)
        accent_hover = self.mix(accent, (255, 255, 255), 0.12)
        muted_text = self.mix(light, (255, 255, 255), 0.20)
        line = self.mix(trace, (255, 255, 255), 0.18)

        return {
            'panel_bg': panel_bg,
            'panel_bg_2': panel_bg_2,
            'card_bg': card_bg,
            'card_bg_hover': card_bg_hover,
            'card_border': card_border,
            'title': (248, 250, 252),
            'body': (225, 231, 239),
            'muted': muted_text,
            'line': line,
            'accent': accent,
            'accent_hover': accent_hover,
            'accent_dark': self.mix(accent, (0, 0, 0), 0.22),
            'danger': self.mix((202, 64, 73), dark, 0.10),
            'danger_hover': self.mix((226, 75, 85), dark, 0.06),
            'success': (72, 187, 120),
            'disabled': (84, 91, 105),
            'overlay': (8, 11, 18, 178),
            'shadow': (0, 0, 0, 70),
            'row_alt': self.mix(card_bg, (255, 255, 255), 0.04),
        }

    def draw_panel_background(self, surface, panel_x, palette):
        pygame.draw.rect(surface, palette['panel_bg'], (panel_x, 0, PANEL_WIDTH, HEIGHT))
        for y in range(0, HEIGHT, 4):
            ratio = y / HEIGHT
            color = self.mix(palette['panel_bg'], palette['panel_bg_2'], ratio)
            pygame.draw.rect(surface, color, (panel_x, y, PANEL_WIDTH, 4))
        pygame.draw.line(surface, palette['line'], (panel_x, 0), (panel_x, HEIGHT), 2)

    def draw_card(self, surface, rect, palette, radius=14, shadow=True):
        if shadow:
            shadow_surface = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow_surface,
                palette['shadow'],
                (5, 6, rect.width, rect.height),
                border_radius=radius
            )
            surface.blit(shadow_surface, (rect.x - 5, rect.y - 5))

        pygame.draw.rect(surface, palette['card_bg'], rect, border_radius=radius)
        pygame.draw.rect(surface, palette['card_border'], rect, width=1, border_radius=radius)

    def draw_text(self, surface, text, font, color, x, y):
        label = font.render(str(text), True, color)
        surface.blit(label, (x, y))

    def draw_text_right(self, surface, text, font, color, right_x, y):
        label = font.render(str(text), True, color)
        surface.blit(label, (right_x - label.get_width(), y))

    def draw_centered_text(self, surface, text, font, color, center_x, y):
        label = font.render(str(text), True, color)
        rect = label.get_rect(center=(center_x, y))
        surface.blit(label, rect)

    def truncate_text(self, text, font, max_width):
        text = str(text)
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = '...'
        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]
        return text + ellipsis

    def draw_wrapped_text(self, surface, text, font, color, rect, max_lines=2):
        words = str(text).split(' ')
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
            if i == max_lines - 1 and len(lines) > max_lines:
                line = self.truncate_text(line, font, rect.width)
            self.draw_text(surface, line, font, color, rect.x, rect.y + i * 20)

    def draw_chip(self, surface, rect, text, palette, selected=False):
        fill = palette['accent'] if selected else self.mix(palette['card_bg'], (255, 255, 255), 0.06)
        border = palette['accent_hover'] if selected else palette['card_border']
        pygame.draw.rect(surface, fill, rect, border_radius=14)
        pygame.draw.rect(surface, border, rect, width=1, border_radius=14)
        label_color = palette['title'] if selected else palette['body']
        label = self.small_font.render(text, True, label_color)
        surface.blit(label, label.get_rect(center=rect.center))

    def draw_button(self, surface, rect, text, bg_color, text_color=(255, 255, 255), disabled=False):
        palette = self.ui_palette()
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos) and not disabled
        fill = self.mix(bg_color, (255, 255, 255), 0.10) if hovered else bg_color
        border = self.mix(fill, (255, 255, 255), 0.32)

        shadow_surface = pygame.Surface((rect.width + 8, rect.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, palette['shadow'], (4, 5, rect.width, rect.height), border_radius=12)
        surface.blit(shadow_surface, (rect.x - 4, rect.y - 4))

        pygame.draw.rect(surface, fill, rect, border_radius=12)
        pygame.draw.rect(surface, border, rect, width=1, border_radius=12)
        label = self.button_font.render(text, True, text_color)
        label_rect = label.get_rect(center=rect.center)
        surface.blit(label, label_rect)

    def draw_history_scrollbar(self, surface, palette, pairs_count, visible_rows):
        if pairs_count <= visible_rows:
            return

        track = pygame.Rect(self.history_view_rect.right - 10, self.history_view_rect.y + 42, 5, self.history_view_rect.height - 52)
        pygame.draw.rect(surface, self.mix(palette['card_bg'], (255, 255, 255), 0.12), track, border_radius=5)

        thumb_height = max(34, int(track.height * (visible_rows / pairs_count)))
        max_scroll = max(1, pairs_count - visible_rows)
        start_index = max_scroll - self.history_scroll
        scroll_ratio = start_index / max_scroll
        thumb_y = track.y + int((track.height - thumb_height) * scroll_ratio)

        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        pygame.draw.rect(surface, palette['accent_hover'], thumb, border_radius=5)

    def draw_header(self, surface, panel_x, palette):
        self.draw_text(surface, 'CHESS ENGINE', self.title_font, palette['title'], panel_x + self.panel_margin, 24)
        self.draw_text(surface, 'Python + Pygame AI', self.small_font, palette['muted'], panel_x + self.panel_margin + 2, 58)

        badge = pygame.Rect(panel_x + self.panel_margin, 82, self.panel_inner_width, 38)
        self.draw_card(surface, badge, palette, radius=14, shadow=False)
        self.draw_text(surface, 'Mode', self.small_font, palette['muted'], badge.x + 14, badge.y + 12)
        self.draw_text_right(surface, f'{self.human_color.capitalize()} vs AI', self.body_bold_font, palette['title'], badge.right - 14, badge.y + 10)

    def draw_player_card(self, surface, panel_x, palette):
        card = pygame.Rect(panel_x + self.panel_margin, 132, self.panel_inner_width, 80)
        self.draw_card(surface, card, palette)

        self.draw_text(surface, 'PLAYERS', self.small_font, palette['muted'], card.x + 14, card.y + 12)
        self.draw_text(surface, 'You', self.body_font, palette['body'], card.x + 14, card.y + 38)
        self.draw_text_right(surface, self.human_color.capitalize(), self.body_bold_font, palette['title'], card.right - 14, card.y + 38)
        self.draw_text(surface, 'AI', self.body_font, palette['body'], card.x + 14, card.y + 58)
        self.draw_text_right(surface, self.ai_color.capitalize(), self.body_bold_font, palette['title'], card.right - 14, card.y + 58)

    def draw_difficulty_card(self, surface, panel_x, palette):
        card = pygame.Rect(panel_x + self.panel_margin, 228, self.panel_inner_width, 88)
        self.draw_card(surface, card, palette)
        self.draw_text(surface, 'DIFFICULTY', self.small_font, palette['muted'], card.x + 14, card.y + 12)

        levels = ['Easy', 'Medium', 'Hard']
        chip_width = (card.width - 38) // 3
        for i, level in enumerate(levels):
            chip = pygame.Rect(card.x + 14 + i * (chip_width + 5), card.y + 36, chip_width, 28)
            self.draw_chip(surface, chip, level, palette, selected=(level == self.difficulty))

        helper = 'Click card to change AI level'
        self.draw_text(surface, helper, self.tiny_font, palette['muted'], card.x + 14, card.y + 68)
        self.difficulty_button = card

    def draw_status_card(self, surface, panel_x, palette):
        card = pygame.Rect(panel_x + self.panel_margin, 330, self.panel_inner_width, 78)
        self.draw_card(surface, card, palette)
        self.draw_text(surface, 'STATUS', self.small_font, palette['muted'], card.x + 14, card.y + 12)
        text_rect = pygame.Rect(card.x + 14, card.y + 34, card.width - 28, 40)
        self.draw_wrapped_text(surface, self.status_message, self.body_bold_font, palette['title'], text_rect, max_lines=2)

    def draw_history_card(self, surface, panel_x, palette):
        card = pygame.Rect(panel_x + self.panel_margin, 424, self.panel_inner_width, 210)
        self.draw_card(surface, card, palette)
        self.draw_text(surface, 'MOVE HISTORY', self.small_font, palette['muted'], card.x + 14, card.y + 12)
        self.draw_text_right(surface, f'{len(self.move_history)} moves', self.tiny_font, palette['muted'], card.right - 14, card.y + 13)

        self.history_view_rect = pygame.Rect(card.x + 10, card.y + 36, card.width - 20, card.height - 46)
        header = pygame.Rect(self.history_view_rect.x, self.history_view_rect.y, self.history_view_rect.width, 26)
        pygame.draw.rect(surface, self.mix(palette['card_bg'], (255, 255, 255), 0.08), header, border_radius=8)

        self.draw_text(surface, '#', self.tiny_font, palette['muted'], header.x + 10, header.y + 8)
        self.draw_text(surface, 'White', self.tiny_font, palette['muted'], header.x + 40, header.y + 8)
        self.draw_text(surface, 'Black', self.tiny_font, palette['muted'], header.x + 128, header.y + 8)

        pairs = self.get_move_pairs()
        rows_area_height = self.history_view_rect.height - 32
        visible_rows = max(1, rows_area_height // self.history_row_height)
        max_scroll = max(0, len(pairs) - visible_rows)
        self.history_scroll = max(0, min(max_scroll, self.history_scroll))
        start_index = max_scroll - self.history_scroll
        visible_pairs = pairs[start_index:start_index + visible_rows]

        previous_clip = surface.get_clip()
        rows_clip = pygame.Rect(self.history_view_rect.x, self.history_view_rect.y + 30, self.history_view_rect.width, rows_area_height)
        surface.set_clip(rows_clip)

        for row_index, (index, white_move, black_move) in enumerate(visible_pairs):
            y = rows_clip.y + (row_index * self.history_row_height)
            row_rect = pygame.Rect(rows_clip.x, y, rows_clip.width - 14, self.history_row_height - 2)
            if row_index % 2 == 0:
                pygame.draw.rect(surface, palette['row_alt'], row_rect, border_radius=6)

            self.draw_text(surface, f'{index}.', self.tiny_font, palette['muted'], row_rect.x + 10, y + 7)
            self.draw_text(surface, self.truncate_text(white_move, self.small_font, 76), self.small_font, palette['title'], row_rect.x + 40, y + 6)
            self.draw_text(surface, self.truncate_text(black_move, self.small_font, 76), self.small_font, palette['body'], row_rect.x + 128, y + 6)

        surface.set_clip(previous_clip)
        self.draw_history_scrollbar(surface, palette, len(pairs), visible_rows)

    def draw_controls_card(self, surface, panel_x, palette):
        card = pygame.Rect(panel_x + self.panel_margin, 650, self.panel_inner_width, 58)
        self.draw_card(surface, card, palette, radius=12, shadow=False)
        self.draw_text(surface, 'CONTROLS', self.small_font, palette['muted'], card.x + 14, card.y + 10)
        self.draw_text(surface, 'T theme     R reset', self.tiny_font, palette['body'], card.x + 14, card.y + 32)
        self.draw_text_right(surface, 'Wheel scrolls moves', self.tiny_font, palette['body'], card.right - 14, card.y + 32)

    def draw_panel(self, surface):
        panel_x = BOARD_SIZE
        palette = self.ui_palette()

        self.draw_panel_background(surface, panel_x, palette)
        self.draw_header(surface, panel_x, palette)
        self.draw_player_card(surface, panel_x, palette)
        self.draw_difficulty_card(surface, panel_x, palette)
        self.draw_status_card(surface, panel_x, palette)
        self.draw_history_card(surface, panel_x, palette)
        self.draw_controls_card(surface, panel_x, palette)

        resign_color = palette['danger'] if not self.game_over else palette['disabled']
        draw_color = palette['accent'] if not self.game_over else palette['disabled']
        self.draw_button(surface, self.resign_button, 'Surrender', resign_color, disabled=self.game_over)
        self.draw_button(surface, self.draw_offer_button, 'Ask for Draw', draw_color, disabled=self.game_over)

    def draw_result_overlay(self, surface):
        if not self.game_over:
            return

        palette = self.ui_palette()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill(palette['overlay'])
        surface.blit(overlay, (0, 0))

        card_width = 520
        card_height = 320
        card = pygame.Rect((WIDTH - card_width) // 2, (HEIGHT - card_height) // 2, card_width, card_height)

        shadow = pygame.Surface((card_width + 20, card_height + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 130), (10, 12, card_width, card_height), border_radius=22)
        surface.blit(shadow, (card.x - 10, card.y - 10))

        pygame.draw.rect(surface, palette['card_bg'], card, border_radius=22)
        pygame.draw.rect(surface, palette['card_border'], card, width=1, border_radius=22)

        top_bar = pygame.Rect(card.x, card.y, card.width, 76)
        pygame.draw.rect(surface, palette['accent_dark'], top_bar, border_top_left_radius=22, border_top_right_radius=22)
        pygame.draw.line(surface, palette['line'], (card.x, card.y + 76), (card.right, card.y + 76), 1)

        center_x = card.centerx
        self.draw_centered_text(surface, 'GAME OVER', self.small_font, palette['muted'], center_x, card.y + 26)
        self.draw_centered_text(surface, self.result_title, self.result_font, palette['title'], center_x, card.y + 58)
        self.draw_centered_text(surface, self.result_message, self.body_bold_font, palette['body'], center_x, card.y + 124)

        if self.result_detail:
            self.draw_centered_text(surface, self.result_detail, self.body_font, palette['muted'], center_x, card.y + 154)

        self.draw_centered_text(surface, 'Press R to reset or click Play Again.', self.small_font, palette['muted'], center_x, card.y + 210)
        self.draw_button(surface, self.play_again_button, 'Play Again', palette['accent'])

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
