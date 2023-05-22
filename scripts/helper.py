import math

import numpy as np

from scripts import modifiedPhantom


def getPhantom(size):
    size = int(size)
    phantom = modifiedPhantom.modshepp_logan((size, size), dtype=float)
    phantom = phantom * (255 / np.max(phantom))
    return phantom


def rotationX(self, matrix, angle):
    shape = np.shape(matrix)
    rows = shape[0]
    cols = shape[1]
    angle = angle * (math.pi / 180)
    newMatrix = np.zeros(shape)
    for i in range(0, rows):
        for j in range(0, cols):
            newMatrix[i, j] = np.dot(
                np.array(
                    [[1, 0, 0], [0, math.cos(angle), -1 * math.sin(angle)], [0, math.sin(angle), math.cos(angle)]]),
                matrix[i, j])
    return newMatrix


def gradientXY(self, matrix, stepY, stepX):
    shape = np.shape(matrix)
    rows = shape[0]
    cols = shape[1]
    newMatrix = np.zeros(shape)
    for i in range(0, rows):
        for j in range(0, cols):
            angle = stepY * j + stepX * i
            angle = (angle) * (math.pi / 180)
            newMatrix[i, j] = np.dot(
                np.array(
                    [[math.cos(angle), -1 * math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]]),
                matrix[i, j])
    return newMatrix


def prepImage(self):
    shape = np.shape(self.weighted)
    phantomSize = shape[0]
    imgVectors = np.zeros((phantomSize, phantomSize, 3))
    imgVectors[:, :, 2] = self.weighted

    if(self.prepDataRef["Title"] == "T1-Prep"):
        angle = self.prepDataRef["FA"]
        for i in range(0, phantomSize):
            rotatedMat = rotationX(self, imgVectors, angle)
    else:
        angle = self.prepDataRef["FA"][0]
        for i in range(0, phantomSize):
            rotatedMat = rotationX(self, imgVectors, angle)
        angle = self.prepDataRef["FA"][1]
        for i in range(0, phantomSize):
            rotatedMat = rotationX(self, rotatedMat, angle)

    return rotatedMat

def reconstructImage(self):
    shape = np.shape(self.weighted)
    phantomSize = shape[0]
    kSpace = np.zeros((phantomSize, phantomSize), dtype=complex)
    imgVectors = np.zeros((phantomSize, phantomSize, 3))
    imgVectors= prepImage(self)

    for i in range(0, phantomSize):
        rotatedMat = rotationX(self, imgVectors, self.seqDataRef["FA"])
        decayedRotatedMatrix = decay(rotatedMat, self.T2, self.seqDataRef["TE"])
        for j in range(0, phantomSize):
            stepX = (360 / phantomSize) * i
            stepY = (360 / phantomSize) * j
            phaseEncodedMatrix = gradientXY(self, decayedRotatedMatrix, stepY, stepX)
            sigmaX = np.round(np.sum(phaseEncodedMatrix[:, :, 0]), 5)
            sigmaY = np.round(np.sum(phaseEncodedMatrix[:, :, 1]), 5)
            valueToAdd = complex(-1 * sigmaY, -1 * sigmaX)
            kSpace[i, j] = valueToAdd

        imgVectors = recovery(decayedRotatedMatrix, self.T1, self.seqDataRef["TR"])
        decayedRotatedMatrix[:, :, 0] = 0
        decayedRotatedMatrix[:, :, 1] = 0
        self.setKspaceimg(kSpace)

    reconstructedImg = np.fft.ifft2(kSpace)
    reconstructedImg = np.round(np.abs(reconstructedImg), 0)
    self.setKspaceimg(kSpace)
    return reconstructedImg


def decay(matrix, T2, t):
    rows = matrix.shape[0]
    cols = matrix.shape[1]
    decayedMat = np.zeros(np.shape(matrix))
    for i in range(0, rows):
        for j in range(0, cols):
            exp = np.array([[np.exp(-t / (T2[i][j])), 0, 0],
                            [0, np.exp(-t / (T2[i][j])), 0],
                            [0, 0, 1]])
            decayedMat[i, j] = exp.dot(matrix[i][j])
    return decayedMat


def recovery(matrix, T1, t=1):
    rows = matrix.shape[0]
    cols = matrix.shape[1]
    recoveryMat = np.zeros(np.shape(matrix))
    for i in range(0, rows):
        for j in range(0, cols):
            exp = np.array([[1, 0, 0],
                            [0, 1, 0],
                            [0, 0, np.exp(-t / (T1[i][j]))]])
            recoveryMat[i, j] = exp.dot(matrix[i][j]) + np.array([0, 0, 1 - np.exp(-t / (T1[i][j]))])
    return recoveryMat
