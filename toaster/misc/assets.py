from pathlib import Path
from toaster.registry.registry_item import RegistryItem
from toaster.asset_loaders.spritesheet_loader import load_spritesheet

ASSETS_PATH = Path("assets")

def load_assets_from_dir(
    root: str | Path,
    loader,
    *,
    allow_files: bool = False
) -> dict:
    root = Path(root)
    assets = {}

    if not root.exists():
        return assets

    for entry in root.iterdir():
        if entry.is_dir(): assets[entry.name] = loader(entry)
        elif allow_files and entry.is_file(): assets[entry.stem] = loader(entry)
    return assets

class AssetManager(RegistryItem):
    def __init__(self):
        super().__init__("assets")

        self.sheets = load_assets_from_dir(
            ASSETS_PATH / "spritesheets",
            load_spritesheet
        )

        self.shaders = load_assets_from_dir(
            ASSETS_PATH / "shaders",
            lambda p: p.read_text(),
            allow_files=True
        )

    def get_shader(self, name):
        return self.shaders[name]

    def get_tile_surf(self, tile):
        return self.sheets[tile['group']]['sprites'][tile['variant']]
