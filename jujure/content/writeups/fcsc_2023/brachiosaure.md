---
title: "Inverting a bunch of matrices because reverse engineering or something | Brachiosaure @ FCSC 2023"
date: "2023-04-30 18:00:00"
author: "Juju"
tags: ["Reverse", "Writeup", "fcsc"]
toc: true
---

# Intro

Brachiosaure is a math/puzzle challenge from `\J` for the 2023 edition of the
FCSC. It's difficulty is not in the reversing process, which is fairly trivial
here, but in solving of underlying problem.

## Challenge description
`reverse` | `477 pts` `10 solves` `:star::star:`

```
Vous aimez les QR Codes ? On vous demande d'écrire un générateur d'entrées
valides pour ce binaire, puis de le valider sur le service web fourni où un nom
aléatoire est proposé toutes les 5 secondes.
```

Author: `\J`

## Given files

[brachiosaure](/brachiosaure/brachiosaure)


## Overview

As we can guess from the challenge description, this binary will take images
as input. QR codes images for that matter.

```console
$ file brachiosaure
brachiosaure: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV),
dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1
=3e4d225f1053b2a64de1cd133563e6e655049aca, for GNU/Linux 3.2.0, stripped

$ ldd brachiosaure
	linux-vdso.so.1 (0x00007ffd833bd000)
	libzbar.so.0 => /usr/lib/libzbar.so.0 (0x00007f3ec2325000)
	libpng16.so.16 => /usr/lib/libpng16.so.16 (0x00007f3ec22ec000)
	libcrypto.so.1.1 => /usr/lib/libcrypto.so.1.1 (0x00007f3ec1fff000)
	libc.so.6 => /usr/lib/libc.so.6 (0x00007f3ec1e18000)
	libdbus-1.so.3 => /usr/lib/libdbus-1.so.3 (0x00007f3ec1dc7000)
	libv4l2.so.0 => /usr/lib/libv4l2.so.0 (0x00007f3ec1db8000)
	libX11.so.6 => /usr/lib/libX11.so.6 (0x00007f3ec1c73000)
	libXv.so.1 => /usr/lib/libXv.so.1 (0x00007f3ec1c6b000)
	libjpeg.so.8 => /usr/lib/libjpeg.so.8 (0x00007f3ec1be8000)
	libz.so.1 => /usr/lib/libz.so.1 (0x00007f3ec1bce000)
	libm.so.6 => /usr/lib/libm.so.6 (0x00007f3ec1ae6000)
	/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007f3ec23a2000)
	libsystemd.so.0 => /usr/lib/libsystemd.so.0 (0x00007f3ec1a09000)
	libv4lconvert.so.0 => /usr/lib/libv4lconvert.so.0 (0x00007f3ec198e000)
	libxcb.so.1 => /usr/lib/libxcb.so.1 (0x00007f3ec1963000)
	libXext.so.6 => /usr/lib/libXext.so.6 (0x00007f3ec194e000)
	libcap.so.2 => /usr/lib/libcap.so.2 (0x00007f3ec1942000)
	libgcrypt.so.20 => /usr/lib/libgcrypt.so.20 (0x00007f3ec17fa000)
	liblzma.so.5 => /usr/lib/liblzma.so.5 (0x00007f3ec17c7000)
	libzstd.so.1 => /usr/lib/libzstd.so.1 (0x00007f3ec16f5000)
	liblz4.so.1 => /usr/lib/liblz4.so.1 (0x00007f3ec16d3000)
	libgcc_s.so.1 => /usr/lib/libgcc_s.so.1 (0x00007f3ec16b3000)
	libXau.so.6 => /usr/lib/libXau.so.6 (0x00007f3ec16ae000)
	libXdmcp.so.6 => /usr/lib/libXdmcp.so.6 (0x00007f3ec16a6000)
	libgpg-error.so.0 => /usr/lib/libgpg-error.so.0 (0x00007f3ec1680000)
```

That's a lot of libraries, this is really good news because we can just look up
the documentation of those libraries to understand what is going on.

The most important ones are `libpng` to read the image data and `libzbar` which
is used to read data from a QR code. Turns out symbols are really self
explanatory by themselves, the code basically reads like sources even though it
is stripped.

By executing it, we can already what the program is expecting: a username,
and two png, one for the username and one for the serial, probably QR codes
encoding said username and its serial.

```console
$ ./brachiosaure
Usage: ./brachiosaure <username> <username.png> <serial.png>
```

So is this just a simple keygen that needs to output its key as a QR code ?
(Spoiler it isn't)

## Reversing

### Main

I'm saving you the trouble of renaming the variables, the function I called
`get_qr_data` reads like a charm. It basically is just a succession of calls to
`libpng` and `libzbar`, it does exactly what you think it does, reads an image
file, decode the QR code it contains and outputs everything in the pointers
passed as parameters so I won't show the process of reversing it.

The only thing worth pointing is that it grayscales the input image.


{{< code file="/static/brachiosaure/main.c" language="c" >}}

So we compute the `sha512` of the username, this gives us a digest, that we will
keep for later, just remember that we have this digest of the username.

We then decode the 2 QR codes, both seem to need to encode `0x40` bytes of data.
(I know you already guessed it, a sha512 is also 0x40 bytes long).

And finally we perform some checks:

- Both pictures needs to be a square of the same size
- The encoded data of the user QR code needs to be equal to the user digest
- The serial check, taking both QR datas as input
- And finally a last check but this time taking both images data instead of the QR data.

### check_serial

{{< code file="/static/brachiosaure/check_serial.c" language="c" >}}

Hmmm we find again the same interesting check that was performed in the main
function, something is already interesting but let's first note things that
we can already guess from this:

Since it take our images as input in main and image width, it certainly
interprets the data as a linearized 2 dimensionnal array, taking the width as
parameter. We can confirm this since the check serial is called with size `0x8`
as parameter and `0x8 * 0x8 == 0x40`.

Now let's see what is different:

```c
// Inside check serial
something_interesting(user_digest, user_digest, &buff, size);
res = memcmp(serial, buff, size * size) == 0;

// Inside main
int32_t win = something_interesting(username_img_data, serial_img_data,
	&an_interesting_output, user_width);
```

First the result is not used in the same way:

- Inside `check_serial`, the return value is discarded, and the output buffer is
compared to the serial, so it is bascically a keygen, seems easy enough

- Inside `main`, the output buffer is discarded and only the return value is
checked

Then in the `main`, the function is called with the user and serial images data,
but in check_serial, it is called with the digest data twice.

OK let's see what this does, we need to understand what doest it put in the
output buffer since it will be the serial we will need to encode in the second
QR code of the input, but we also need to understand the return value.


### dot_product

Cutting drama right now, it is simply a matrix dot product:

{{< code file="/static/brachiosaure/dot_product.c" language="c" >}}

Alright so to recap what actually happens:

- In check serial, we perform the dot product of the user digest, interpreted a
linearized 8 * 8 matrix, with itself, effectively squaring it, which gives us
our serial (also in a linearized 8 * 8 matrix).

- In main, we perform the dot product of the user and serial IMAGES, and we can
see from the code that the return value indicates wether or not the resulting
dot product is the identity matrix.

So yeah, congratulation, it is the end of the reversing part.

We now need to, given a random username:

- Compute its digest
- Square it to get the serial
- Output both the digest and the serial to a QR code each
- (The fun part) Make sure that the images of said QR codes are invertible


## Splitting the problem

So at first I though this was impossible, but I gradually had more and more
tricks up my sleeve to solve this, which I finally almost all threw by the
window when I discovered how easy the solver actually is.

I still think that even though completely over engineered and full of dead ends,
my though process may be of value for someone I guess.

### Recontextualizing

So first we need to understand that we are not doing any kind of dot product and
are not working with any kind of matrices.

Both only operate over the unsigned integers modulo 256, since the dot product
stores its output on a `char`. This will be the key to make the matrix
invertible.

You can then notice that in the fieds of integers modulo 256, `0xff * 0xff ==
1`. When I noticed I started to think that I could carefully place white pixels
on the QR code to specifically put some 1s where I wanted, but since patching a
single byte of the first/second matrix will impact the entire corresponding
row/column of the dot product, it doesn't work obviously

Now, obviously we will need to patch the QR code image, the question is how much
so that `libzbar` still decodes the correct digests and serial. So obviously,
we may resize the images of the QR codes to add some data.

### Dead end

So then this is where I had a really dumb idea. I though that maybe I could
append carefully crafted columns and empty lines to the first matrix, and
carefully crafted line and empty columns to the second matrix so that the result
of the dot product int overflow back to 0 or 1. Thus outputing 2 new images with the QR code in the top left corner.

And it actually kind of worked, but not entirely so I won't detail the
algorithm, I still implemented it entirely because I was really convincend this
was the intended way.

Why it doesn't work is because yes by adding rows and columns like that, being
carefull that everything cancels nicely with the data you inject on the other
matrix, the first N rows and columns of the original images have indeed been
inverted, but now you have a matrix which is somewhat bigger, and the parts you
added are not inverted, it was entirely 0 if I did not put the diagonal to 1 to
the rows/columns I added. If I decided to put the diagonal, then the bytes you
carefully injected are then reflected allong the dot product in this new bigger
matrix. So either way you need to perform the same process to repatch everyting
over this bigger matrix, infinetely recursing.


### How it's actually done

OK, so after this misadventure, the next step is to understand that a single
element of coordinates (i, j) from the dot product is impacted by all elements
of the ith line of the first matrix and all elements of the jth line. (You
actually already needed to understand this to implement my dumb idea but now we
will make it interesting).

Let's say that I take my first QR code and I double it's size and width like
this where the purple ones are all 0 matrices and the green one is the identity:

{{< image src="/brachiosaure/resizing.png" style="border-radius: 8px;" >}}

You can clearly see that if you patch any bytes in the identity matrix in the bottom right you will never impact the result of the top left corner of the dot
product.

If you are not convinced: take this more striking example:

{{< image src="/brachiosaure/dissociate.png" style="border-radius: 8px;" >}}

See how you can perform the dot product on each of the corner independently ?
That is the key to solving this, because now instead of putting the identity
matrix in the corresponding corner in the other image, we can simply compute the
inverse of the QR code:


{{< image src="/brachiosaure/overlap_inverses.png" style="border-radius: 8px;" >}}


## Inverting the two matrices

You may think "Ok this is over GG NO RE", but it is not that simple, at least it
wasn't for me because I suck at maths.

So I tried multiple implementations of the matrix modular inversion, some
worked, some didn't, but most importantly, all of them took ages to run on
actual images, about 10 minutes for most, and we are limited to 5 seconds on the
remote service.

The best implementation was the `sagemath` one which computed real size images
inverses in about 20 seconds, still too slow. But at least I could test locally
that the generated images were accepted by the program, and they were, so I knew
I was on the right track.

I tried reducing the size of the QR code to make it faster, and it ran in less
than a second, but the program could not recognize the data in the QR code
anymore.

Well we need another strategy. First because it is taking too long, but also
because not every matrix turns out to be invertible at all. And I don't want to
bruteforce the remote service to be lucky to have a username AND a serial matrix
that are both invertible and then be lucky enough that the program successfully
decodes the QR code.


## If it isn't invertible, juste make it invertible duh

So I go for a cleaner approach. I am not guaranteed that the QR code is invertible, fine, patch it to make it invertible.

And there is a really interesting property indeed:

{{< image src="/brachiosaure/invertible.png" style="border-radius: 8px;" >}}

By adding empty matrices and an identity matrix in the bottom right corner, the
resulting matrix is always invertible, and the inverse can be trivially computed
since it is simply moving matrices arround and negating the original image modulo 256 `notice the "-(QRuser)" in the inverted matrix`.

## Putting everything together

So what we need to do given a random username:

- Compute its sha512 digest
- Compute the serial, the square of the matrix of the digest
- Generate a QR code for the digest and another one for the serial
- Make both QR code invertible by adding empty and identity matrices as shown above
- Compute the said inverse of said matrices
- In the result user.png put:
	- The invertible digest QR code in the top left corner
	- The inverted serial QR code in the bottom right corner
- In the result serial.png put:
	- The inverted digest QR code in the top left corner
	- The invertible serial QR code in the bottom right corner


{{< image src="/brachiosaure/final.png" style="border-radius: 8px;" >}}


## Solver

Here is the final solver script, which also automates fetching the username
from the remote service and the upload of the images to recover the flag.

But before leaving this writeup there is still something I want to show you at the end.

{{< code file="/static/brachiosaure/solve_writeup.py" language="c" >}}


```console
$ ./solve_writeup.py
   <strong>FCSC{c2ddbd0310bcf5f65c576453ee9697774afd38dc887b64f4dccc63ac598d084b}</strong>
```

## Side notes

Here are examples of images generated by this solver for username `90QOCSdkzFE3rrYD2GdkrZkh4q`:


The original user digest QR code:

{{< image src="/brachiosaure/user.png" style="border-radius: 8px;" >}}


The original serial QR code:

{{< image src="/brachiosaure/serial.png" style="border-radius: 8px;" >}}


The patched user png

{{< image src="/brachiosaure/90QOCSdkzFE3rrYD2GdkrZkh4q_usr.png" style="border-radius: 8px;" >}}

The patched serial png

{{< image src="/brachiosaure/90QOCSdkzFE3rrYD2GdkrZkh4q_serial.png" style="border-radius: 8px;" >}}


As you can notice, there isn't any noise visible by naked eye, this script therefore get the flag 100% of the time.

Why is it so clean ? Simply because of the strategy we used to compute the
inverse matrix:

- We add empty matrices: they are black so no noise

- We add identity matrices: they only have the diagonal set to 1 so only a little bit grayer than the black, no noise visible by naked eyes

- We add the opposite of the matrix, and this is the clean part: our original matrices only hold black and white pixels so respectively `0x0` and `0xff`, so the opposite of `0` is still `0` and the opposite of `0xff` if `1` modulo 256, so like the identity matrix, they are nearly invisible. If you look closely though :eyes: you will see that all white pixels of the QR code were indeed reflected as very faint taint of gray in its inverse matrix on the other image.