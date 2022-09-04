---
title: "Exploiting logical bug to solve NP-complete reversing puzzle | Diplodocus @ FCSC 2022"
date: "2022-05-08 18:00:00"
author: "Juju"
tags: ["Reverse", "Writeup", "fcsc"]
toc: true
---

# Intro

Diplodocus is I think by far my favorite challenge of the 2022 edition of the
FCSC.  First it is a reverse challenge, my reference category, then it does not
feature weird unknown CPU architecture, just plain x64 with the only layer of
obfuscation being the heavy optimization of the compiler. Finally it is an
algorithmic problem, and I love algorithms.

The complexity of this challenge relies on the underlying problem it
implements. Diplodocus is the successor of Triceratops, a similar challenge
from the 2021 edition of the FCSC where you were also asked to solve an
NP-complete puzzle to get the flag.

The twist here is that a conceptual flaw of the program allows us to recover
the flag without actually solving the intended puzzle, but more on that later.

{{< image src="/diplodocus/yee-dinosaur.gif" style="border-radius: 8px;" >}}

## Challenge description
`reverse` | `477 pts` `10 solves` `:star::star::star:`
```
Trouvez une entrée qui valide, et soumettez-la au service en ligne pour obtenir
le flag.

`nc challenges.france-cybersecurity-challenge.fr 2201`

SHA256(`diplodocus`) =
`9af3062da630d2b94ad3bfa0b5fd67328d2c6c7bbb79607d7d2fa28a67c7ff9c`.
```

Author: `\J`

## Given files

[diplodocus](/diplodocus/diplodocus)

# Writeup

## Overview

As stated the program is simply an x64 stripped ELF.

```console
$ file diplodocus
diplodocus: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV),
dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
BuildID[sha1]=c489721789271e74d301cda200feb877bd22d80a, for GNU/Linux 3.2.0,
stripped
```

If we try to execute the program, it reads a line from standard input and exits
with status code 1.

```console
$ ./diplodocus
input
$ echo $status
1
```

stracing and ltracing doesn't apport much more information, the program indeed
only calls `read(2)`.

## Main

It's now time to open our favorite decompiler and investigate the main
function.

After cleaning up the decompiler output and renaming the variables we get the
following code:

{{< code file="/static/diplodocus/main.c" language="c" >}}

The code is really simple here, it reads the standard input and pass the input
to a function that seems to perform a check.

If the check is sucessful, the program prints the flag, otherwise it exits with
1.

## Check

The Check function starts by setting up some local variables like a pointer to
the start and to the end of the input and what seems to be a struct that I
called context that may contain informations relevant to the ongoing puzzle.
Most of this struct is set to 0:

{{< code file="/static/diplodocus/check_init.c" language="c" >}}

## Instruction fetching and dispatch

My first observation of this main function made me think it was a really small
virtual machine. We can see it goes through every character in the input and
matches it against opcodes between 0 and 4 included. Every other values seems
to end the main loop with a return value of 1, indicating an error.

Since I see that the return value is set by oring a field of the context (which
I assumed at that time was a processor structure) I assume that this field holds
some sort of error flags that will invalidate our puzzle.

We then have the main dispatcher, processing the correct instruction. One thing
that can be noted is the two `break` statement in `case 0`, this is obviously
my decompiler trolling me but what he is trying to say is that this case will
end the main loop as well. It thus probably is the only way to end the function
with a return value of 0. It must then be the instruction performing the final
check after executing all our instructions. We will take a look at it last
since other instructions will give us a better idea of the internal structure
of the context and are easier to reverse.

{{< code file="/static/diplodocus/check_loop.c" language="c" >}}

### Case 1

This instruction is really simple, it makes one field of the context cycle
between 0 and 3 included. Let's simply remember the offset of this field
(`0xa0`) for now to see where it is used.

{{< code file="/static/diplodocus/case1.c" language="c" >}}

### Case 2

Well we did not need to wait a long time to see where the field from case 1
is used. Right at the beginning of case 2, the program matches the value of the
variable against all its possible values, it then creates a copy of two other
variable of the context and update them depending on our matching.

The 2 variables are then bound checked against `0xb` and used to index what
seems to be an array of `int32_t`. We can therefore understand that the two
variables are indexes of this array and that the variable from case 1 is an
enum describing possible movements in this array. I therefore name them `move`,
`i` and `j`.

Next we notice that we check that the `jth` bit of the `ith` row of the array,
if is not set, it sets the said bit and update the coordinates in the context.
If however it is already set, the program sets the error flag that we already
identified earlier.

Clearly this is some sort of 12 * 12 bitboard implementation, the first thing
that came to my mind is chess since I'm familiar with bitboard based chess
engines programming so it was at this exact moment that I understood this
problem was probably a puzzle or some sort of board game.

So to rephrase all this information, this instruction changes our coordinates
on a 12 * 12 board based on a preselected move from case 1, it places a marker
at our new coordinates and errors if we already visited this tile.

I now know one rule of the game: I cannot step twice on the same tile. By lack
of inspiration, I name this bitboard `visited` since it keeps track of all my
visited tiles.

Bellow is the cleaned up pseudo-C code from the decompiler with all variables
renamed accordingly.

{{< code file="/static/diplodocus/case2.c" language="c" >}}

And here is the moves enum to understand better how case 1 manipulates our
moves.

{{< code file="/static/diplodocus/move_enum.c" language="c" >}}

### Case 3

Case 3 uses a variable from the context that we previously saw initialized to
`0xffffff` at the very start of the check function without understanding it.

We can now see that it is in fact a queue of 24 bits that is popped in case 3
to place the said bit on a different bitboard than case 2 but with the same
coordinates. If the bit queue is empty then we output an error.

So I understand here that we must place 24 bits on another board while
simultaneously moving on the first one that tracks the tiles we already visited.

Seems easy enough, however, the instruction does not end here, it calls a
function passing the row of the bitboard as parameter, if the return value of
this function is more than `2` we output an error.

{{< code file="/static/diplodocus/case3_stripped.c" language="c" >}}

#### Pop count

Here is the said function, so it seems to perform magic bitwise operation.
Could be anything really, my intuition tells me it count the number of bits set
on the line but it may as well be some weird bitboard magic, I mean you never
know the stuff I found on [chess programming](chessprogramming.org) while
working on chess engines really blows my mind.

By googling the first constant `0x5555555555555555` I confirm really fast my
intuition. It is indeed a population count function, the fifth result of the
search being, guess what? [Chess programming wiki on population
count](https://www.chessprogramming.org/Population_Count). I now really start
thinking that this is actually a chess problem.

{{< code file="/static/diplodocus/pop_count.c" language="c" >}}

With this information we can now rename the variables and symbols from case 3
and we now understand that we place a bit from the bit queue on the board, we
cannot allign more than 2 bits on the same line.

{{< code file="/static/diplodocus/case3.c" language="c" >}}


### Case 4

Do not be misled, this instruction seems simple enough but is by far the
hardest one of the challenge.

So first this instruction fetch 2 operand, these operands are later used to
access a third bitboard, so I name them accordingly `i` and `j`.

Then we check if our bit queue is empty, if it is not then we output an error.
This mean that we can call this instruction only when we placed all the 24
points at our disposition.

Now comes the fun part, we call a function passing the coordinates and the
whole context as parameter, this function will output a bit that will be placed
on a third bitboard at the coordinates indexed by the operands.

So my decompiler really despise this function, I told you it took the whole
context as parameters but its not exactly true as it actually packs the whole
context in 10 `int128_t` arguments using SIMD instructions. I cleaned up the
function call for your eyes so you do not have de keep track of the 12
parameters of the function.

{{< code file="/static/diplodocus/case4_stripped.c" language="c" >}}

#### \J dabbing on me

You can see below a decompilation of the function, looks fun right? And this is
actually cleaned up so you don't see the SIMD registers and weird struct
packing. Now I really recommend you to not actually read this code but to get
the main idea from the comments and my explanations. A much more readable python
reimplementation is available right after for your sanity.

Most variables are not renamed correctly because I did not actually reverse and
understood all this function. This is simply what it looked like in my
decompiler at the moment I undestood enough to throw it by the window, modulo
of course SIMD and stack fengshui :eyes:.

Let's not care too much about weird constants and implementation details for
now as I did not understood them at the time either.

The main idea of this is code is that it will run through all possible
increments combinations that will iterate on the second board (the one from
case 3, where we manually place our bits from the bit queue).

Basically, we check every possible way we can run through the board.

For each of these increment combination we see a weird loop performing modulos
of the increments. This is actually the euclidean algorithm that computes the
GCD of 2 numbers. This GCD is compared to 1. If it is not one then we skip this
increments combination and go to the next loop iteration. We are therefore only
concerned about running through the board using coprime increments, confusing I
know.

We then iterate on the board using these increments and count the number of
bits set while doing so. If at any point we encounter more than 2 points during
the same passing of the board we set a result flag. The function will output
`1` if and only if no result flag was set for any iteration. Meaning for any
traversal of the board, we did not encounter more than 2 bits.

Here I was really scared because I started to think that this was maybe `\J`
trolling me with again a cryptography problem modelised using bitboards are
something. And everyone who checks my results of the FCSC know how bad I am at
cryptography.

{{< code file="/static/diplodocus/check_align.c" language="c" >}}

#### Alignement count

So now I am really unhappy, I was having fun finding out puzzle and placing
bits on boards but now `\J` is throwing modular arithmetic at me.

I take a break crying in my bed after these findings before actually thinking.

Running through the array using coprime increments probably has a really
interesting property that may be plotted visually.

So I reimplemented this function in python but instead of summing the bits I
encountered, I mark the bits I would have summed to see the path that I take in
the array.

Which gives us this much more readable code:

{{< code file="/static/diplodocus/show.py" language="py" >}}

With this output (only a sample):

{{< code file="/static/diplodocus/show.out" >}}

It is now obvious what this function is doing, it draws every straight line
passing through the point given as parameter and checks if more than 2 points
of the board are alligned.

If we remember the context were this function is used, it means that we will
set a bit in the third bitboard if and only if no line passing through this
point intersects more than 2 points.

### Case 0 (Final check)

So case 0 is the instruction that performs the final check to see if our board
match the desired state. Again there is a lot of SIMD magic going on so I tried
to clean it a little bit, you lose the actual result of the decompilation but
the code is semantically equivalent.

First we perform a pop count on all lines of the `visited` bitboard, comparing
the total sum to `0x90` which is `12 * 12`, the total number of tiles. We must
therefore go through every single tile of the board exactly once.

Then, we pack the third bitboard (the one that stores if 3 points are alligned)
into the `zmm0` 128 bit register because why not? And basically `shifting` and
`bitwise anding` it to check that every bit of the board are set. So its
basically the same check than before but for the third bitboard, meaning that
no line drawn from any point on the board must intersect with more than 2
points.

The last check simply performs a xor on every line of the board and outputs
an error if it is different from 0. This means that every column of the board
must contain an even number of points.


{{< code file="/static/diplodocus/case0.c" language="c" >}}

Great we have everything ready to go! We simply need to go trough the board and
place 24 points on it and make sure there are never 3 points alligned.

So it turns out this problem is NP-complete (I learned after solving the
challenge that is called the Not-three-in-line problem), I might have a hard
time solving it manually. I might start to implement a SAT solver or som...

But wait, did you spot something sus with this implementation ?

{{< image src="/diplodocus/the_rock.gif" style="border-radius: 8px;" >}}

## Bypassing the puzzle

There are actually two distinct bugs in this implementation of the puzzle.

First, the program does not check that you place a point when there is already
one. It does check that you do not go twice on the same tile but you can still
place multiple points without moving.

The second, the one I exploited here, is that the weird function we
reimplemented actually only count alligned points on all straight lines
**except** for lines and columns.

The special case of the line is checked independently in case 3 when inserting
the point if you remember well.

However the only columns check is in case 0 where it simply checks that there
is an even number of point per column.

Nothing forbids us to put 12 points on the first and last column, which
validates all our constraints.

```
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
|X| | | | | | | | | | |X|
```

{{< image src="/diplodocus/stop_the_count.png" style="border-radius: 8px;" >}}

## Solve

We now simply need to write the input that will give instructions to the
program to write this bugged board.

We first fill the first column, by going downward.

Then we go through the 10 next columns without placing any bit and we fill
the last one.

Finally we need to fill the third bitboard by manually performing the alignment
check for every point in the bitboard so we call case 4 for every coordinates.

We do not forget to put case 0 at the end to validate everything went fine.

{{< code file="/static/diplodocus/solve.py" language="py" >}}

```console
$ ./solve.py | ./diplodocus
Well done! You can submit your input to the remote service to grab the flag!
```

```console
$ ./solve.py | nc challenges.france-cybersecurity-challenge.fr 2201
Well done, the flag is FCSC{bf809d2614501166a890740116103410a69ede950b57a9186bf49eb734eaa1a1}
```
