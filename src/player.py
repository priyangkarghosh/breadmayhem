from toaster.entity.game_object import GameObject


class Player(GameObject):
    def __init__(self):
        super().__init__("player")
