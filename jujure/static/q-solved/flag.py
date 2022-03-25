#!/usr/bin/env python3
import json
from z3 import *

with open('circuit.json', 'r') as f:
    j = json.load(f)

nq = j['memory']

system = [Bool(str(i)) for i in range(nq)]

s = Solver()

for cs in j['circuit']:
    term = Or()
    for c in cs:
        term = Or(term, system[c[1]] == c[0])
    s.add(term)

print(s)
print(s.check())

m = s.model()

result_arr = [''] * nq

for d in m.decls():
    result_arr[int(d.name())] = '1' if m[d] else '0'

result_arr.reverse()
result = "".join(result_arr)

print(int.to_bytes(int(result, 2), nq//8, 'little'))
