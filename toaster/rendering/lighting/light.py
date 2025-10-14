class Light:
    def __init__(self, layer=0, tint=(255, 255, 255), intensity=0.01, opacity=0.2):
        self.layer = layer

        self.tint = tint
        self.opacity = opacity
        self.intensity = intensity
        self.enabled = True


class PointLight(Light):
    def __init__(self, position=(0, 0), direction=(1, 0), angle_range=-1, layer=0, radius=900, power=2,
                 tint=(255, 255, 255), intensity=0.01, opacity=0.5):
        super().__init__(layer, tint, intensity, opacity)
        self.position = list(position).copy()
        self.direction = list(direction).copy()

        self.angle_range = angle_range
        self.radius = radius
        self.power = power


class GlobalLight(Light):
    def __init__(self, layer=0, tint=(255, 255, 255), intensity=0.01, opacity=0.3):
        super().__init__(layer, tint, intensity, opacity)
