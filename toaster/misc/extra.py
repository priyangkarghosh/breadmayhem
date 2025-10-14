import json

from pygame.locals import *


def rect_area(rect):
    return rect.width * rect.height


def button_code(name):
    match name:
        case "lmb":
            return BUTTON_LEFT
        case "mmb":
            return BUTTON_MIDDLE
        case "mmb":
            return BUTTON_RIGHT
        case "mwu":
            return BUTTON_WHEELUP
        case "mwd":
            return BUTTON_WHEELUP
        case _:
            raise ValueError


def load_json_file(path, default):
    try:
        with open(path, 'r') as file:
            data = json.load(file)
        file.close()

    except FileNotFoundError:
        data = default
        with open(path, 'w') as file:
            file.write(json.dumps(data))
        file.close()
    return data


# turn a tuple into a string
def stringify(value):
    if isinstance(value, int): return str(value) + "i"
    if isinstance(value, float): return str(value) + "f"
    if isinstance(value, str): return str(value) + "s"
    if isinstance(value, tuple):
        return '(' + ', '.join([stringify(i) for i in value]) + ')'


# turn a string into a tuple
def tuplify(string):
    tuplified = string[1:-1].split(', ')

    i = 0
    nest_starts = []
    length = len(tuplified)
    while i < length:
        if tuplified[i][0] == '(':
            nest_starts.append(i)
            tuplified[i] = tuplified[i][1:]

        elif tuplified[i][-1] == ')':
            tuplified[i] = tuplified[i][0:-1]

            # tuplify the nested tuple
            start_index = nest_starts.pop()
            tuplified[i] = tuple([str_to_type(tuplified[j]) for j in range(start_index, i + 1)])
            tuplified = tuplified[0:start_index] + tuplified[i:]

            # update the old indices
            offset = start_index - i
            nest_starts = [j if j < start_index else j + offset for j in nest_starts]
            length += offset

            # offset the current index
            i = start_index
        i += 1

    return tuple([str_to_type(j) for j in tuplified])


# in form 3i or 2.0f
def str_to_type(string):
    match string[-1]:
        case 'i':
            return int(string[0:-1])
        case 'f':
            return float(string[0:-1])
        case 's':
            return string[0:-1]
    return string
