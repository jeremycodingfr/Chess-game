import pygame

from const import *


class Dragger:

    def __init__(self):
        self.piece = None
        self.dragging = False
        self.mouseX = 0
        self.mouseY = 0
        self.initial_row = 0
        self.initial_col = 0
        self.image_cache = {}

    # blit method

    def get_piece_image(self):
        self.piece.set_texture(size=128)
        texture = self.piece.texture

        if texture not in self.image_cache:
            self.image_cache[texture] = pygame.image.load(texture).convert_alpha()

        return self.image_cache[texture]

    def update_blit(self, surface):
        img = self.get_piece_image()
        img_center = (self.mouseX, self.mouseY)
        self.piece.texture_rect = img.get_rect(center=img_center)
        surface.blit(img, self.piece.texture_rect)

    # other methods

    def update_mouse(self, pos):
        self.mouseX, self.mouseY = pos

    def save_initial(self, pos):
        self.initial_row = pos[1] // SQSIZE
        self.initial_col = pos[0] // SQSIZE

    def drag_piece(self, piece):
        self.piece = piece
        self.dragging = True

    def undrag_piece(self):
        self.piece = None
        self.dragging = False
