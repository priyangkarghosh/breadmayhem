from pathlib import Path
from pygame import Rect

from toaster.asset_loaders.map_loader import load_map
from toaster.physics.physics_handler import COLLISION_MATRIX, STATIC
from toaster.registry.registry_item import RegistryItem
from toaster.physics.physics_rect import PhysicsRect

MAPS_DIR = "assets/maps"
NEIGHBOUR_CHECKS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (0, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


class MapManager(RegistryItem):
    def __init__(self):
        super().__init__("maps")
        
        maps_path = Path(MAPS_DIR)
        self.maps = {}

        # load all maps
        if maps_path.exists():
            for map in maps_path.glob("*.tmap"):
                tilemap = load_map(str(map))
                self._render_map(tilemap)  # cache rendered map
                self.maps[map.stem] = tilemap
        
        # current map is none
        self.current_map_id = None

    @property
    def current_map(self):
        return self.maps[self.current_map_id]

    def set_map(self, map_id):
        if map_id not in self.maps:
            return
            
        self.current_map_id = map_id
        
        # add collision rects to physics
        for rect in self.current_map.assets['coll_rects']:
            self.registry['physics'].add_physics_rect(PhysicsRect(STATIC, 0, rect))

    def _render_map(self, tilemap):
        for layer in range(tilemap.num_layers):
            # render grid tiles
            tilemap.assets['grid_surfs'][layer].fill((0, 0, 0, 0))
            for tile in tilemap.assets['grid_tiles'][layer]:
                tilemap.assets['grid_surfs'][layer].blit(
                    self.registry['assets'].get_tile_surf(tile), 
                    tile['world_position']
                )
            
            # render off-grid tiles
            tilemap.assets['off_grid_surfs'][layer].fill((0, 0, 0, 0))
            for tile in tilemap.assets['off_grid_tiles'][layer]:
                tilemap.assets['off_grid_surfs'][layer].blit(
                    self.registry['assets'].get_tile_surf(tile), 
                    tile['world_position']
                )
            
            # combine both onto the main map surface
            tilemap.map_surf.blit(tilemap.assets['grid_surfs'][layer], (0, 0))
            tilemap.map_surf.blit(tilemap.assets['off_grid_surfs'][layer], (0, 0))

    def get_grid_position(self, world_position):
        tile_size = self.current_map.tile_size
        return world_position[0] // tile_size[0], world_position[1] // tile_size[1]

    def get_collisions(self, obj, coll_layer):
        if isinstance(obj, Rect):
            return self._get_rect_collisions(obj, coll_layer)
        return self._get_point_collisions(obj, coll_layer)

    def _get_rect_collisions(self, coll_rect, coll_layer):
        collisions = []
        coll_tiles = self.current_map.assets['coll_tiles']
        coll_rects = self.current_map.assets['coll_rects']

        # get grid bounds
        top_left = self.get_grid_position(coll_rect.topleft)
        bottom_right = self.get_grid_position(coll_rect.bottomright)
        
        # check each grid cell that the rect overlaps
        for x in range(top_left[0], bottom_right[0] + 1):
            for y in range(top_left[1], bottom_right[1] + 1):
                # check this cell and its neighbors
                for dx, dy in NEIGHBOUR_CHECKS:
                    pos = (x + dx, y + dy)
                    rect_info = coll_tiles.get(pos)
                    
                    if rect_info and COLLISION_MATRIX[coll_layer][rect_info[2]]:
                        rect = coll_rects[rect_info[0]]
                        if rect not in collisions:
                            collisions.append(rect)
        
        return collisions

    def _get_point_collisions(self, point, coll_layer):
        collisions = []
        coll_tiles = self.current_map.assets['coll_tiles']
        coll_rects = self.current_map.assets['coll_rects']

        grid_pos = self.get_grid_position(point)
        
        # check neighboring cells
        for dx, dy in NEIGHBOUR_CHECKS:
            pos = (grid_pos[0] + dx, grid_pos[1] + dy)
            rect_info = coll_tiles.get(pos)
            
            if rect_info and COLLISION_MATRIX[coll_layer][rect_info[2]]:
                rect = coll_rects[rect_info[0]]
                if rect not in collisions:
                    collisions.append(rect)

        return collisions