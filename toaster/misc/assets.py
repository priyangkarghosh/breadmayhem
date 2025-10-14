from pathlib import Path
from toaster.misc.extra import load_json_file
from toaster.registry.registry_item import RegistryItem
from toaster.asset_loaders.animation_loader import load_animation
from toaster.asset_loaders.spritesheet_loader import load_spritesheet

ASSETS_PATH = "config/assets_config.json"
DEFAULT_ASSETS_CONFIG = {
    "sheets": {},
    "animations": {},
    "maps": {},
    "shaders": {}
}


class AssetManager(RegistryItem):
    def __init__(self):
        super().__init__("assets")

        config = load_json_file(ASSETS_PATH, DEFAULT_ASSETS_CONFIG)
        self.sheets = {name: load_spritesheet(path) for name, path in config['sheets'].items()}
        self.animations = {name: load_animation(path) for name, path in config['animations'].items()}
        self.shaders = {name: Path(path).read_text() for name, path in config['shaders'].items()}

    def get_shader(self, name):
        return self.shaders[name]

    def get_animation(self, name):
        return self.animations[name]

    def get_tile_surf(self, tile):
        return self.sheets[tile['group']]['sprites'][tile['variant']]
