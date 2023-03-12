import math
import numpy as np

from Mri_Simulator.scripts import modifiedPhantom


def getPhantom(size):
    size=int(size)
    #phantom = sigpy.shepp_logan([size, size], dtype=float)
    phantom= modifiedPhantom.modshepp_logan([size, size], dtype=float)
    phantom = phantom * (255 / np.max(phantom))
    return phantom





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


def construct(matrix,img):
    rows = matrix.shape[0]
    cols = matrix.shape[1]
    res = np.zeros(np.shape(matrix))
    for i in range(0, rows):
        for j in range(0, cols):
            exp = np.array([[np.exp(-1 / (img[i][j])), 0, 0],
                            [0, np.exp(-1 / (img[i][j])), 0],
                            [0, 0, 1]])
            res[i, j] = np.dot(exp,matrix[i][j])
    return res



def reconstructImage(img):
    size=np.shape(img)[0]
    kSpace = np.zeros((size, size), dtype=np.complex_)
    vectors = np.zeros((size, size, 3))
    vectors[:, :, 2] = 1

    for i in range(0, size):
        rotatedMatrix = rotateX(vectors,90)
        decayedRotatedMatrix = construct(rotatedMatrix,img)
        for j in range(0, size):
            stepX = (360 / size) * i
            stepY = (360 / size) * j
            phaseEncodedMatrix = gradientXY(decayedRotatedMatrix, stepY, stepX)
            sigmaX = np.sum(phaseEncodedMatrix[:, :, 0])
            sigmaY = np.sum(phaseEncodedMatrix[:, :, 1])
            valueToAdd = complex(sigmaX, sigmaY)
            kSpace[i, j] = valueToAdd
        decayedRotatedMatrix[:, :, 0] = 0
        decayedRotatedMatrix[:, :, 1] = 0

    print(np.fft.fft2(kSpace))


