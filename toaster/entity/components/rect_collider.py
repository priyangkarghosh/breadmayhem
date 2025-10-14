from math import ceil

from pygame import Rect
from pygame.math import clamp
from toaster.entity.component import Component

from toaster.physics.physics_rect import *

VELOCITY_TOLERANCE = 30
TIME_TO_SLEEP = 0.47

MIN_PROCESS_DISPLACEMENT = 0.2
MAX_ITERATION_DISPLACEMENT = 1
MAX_ITERATIONS = 40


class RectCollider(Component, PhysicsRect):
    def __init__(self, size, collision_mode, collision_layer, offset=(0, 0), restitution=(0, 0), damping=(0, 0)):
        Component.__init__(self, "rect_collider")
        PhysicsRect.__init__(self, collision_mode=collision_mode, collision_layer=collision_layer)

        self.transform = None
        self.size = list(size).copy()
        self.offset = list(offset).copy()

        self._restitution = restitution
        self._damping = damping

        self._velocity = [0, 0]
        self._forces = [0, 0]
        self._last_shift = [0, 0]

        self._awake = True
        self._sleep_timer = 0.0

        self._collision_cache = []
        self.collision_directions = {
            'up': False, 'down': False, 'left': False, 'right': False
        }

    def on_attach(self):
        super().on_attach()
        self.transform = self.owner.get_component("transform")
        if self.transform is None:
            return Exception("Entity does not have a transform component attached.")

    @property
    def awake(self):
        return self._awake

    @awake.setter
    def awake(self, value: bool):
        if value:
            self._sleep_timer = 0.0
        else:
            self._sleep_timer = 0.0
            self._velocity = [0, 0]
            self._forces = [0, 320]
        self._awake = value

    @property
    def rect(self):
        return Rect(*self.transform.position, *self.size)

    def update_position(self, new_position):
        self.transform.position = new_position

    def step(self):
        if not self._awake: return
        self._velocity[0] += self._forces[0] * self.registry['window'].dt
        self._velocity[1] += self._forces[1] * self.registry['window'].dt
        self._velocity[0] *= pow(1 - self._damping[0], self.registry['window'].dt)
        self._velocity[1] *= pow(1 - self._damping[1], self.registry['window'].dt)

        # self.last_collision_cache += 1
        if abs(self._velocity[0]) < VELOCITY_TOLERANCE and abs(self._velocity[1]) < VELOCITY_TOLERANCE:
            self._sleep_timer += self.registry['window'].dt
            if self._sleep_timer >= TIME_TO_SLEEP:
                self.awake = False
                return
        else:
            self._sleep_timer = 0.0

        displacement = (self._velocity[0] * self.registry['window'].dt, self._velocity[1] * self.registry['window'].dt)
        self._collision_cache = self.registry['physics'].get_collisions(self)
        self.move(displacement)

    def move(self, displacement):
        # reset the collision directions
        self.collision_directions = {
            'up': False, 'down': False, 'left': False, 'right': False
        }

        # reset the shift
        self._last_shift = [0, 0]
        # possible_collisions.sort(key=lambda x: x.rect.x)
        if abs(displacement[0]) <= MAX_ITERATION_DISPLACEMENT:
            self._last_shift[0] = displacement[0]
            self.transform.position[0] += displacement[0]
            self.process_collisions()
        else:
            self.tunnel(0, displacement)

        # check the y direction
        self._last_shift = [0, 0]
        # possible_collisions.sort(key=lambda x: x.rect.y)
        if abs(displacement[1]) <= MAX_ITERATION_DISPLACEMENT:
            self._last_shift[1] = displacement[1]
            self.transform.position[1] += displacement[1]
            self.process_collisions()
        else:
            self.tunnel(1, displacement)
        self._last_shift = displacement

    def tunnel(self, ind, displacement):
        # ind will either always be 0(x) or 1(y)
        iterations = int(clamp(abs(displacement[ind] // MAX_ITERATION_DISPLACEMENT), 0, MAX_ITERATIONS))
        step = MAX_ITERATION_DISPLACEMENT if displacement[ind] > 0 else -MAX_ITERATION_DISPLACEMENT

        coll_found = False
        self._last_shift[ind], self._last_shift[not ind] = step, 0
        for i in range(iterations):
            self.transform.position[ind] += step
            if self.process_collisions():
                coll_found = True
                break

        if coll_found: return

        offset = displacement[ind] - iterations * step
        self._last_shift[ind], self._last_shift[not ind] = offset, 0
        self.transform.position[ind] += self._last_shift[ind]
        if abs(self._last_shift[ind]) > MIN_PROCESS_DISPLACEMENT:
            self.process_collisions()

    def process_collisions(self):
        coll = False
        temp_rect = self.rect
        for physics_rect in self._collision_cache:
            collision_rect = physics_rect.rect

            clip = list(collision_rect.clip(temp_rect).size)
            if clip[0] > 0 and clip[1] > 0:
                if clip[0] == temp_rect.width or clip[1] == temp_rect.height or clip[0] == clip[1]:
                    self.simple_resolve(temp_rect, collision_rect)
                else:
                    clip[0] /= float(temp_rect.width)
                    clip[1] /= float(temp_rect.height)

                    if physics_rect.dynamic:
                        self.dynamic_resolve(clip, temp_rect, collision_rect, physics_rect)
                    else:
                        self.static_resolve(clip, temp_rect, collision_rect)
                self.awake = True
                coll = True

            if temp_rect.left != int(self.transform.position[0]):
                self.transform.position[0] = temp_rect.left
            if temp_rect.top != int(self.transform.position[1]):
                self.transform.position[1] = temp_rect.top
        return coll

    def dynamic_resolve(self, clip, temp_rect, collision_rect, physics_rect):
        if clip[0] < clip[1]:
            delta = ceil(clip[0] / 2)
            if temp_rect.right > collision_rect.left > temp_rect.left:
                temp_rect.right -= delta
                collision_rect.right += delta
            else:
                temp_rect.right += delta
                collision_rect.right -= delta

            if physics_rect._awake:
                temp_velocity = self._velocity[0]
                self._velocity[0] = physics_rect._velocity[0] * self._restitution[0] * (
                        abs(physics_rect._velocity[0]) > VELOCITY_TOLERANCE)
                physics_rect._velocity[0] = temp_velocity * physics_rect._restitution[0] * (
                        abs(temp_velocity) > VELOCITY_TOLERANCE)
            else:
                self._velocity[0] *= -self._restitution[0] * (abs(self._velocity[0]) > VELOCITY_TOLERANCE)

        else:
            delta = ceil(clip[1] / 2)
            if temp_rect.top < collision_rect.bottom < temp_rect.bottom:
                temp_rect.top += delta
                collision_rect.top -= delta
            else:
                temp_rect.top -= delta
                collision_rect.top += delta

            if physics_rect._awake:
                temp_velocity = self._velocity[1]
                self._velocity[1] = physics_rect._velocity[1] * (abs(physics_rect._velocity[1]) > VELOCITY_TOLERANCE)
                physics_rect._velocity[1] = temp_velocity * (abs(temp_velocity) > VELOCITY_TOLERANCE)
            else:
                self._velocity[1] *= -self._restitution[1] * (abs(self._velocity[1]) > VELOCITY_TOLERANCE)

        if collision_rect.left != int(physics_rect.transform.position[0]):
            self.transform.position[0] = collision_rect.left
        if collision_rect.top != int(physics_rect.transform.position[1]):
            self.transform.position[1] = collision_rect.top
        physics_rect.awake = True
        self.awake = True

    def static_resolve(self, clip, temp_rect, collision_rect):
        if clip[0] < clip[1]:
            if temp_rect.right > collision_rect.left > temp_rect.left:
                temp_rect.right = collision_rect.left
                self.collision_directions['right'] = True
            else:
                temp_rect.left = collision_rect.right
                self.collision_directions['left'] = True
            self._velocity[0] *= -self._restitution[0] * (abs(self._velocity[0]) > VELOCITY_TOLERANCE)
        else:
            if temp_rect.top < collision_rect.bottom < temp_rect.bottom:
                temp_rect.top = collision_rect.bottom
                self.collision_directions['up'] = True
            else:
                temp_rect.bottom = collision_rect.top
                self.collision_directions['down'] = True
            self._velocity[1] *= -self._restitution[1] * (abs(self._velocity[1]) > VELOCITY_TOLERANCE)

    def simple_resolve(self, temp_rect, collision_rect):
        if abs(self._last_shift[0]) > abs(self._last_shift[1]):
            if self._last_shift[0] > 0:
                temp_rect.right = collision_rect.left
                self.collision_directions['right'] = True
            else:
                temp_rect.left = collision_rect.right
                self.collision_directions['left'] = True
            self._velocity[0] *= -self._restitution[0] * (abs(self._velocity[0]) > VELOCITY_TOLERANCE)
        else:
            if self._last_shift[1] < 0:
                temp_rect.top = collision_rect.bottom
                self.collision_directions['up'] = True
            else:
                temp_rect.bottom = collision_rect.top
                self.collision_directions['down'] = True
            self._velocity[1] *= -self._restitution[1] * (abs(self._velocity[1]) > VELOCITY_TOLERANCE)
