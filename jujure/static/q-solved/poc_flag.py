#!/usr/bin/env python3
import json

with open('circuit.json', 'r') as f:
    j = json.load(f)

nq = j['memory']

system = ['0'] * nq

for cs in j['circuit']:
    if len(cs) == 1:
        system[cs[0][1]] = '1' if cs[0][0] else '0'


system.reverse()
result = "".join(system)

print(int.to_bytes(int(result, 2), nq//8, 'little'))
