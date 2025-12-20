import os
import pygame.image
from toaster.misc.extra import load_json_file

TOP_LEFT_SHIFT = 0b0111   # 7: bottom-right, bottom, right pixels are split_colour
TOP_RIGHT_SHIFT = 0b1011  # 11: bottom-right, bottom, left pixels are split_colour

CONFIG_PATH = "config.json"
TEXTURE_PATH = "texture.png"
DEFAULT_CONFIG = {
    "colourkey": (0, 0, 0)
}

def load_spritesheet(path, split_colour=(255, 0, 255)):
    config = load_json_file(os.path.join(path, CONFIG_PATH), DEFAULT_CONFIG)
    sheet_surf = pygame.image.load(os.path.join(path, TEXTURE_PATH)).convert()
    sheet_surf.set_colorkey(config['colourkey'])
    
    width = sheet_surf.get_width()
    height = sheet_surf.get_height()
    
    # create 2d pixel array for fast access
    pxarray = pygame.surfarray.pixels2d(sheet_surf)
    split_val = sheet_surf.map_rgb(split_colour)
    
    sprites = {}
    sheet_pos_y = 0
    
    for y in range(height - 1):
        sheet_pos_x = 0
        tile_start = None
        tile_in_progress = False
        
        for x in range(width - 1):
            # check if current pixel matches split colour
            if pxarray[x, y] != split_val: continue
            
            # compute bitmask for 2x2 pixel block
            bshift = (
                1 |
                ((pxarray[x + 1, y] == split_val) << 1) |
                ((pxarray[x, y + 1] == split_val) << 2) |
                ((pxarray[x + 1, y + 1] == split_val) << 3)
            )
            
            if bshift == TOP_LEFT_SHIFT:
                # this would be the top left corner
                tile_in_progress = True
                tile_start = (x + 1, y + 1)
                
            elif bshift == TOP_RIGHT_SHIFT and tile_start is not None:
                # this would be the top right corner
                y2 = y + 1
                while y2 < height and pxarray[x, y2] != split_val:
                    y2 += 1
                
                # extract tile subsurface
                tile = sheet_surf.subsurface(
                    tile_start[0], 
                    tile_start[1],
                    x + 1 - tile_start[0],
                    y2 - tile_start[1]
                )

                sprites[(sheet_pos_x, sheet_pos_y)] = tile
                tile_in_progress = False
                sheet_pos_x += 1
        
        # move to next row if tiles were found on this row
        if tile_start is not None and not tile_in_progress:
            sheet_pos_y += 1

    # release pixel array lock
    del pxarray
    
    # return sprites
    return {
        'sprites': sprites,
        'config': config,
    }
