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
render_size = (600, 480)
window_size = (1200, 960)
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

while 1:
    reg["window"].update()
    reg["camera"].update()

    mp = list(reg.inputs.mouse_pos)
    mp[0] *= 0.5; mp[1] *= 0.5
    reg["renderer"].layers[0]['emissive_surf'].fill((255, 255, 255), (mp[0], mp[1], 5, 5))

    reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (70, 90, 25, 25))
    reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (400, 300, 25, 25))
    reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (50, 2, 5, 5))
    reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (300, 420, 15, 25))

    reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (70, 90, 25, 25))
    reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (400, 300, 25, 25))
    reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (50, 2, 5, 5))
    reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (300, 420, 15, 25))
    reg.renderer.mark_dirty(0, 'albedo')
    reg["renderer"].render()
