import random

import pygame
from pygame import *

from toaster.game import ToasterApp
from toaster.misc.assets import AssetManager
from toaster.misc.inputs import InputHandler
from toaster.misc.maps import MapManager
from toaster.physics.physics_handler import PhysicsHandler
from toaster.rendering.camera import Camera
from toaster.rendering.renderer import Renderer

from toaster.rendering.window import Window


class BM(ToasterApp):
    def load(self):
        # initialize pygame
        pygame.init()
        pygame.mixer.init()

        # set the sizes for the game
        render_size = (400, 320)
        window_size = (1200, 960)

        # create the window
        Window(flags=HWACCEL, fps_cap=65, size=window_size)
        Camera(1, [4, 6, 12, 20, 32], smoothing=3, origin=(160, 90))
        Renderer(render_size=render_size)

        AssetManager()
        InputHandler()
        PhysicsHandler()
        MapManager().set_map("test")

    def update(self):
        self.registry["window"].update()
        self.registry["camera"].update()

        avg = [0, 0]
        self.registry["physics"].update()
        # self.registry["physics"].rect_tree.render(display, (255, 0, 0, 120))
        for i, test_rect in enumerate(tests):
            if test_rect.rect.top > 500:
                test_rect.transform.position = [random.randint(16, 450), random.randint(-150, -100)]
            self.registry["renderer"].layers[1]['lit_surf'].fill(test_colours[i], (
            *self.registry["camera"].world_to_camera(1, test_rect.rect.topleft), *test_rect.rect.size))
            avg[0] += test_rect.transform.position[0]
            avg[1] += test_rect.transform.position[1]
        avg[0] /= len(tests)
        avg[1] /= len(tests)

        self.registry["renderer"].layers[0]['unlit_surf'].fill((255, 255, 255),
                                                     (*self.registry["camera"].world_to_camera(0, (50, 50)), 160, 100))
        self.registry["renderer"].layers[3]['unlit_surf'].fill((255, 255, 255),
                                                     (*self.registry["camera"].world_to_camera(3, (300, 0)), 100, 100))
        self.registry["renderer"].layers[1]['lit_surf'].blit(self.registry['maps'].current_map.map_surf,
                                                   self.registry["camera"].world_to_camera(1, (0, 0)))

        self.registry["camera"].set_target(avg)

        self.registry["renderer"].layers[1]['render_lit'] = True
        self.registry["renderer"].layers[3]['render_unlit'] = True
        self.registry["renderer"].layers[0]['render_unlit'] = True
        self.registry["renderer"].render()

    def run(self):
        self.load()
        while 1:
            self.update()
