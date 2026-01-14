import random
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)

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
from pygame._sdl2 import Window as SDLWindow
from pygame._sdl2 import Renderer as SDLRenderer
from pygame._sdl2 import Texture

# set the sizes
render_size = (800, 450)
window_size = (1600, 900)
Window(flags=HWACCEL, fps_cap=0, size=window_size)

# initialize pygame
pygame.mixer.init()
pygame.font.init()

# create debug window
# debug_win = SDLWindow("debug", size=(300, 120))
# debug_ren = SDLRenderer(debug_win)
# debug_font = pygame.font.SysFont(None, 16)

AssetManager()
InputHandler()
PhysicsHandler()
MapManager().set_map("test")
Camera(0, [1], smoothing=3, origin=(300, 240))
Renderer(render_size=render_size)

# def draw_debug_window(t, fps, mouse_pos):
#     # set background color
#     debug_ren.draw_color = (0, 0, 0, 255)
#     debug_ren.clear()

#     lines = [
#         f"reflectivity: {t / 255.0}",
#         f"fps: {fps:.1f}",
#         f"mouse: ({mouse_pos[0]}, {mouse_pos[1]})",
#     ]

#     y = 10
#     for line in lines:
#         surf = debug_font.render(line, True, (255, 255, 255))
#         tex = Texture.from_surface(debug_ren, surf)

#         r = surf.get_rect()
#         r.topleft = (10, y)
#         debug_ren.blit(tex, r)
#         y += 18

#     debug_ren.present()

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

t = 200
def draw_rect_sides(surf, rect, colors, thickness):
    x, y, w, h = rect
    top, right, bottom, left = colors

    pygame.draw.line(surf, top,    (x, y),     (x+w, y),     thickness)
    pygame.draw.line(surf, right,  (x+w, y),   (x+w, y+h),   thickness)
    pygame.draw.line(surf, bottom, (x+w, y+h), (x,   y+h),   thickness)
    pygame.draw.line(surf, left,   (x,   y+h), (x,   y),     thickness)

while 1:
    reg["window"].update()
    reg["camera"].update()

    # vtest()
    pygame.draw.circle(reg["renderer"].layers[0]['absorption_surf'], (255, 255, 255), (200, 225), 32)
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (1, 1, 1), (200, 225), 32)

    pygame.draw.circle(reg["renderer"].layers[0]['absorption_surf'], (255, 255, 255), (600, 225), 32)
    pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (1, 1, 1), (600, 225), 32)

    pygame.draw.line(reg["renderer"].layers[0]['absorption_surf'], (255, 255, 255), (400, 0), (400, 200), 15)
    pygame.draw.line(reg["renderer"].layers[0]['absorption_surf'], (255, 255, 255), (400, 250), (400, 450), 15)
    pygame.draw.line(reg["renderer"].layers[0]['albedo_surf'], (1, 1, 1), (400, 0), (400, 200), 15)
    pygame.draw.line(reg["renderer"].layers[0]['albedo_surf'], (1, 1, 1), (400, 250), (400, 450), 15)

    # pygame.draw.rect(reg["renderer"].layers[0]['absorption_surf'], (255, 255, 255), (0, 0, 800, 450), 15)
    # pygame.draw.rect(reg["renderer"].layers[0]['albedo_surf'], (t, t, t), (0, 0, 800, 450), 15)
    draw_rect_sides(
        reg["renderer"].layers[0]['absorption_surf'],
        (0, 0, 800, 450),
        [(255,255,255), (255,255,255), (255,255,255), (255,255,255)],
        15
    )

    draw_rect_sides(
        reg["renderer"].layers[0]['albedo_surf'],
        (0, 0, 800, 450),
        [(t,0,0), (t,0,0), (0,0,t), (0,0,t)],
        15
    )

    if not reg.inputs['enable'].pressed:
        mp = list(reg.inputs.mouse_pos)
        mp[0] *= 0.5; mp[1] *= 0.5
        pygame.draw.circle(reg["renderer"].layers[0]['albedo_surf'], (1, 1, 1), mp, 4)
        pygame.draw.circle(reg["renderer"].layers[0]['emissive_surf'], (255, 255, 255), mp, 4)
        pygame.draw.circle(reg["renderer"].layers[0]['absorption_surf'], (255, 255, 255), mp, 4)
    
    if reg.inputs.mouse_scroll != 0:
        t += 5 * reg.inputs.mouse_scroll
        t = max(0, min(250, t))

    # reg.renderer.mark_dirty(0, 'unlit')
    reg.renderer.mark_dirty(0, 'albedo')
    reg["renderer"].render()
    pygame.display.set_caption(str(reg.window.fps))

    # draw_debug_window(t, reg.window.fps, reg.inputs.mouse_pos)

