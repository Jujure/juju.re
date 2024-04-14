---
title: "Decompiling a nanomites based VM back to C | Megalosaure @ FCSC 2024"
date: "2024-04-13 12:00:00"
author: "Juju"
tags: ["Reverse", "Writeup", "fcsc"]
toc: true
---

# Intro

Yes it's the third year in a row that I writeup the dinosaur reverse challenge.

But this time it is neither a math or puzzle challenge.

We are instead met with a program that takes 20 minutes to validate the input and forks tens of thousands of processes.


{{< image src="/megalosaure/meme.jpg" style="border-radius: 8px;" >}}

## Challenge description

`reverse` | `487 pts` `6 solves` :star::star::star:

```
Voici un binaire qui vérifie si ce qu'on lui passe est le flag. À vous de jouer !
```

Author: `Cryptanalyse`

## Given files

[megalosaure](/megalosaure/megalosaure)


# Writeup

## Overview

Nothing out of the ordinary at the first look.

```console
$ file megalosaure
megalosaure: ELF 64-bit LSB pie executable, x86-64, version 1
(SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
BuildID[sha1]=b8bd171568d3bd03eca826edb869205684411dab, for GNU/Linux 3.2.0,
stripped
```

Dynamic analysis however ... the binary first tells us to add a
capability to the binary, `stracing` and `gdb` will thus require higher
privileges to not drop said capability.

`stracing` will show us that the program starts by creating about 10 thousands `pipes`. Before prompting for the flag, inputting
a correctly formatted `FCSC{...}` flag will then cause the program
to fork endlessly for about 20 minutes before refusing the flag.

## Code analysis


### Main function

Here is a decompiled main function.

We can see that the code creates the pipes in `setup_process_limit_and_IPC`,
then creates a shared memory mapping..

It will then ask for the flag, check its format, and split the
input into `0x12` `uint32_t`.

These `int` are then xored in the shared memory by groups of two
and the same function is ran `0x2c` times for each group but more
on this later.

Once this is done, the program saves some bytes in the shared
memory else where, and shift the global shared memory pointer,
before doing the same thing for the next 2 `int` in the input.

The final check simply is an equality test of all the saved values
mentionned above against an hardcoded reference array.

```c
uint32_t* shared_mem = nullptr;

int32_t main(int32_t argc, char** argv, char** envp)
{
    setup_process_limit_and_IPC();
    shared_mem = mmap(nullptr, 0x100000, 3, 0x21, 0xffffffff, 0);
    if (shared_mem == -1)
    {
        perror("mmap");
        exit(1);
    }
    int32_t* shared_mem_original = shared_mem;
    puts("Enter the flag:");
    char input[0x46];
    memset(&input, 0, 0x46);
    if (read(0, &input, 0x46) <= 0)
    {
        perror("read");
        exit(1);
    }
    if (check_format(&input) != 0)
    {
        puts("Wrong flag format!");
        exit(1);
    }
    uint32_t (* input_ints)[0x12] = &input;
    for (int32_t i = 0; i <= 0x11; i += 2)
    {
        shared_mem[0] = (shared_mem[0] ^ input_ints[i]);
        shared_mem[1] = (shared_mem[1] ^ input_ints[i + 1]);
        for (int32_t j = 0; j < 0x2c; j += 1)
            start_pod(pod_infos[j].n_children, code, 9);
        *(uint64_t*)(((((i + (i >> 0x1f)) >> 1) + 0x100) << 3) + shared_mem_original)
            = *(uint64_t*)(shared_mem + 0xb0);
        shared_mem = &shared_mem[0x2c];
    }
    shared_mem = shared_mem_original;
    int64_t lose = 0;
    for (int32_t i = 0; i <= 8; i++)
        lose = (lose | (ref[i] ^ *(uint64_t*)(shared_mem + 0x800) + (i_1 << 3)));
    if (lose != 0)
        puts("Nope.");
    else
        puts("Win!!");
    if (munmap(shared_mem, 1) != 0xffffffff)
        return 0;
    perror("munmap");
    exit(1);
}
```

### Check format

Let's take a quick look at the `check_format` function:

```c
uint64_t check_format(int32_t* input)
{
    shared_mem[0] = input[0];
    shared_mem[1] = 0x1337;
    shared_mem[2] = 0xa4e1a60a;
    start_pod(5, check_bytecode, 0x78 / 10);
    return 0 | shared_mem[0] | shared_mem[1] | shared_mem[2];
}
```

We can see that it initializes the shared memory with the first
`uint32_t` of the input then starts the same `start_pod` function
than in main.


### Start pod

The `start_pod` function takes as first parameter what I called a
`pod_info` struct, which is just two `uint32_t`, the first one
is the number of children the pod will fork, the second one is an
offset in some array of `uint16_t` I called `code` given in
parameter, you will understand the name really fast once we check
the `child` function.

The last parameter is the size of a single `code` block given to
`child`. Thus offsetting by this much between each `fork`.

In my terminology, a `pod` is a complete run of all the children
denoted by their `pod_info` and associated `code`.

```c
__pid_t start_pod(int32_t pod_info[2], uint16_t* code, int64_t code_size)

{
    for (int32_t i = 0; i < pod_info[0]; i = (i + 1))
    {
        pid_t pid = fork();
        if (pid == 0xffffffff)
        {
            perror("fork");
            exit(1);
        }
        if (pid == 0)
        {
            child(&code[(i + pod_info[1]) * code_size]);
            /* no return */
        }
    }
    __pid_t i;
    do
    {
        i = wait(nullptr);
    } while (i > 0);
    return i;
}
```


### Child

We are met with a `while true` loop, which selects an `uint16_t`
from the `code` array and dispatches it in a huge switch.

I immediatly recognize the pattern of a virtual machine,
and start identifying the instruction pointer `ip` and the 
`stack` by looking the first few instructions of the switch.

I will not show how I reversed all the instruction as many of
them are really similar but I will show the interesting ones.

```c
void child(uint16_t* code) __noreturn

{
    uint32_t stack[0x400];
    memset(&stack, 0, 0x1000);
    int32_t next_ip = 0;
    int32_t sp = 0;
    uint16_t opcode;
    while (true)
    {
        int32_t ip = netx_ip;
        next_ip = ip + 1;
        opcode = code[ip];
        switch (opcode)
        {
            case 0x0:
            {
                ...
            }
            case 0x1:
            ...
        }
    }
    if (opcode != 0x12)
        exit(1);
    exit(0);
}
```


## Instruction set analysis

### Push

First let's look at opcodes `0x1` and `0x2`.

These are how I recognized and was able to rename the stack
memory and stack pointers.

We can see that the first instruction takes one operand right
after the opcode, it then increments the stack pointer, fetches
an `uint32_t` from the shared memory, indexed by the first
operand, and stores it in the stack.

Basically a `push mem` instruction

The second one is really similar but takes two immediate operands,
both operands are `uint16_t` but they are packed as a single
`uint32_t` and stored on the stack, so this is the `push imm`
instruction

```c
case 1:
{
    int32_t operand_ptr = next_ip;
    next_ip = (operand_ptr + 1);
    int32_t old_sp = sp;
    sp = old_sp + 1;
    stack[old_sp] = shared_mem[code[operand_ptr]];
    break;
}
case 2:
{
    int32_t operand2_ptr = next_ip + 1;
    int64_t operand1_ptr = next_ip;
    next_ip = operand2_ptr + 1;
    int32_t old_sp = sp;
    sp = old_sp + 1;
    stack[old_sp] = code[operand1_ptr] | (code[operand2_ptr] << 0x10);
    break;
}
```

### Pop

This is the inverse operation, takes an `uint32_t` from the stack
and stores it in the shared memory indexed on the instruction's
operand.

```c
case 4:
{
    int32_t operand_ptr = next_ip;
    next_ip = operand_ptr + 1;
    uint32_t operand = code[operand_ptr];
    sp = sp - 1;
    int32_t val = stack[sp];
    stack[sp] = 0;
    shared_mem[operand] = val;
    break;
}
```


### Add

I will show only a single arithmetic instruction, all the others
work in a similar way:

This one pops two operands from the stack, add them together, and
stores the result back on the stack.

So we now know that this VM is stack based, similar to `python`
or `WASM` bytecode, operands and result of each instruction are
fetched and stored from/on the stack.

```c
case 6:
{
    int32_t first_op_ptr = (sp - 1);
    int32_t stack_op = stack[first_op_ptr];
    stack[first_op_ptr] = 0;
    int32_t second_op_ptr = first_op_ptr - 1;
    int32_t stack_op2 = stack[second_op_ptr];
    stack[second_op_ptr] = 0;
    sp = second_op_ptr + 1;
    stack[second_op_ptr] = stack_op2 + stack_op;
    break;
}
```

### IPC

Before doing more work, two other instructions are really
important, check the code first:

```c
case 3:
{
    int32_t operand_ptr = next_ip;
    next_ip = (operand_ptr + 1);
    uint32_t operand_1 = code[operand_ptr];
    sp = sp - 1;
    int32_t val = stack[sp];
    stack[sp] = 0;
    for (int32_t i = 0; i < operand; i++)
    {
        int32_t operand_i_ptr = next_ip;
        next_ip = operand_i_ptr + 1;
        if (write(pipes[code[operand_i_ptr]][1], &val, 4) == -1)
        {
            perror("write");
            exit(1);
        }
    }
    break;
}
```

This instruction takes one operand from the stack and one operand
after the opcode.

The operand encoded in the instruction is used to know how many
more operands are left.

For each of them, the instruction will write the stack operand in
the pipe corresponding to the current operand.

We can guess that this is how IPC is performed between each child.

So let's look at the read instruction:

It works in a really similar way and takes the same operand,
except that this time it will setup an epoll instance to read on 
very pipe given as operand and store the `read` output on the
stack for each operand.

```c
case 0:
{
    int32_t n_operands_ptr = next_ip;
    next_ip = n_operands_ptr + 1;
    uint32_t n_operands = code[n_operands_ptr];
    int32_t epoll = epoll_create1(0);
    if (epoll == 0xffffffff)
    {
        perror("epoll_create1");
        exit(1);
    }
    for (int32_t i = 0; i < n_operands; i++)
    {
        int32_t n_operands_i_ptr = next_ip;
        next_ip = n_operands_i_ptr + 1;
        int32_t fd = pipes[code[n_operands_i_ptr]][0];
        int32_t epoll_event = 1;
        int64_t var_1100_1 = fd | (i << 0x20);
        if (epoll_ctl(epoll, 1, fd, &epoll_event) != 0)
        {
            perror("epoll_ctl");
            exit(1);
        }
    }
    uint32_t n_operands_cpy = n_operands;
    do
    {
        struct epoll_event events;
        int32_t nb_events = epoll_wait(epoll, &events, 1, 0xffffffff);
        for (int32_t j = 0; j < nb_events; j++)
        {
            // Weird but basically recovers the FD from the event
            int64_t fd = *(j * 0xc + &var_8) - 0x1104;
            if (read(fd, &stack[(fd >> 0x20) + sp], 4) <= 0)
            {
                perror("read");
                exit(1);
            }
        }
        n_operands_cpy = n_operands_cpy - 1;
    } while (n_operands_cpy != 0);
    sp = sp + n_operands;
    if (close(epoll) != 0)
    {
        perror("close");
        exit(1);
    }
    break;
}
```


## Disassembling

Right, so let's not look too much at the IPC thingy.

I will start by disassembling the byte code of independant
children, then we will see if we can deduce patterns.

So I implemented a `binaryninja` plugin (my predilection decompiler) for the VM.

{{< code file="/static/megalosaure/src/plugin/__init__.py" language="python" >}}

Remember the `start_pod` and `check_format` functions ?

The check format passed a specific byte code to only 5 children.

This is probably a good first look

Here is how the plugin looked like on the check format bytecode:

{{< image src="/megalosaure/binja_plugin.png" style="border-radius: 8px;" >}}

Every function defined here is a specific child.

The first one pushes the first `uint32_t` of the `shared_memory`
(I wrote this as `m[0x0]` in the disassembler)
on the stack, then pops it and writes it on the first pipe (`r0x0`).

I consider pipes as registers.

The second child does the same but with `m[0x1]` and `r0x1`.

Third child reads `r0x0`, then `r0x1`, multiplies the two values
and writes the result to `r0x2`

Fourth child reads `r0x2`, pushes `m[0x2]`, xor both values,
and writes the result to `r0x3`.

Finally, the last child reads `r0x3`, dupplicates the value on the
stack twice and pop them all in `m[0x0]`, `m[0x1]` and `m[0x2]`

If we look again at the `check_format` function:

```c
uint64_t check_format(int32_t* input)
{
    shared_mem[0] = input[0];
    shared_mem[1] = 0x1337;
    shared_mem[2] = 0xa4e1a60a;
    start_pod(5, check_bytecode, 0x78 / 10);
    return 0 | shared_mem[0] | shared_mem[1] | shared_mem[2];
}
```

It checks that once the pod has executed, `m[0:3]` is all `0`.

Doing it in the inverse order, it means that the result of the
xor must be 0, thus `input[0] * 0x1337 == 0xa4e1a60a`

This small script does the modular inverse the retrieve
`input[0]`:

```python
#!/usr/bin/env python3

from Crypto.Util.number import inverse
import struct
import os

N = 2**32
def reverse(desired_out, mult):
    return ((desired_out) * inverse(mult, N)) % N

first = reverse(0xa4e1a60a, 0x1337)
print(struct.pack('<L', first))
```

With this output:

```console
$ ./invert.py
b'FCSC'
```

Good, we are definitely on the right track.


## Lifting

Great but now if we look at real pods launched for the flag checking,
they contain thousands of children, and have 2 inputs instead of one
(given through `m[0x0]` and `m[0x1]`)

We need to do something smart.

We noticed in the `check_format` example that children essentialy
recover one or two inputs (from memory, immediate, or register),
perform a single operation, and output the result to a register
or memory.

Looking back at the `code_size` given to `start_pod` in the `main` function, we can see that there are at most 9 instructions per child.

So it is unlikely that the real check children can do much more
than take inputs, compute a single operation and send its outputs.

The `binja` plugin must be improved, and we will throw away the
binja part actually.

Instead of disassembling independant children, I need to disassemble
a whole pod.

### Creating an AST

First thing we can build is each child's register dependencies.
I will simply mark which registers the child reads from and which
ones he writes to.

Now, knowing by which register a child is "locked" by reading
and which one he "unlocks" by writing, I can build the dependency
graph of all children.

To do that I implemented a simple algorithm which marks locked
and ready registers and by which child a register was unlocked.

Any child wanting to read a register will be able to do so only
if it is unlocked, if it is, I will give the current child a
reference to the child which originally unlocked the register
it is trying to read. The register will thus be consumed by the
child and be marked as locked again.

Any child which wants to write to a regiser will simply unlock
the register and mark itself as the one which unlocked it.
Obviously, this can only be done if all the child's registers
where consumed, otherwise, the child is still waiting for its
input and cannot write its output.

We do this in a loop until all children have been scheduled.

Inspecting the built graph, I quickly notice that all children
converge to a single output child and that there is no circular
dependency. The graph is thus an AST.

Each node of the AST performs and outputs a single operation based
on one or two inputs registers.

The leafs of the AST do not have dependencies, they simply
take inputs from immediate values or shared memory.

I also notice that the root of the AST has a single input,
which is simply outputed in shared memory.

Further analysis will show me that in the AST of every pod, given
pod number `n`:

* Only the root child outputs to memory, and at index `n+2`
* Only the leafs reads from memory, at indexes `n` and `n+1`


### Recalling the objective

As a reminder, here is the for loop which computes the result
tested against the `ref`.

```c
uint32_t (* input_ints)[0x12] = &input;
for (int32_t i = 0; i <= 0x11; i = (i + 2))
{
    shared_mem[0] = (shared_mem[0] ^ input_ints[i]);
    shared_mem[1] = (shared_mem[1] ^ input_ints[i + 1]);
    for (int32_t j = 0; j < 0x2c; j++)
        start_pod(pod_infos[j].n_children, code, 9);
    *(uint64_t*)(((((i + (i >> 0x1f)) >> 1) + 0x100) << 3) + shared_mem_original)
        = *(uint64_t*)(shared_mem + 0xb0);
    shared_mem = &shared_mem[0x2c];
}
```

The output is recovered from `shared_memory[0x2c]` (`0xb0` is `0x2c * 4`) on 8 bytes, which are the output of the two last pods

So we have `0x2c` pods, each one outputting the inputs for the next
one.

Once all pods have run, notice we shift, the shared_mem by `0x2c`
thus right on the last pods output. Which will be used to xor
the next input for the run of `0x2b` pods.

This seems like a `cbc` mode of operation but I did not made any
link to block ciphers at that time.

I will split the problem by solving each block of 8 input bytes
independently.

So I have a reference `uint64_t`, I want to find the two
`uint32_t` which will give this output after passing in all
of my `0x2c` ASTs.

### Do the intstructions backward :clown:

I thought about simply taking the desired output and inverting
every operation since I have the complete AST. However I quickly
noticed it was not possible because of operations like `shl`, `shr`, `or` and `and`.

These operations plus the fact that our inputs are fetched from
multiple leafs of the AST make the whole thing close to
impossible to invert.

### z3 attempt

This is actually not the attempt I made first but I went back and
forth on many ideas so I will explain my failed ideas here so
it doesn't cut the flow of the rest of the writeup.

So at some point I tried to build a z3 solver by traversing the
AST.

It did not work out in the end because I found a promising
solution which was showing results in parallel.

Now I know that it didn't find anything because I built the
solver by traversing all the `0x2c` ASTs, which is too much
obviously.

Basically my mistake was that at the time, I didn't know that
the VM was a symetric cipher, thus I has no idea of the unicity
of the input. So I thought that I NEEDED, to add a constraint
on the first input `uint32_t` (which I knew was `FCSC`) to
find a single solution.

But now I know that the input of every AST is unique so
solving ASTs one by one is much easier.


### Lifting to C

My actual first idea was that I knew that the flag started with
`FCSC{`, which only let me 3 unknown bytes in the first block.

This would be fairly trivial to bruteforce if the VM did not need
3 minutes to compute a single block.

I could have implemented an interpreter on top of the AST, but
since I decided to go for the bruteforce solution, I went for it
all and transpiled it to C.

{{< code file="/static/megalosaure/src/disasm.py" language="python" >}}

Running it will give this output, and a file `megalosaure.c`


```console
$ ./disasm.py 
[*] '/home/juju/ctf/fcsc_2024/reverse/megalosaure/megalosaure'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      PIE enabled
[+] Loading virtual machines
[+] Lifting AST
[+] Transpiling to C
[+] Transpiled to ./megalosaure.c
```

The `megalosaure.c` file is an implementation of a single run of
all the `0x2c` pods.

If you are interesed the disasm.py script also contains the code
of my z3 attempt.

## Bruteforcing until we win

### First block

The first block is trivial to bruteforce so I implemented a
simple bruteforce c program which links against a heavily optimised `megalosaure.c`.

{{< code file="/static/megalosaure/src/simple.c" language="c" >}}

With the following `Makefile` (which also has the final targets for the final
solver)

{{< code file="/static/megalosaure/src/Makefile" language="makefile" >}}

You can run `make simple` to build this simple bruteforcer for the first block.

```console
$ ./simple 
FCSC{454
```

Great I have the first 8 bytes of the flag. Now what ?

This strategy will not work on other blocks, where all of the 8
bytes are unknown.

### Angr attempt

So since I had the source code, I thought that I could try angr
on this one, surprisingly enough, this did not give anything.

For the same reason as z3, doing all the pods at once is just
too much.

### Reducing the character set

Now things are becoming really nasty for my solver, I was
working in parallel on the z3 solver and as I ran it on my first
try, I thought

> Hey "FCSC{454" does not look like a funny string, maybe this flag is only a hexstring

So I started bruteforcing all the blocks but only on hex digits,
which comes back to 2^32 iterations per block, completly doable.

However just remember that before being inputted in the first
pod, the input is xored with the output of the previous block.

Since I have the reference array, I know the desired output of
all the blocks and can bruteforce them in parralel.

Watch out, the code is dirty.

{{< code file="/static/megalosaure/src/main.c" language="c" >}}

You can run `make` to compile the solver.

It takes about 20 minutes to run, and prints each block when it
finds one.

```console
$ time ./solver 
Block 6: 06a5611b
Block 1: 2d32e27c
Block 4: 4016b156
Block 8: 420ac}
Block 7: c18edd32
Block 3: d3418e7a
Block 2: de2d7cf7
Block 5: e4df7f0c

real	21m18,662s
user	107m44,082s
sys	0m0,936s
```

I then reconstituted the flag manually by pasting each block

`FCSC{4542d32e27cde2d7cf7d3418e7a4016b156e4df7f0c06a5611bc18edd32420ac}`

After solving the challenge and discussing with its author,
I learned that the VM actually implemented a symetric block cipher (SIMON-64-128), with a null IV, and CBC mode of operation.

The key was embeded in the code, so it was actually a whitebox.

Looking back at everything, we can clearly see that one pod is
actually a round of encryption, a block is encrypted through
`0x2c` rounds, with each block input being xored with the output
of the previous block (0 for the first block), thus the CBC and
null IV.
