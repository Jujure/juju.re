#!/usr/bin/env python3

import sys
import os

with open('./disk.img', 'rb') as f:
    data = f.read()
    blocks = [data[i * 0x1000:(i * 0x1000) + 0x1000] for i in range(len(data) // 0x1000)]

clear = bytearray()

for block in blocks:
    x = 0
    for b in block:
        c = x ^ b
        clear.append(c)
        x = c

os.write(1, clear)
