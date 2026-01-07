import sys

import pygame
from pygame.locals import *

from toaster.misc.extra import load_json_file, button_code
from toaster.registry.registry import Registry
from toaster.registry.registry_item import RegistryItem

INPUTS_PATH = "config/inputs_config.json"
DEFAULT_INPUT_MAPPINGS = {"keyboard": {}, "mouse-button": {}, "mouse-wheel": {}}
VALID_EVENTS = (QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEWHEEL)


class InputHandler(RegistryItem):
    def __init__(self):
        super().__init__("inputs")
        config = load_json_file(INPUTS_PATH, DEFAULT_INPUT_MAPPINGS)

        self.mappings = {}
        self.inputs = {"key": {}, "button": {}, "wheel": {}}

        # go through key mappings
        for mapping, key in config['keyboard'].items():
            key_code = pygame.key.key_code(key)
            self.mappings[mapping] = ("key", key_code)
            self.inputs["key"][key_code] = InputState()

        # go through mouse button mappings
        for mapping, button in config['mouse-button'].items():
            key_code = button_code(button)
            self.mappings[mapping] = ("button", key_code)
            self.inputs["button"][key_code] = MouseInputState()

        self.mouse_pos = (0, 0)
        self.mouse_scroll = 0
        pygame.event.set_allowed(VALID_EVENTS)

    def __getitem__(self, key):
        mapping_info = self.mappings[key]
        return self.inputs[mapping_info[0]][mapping_info[1]]

    def update(self):
        # update mouse position
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_scroll = 0

        # process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.registry["renderer"].quit()
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                key = self.inputs["key"].get(event.key)
                if key: key.press()
            if event.type == KEYUP:
                key = self.inputs["key"].get(event.key)
                if key: key.unpress()

            if event.type == MOUSEBUTTONDOWN:
                button = self.inputs["button"].get(event.button)
                if button: button.press()
            if event.type == MOUSEBUTTONUP:
                button = self.inputs["button"].get(event.button)
                if button: button.unpress()

            if event.type == pygame.MOUSEWHEEL:
                self.mouse_scroll = event.y


class InputState:
    def __init__(self):
        self.pressed = False
        self.just_pressed = False
        self.just_released = False

    def press(self):
        self.pressed = True
        self.just_pressed = False

    def unpress(self):
        self.pressed = False
        self.just_released = False

    def update(self):
        self.just_pressed = False
        self.just_released = False


class MouseInputState(InputState):
    def __init__(self):
        super().__init__()

        self.press_position = (0, 0)
        self.unpress_position = (0, 0)

    def press(self):
        super().press()
        self.press_position = Registry.instance()['inputs'].mouse_pos

    def unpress(self):
        super().unpress()
        self.unpress_position = Registry.instance()['inputs'].mouse_pos
