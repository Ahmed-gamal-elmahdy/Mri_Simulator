import math
import numpy as np

def rotationX(matrix, angle):
    shape = np.shape(matrix)
    rows = shape[0]
    cols = shape[1]
    angle = (angle) * (math.pi / 180)
    newMatrix = np.zeros(shape)
    for i in range(0, rows):
        for j in range(0, cols):
            newMatrix[i, j] = np.dot(
                np.array([[1, 0, 0], [0, math.cos(angle), -1 * math.sin(angle)], [0, math.sin(angle), math.cos(angle)]]), matrix[i, j])
    return newMatrix


def gradientXY(matrix, stepY, stepX):
    shape = np.shape(matrix)
    rows = shape[0]
    cols = shape[1]
    newMatrix = np.zeros(shape)
    for i in range(0, rows):
        for j in range(0, cols):
            angle = stepY * j + stepX * i
            angle = (angle) * (math.pi / 180)
            newMatrix[i, j] = np.dot(
                np.array([[math.cos(angle), -1 * math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]]), matrix[i, j])
    return newMatrix


def reconstructImage(phantom):
    shape = np.shape(phantom)
    phantomSize = shape[0]
    kSpace = np.zeros((phantomSize, phantomSize), dtype=complex)
    imgVectors = np.zeros((phantomSize, phantomSize, 3))
    imgVectors[:, :, 2] = phantom
    angle = 90

    for i in range(0, phantomSize):
        rotatedMat = rotationX(imgVectors, angle)
        for j in range(0, phantomSize):
            stepX = (360 / phantomSize) * i
            stepY = (360 / phantomSize) * j
            phaseEncodedMatrix = gradientXY(rotatedMat, stepY, stepX)
            sigmaX = np.round(np.sum(phaseEncodedMatrix[:, :, 0]) , 3)
            sigmaY = np.round(np.sum(phaseEncodedMatrix[:, :, 1]) , 3)
            valueToAdd = complex(sigmaY, sigmaX)
            kSpace[i, j] = valueToAdd

        rotatedMat[:, :, 0] = 0
        rotatedMat[:, :, 1] = 0
        imgVectors = np.zeros((phantomSize, phantomSize, 3))
        imgVectors[:, :, 2] = phantom

    reconstructedImg = np.fft.ifft2(kSpace)
    reconstructedImg = np.round(np.abs(reconstructedImg),3)
    return reconstructedImg

phantom = [[1, 2, 3],[4, 5, 6],[7, 8, 9]]
k = reconstructImage(phantom)
