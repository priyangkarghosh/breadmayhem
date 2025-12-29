import random

import pygame
from pygame.locals import *

from toaster.entity.components.rect_collider import RectCollider
from toaster.entity.game_object import GameObject
from toaster.rendering.renderer import Renderer
from toaster.physics.physics_handler import PhysicsHandler
from toaster.misc.assets import AssetManager
from toaster.rendering.camera import Camera
from toaster.misc.inputs import InputHandler
from toaster.misc.maps import MapManager
from toaster.rendering.window import Window
from toaster.registry.registry import Registry
from toaster.physics.physics_rect import DYNAMIC

# set the sizes
render_size = (1600, 900)
window_size = (1600, 900)
Window(flags=HWACCEL, fps_cap=65, size=window_size)

# initialize pygame
pygame.mixer.init()

AssetManager()
InputHandler()
PhysicsHandler()
MapManager().set_map("test")
Camera(0, [1], smoothing=3, origin=(300, 240))
Renderer(render_size=render_size)

# TESTING
reg = Registry.instance()

def vtest():
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (255, 255, 255), (1200, 450), 100, 15)
    pygame.draw.rect(reg["renderer"].layers[0]['albedo_surf'], (0, 0, 0), (1100, 412.5, 25, 75))
    pygame.draw.circle(reg["renderer"].layers[0]['emissive_surf'], (0, 127, 255), (1200, 450), 100, 15)
    pygame.draw.rect(reg["renderer"].layers[0]['emissive_surf'], (0, 0, 0), (1100, 412.5, 25, 75))
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (0, 255, 0), (800, 450), 25)

while 1:
    reg["window"].update()
    reg["camera"].update()

    vtest()

    reg.renderer.mark_dirty(0, 'unlit')
    reg.renderer.mark_dirty(0, 'albedo')
    reg["renderer"].render()
    pygame.display.set_caption(str(reg.window.fps))

