from os import listdir

import pygame

from toaster.misc.extra import load_json_file

DEFAULT_ANIMATION_CONFIG = {
    'frames': [],
    'looping': True,
    'frame_time': 0.2,
    'pivot': [0, 0],
    'colour_key': (0, 0, 0),
}


def load_img(path, colourkey):
    img = pygame.image.load(path).convert()
    img.set_colorkey(colourkey)
    return img


def load_animation(path):
    config_path = path + "/config.json"
    config = load_json_file(config_path, DEFAULT_ANIMATION_CONFIG)

    # get a list of all the image surfaces
    image_list = [
        (int(img.split('.')[0]), load_img(path + '/' + img, config['colourkey']))
        for img in listdir(path) if img.split('.')[-1] == 'png'
    ]

    # sort the images to make sure they're in the right order
    image_list.sort(key=lambda x: x[0])
    image_list = [v[1] for v in image_list]

    # make sure config['frames'] is defined
    if not config['frames']:
        config['frames'] = [1 for i in range(len(image_list))]

    # set up the final animation list
    frames = []
    for index, repeats in enumerate(config['frames']):
        frames.extend([index] * repeats)

    return {
        'config': config,
        'frames': frames,
        'surfs': image_list
    }
