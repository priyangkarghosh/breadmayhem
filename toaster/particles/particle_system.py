import numpy
from pygame import Rect

TEST_NUMBER = 1


class ParticleSystem:
    def __init__(self):
        self.positions = numpy.array([(numpy.random.randint(0, 800), 0.0) for i in range(TEST_NUMBER)])
        self.previous_positions = numpy.array(
            [self.positions[i] + (numpy.random.randint(-20, 20), numpy.random.randint(-2, 2)) for i in
             range(TEST_NUMBER)])
        self.forces = numpy.array([(0, 320) for i in range(TEST_NUMBER)])
        self.coll_set = set()

    def update(self, dt, map):
        self.coll_set.clear()
        displacement = self.positions - self.previous_positions
        self.previous_positions = self.positions.copy() + displacement * dt * 0.7
        self.positions += displacement + self.forces * dt ** 2

        for i in range(TEST_NUMBER):
            self.handle(map, displacement, i)

            if self.positions[i][0] > 400:
                self.positions[i][0] = 400
                self.previous_positions[i][0] = self.positions[i][0] + displacement[i][0] * 0.6
            if self.positions[i][0] < 0:
                self.positions[i][0] = 0
                self.previous_positions[i][0] = self.positions[i][0] + displacement[i][0] * 0.6
            if self.positions[i][1] > 460:
                self.positions[i][1] = 460
                self.previous_positions[i][1] = self.positions[i][1] + displacement[i][1] * 0.6
            if self.positions[i][1] < 0:
                self.positions[i][1] = 0
                self.previous_positions[i][1] = self.positions[i][1] + displacement[i][1] * 0.6

    def handle(self, map, displacement, i):
        for tile in map.get_collisions(self.positions[i], 1):
            self.coll_set.add((*tile.topleft, *tile.size))
            if tile.collidepoint(self.positions[i]):
                left_distance = self.positions[i][0] - tile.left
                right_distance = tile.right - self.positions[i][0]
                top_distance = self.positions[i][1] - tile.top
                bottom_distance = tile.bottom - self.positions[i][1]

                min_distance = min(left_distance, right_distance, top_distance, bottom_distance)
                if min_distance == left_distance:
                    self.positions[i][0] = tile.left
                elif min_distance == right_distance:
                    self.positions[i][0] = tile.right
                elif min_distance == top_distance:
                    self.positions[i][1] = tile.top
                else:
                    self.positions[i][1] = tile.bottom

                    # Adjust previous positions based on the updated positions
                if min_distance in {left_distance, right_distance}:
                    self.previous_positions[i][0] = self.positions[i][0] + displacement[i][0] * 0.6
                else:
                    self.previous_positions[i][1] = self.positions[i][1] + displacement[i][1] * 0.6
