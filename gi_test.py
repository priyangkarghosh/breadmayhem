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

while 1:
    reg["window"].update()
    reg["camera"].update()

    # pygame.draw.rect(reg["renderer"].layers[0]['occlusion_surf'], (255, 255, 255), (300 - 25, 240 - 25, 50, 50))
    # pygame.draw.rect(reg["renderer"].layers[0]['emissive_surf'], (255, 255, 255), (300 - 25, 240 - 25, 50, 50))

    # mp = list(reg.inputs.mouse_pos)
    # pygame.draw.circle(reg["renderer"].layers[0]['occlusion_surf'], (255, 255, 255), (mp[0], mp[1]), 25)
    # pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (12, 25, 255), (mp[0], mp[1]), 25)

    #pygame.draw.circle(reg["renderer"].layers[0]['occlusion_surf'], (255, 255, 255), (384, 384), 25)
    #pygame.draw.circle(reg["renderer"].layers[0]['emissive_surf'], (255, 255, 0), (384, 384), 25)

    #pygame.draw.circle(reg["renderer"].layers[0]['occlusion_surf'], (100, 100, 100), (704, 504), 24)
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (100, 100, 100), (704, 504), 24)
    pygame.draw.circle(reg["renderer"].layers[0]['emissive_surf'], (255, 0, 255), (704, 504), 24)

    #pygame.draw.circle(reg["renderer"].layers[0]['occlusion_surf'], (255, 255, 255), (455, 402), 15)
    #pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (255, 255, 255), (455, 402), 15)


    # reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (70, 90, 25, 25))
    # reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (400, 300, 25, 25))
    # reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (50, 2, 5, 5))
    # reg["renderer"].layers[0]['albedo_surf'].fill((255, 255, 255), (300, 420, 15, 25))

    # reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (70, 90, 25, 25))
    # reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (400, 300, 25, 25))
    # reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (50, 2, 5, 5))
    # reg["renderer"].layers[0]['occlusion_surf'].fill((255, 255, 255), (300, 420, 15, 25))
    reg.renderer.mark_dirty(0, 'albedo')
    reg["renderer"].render()
