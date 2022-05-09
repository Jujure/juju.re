#!/usr/bin/env python3
import os

def check_align(i, j):
    return b'\x04' + j.to_bytes(1, 'little') + i.to_bytes(1, 'little')

def cycle():
    return b'\x01'

def done():
    return b'\x00'

def move():
    return b'\x02'

def place():
    return b'\x03'


def fill_column(skip = True):
    res = b''
    for _ in range(0xb):
        if not skip:
            res += place()
        res += move()
    if not skip:
        res += place()
    return res



def fill():
    res = b''
    res += cycle() * 3
    res += fill_column(False)
    for _ in range(5):
        res += cycle() + move() + cycle()
        res += fill_column()
        res += cycle() * 3 + move() + cycle() * 3
        res += fill_column()
    res += cycle() + move() + cycle()
    res += fill_column(False)

    for i in range(0xc):
        for j in range(0xc):
            res += check_align(i, j)

    return res + done()

res = fill()
os.write(1, res)
