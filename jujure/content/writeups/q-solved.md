---
title: "Reversing quantum algorithms ~~for ctf points~~ | q-solved - zer0pts 2022"
date: "2022-03-25 18:00:00"
author: "Juju"
tags: ["Reverse", "Quantum", "Writeup", "zer0pts"]
---

# Challenge description
`quantum` `reverse` | `304 pts` `8 solves`
```
I copied the solver of a reversing task from the future. But it doesn't
show the flag forever :thinking:
```

# Given files

{{< code file="/static/q-solved/solve.py" language="py" >}}

[circuit.json](/q-solved/circuit.json)

# TL;DR

The scripts builds a quantum circuit describing an unstructured search
algorithm inspired by the grover's algorithm. Its goal is to find among all
possible inputs, the one(s) with the highest probability to match a predefined
criteria.

It is composed of an `oracle` and a `diffuser`. The oracle is a black-box
function taking a state vector as input and introducing a phase shift in the
target qubit if the input matches the predefined criteria.

The diffuser then performs amplitude amplification using the target qubit's
phase kickback when the oracle matches, thus increasing the probability of a
matching input vector to be measured.

Basically, the output of the circuit is the input matching the criteria
described by the oracle.

All that remains to do for us is to understand what that criteria is.

# Reversing the Oracle

We can see that the oracle is built using the `circuit.json`.

The oracle is composed of 1408 multi-controlled X (MCX) gates, each controlled by 1
or 3 input qubits with with a control state given in the json. Each MCX gate
acts on a dedicated ancilla qubit.

After all 1408 MCX, the circuit adds an other MCX on the target qubit with all
control states set to 0. The target qubit is therefore introduced a phase shift
when all ancillas are in `|0>`.

So we want all ancillas to be `|0>` but it is also their original state. We
therfore have to influence the control qubits of each MCX so that none actually
performs the X gate on any ancilla. This means that among all control qubits of
a MCX, at least one must have a state different from its control state, thus
deactivating the gate.

If we look closely, we can see that the control state of a control qubit is `1`
when the json specifies `False`, and `0` when `True`.

Remember, inputs must be different from their control state specified on the
gate. Therefore a qubit marked as `False`, must take value `|0>` to deactivate
the gate. Similarly, a qubit marked `True` must take value `|1>`.

So we said earlier that the MCX have either 3 or 1 control bits and that at
least 1 of the control qubits must mismatch from their control state.

# POC with trivial qubits

Obviously this results in an equation system but let's see what we get with
only the obvious qubits: the ones controlling an ancilla by themselves.

Indeed if an ancilla is controlled by a single input qubit then this qubit MUST
be different from his control state so the X gate stays disabled. Therefore, any input qubit marked as `False` and as the only control of a gate MUST be set to `|0>` to match the oracle. Same is true for qubits marked as `True` that must be in state `|1>`.

So let's try to set all obvious qubits:

{{< code file="/static/q-solved/poc_flag.py" language="py" >}}

{{< image src="/q-solved/poc_flag.png" style="border-radius: 8px;" >}}

Well, most of them are 0, except, the first byte: `z`

Which is a really good sign that we are indead decoding a flag of the form
`zer0pts{...}`

# Equation system

For MCX with 3 control bits, we simply need to put them in an equation system,
with the trivial qubits.

We will have a total of 1408 equations, 1 for each MCX, each equation basically
saying that at least 1 Qubit must be different from its control state, and
therefore equal to its assigned boolean in the json.

Once the system is solved, we will know the state of all qubits that match the
oracle, which is the one outputed by the quantum circuit. We will then be able
to decode it to get the flag.

# Solve

I used z3 to build and solve the equation system:

{{< code file="/static/q-solved/flag.py" language="py" >}}

Running the script outputs us the equation system, sat indicating that z3 found
a solution to the system and the decoded solution of the system with the flag:
`zer0pts{FLAG_by_Gr0v3r's_4lg0r1thm}`

{{< image src="/q-solved/flag.png" style="border-radius: 8px;" >}}
