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
render_size = (400, 320)
window_size = (1200, 960)
Window(flags=HWACCEL, fps_cap=65, size=window_size)

# initialize pygame
pygame.mixer.init()

AssetManager()
InputHandler()
PhysicsHandler()
MapManager().set_map("test")
Camera(1, [4, 6, 12, 20, 32], smoothing=3, origin=(160, 90))
Renderer(render_size=render_size)

# TESTING
reg = Registry.instance()

# test rect
tests = []

# collision test
for i in range(200):
    test_rect = GameObject("test" + str(i), position=(48 + int(i / 10) * 12 + random.randint(-60, 60), int(i * -12) + i))
    test_rect.attach_component(RectCollider((5, 10), DYNAMIC, 1, restitution=(0.6, 0.6), damping=(0.6, 0.6)))
    test_rect = test_rect.get_component("rect_collider")
    test_rect._forces[1] = 320
    test_rect._velocity[0] = random.randint(-120, 120)
    tests.append(test_rect)
    reg["physics"].add_physics_rect(test_rect)
test_colours = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for i in range(len(tests))]

"""
# particle test
ps = ParticleSystem()
"""
# test_rect = GameObject("test", position=(52, -120))
reg['camera'].set_target((60, 30))

while 1:
    reg["window"].update()
    reg["camera"].update()

    avg = [0, 0]
    reg["physics"].update()
    # reg["physics"].rect_tree.render(display, (255, 0, 0, 120))
    for i, test_rect in enumerate(tests):
        if test_rect.rect.top > 500:
            test_rect.transform.position = [random.randint(16, 450), random.randint(-150, -100)]
        reg["renderer"].layers[1]['lit_surf'].fill(test_colours[i], (*reg["camera"].world_to_camera(1, test_rect.rect.topleft), *test_rect.rect.size))
        avg[0] += test_rect.transform.position[0]
        avg[1] += test_rect.transform.position[1]
    avg[0] /= len(tests)
    avg[1] /= len(tests)

    reg["renderer"].layers[0]['unlit_surf'].fill((255, 255, 255), (*reg["camera"].world_to_camera(0, (50, 50)), 160, 100))
    reg["renderer"].layers[3]['unlit_surf'].fill((255, 255, 255), (*reg["camera"].world_to_camera(3, (300, 0)), 100, 100))
    reg["renderer"].layers[1]['lit_surf'].blit(reg['maps'].current_map.map_surf, reg["camera"].world_to_camera(1, (0, 0)))

    reg["camera"].set_target(avg)

    reg["renderer"].layers[1]['render_lit'] = True
    reg["renderer"].layers[3]['render_unlit'] = True
    reg["renderer"].layers[0]['render_unlit'] = True
    reg["renderer"].render()

    print(reg["window"].fps)
