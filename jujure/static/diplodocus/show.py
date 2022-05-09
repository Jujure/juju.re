#!/usr/bin/env python3
import os
from math import gcd

def pretty_print(arr):
    res = ""
    for row in arr:
        res += '|'
        for el in row:
            res += el + '|'
        res += '\n'
    return res

def count_alligned(i, j):
    for y in range(-0xb, 0xc):
        if y == 0:
            continue

        start_row = i + 0x79
        start_column = (y + 1) * -0xb + j + 11

        for x in range(-0xb, 0xc):
            if x == 0:
                start_row -= 0xb
                continue
            pgcd = gcd(y, x)
            if pgcd == 1:
                arr = [[' ' for _ in range(0xc)] for _ in range(0xc)]
                row = start_row
                column = start_column
                for _ in range(0x17):
                    if column <= 0xb and row <= 0xb and column >= 0 and row >= 0:
                        print(row, column)
                        arr[row][column] = 'X'
                    column += y
                    row += x

                print(pretty_print(arr))
            start_row -= 0xb


count_alligned(5, 6)
