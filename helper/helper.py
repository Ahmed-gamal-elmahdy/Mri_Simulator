import math
import numpy as np


def rotateX(matrix, angle):
    shape = np.shape(matrix)
    angle = angle * (math.pi / 180)
    res = np.zeros(shape)
    for i in range(0, shape[0]):
        for j in range(0, shape[1]):
            res[i, j] = np.dot(
                np.array([[1, 0, 0],
                          [0, math.cos(angle), -1 * math.sin(angle)],
                          [0, math.sin(angle), math.cos(angle)]])
                , matrix[i, j])
    return res


def rotateZ(matrix, angle):
    shape = np.shape(matrix)
    angle = angle * (math.pi / 180)
    res = np.zeros(shape)
    for i in range(0, shape[0]):
        for j in range(0, shape[1]):
            res[i, j] = np.dot(
                np.array([[math.cos(angle), -1 * math.sin(angle), 0],
                          [math.sin(angle), math.cos(angle), 0],
                          [0, 0, 1]])
                , matrix[i, j])
    return res


def gradientXY(matrix, stepX, stepY):
    shape = np.shape(matrix)
    res = np.zeros(shape)
    for i in range(0, shape[0]):
        for j in range(0, shape[1]):
            angle = (stepY * j + stepX * i) * (math.pi / 180)
            res[i, j] = np.dot(
                np.array([[math.cos(angle), -1 * math.sin(angle), 0],
                          [math.sin(angle), math.cos(angle), 0],
                          [0, 0, 1]])
                , matrix[i, j])
    return res
