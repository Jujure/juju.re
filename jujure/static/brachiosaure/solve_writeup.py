#!/usr/bin/env python3

import hashlib
import qrcode
from PIL import Image
import numpy as np

import requests


def get_user():
    r = requests.get("https://brachiosaure.france-cybersecurity-challenge.fr/")
    name = r.text.split("text-warning\">")[1].split('<')[0]
    return name

def get_digest(name):
    m = hashlib.sha512()
    m.update(name.encode())
    digest = m.digest()
    return digest

def linearize_serial(matrix_serial):
    serial = bytearray()

    for line in matrix_serial:
        for b in line:
            serial.append(b % 256)
    return bytes(serial)

def img_to_matrix(img):
    array = list(img.getdata())
    width, height = img.size

    matrix_img = [[array[i * width + j] for j in range(width)] for i in range(height)]
    return matrix_img


def matrix_to_img(mat, path):
    array = np.uint8(mat)
    img = Image.fromarray(array)
    img.save(path)


def gen_qrcode(data, path):
    qr = qrcode.QRCode(version = 1, box_size = 2, border = 2)
    qr.add_data(data)
    qr.make()
    qr_usr = qr.make_image()
    qr_usr.save(path)



def identitymatrix(n):
    return [[int(x == y) for x in range(0, n)] for y in range(0, n)]



def get_flag(name):
    files = {
        "upload1": open(f"{name}_usr.png", "rb"),
        "upload2": open(f"{name}_serial.png", "rb")
    }
    r = requests.post("https://brachiosaure.france-cybersecurity-challenge.fr/login", files=files)
    for line in r.text.split('\n'):
        if "FCSC{" in line:
            print(line)


name = get_user()
digest = get_digest(name)

matrix_usr = [[digest[i * 8 + j] for j in range(8)] for i in range(8)]
matrix_usr = np.array(matrix_usr)

matrix_serial = np.dot(matrix_usr, matrix_usr)
serial = linearize_serial(matrix_serial)


gen_qrcode(digest, "user.png")
gen_qrcode(serial, "serial.png")


img_usr = Image.open("./user.png", "r")
img_serial = Image.open("./serial.png", "r")

matrix_img_usr = img_to_matrix(img_usr)
matrix_img_serial = img_to_matrix(img_serial)


def invert(usr, serial):
    # Add empty and identity matrices to maka it invetible
    usr = make_invertible(usr)
    serial = make_invertible(serial)

    n = len(usr)
    # Total size after redimensionning
    new_n = n * 2

    # The magic inversion by swapping corners and computing matrix opposite
    usr_inv = invert_magic(usr)
    serial_inv = invert_magic(serial)

    # Will hold the final user png
    new_usr = []
    # Will hold the final serial png
    new_serial = []


    # Create the new_usr
    for i in range(new_n):
        line = [0] * new_n
        if i < n:
            for j in range(n):
                line[j] = usr[i][j]
        if i >= n:
            for j in range(n):
                line[j + n] = int(serial_inv[i - n][j])
        new_usr.append(line)


    # Create the new_serial
    for i in range(new_n):
        line = [0] * new_n
        if i < n:
            for j in range(n):
                line[j] = int(usr_inv[i][j])
        if i >= n:
            for j in range(n):
                line[j + n] = serial[i - n][j]
        new_serial.append(line)


    return new_usr, new_serial


def make_invertible(mat):
    res = []
    n = len(mat)
    ident = identitymatrix(n)

    # Add the identity matrix below the original
    for line in ident:
        mat.append(line)


    for i in range(len(mat)):
        line = mat[i]
        for j in range(n):
            # Add the identity matrix at the right of the original
            if i < n:
                line.append(ident[i][j])
            # Add the empty matrix at the bottom right corner
            else:
                line.append(0)

    return mat


def invert_magic(mat):
    n_tot = len(mat)
    n = n_tot // 2

    #Create a new empty matrix to hold the result
    res = [[0 for _ in range(n)] for _ in range(n)]

    ident = identitymatrix(n)

    # Add the identity matrix below
    for line in ident:
        res.append(line)


    for i in range(len(mat)):
        line = res[i]
        for j in range(n):
            # Identity matrix on the right
            if i < n:
                line.append(ident[i][j])

            # Oposite of the original in the bottom right corner
            else:
                el = -mat[i - n][j] % 256
                line.append(el)

    return res

res_usr, res_serial = invert(matrix_img_usr, matrix_img_serial)

matrix_to_img(res_usr, f"{name}_usr.png")
matrix_to_img(res_serial, f"{name}_serial.png")

get_flag(name)
