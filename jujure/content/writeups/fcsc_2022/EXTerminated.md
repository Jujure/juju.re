---
title: "Decrypting cryptolocked partition | EXTerminated @ FCSC 2022"
date: "2022-05-08 19:00:00"
author: "Juju"
tags: ["Reverse", "Writeup", "fcsc"]
toc: true
---

# Intro

EXTerminated is a malware reversing challenge. You are handed an EXT4 partition
that has been encrypted by a malware, your goal is to recover the original
unencrypted files.

The description of the challenge tells us that the malware does not use any
known cryptosystem to encrypt data, let's find this out.

{{< image src="/EXTerminated/panik.png" style="border-radius: 8px;" >}}

## Challenge description
`reverse` | `472 pts` `12 solves` :star::star:
```
Un client a détecté un seveur compromis sur son parc. Ce serveur semble avoir
perdu l'ensemble de ses données suite à une infection. Il nous indique que les
attaquants exigent une rançon et affirment pouvoir récupérer les fichiers
disparus.

Une analyse rapide du virus indique que ce dernier ne disposerait à première
vue d'aucun algorithme cryptographique connu.

On vous demande d'analyser ce disque, et de récupérer les fichiers originaux.

SHA256(disk.img) = a9e7891224868af43e2aa134152beaa2a83f43cde21af8038d138001377157dc.
```

Author: `Nofix`

## Given files

[disk.img](/EXTerminated/disk.img)

# Writeup

## Overview

So we can see we are given an EXT4 partition.

```console
$ file disk.img
disk.img: Linux rev 1.0 ext4 filesystem data,
UUID=c26167b3-e0b9-441d-ab4d-a5f4b5b1fcd0 (extents) (64bit) (large files)
(huge files)
```

Let's try to mount it.

We can see that there are multiple pictures, a pdf and an executable called
`wannaweep`, which is probably our malware.

```console
$ sudo mount -o loop ./disk.img mnt/
$ tree mnt/
mnt/
├── Documents
│   └── anssi-guide-ransomware_attacks_all_concerned-v1.0.pdf
├── Images
│   ├── accident.png
│   ├── disk.jpg
│   ├── flag.jpg
│   ├── martine.jpg
│   ├── smile.png
│   ├── tintin.jpeg
│   └── valide.png
├── lost+found  [error opening dir]
└── wannaweep

3 directories, 9 files
```

By further investigating we can see that all data of the files have been erased
except for wannaweep, which definitely is the malware, an x64 stripped and
dinamically linked ELF.

```console
$ file mnt/Images/flag.jpg 
mnt/Images/flag.jpg: data
$ xxd mnt/Images/flag.jpg | head
00000000: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000010: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000020: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000030: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000040: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000050: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000060: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000070: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000080: 0000 0000 0000 0000 0000 0000 0000 0000  ................
00000090: 0000 0000 0000 0000 0000 0000 0000 0000  ................
$ file mnt/wannaweep
mnt/wannaweep: ELF 64-bit LSB executable, x86-64, version 1 (SYSV),
dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2,
BuildID[sha1]=590a9f68cde37ffceb8e7441db343742e4032f47, for GNU/Linux
3.2.0, stripped
```

We can see that the binary links to `libext2fs.so.2`, a library for EXT file
system parsing and manipulation. Since it is dinamically linked we will still
have the corresponding symbols so I'm guessing I won't have too much trouble
understanding what the malware does even though I do not know the EXT
specification.

```console
$ ldd mnt/wannaweep
	linux-vdso.so.1 (0x00007ffccb2b3000)
	libext2fs.so.2 => /usr/lib/libext2fs.so.2 (0x00007f8059117000)
	libcom_err.so.2 => /usr/lib/libcom_err.so.2 (0x00007f8059111000)
	libc.so.6 => /usr/lib/libc.so.6 (0x00007f8058f07000)
	/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007f80591ad000)
```

## Main

It is now the perfect time for me to absolutely not launch this program, I
could have setup a sandboxed environment but it turned out it wasn't necessary,
the code was really straight forward.

So I start my favorite decompiler and I download the source code of libext2fs.

A small fast forward in time as the main function is really straight forward,

The program takes the path to the device to encrypt as argument, calls a bunch
of function that are mostly wrappers around libext2fs functions to initialize
some global variables holding structures of the EXT filesystem. It also checks
that some flags are set in the structures of libext2fs, I do not know if these
flags are implementation specific or are standard EXT flags but I did not
bother too much with this.

The interesting stuff is at the end, I can see that it calls a function that
I called `encrypt_folder` after reversing it. It then flushes the filesystem to
disk and write the inode bitmap.

{{< code file="/static/EXTerminated/main.c" language="c" >}}

## Encrypt folder

Alright so let's take a look at the `encrypt_folder` to understand why I called
it this way.

I could clearly see from `main` that this function was called with the string
`.` to reference the current directory, and a function pointer that was still
unkown to me at the time but that I renamed `encrypt_file`.

How I knew that the function was encrypting folders and that the parameter was
a callback to encrypt files is really simple, you can clearly see the libc
symbols calling `opendir` on the path given as argument (`.`), reading all the
entries of the directory and calling the callback if the entry is a file.

If it is not a file, it will `chdir` in the said directory, before recursively
calling itself with the same arguments.

{{< code file="/static/EXTerminated/encrypt_folder.c" language="c" >}}


## Encrypt file

Let's now look at the `encrypt_file` we guessed. Again, mostly wrapper
functions so I did not bother to show you why I named them this way, the code
basically reads the content of the file to encrypt, encrypts it in a dedicated
block, puts it in the file system before deleting the original content of the
file.

{{< code file="/static/EXTerminated/encrypt_file.c" language="c" >}}

## Encrypt block

Well, I was scared of custom cryptography but this seems simple enough for me.
To encrypt a plain text block, the malware starts at the last byte of the block
and xor it with the previous one until it reaches the start.
Actually this function does a heap buffer underflow when xoring the first byte
of the block, since it will xor it with the byte right before the block in the
heap.

Reversing the encryption is trivial, the only undefined behaviours is with the
underflow because we cannot know the value of the byte preceding the block.
However, I assumed it would really likely be 0.

{{< code file="/static/EXTerminated/encrypt_block.c" language="c" >}}

## Decrypting

So to decrypt a block, we simply need to know the value of the byte preceding
the buffer. Let's assume it is 0 since it is the most likely.

I will xor this byte with the first byte of cipher text and that will give
me the first byte of plain text, I then repeat the operation, xoring the
first byte of plain text with the second byte of cipher text and I do this
for the whole block to recover the entire block.


## Solve

So know I know how to decrypt a block, let's decrypt the whole filesystem.

I could do something really smart and overengineered to recover a valid
decrypted EXT filesystem that I could mount to recover the original files.

However I'm not familiar with the EXT specification and their are still small
shadow zones in the malware code for me, so I try a naive solution.

I'm guessing that data blocks of files or all alligned on `0x1000`, it would be
kind of weird otherwise for me. So if I just cut the whole filesystem in
`0x1000` sized blocks without any consideration of the semantic of those blocks
in the EXT structure, I could just decrypt each of these blocks individually,
and prey that I recover some files whose blocks were contiguous in the EXT
structure.

Obviously that will corrupt all the EXT metadata but it doesn't really matter
as long as I can recover the files.

{{< code file="/static/EXTerminated/decrypt.py" language="py" >}}

Now let's try to output the result and see if we find any file signatures:

```console
$ ./decrypt.py > decrypted.img
$ binwalk decrypted.img

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
9289728       0x8DC000        PNG image, 473 x 306, 8-bit/color RGB, non-interlaced
9531392       0x917000        JPEG image data, JFIF standard 1.01
9625600       0x92E000        PNG image, 500 x 564, 8-bit/color RGBA, non-interlaced
10125312      0x9A8000        JPEG image data, JFIF standard 1.01
10212833      0x9BD5E1        bix header, header size: 64 bytes, header CRC: 0x6003083D, created: 2004-01-10 13:39:36, image size: 2097152 bytes, Data Address: 0x22120000, Entry Point: 0x1E040003, data CRC: 0xD2100008, CPU: IA64, image name: ""
10231808      0x9C2000        JPEG image data, EXIF standard
10231820      0x9C200C        TIFF image data, big-endian, offset of first image directory: 8
10330112      0x9DA000        JPEG image data, EXIF standard
10330124      0x9DA00C        TIFF image data, big-endian, offset of first image directory: 8
10403840      0x9EC000        PNG image, 482 x 367, 8-bit/color RGB, non-interlaced
10403902      0x9EC03E        Zlib compressed data, default compression
34263365      0x20AD145       Cisco IOS experimental microcode, for ""
46640306      0x2C7ACB2       MySQL ISAM compressed data file Version 9
46691658      0x2C8754A       GIF image data 15531 x
```

We do! So let's try to extract them

```console
$ binwalk --dd='.*' decrypted.img 

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
9289728       0x8DC000        PNG image, 473 x 306, 8-bit/color RGB, non-interlaced
9531392       0x917000        JPEG image data, JFIF standard 1.01
9625600       0x92E000        PNG image, 500 x 564, 8-bit/color RGBA, non-interlaced
10125312      0x9A8000        JPEG image data, JFIF standard 1.01
10212833      0x9BD5E1        bix header, header size: 64 bytes, header CRC: 0x6003083D, created: 2004-01-10 13:39:36, image size: 2097152 bytes, Data Address: 0x22120000, Entry Point: 0x1E040003, data CRC: 0xD2100008, CPU: IA64, image name: ""
10231808      0x9C2000        JPEG image data, EXIF standard
10231820      0x9C200C        TIFF image data, big-endian, offset of first image directory: 8
10330112      0x9DA000        JPEG image data, EXIF standard
10330124      0x9DA00C        TIFF image data, big-endian, offset of first image directory: 8
10403840      0x9EC000        PNG image, 482 x 367, 8-bit/color RGB, non-interlaced
10403902      0x9EC03E        Zlib compressed data, default compression
34263365      0x20AD145       Cisco IOS experimental microcode, for ""
46640306      0x2C7ACB2       MySQL ISAM compressed data file Version 9
46691658      0x2C8754A       GIF image data 15531 x

$ file _decrypted.img.extracted/*
_decrypted.img.extracted/2C7ACB2:  MySQL ISAM compressed data file Version 9
_decrypted.img.extracted/2C8754A:  GIF image data 15531 x
_decrypted.img.extracted/8DC000:   PNG image data, 473 x 306, 8-bit/color RGB, non-interlaced
_decrypted.img.extracted/9A8000:   JPEG image data, JFIF standard 1.01, aspect ratio, density 1x1, segment length 16, progressive, precision 8, 660x424, components 3
_decrypted.img.extracted/9BD5E1:   data
_decrypted.img.extracted/9C200C:   TIFF image data, big-endian, direntries=0
_decrypted.img.extracted/9C2000:   JPEG image data, Exif standard: [TIFF image data, big-endian, direntries=0], comment: "CREATOR: gd-jpeg v1.0 (using IJG JPEG v62), quality = 90", baseline, precision 8, 481x600, components 3
_decrypted.img.extracted/9DA000:   JPEG image data, Exif standard: [TIFF image data, big-endian, direntries=0], baseline, precision 8, 683x500, components 3
_decrypted.img.extracted/9DA00C:   TIFF image data, big-endian, direntries=0
_decrypted.img.extracted/9EC000:   PNG image data, 482 x 367, 8-bit/color RGB, non-interlaced
_decrypted.img.extracted/9EC03E:   empty
_decrypted.img.extracted/9EC03E-0: zlib compressed data
_decrypted.img.extracted/20AD145:  cisco IOS experimental microcode for ''
_decrypted.img.extracted/92E000:   PNG image data, 500 x 564, 8-bit/color RGBA, non-interlaced
_decrypted.img.extracted/917000:   JPEG image data, JFIF standard 1.01, aspect ratio, density 1x1, segment length 16, baseline, precision 8, 495x669, components 3
```

Displaying the images we just extracted, we find the following one, giving us
the flag.

{{< image src="/EXTerminated/flag.png" style="border-radius: 8px;" >}}
