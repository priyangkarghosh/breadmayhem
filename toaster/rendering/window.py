import time
import pygame

from pygame.locals import *

from toaster.registry.registry_item import RegistryItem


class Window(RegistryItem):
    def __init__(self, size=(640, 480), caption='test_window', flags=0, fps_cap=65, dt_cap=0.2):
        super().__init__("window")

        self.size = size
        self.background_colour = (0, 0, 0)
        self.flags = flags | OPENGL | DOUBLEBUF

        self.fps_cap, self.dt_cap = fps_cap, dt_cap
        self.start_time = self.time = self.last_frame_time = time.time()
        self.frame_log, self.dt = [], 0

        pygame.init()
        pygame.display.set_caption(caption)
        self.screen = pygame.display.set_mode(self.size, self.flags)
        self.clock = pygame.time.Clock()

    @property
    def runtime(self):
        return self.time - self.start_time

    @property
    def fps(self):
        return len(self.frame_log) / sum(self.frame_log)

    def update(self):
        # render the frame
        pygame.display.flip()
        self.clock.tick(self.fps_cap)

        # calculate dt
        self.time = time.time()
        self.dt = min(self.time - self.last_frame_time, self.dt_cap)
        self.last_frame_time = self.time

        # add dt to the frame log
        self.frame_log.append(self.dt)
        self.frame_log = self.frame_log[-self.fps_cap:]

        # process input
        self.registry['inputs'].update()

        # reset the screen
        self.screen.fill(self.background_colour)
