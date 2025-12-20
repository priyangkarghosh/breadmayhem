from math import copysign
from pygame import Rect
from toaster.entity.component import Component
from toaster.physics.physics_rect import *

VELOCITY_TOLERANCE = 30
TIME_TO_SLEEP = 0.47
MAX_STEP = 1.0


class RectCollider(Component, PhysicsRect):
    def __init__(self, size, collision_mode, collision_layer, offset=(0, 0), 
                 restitution=(0, 0), damping=(0, 0)):
        Component.__init__(self, "rect_collider")
        PhysicsRect.__init__(self, collision_mode=collision_mode, 
                           collision_layer=collision_layer)

        self.transform = None
        self.size = list(size)
        self.offset = list(offset)
        
        self._restitution = restitution
        self._damping = damping
        
        self._velocity = [0.0, 0.0]
        self._forces = [0.0, 0.0]
        
        self._awake = True
        self._sleep_timer = 0.0
        
        self.collision_directions = {
            'up': False, 'down': False, 'left': False, 'right': False
        }

    def on_attach(self):
        super().on_attach()
        self.transform = self.owner.get_component("transform")
        if self.transform is None:
            raise Exception("Entity does not have a transform component attached.")

    @property
    def awake(self):
        return self._awake

    @awake.setter
    def awake(self, value: bool):
        self._awake = value
        if not value:
            self._velocity = [0.0, 0.0]
            self._sleep_timer = 0.0

    @property
    def rect(self):
        return Rect(self.transform.position[0], self.transform.position[1], 
                   self.size[0], self.size[1])

    def step(self):
        if not self._awake:
            return
            
        dt = self.registry['window'].dt
        
        # Apply forces to velocity
        self._velocity[0] += self._forces[0] * dt
        self._velocity[1] += self._forces[1] * dt
        
        # Apply damping
        self._velocity[0] *= pow(1 - self._damping[0], dt)
        self._velocity[1] *= pow(1 - self._damping[1], dt)
        
        # Sleep logic
        if (abs(self._velocity[0]) < VELOCITY_TOLERANCE and 
            abs(self._velocity[1]) < VELOCITY_TOLERANCE):
            self._sleep_timer += dt
            if self._sleep_timer >= TIME_TO_SLEEP:
                self.awake = False
                return
        else:
            self._sleep_timer = 0.0
        
        # Move with collision resolution
        displacement = [self._velocity[0] * dt, self._velocity[1] * dt]
        self.move(displacement)

    def move(self, displacement):
        # Reset collision flags
        self.collision_directions = {
            'up': False, 'down': False, 'left': False, 'right': False
        }
        
        # Move X axis
        if displacement[0] != 0:
            self._move_axis(0, displacement[0])
        
        # Move Y axis
        if displacement[1] != 0:
            self._move_axis(1, displacement[1])

    def _move_axis(self, axis, amount):
        """Move along one axis and resolve collisions incrementally"""
        remaining = amount
        
        while abs(remaining) > 0.001:
            step = remaining
            if abs(step) > MAX_STEP:
                step = copysign(MAX_STEP, remaining)
            
            # Move
            self.transform.position[axis] += step
            
            # Get current collisions
            collisions = self.registry['physics'].get_collisions(self)
            
            # Check for overlaps
            my_rect = self.rect
            hit = False
            
            for other in collisions:
                other_rect = other.rect
                
                if my_rect.colliderect(other_rect):
                    hit = True
                    self._resolve_collision(axis, my_rect, other_rect, other, step)
                    break  # Resolve one collision at a time
            
            if hit:
                break  # Stop moving on this axis after collision
            
            remaining -= step

    def _resolve_collision(self, move_axis, my_rect, other_rect, other, step_amount):
        """Resolve a collision between two rectangles"""
        # Calculate overlap on both axes
        if my_rect.right > other_rect.left and my_rect.left < other_rect.left:
            overlap_x = my_rect.right - other_rect.left
        else:
            overlap_x = other_rect.right - my_rect.left
            
        if my_rect.bottom > other_rect.top and my_rect.top < other_rect.top:
            overlap_y = my_rect.bottom - other_rect.top
        else:
            overlap_y = other_rect.bottom - my_rect.top
        
        # Resolve on the axis with less penetration (or the move axis if similar)
        if move_axis == 0 or (overlap_x < overlap_y):
            # Resolve horizontally
            if step_amount > 0:  # Moving right
                self.transform.position[0] = other_rect.left - self.size[0]
                self.collision_directions['right'] = True
            else:  # Moving left
                self.transform.position[0] = other_rect.right
                self.collision_directions['left'] = True
            
            if other.dynamic:
                self._exchange_momentum(0, other)
            else:
                self._bounce(0)
        else:
            # Resolve vertically
            if step_amount > 0:  # Moving down
                self.transform.position[1] = other_rect.top - self.size[1]
                self.collision_directions['down'] = True
            else:  # Moving up
                self.transform.position[1] = other_rect.bottom
                self.collision_directions['up'] = True
            
            if other.dynamic:
                self._exchange_momentum(1, other)
            else:
                self._bounce(1)
        
        self.awake = True
        if hasattr(other, 'awake'):
            other.awake = True

    def _bounce(self, axis):
        """Apply restitution for static collision"""
        if abs(self._velocity[axis]) > VELOCITY_TOLERANCE:
            self._velocity[axis] *= -self._restitution[axis]
        else:
            self._velocity[axis] = 0

    def _exchange_momentum(self, axis, other):
        """Exchange momentum between two dynamic objects"""
        if other._awake and abs(other._velocity[axis]) > VELOCITY_TOLERANCE:
            # Both moving - exchange velocities with restitution
            temp = self._velocity[axis]
            self._velocity[axis] = other._velocity[axis] * self._restitution[axis]
            other._velocity[axis] = temp * other._restitution[axis]
        else:
            # Other is stationary - just bounce
            self._bounce(axis)