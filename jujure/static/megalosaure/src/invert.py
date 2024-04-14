#!/usr/bin/env python3

from Crypto.Util.number import inverse
import struct
import os

N = 2**32
def reverse(desired_out, mult):
    return ((desired_out) * inverse(mult, N)) % N

first = reverse(0xa4e1a60a, 0x1337)
print(struct.pack('<L', first))
