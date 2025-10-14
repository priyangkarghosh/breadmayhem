import sys
import pygame

from toaster.registry.registry_item import RegistryItem


class ToasterApp(RegistryItem):
    def load(self):
        pass

    def update(self):
        pass

    def run(self):
        self.load()
        while True:
            self.update()

    def quit(self):
        pygame.quit()
        sys.exit()
