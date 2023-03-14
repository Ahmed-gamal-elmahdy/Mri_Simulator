import math
import numpy as np

from scripts import modifiedPhantom


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


def reconstructImage(self):
    kSpace = np.zeros((self.phantomSize, self.phantomSize), dtype=np.complex_)
    vectors = np.zeros((self.phantomSize, self.phantomSize, 3))
    vectors[:, :, 2] = 1

    for i in range(0, self.phantomSize):
        rotatedMatrix = rotateX(vectors, self.cosFA, self.sinFA)
        decayedRotatedMatrix = decay(rotatedMatrix, self.T2, self.TE)


        for j in range(0, self.phantomSize):
            stepX = (360 / self.phantomSize) * i
            stepY = (360 / self.phantomSize) * j
            phaseEncodedMatrix = gradientXY(decayedRotatedMatrix, stepY, stepX)
            sigmaX = np.sum(phaseEncodedMatrix[:, :, 0])
            sigmaY = np.sum(phaseEncodedMatrix[:, :, 1])
            valueToAdd = np.complex(sigmaX, sigmaY)
            kSpace[i, j] = valueToAdd

        vectors = recovery(decayedRotatedMatrix, self.T1, self.TR)
        decayedRotatedMatrix[:, :, 0] = 0
        decayedRotatedMatrix[:, :, 1] = 0
        # vectors = np.zeros((self.phantomSize, self.phantomSize, 3))
        # vectors[:, :, 2] = 1
        self.showKSpace(kSpace)
        print(i)

    # kSpace = np.fft.fftshift(kSpace)
    # kSpace = np.fft.fft2(kSpace)
    # for i in range(0, self.phantomSize):
    #     kSpace[i, :] = np.fft.fft(kSpace[i, :])
    # for i in range(0, self.phantomSize):
    #     kSpace[:, i] = np.fft.fft(kSpace[:, i])
    kSpace = np.fft.fft2(kSpace)
    self.showKSpace(kSpace)

def decay(matrix, T2, t=1):
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



