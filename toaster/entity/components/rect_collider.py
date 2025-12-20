from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING
if TYPE_CHECKING: from components.transform import Transform

from math import copysign
from pygame import Rect
from toaster.entity.component import Component
from toaster.physics.physics_rect import PhysicsRect


VELOCITY_TOLERANCE: float = 30.0
TIME_TO_SLEEP: float = 0.47
MAX_STEP: float = 1.0


class RectCollider(Component, PhysicsRect):
    def __init__(
        self,
        size: Tuple[float, float],
        collision_mode: int,
        collision_layer: int,
        offset: Tuple[float, float] = (0, 0),
        restitution: Tuple[float, float] = (0, 0),
        damping: Tuple[float, float] = (0, 0)
    ) -> None:
        Component.__init__(self, "rect_collider")
        PhysicsRect.__init__(
            self,
            collision_mode=collision_mode,
            collision_layer=collision_layer
        )

        self.transform: Optional['Transform'] = None
        self.size: List[float] = list(size)
        self.offset: List[float] = list(offset)
        
        self._restitution: Tuple[float, float] = restitution
        self._damping: Tuple[float, float] = damping
        
        self._velocity: List[float] = [0.0, 0.0]
        self._forces: List[float] = [0.0, 0.0]
        
        self._awake: bool = True
        self._sleep_timer: float = 0.0
        
        self.collision_directions: Dict[str, bool] = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }

    def on_attach(self) -> None:
        super().on_attach()
        assert self.owner
        
        transform = self.owner.get_component("transform")
        if transform is None: raise Exception("Entity does not have a transform component attached.")
        self.transform = transform  # type: ignore

    @property
    def awake(self) -> bool:
        return self._awake

    @awake.setter
    def awake(self, value: bool) -> None:
        self._awake = value
        if not value:
            self._velocity = [0.0, 0.0]
            self._sleep_timer = 0.0

    @property
    def rect(self) -> Rect:
        if self.transform is None:
            raise RuntimeError("Transform not initialized")
        return Rect(
            self.transform.position[0],
            self.transform.position[1],
            self.size[0],
            self.size[1]
        )

    def step(self) -> None:
        if not self._awake: return
            
        dt: float = self.registry['window'].dt
        
        # apply forces to velocity
        self._velocity[0] += self._forces[0] * dt
        self._velocity[1] += self._forces[1] * dt
        
        # apply damping
        self._velocity[0] *= pow(1 - self._damping[0], dt)
        self._velocity[1] *= pow(1 - self._damping[1], dt)
        
        # sleep logic
        if (abs(self._velocity[0]) < VELOCITY_TOLERANCE and 
            abs(self._velocity[1]) < VELOCITY_TOLERANCE):
            self._sleep_timer += dt
            if self._sleep_timer >= TIME_TO_SLEEP:
                self.awake = False
                return
        else:
            self._sleep_timer = 0.0
        
        # Move with collision resolution
        displacement: List[float] = [self._velocity[0] * dt, self._velocity[1] * dt]
        self.move(displacement)

    def move(self, displacement: List[float]) -> None:
        # reset collision flags
        self.collision_directions = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }
        
        # move x axis
        if displacement[0] != 0:
            self._move_axis(0, displacement[0])
        
        # move y axis
        if displacement[1] != 0:
            self._move_axis(1, displacement[1])

    def _move_axis(self, axis: int, amount: float) -> None:
        if self.transform is None: raise RuntimeError("Transform not initialized")
            
        remaining: float = amount
        while abs(remaining) > 0.001:
            step: float = remaining
            if abs(step) > MAX_STEP:
                step = copysign(MAX_STEP, remaining)
            
            # move
            self.transform.position[axis] += step
            
            # get current collisions
            collisions: List[RectCollider] = self.registry['physics'].get_collisions(self)
            
            # check for overlaps
            my_rect: Rect = self.rect
            hit: bool = False
            
            for other in collisions:
                other_rect: Rect = other.rect
                if my_rect.colliderect(other_rect):
                    hit = True
                    self._resolve_collision(axis, my_rect, other_rect, other, step)
                    break  # resolve one collision at a time
            
            if hit: break  # stop moving on this axis after collision
            remaining -= step

    def _resolve_collision(
        self,
        move_axis: int,
        my_rect: Rect,
        other_rect: Rect,
        other: 'RectCollider',
        step_amount: float
    ) -> None:
        if self.transform is None:
            raise RuntimeError("Transform not initialized")
            
        # calculate overlap on both axes
        if my_rect.right > other_rect.left and my_rect.left < other_rect.left:
            overlap_x: float = my_rect.right - other_rect.left
        else:
            overlap_x = other_rect.right - my_rect.left
            
        if my_rect.bottom > other_rect.top and my_rect.top < other_rect.top:
            overlap_y: float = my_rect.bottom - other_rect.top
        else:
            overlap_y = other_rect.bottom - my_rect.top
        
        # resolve on the axis with less penetration (or the move axis if similar)
        if move_axis == 0 or (overlap_x < overlap_y):
            # resolve horizontally
            if step_amount > 0:  # moving right
                self.transform.position[0] = other_rect.left - self.size[0]
                self.collision_directions['right'] = True
            else:  # moving left
                self.transform.position[0] = other_rect.right
                self.collision_directions['left'] = True
            
            if hasattr(other, 'dynamic') and other.dynamic:
                self._exchange_momentum(0, other)
            else:
                self._bounce(0)
        else:
            # resolve vertically
            if step_amount > 0:  # moving down
                self.transform.position[1] = other_rect.top - self.size[1]
                self.collision_directions['down'] = True
            else:  # moving up
                self.transform.position[1] = other_rect.bottom
                self.collision_directions['up'] = True
            
            if hasattr(other, 'dynamic') and other.dynamic:
                self._exchange_momentum(1, other)
            else:
                self._bounce(1)
        
        self.awake = True
        if hasattr(other, 'awake'):
            other.awake = True

    def _bounce(self, axis: int) -> None:
        if abs(self._velocity[axis]) > VELOCITY_TOLERANCE:
            self._velocity[axis] *= -self._restitution[axis]
        else: self._velocity[axis] = 0.0

    def _exchange_momentum(self, axis: int, other: 'RectCollider') -> None:
        if (hasattr(other, '_awake') and other._awake and 
            hasattr(other, '_velocity') and abs(other._velocity[axis]) > VELOCITY_TOLERANCE):

            temp: float = self._velocity[axis]
            self._velocity[axis] = other._velocity[axis] * self._restitution[axis]
            if hasattr(other, '_restitution'): other._velocity[axis] = temp * other._restitution[axis]
        else: self._bounce(axis)
