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
render_size = (800, 450)
window_size = (1600, 900)
Window(flags=HWACCEL, fps_cap=0, size=window_size)

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
    convx = render_size[0] / 1600
    convy = render_size[1] / 900
    m = max(convx, convy)
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (255, 255, 255), (1200 * convx, 450 * convy), 100 * convx, int(15 * m))
    pygame.draw.rect(reg["renderer"].layers[0]['albedo_surf'], (0, 0, 0), (1100 * convx, 412.5 * convy, 25 * convx, 75 * convy))
    pygame.draw.circle(reg["renderer"].layers[0]['emissive_surf'], (0, 127, 255), (1200 * convx, 450 * convy), 100 * convx, int(15 * m))
    pygame.draw.rect(reg["renderer"].layers[0]['emissive_surf'], (0, 0, 0), (1100 * convx, 412.5 * convy, 25 * convx, 75 * convx))
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (0, 255, 0), (800 * convx, 450 * convy), int(25 * m))

while 1:
    reg["window"].update()
    reg["camera"].update()

    vtest()

    reg.renderer.mark_dirty(0, 'unlit')
    reg.renderer.mark_dirty(0, 'albedo')
    reg["renderer"].render()
    pygame.display.set_caption(str(reg.window.fps))

