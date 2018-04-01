import numpy as np
from vectors import Point


def two_bytes_to_number(byte_high, byte_low):
    number_result = 256 * byte_low + byte_high
    if number_result >= 32768:
        number_result -= 65536
    return number_result


def ellispoid_fit(data):
    center = Point(0, 0, 0)
    radii = Point(0, 0, 0)
    evecs = np.matrix([[0, 0, 0],
                       [0, 0, 0],
                       [0, 0, 0]])
    if not len(data) == 3:
        return False
    xs = data[0]
    if not len(xs) > 8:
        return False
    ys = data[1]
    if not len(ys) > 8:
        return False
    zs = data[2]
    if not len(zs) > 8:
        return False


