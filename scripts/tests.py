
import math

import cv2
import numpy as np
import matplotlib.pyplot as plt
from scripts import modifiedPhantom


size = 20
def getPhantom(size):
    size=int(size)
    phantom= modifiedPhantom.modshepp_logan([size, size], dtype=float)
    phantom = phantom * (255 / np.max(phantom))
    return phantom

#
# def rotateX(matrix, angle , ):
#     shape = np.shape(matrix)
#     angle = angle * (math.pi / 180)
#     res = np.zeros(shape)
#     for i in range(0, shape[0]):
#         for j in range(0, shape[1]):
#             res[i, j] = np.dot(
#                 np.array([[1, 0, 0],
#                           [0, math.cos(angle), -1 * math.sin(angle)],
#                           [0, math.sin(angle), math.cos(angle)]])
#                 , matrix[i, j])
#     return res
#
#
# def rotateZ(matrix, angle):
#     shape = np.shape(matrix)
#     angle = angle * (math.pi / 180)
#     res = np.zeros(shape)
#     for i in range(0, shape[0]):
#         for j in range(0, shape[1]):
#             res[i, j] = np.dot(
#                 np.array([[math.cos(angle), -1 * math.sin(angle), 0],
#                           [math.sin(angle), math.cos(angle), 0],
#                           [0, 0, 1]])
#                 , matrix[i, j])
#     return res


# def gradientXY(matrix, stepX, stepY):
#     shape = np.shape(matrix)
#     res = np.zeros(shape)
#     for i in range(0, shape[0]):
#         for j in range(0, shape[1]):
#             angle = (stepY * j + stepX * i) * (math.pi / 180)
#             res[i, j] = np.dot(
#                 np.array([[math.cos(angle), -1 * math.sin(angle), 0],
#                           [math.sin(angle), math.cos(angle), 0],
#                           [0, 0, 1]])
#                 , matrix[i, j])
#     return res

def rotateX(matrix, cosFA, sinFA):
    shape = np.shape(matrix)
    rows = shape[0]
    cols = shape[1]
    #angle = (angle) * (pi / 180)
    newMatrix = np.zeros(shape)
    for i in range(0, rows):
        for j in range(0, cols):
            newMatrix[i, j] = np.dot(
                np.array([[1, 0, 0], [0, cosFA, -1 * sinFA], [0, sinFA, cosFA]]), matrix[i, j])
    return newMatrix


def rotateZ(matrix, angle):
    shape = np.shape(matrix)
    rows = shape[0]
    cols = shape[1]
    angle = (angle) * (math.pi / 180)
    newMatrix = np.zeros(shape)
    for i in range(0, rows):
        for j in range(0, cols):
            newMatrix[i, j] = np.dot(
                np.array([[math.cos(angle), -1 * math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]]), matrix[i, j])
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


def reconstructImage():
    kSpace = np.zeros((size, size), dtype=complex)
    vectors = np.zeros((size, size, 3))
    vectors[:, :, 2] = test
    angle = 90 * (math.pi / 180)

    for i in range(0, size):
        rotatedMatrix = rotateX(vectors, math.cos(angle), math.sin(angle))
        #T2 ,  TE
       # decayedRotatedMatrix = decay(rotatedMatrix, self.T2, self.TE)


        for j in range(0, size):
            stepX = (360 / size) * i
            stepY = (360 / size) * j
           # phaseEncodedMatrix = gradientXY(decayedRotatedMatrix, stepY, stepX)
            phaseEncodedMatrix = gradientXY(rotatedMatrix, stepY, stepX)
            sigmaX = np.round(np.sum(phaseEncodedMatrix[:, :, 0]) , 3)
            sigmaY = np.round(np.sum(phaseEncodedMatrix[:, :, 1]) , 3)
            valueToAdd = complex(sigmaY, sigmaX)
            kSpace[i, j] = valueToAdd
# T1 , TR
       # vectors = recovery(decayedRotatedMatrix, self.T1, self.TR)
       # decayedRotatedMatrix[:, :, 0] = 0
       # decayedRotatedMatrix[:, :, 1] = 0
        rotatedMatrix[:, :, 0] = 0
        rotatedMatrix[:, :, 1] = 0
        vectors = np.zeros((size, size, 3))
        vectors[:, :, 2] = test
       # self.showKSpace(kSpace)


    # kSpace = np.fft.fftshift(kSpace)
    # kSpace = np.fft.fft2(kSpace)
    # for i in range(0, self.phantomSize):
    #     kSpace[i, :] = np.fft.fft(kSpace[i, :])
    # for i in range(0, self.phantomSize):
    #     kSpace[:, i] = np.fft.fft(kSpace[:, i])
    # print()
    # print("HIIIIIII")
    # print(kSpace)

    kSpace = np.fft.ifft2(kSpace)
    ks = np.round(np.abs(kSpace),3)
    # plt.plot(kSpace.real)
    # plt.show()
   # print(kSpace)
    return ks

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


test = getPhantom(size)
#plt.plot(test)
four = np.fft.fft2(test)
plt.show()
# print(four)
k = reconstructImage()
k = k/np.max(k) * 255
print(np.round(test,4))
print()
print("hi")
print(k)

plt.subplot(2,1,1)
plt.plot(test)
plt.subplot(2,1,2)
plt.plot(k)
plt.show()
# cv2.imwrite('k.png',k)


