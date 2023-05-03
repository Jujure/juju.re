#!/usr/bin/env python3

import os

alphabet = b"abcdefghjklmnpqrstuvwxyz"

moves = [
    ('g', 2),
    ('o', 3),
    ('g', 3),
    ('b', 2),
    ('y', 2),
    ('g', 3),
    ('w', 1),
    ('o', 3),
    ('r', 3),
    ('y', 1),
    ('r', 3),
    ('w', 1),
    ('b', 1),
    ('o', 2),
    ('g', 1),
    ('y', 2),
    ('g', 1),
    ('y', 2),
    ('r', 2),
    ('g', 2),
    ('w', 2),
    ('o', 2),
]

sequence = b""

def face_id(face):
    res = 0
    if face == 'w':
        res = 2
    if face == 'b':
        res = 4
    if face == 'o':
        res  = 1
    if face == 'r':
        res = 0
    if face == 'y':
        res = 3
    if face == 'g':
        res = 5

    return res

for move in moves:
    i = face_id(move[0]) * 4 + move[1]
    sequence += alphabet[i].to_bytes(1, "little")

os.write(1, sequence + b'\n')
