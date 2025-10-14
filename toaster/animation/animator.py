from pygame.math import clamp

from toaster.misc.extra import load_json_file
from toaster.registry.registry import Registry

COLOUR_KEY = (255, 255, 255)

DEFAULT_CONTROLLER_CONFIG = {
    'animations': None,
    'conditions': None,
    'default': None,
}


class AnimationController:
    def __init__(self, path):
        self.path = path

        # initialize the dicts
        self.animations = {}
        self.transitions = {}

        # load the config file
        config = load_json_file(path, DEFAULT_CONTROLLER_CONFIG)

        # initialize the conditions to false
        self.conditions = {con: False for con in config['conditions']}

        # should be in the form [name, transition]
        # a transition is in the form (condition, true/false, new animation)
        for anim in config['animations']:
            self.animations[anim[0]] = Animation(anim[0])
            self.transitions[anim[0]] = [transition for transition in anim[1]]

        # set the initial animation
        self.current_animation = config['default']

    @property
    def playing(self):
        return self.animations[self.current_animation]

    def update(self, dt):
        self.playing.play(dt)

        for t in self.transitions[self.current_animation]:
            if self.conditions[t[0]] == t[1]:
                self.change_animation(t[2])

    def change_animation(self, new_animation):
        self.playing.reset()
        self.current_animation = new_animation


class Animation:
    def __init__(self, name):
        self.paused = False
        self.current_frame = 0
        self.current_frame_time = 0
        self.animation = Registry.instance().get_animation(name)

    @property
    def frame_surf(self):
        return self.animation['surfs'][self.animation['frames'][self.current_frame]]

    def play(self, dt):
        if self.paused: return

        self.current_frame_time += dt
        if self.current_frame_time >= self.animation['config']['frame_time']:
            self.current_frame_time -= self.animation['config']['frame_time']
            self.change_frame(1)

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

    def reset(self):
        self.paused = False
        self.current_frame = 0
        self.current_frame_time = 0

    def change_frame(self, num_frames, reverse=False):
        if reverse: num_frames = -num_frames

        if self.animation['config']['looping']:
            self.current_frame = (self.current_frame + num_frames) % len(self.animation['frames'])
        else:
            self.current_frame = clamp(self.current_frame + num_frames, 0, len(self.animation['frames']) - 1)
            if self.current_frame == len(self.animation['frames']) - 1: self.pause()

    def rewind_time(self, amount):
        if amount < self.current_frame_time:
            self.current_frame_time -= amount
            return

        amount -= self.animation['config']['frame_time'] - self.current_frame_time
        self.change_frame(int(amount // self.animation['config']['frame_time']), True)
        self.current_frame_time = amount % self.animation['config']['frame_time']

    def rewind_frames(self, num_frames):
        self.change_frame(num_frames, True)
