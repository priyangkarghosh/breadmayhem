from pygame import Rect

from toaster.misc.extra import load_json_file
from toaster.asset_loaders.map_loader import load_map
from toaster.physics.physics_handler import COLLISION_MATRIX, STATIC
from toaster.registry.registry_item import RegistryItem
from toaster.physics.physics_rect import PhysicsRect

MAPS_PATH = "config/maps_config.json"
DEFAULT_MAPS_CONFIG = {}
NEIGHBOUR_CHECKS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (0, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


class MapManager(RegistryItem):
    def __init__(self):
        super().__init__("maps")

        config = load_json_file(MAPS_PATH, DEFAULT_MAPS_CONFIG)
        self.maps = {map_id: load_map(path) for map_id, path in config.items()}
        for tilemap in self.maps.values(): self.render(None, tilemap)

        self.current_map_id = None

    @property
    def current_map(self):
        return self.maps[self.current_map_id]

    def set_map(self, map_id):
        if map_id in self.maps: self.current_map_id = map_id
        for rect in self.current_map.assets['coll_rects']:
            self.registry['physics'].add_physics_rect(PhysicsRect(STATIC, 0, rect))

    def get_grid_position(self, world_position):
        tile_size = self.current_map.tile_size
        return world_position[0] // tile_size[0], world_position[1] // tile_size[1]

    def get_collisions(self, obj, coll_layer):
        if isinstance(obj, Rect):
            return self.get_collisions_rect(obj, coll_layer)
        else:
            return self.get_collisions_point(obj, coll_layer)

    def get_collisions_rect(self, coll_rect, coll_layer):
        collisions = []
        assets = self.current_map.assets

        # find the grid positions for the coll_rect
        top_left_bound = self.get_grid_position(coll_rect.topleft)
        bottom_right_bound = list(self.get_grid_position(coll_rect.bottomright))
        if top_left_bound[0] != bottom_right_bound[0]: bottom_right_bound[0] -= 1
        if top_left_bound[1] != bottom_right_bound[1]: bottom_right_bound[1] -= 1
        bottom_right_bound = tuple(bottom_right_bound)

        # loop through every position
        for x in range(top_left_bound[0], bottom_right_bound[0] + 1):
            for y in range(top_left_bound[1], bottom_right_bound[1] + 1):
                neighbour_checks = [(0, 0)]
                # check the x positions
                if x == top_left_bound[0]: neighbour_checks.append((-1, 0))
                if x == bottom_right_bound[0]: neighbour_checks.append((1, 0))

                # check the y positions
                if y == top_left_bound[1]: neighbour_checks.append((0, -1))
                if y == bottom_right_bound[1]: neighbour_checks.append((0, 1))

                # check the diagonals
                if (x, y) == top_left_bound: neighbour_checks.append((-1, -1))  # top left
                if (x, y) == bottom_right_bound: neighbour_checks.append((1, 1))  # bottom right
                if (x, y) == (bottom_right_bound[0], top_left_bound[1]): neighbour_checks.append((1, -1))  # top right
                if (x, y) == (top_left_bound[0], bottom_right_bound[1]): neighbour_checks.append((-1, 1))  # bottom left

                # add the possible tile collisions
                for neighbour in neighbour_checks:
                    test_position = (x + neighbour[0], y + neighbour[1])
                    rect_info = assets['coll_tiles'].get(test_position, None)
                    if rect_info is not None and COLLISION_MATRIX[coll_layer][rect_info[2]]:
                        return_rect = assets['coll_rects'][rect_info[0]]
                        if return_rect not in collisions: collisions.append(return_rect)
        return collisions

    def get_collisions_point(self, point, coll_layer):
        collisions = []
        assets = self.current_map.assets

        grid_position = self.get_grid_position(point)
        for neighbour in NEIGHBOUR_CHECKS:
            test_position = (grid_position[0] + neighbour[0], grid_position[1] + neighbour[1])
            rect_info = assets['coll_tiles'].get(test_position, None)
            if rect_info and COLLISION_MATRIX[coll_layer][rect_info[2]]:
                return_rect = assets['coll_rects'][rect_info[0]]
                if return_rect not in collisions: collisions.append(return_rect)
        return collisions

    def render(self, map_id, tilemap=None):
        if tilemap is None: tilemap = self.maps[map_id]
        for i in range(tilemap.num_layers):
            self.render_layer(None, i, tilemap)
            tilemap.map_surf.blits((
                (tilemap.assets['grid_surfs'][i], (0, 0)),
                (tilemap.assets['grid_surfs'][i], (0, 0))
            ))

    def render_layer(self, map_id, layer, tilemap=None):
        if tilemap is None: tilemap = self.maps[map_id]
        tilemap.assets['grid_surfs'][layer].fill((0, 0, 0, 0))
        for tile in tilemap.assets['grid_tiles'][layer]:
            tilemap.assets['grid_surfs'][layer].blit(
                self.registry['assets'].get_tile_surf(tile), tile['world_position']
            )

        tilemap.assets['off_grid_surfs'][layer].fill((0, 0, 0, 0))
        for tile in tilemap.assets['off_grid_tiles'][layer]:
            tilemap.assets['off_grid_surfs'][layer].blit(
                self.registry['assets'].get_tile_surf(tile), tile['world_position']
            )
