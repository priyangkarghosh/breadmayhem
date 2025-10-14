import json

from toaster.misc.extra import tuplify
from pygame import Rect, Surface, SRCALPHA


# does NOT render the tilemap
def load_map(path):
    if not path or path.split('.')[-1] != "tmap": return

    data = {}
    try:
        with open(path, 'r') as file:
            data = json.load(file)
        file.close()
    except FileNotFoundError:
        return

    tile_size = tuplify(data['tile_size'])
    grid_size = tuplify(data['grid_size'])
    tilemap = TileMap(tile_size, grid_size, data['num_layers'])

    for layer in data['grid_tiles'].values():
        for tile in layer:
            tile['variant'] = tuplify(tile['variant'])
            tile['grid_position'] = tuplify(tile['grid_position'])
            tile['world_position'] = tuplify(tile['world_position'])
            tilemap.assets['grid_tiles'][tile['layer']].append(tile)

    for layer in data['off_grid_tiles'].values():
        for tile in layer:
            tile['variant'] = tuplify(tile['variant'])
            tile['world_position'] = tuplify(tile['world_position'])
            tilemap.assets['off_grid_tiles'][tile['layer']].append(tile)

    for rect_data in data['collision_rects']:
        collision_rect = Rect(tuplify(rect_data['topleft']), tuplify(rect_data['size']))
        tilemap.assets['coll_rects'].append(collision_rect)

    for pos, data in data['collision_tiles'].items():
        tilemap.assets['coll_tiles'][tuplify(pos)] = tuplify(data)

    return tilemap


class TileMap:
    def __init__(self, tile_size, grid_size, num_layers):
        self.tile_size = tile_size
        self.grid_size = grid_size
        self.num_layers = num_layers

        self.world_size = (
            self.tile_size[0] * self.grid_size[0],
            self.tile_size[1] * self.grid_size[1]
        )

        self.assets = {
            'grid_tiles': [], 'off_grid_tiles': [],
            'grid_surfs': [], 'off_grid_surfs': [],
            'coll_tiles': {}, 'coll_rects': [],
        }

        self.map_surf = Surface(self.world_size, SRCALPHA)
        for i in range(self.num_layers):
            self.assets['grid_tiles'].append([])
            self.assets['off_grid_tiles'].append([])

            self.assets['grid_surfs'].append(self.map_surf.copy())
            self.assets['off_grid_surfs'].append(self.map_surf.copy())
