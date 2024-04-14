---
title: "Black box reversing | Archiver @ FCSC 2024"
date: "2024-04-13 22:00:00"
author: "Juju"
tags: ["Reverse", "Writeup", "fcsc"]
toc: true
---

# Intro

This writeup is not a really serious one, if you are reading this
as part of the FCSC writeup reviews, my submitted writeups are
actually for `svartalfheim` and `megalosaure`. I still thought
it would be funny to include this one as it is not that long and
I think my solution is kind of unintended.

Basically we are given a `Windows` stripped binary, compiled
from `rust`. The binary is an encrypted archive manager.

This challenge managed to put every single reverser red flag
in a single binary.

I tried opening up the binary in `binary ninja` or `IDA`, but it
was as expected: stripped `rust`.

So let's close this up, never touch it again and see what we can
do without reading the code or debugging.

{{< image src="/archiver/meme.jpg" style="border-radius: 8px;" >}}

## Challenge description

`reverse` | `490 pts` `5 solves` `:star::star:`

```
Notre équipe SIGINT a intercepté un e-mail contenant une pièce jointe
result.fcsc. Vu l'extension, il doit s'agir d'une archive au format
propriétaire FCSC. Nous avons pu récupérer l'utilitaire dans sa version
Windows, archiver.exe.

Vu le contenu de l'e-mail, ça a l'air assez important. Est-ce qu'on a une
chance de savoir ce qu'il y a dedans ?

Votre prédécesseur, après avoir réussi une analyse similaire, a sombré
dans la folie et réside désormais dans un asile psychiatrique. Il
murmurait des mots étranges comme "TTD" et parlait sans arrêt de hardware
breakpoint.

Note : La chaîne que vous trouverez est à mettre entre FCSC{} pour avoir
le flag.

```

## Given files

[archiver.exe](/archiver/archiver.exe)

[result.fcsc](/archiver/result.fcsc)

# Writeup

## Overview

With the binary, we are also given a `result.fcsc`, which is
an archive encrypted with the given binary.

This archive contains the flag and we must decrypt it.

```console
$ xxd result.fcsc 
00000000: 0100 0000 0000 0000 21e2 ae0f b85f de7b  ........!...._.{
00000010: b246 ed90 194f 601e 041b 3c8a c6e9 37b1  .F...O`...<...7.
00000020: 878b d8e0 e796 a098 1800 0000 0000 0000  ................
00000030: d44a b96f ea76 8c55 73a0 7266 1a5e b5fd  .J.o.v.Us.rf.^..
00000040: c3bf cc29 8ed7 e925 1800 0000 0000 0000  ...)...%........
00000050: f96d be51 956d 9342 7e3d 1c0d bbef ad7a  .m.Q.m.B~=.....z
00000060: bc57 7bf0 f36a cb23                      .W{..j.#
```


## Common fields

### Sizes

First thing we can see are 3 `uint64_t` packed in little endian at offsets:

* `0x0`
* `0x28`
* `0x48`

Given how small these numbers are, they are probably representing
some sizes.

If we count manually, we see that the last two `uint64_t` represent the size of the data that immediatly follows them.

The first one is still unknown but as it is `1`, it probably just
is the number of files in the archive.

### sha256

Now let's try to create our own archive:

```console
$ echo -n 'FCSC{test_flag}' > flag.txt
$ $ ./archiver.exe create password test.db flag.txt
$ xxd test.db 
00000000: 0100 0000 0000 0000 21e2 ae0f b85f de7b  ........!...._.{
00000010: b246 ed90 194f 601e 041b 3c8a c6e9 37b1  .F...O`...<...7.
00000020: 878b d8e0 e796 a098 1800 0000 0000 0000  ................
00000030: 8257 3ccc 2608 498d b6b7 5801 740f 2e4e  .W<.&.I...X.t..N
00000040: 8b36 0169 9273 2c91 1f00 0000 0000 0000  .6.i.s,.........
00000050: a278 0ee8 7308 548a 84af 1ad4 6c0c 0844  .x..s.T.....l..D
00000060: de13 a830 ea7f 4d37 19ea 7efe 14b5 c5    ...0..M7..~....
```

Two things are already weird:

* Everything is identical to the given archive until offset `0x30`
* This archive is larger than the given one. Either the flag is really small or data is compressed.

Let's try to archive a really low entropy file to see if the archive is smaller:

```console
$ echo -n 'aaaaaaaaaaaaaaa' > aaaaaaaa
$ ./archiver.exe create password low_entropy.db aaaaaaaa 
$ xxd low_entropy.db 
00000000: 0100 0000 0000 0000 1f3c e404 15a2 081f  .........<......
00000010: a3ee e75f c39f ff8e 56c2 2270 d1a9 78a7  ..._....V."p..x.
00000020: 249b 592d cebd 20b4 1800 0000 0000 0000  $.Y-.. .........
00000030: b2b6 ed4e 38bb 52b8 5cd7 12a7 7df6 261b  ...N8.R.\...}.&.
00000040: 2bbf f8df 77c4 dfe8 1f00 0000 0000 0000  +...w...........
00000050: b2b6 ed4e 38bb 52b8 8876 7671 b114 9799  ...N8.R..vvq....
00000060: cb38 24e6 02f9 26f9 25ec a7b8 bdb9 56    .8$...&.%.....V
```

I put exactly the same sizes in the file name and size data.

The resulting archive is exactly the same size so no compression
is performed.

But wait ! Something changed !

In our first archive, the firsts `0x30` bytes where identical
but now they differ starting at `0x8`, they differ for `0x20` bytes
before becoming the same again on the field we identified as a size.

Well, we changed two things: the filename and the file data.

It is unlikely that we guessed the file data on our first try.

But the filename however ? What if the the format stores a hash
of the filename on `0x20` bytes at offset `0x8` ?

```console
$ echo -n 'flag.txt' | sha256sum 
21e2ae0fb85fde7bb246ed90194f601e041b3c8ac6e937b1878bd8e0e796a098  -
```

Bingo ! It matches the bytes we have in our first custom archive
and the one given.

So we know that the filename is `flag.txt` and that the archives
stores the `sha256` of the filename at offset `0x8`.

### Cipher texts

I wil now try to play with data sizes to identify what are the sizes in the binary refering to.

Let's create an archive with a filename 1 byte smaller, and data 1 byte larger:

```console
$ echo -n 'aaaaaaaaaaaaaaaa' > aaaaaaa
$ ./archiver.exe create password sizes.db aaaaaaa
$ xxd sizes.db 
00000000: 0100 0000 0000 0000 e462 4071 4b5d b3a2  .........b@qK]..
00000010: 3eee 6047 9a62 3efb a4d6 33d2 7fe4 f03c  >.`G.b>...3....<
00000020: 904b 9e21 9a7f be60 1700 0000 0000 0000  .K.!...`........
00000030: 8ab9 acd8 126c cc48 064e 9843 2fa1 9492  .....l.H.N.C/...
00000040: 8503 ce34 399c 9820 0000 0000 0000 008a  ...49.. ........
00000050: b9ac d812 6ccc f370 a362 da68 de94 c7d2  ....l..p.b.h....
00000060: aa91 eb29 2be2 0aa3 a74f fd99 4dc0 ca    ...)+....O..M..
```

Notice that the first `uint64_t` went from `0x18` to `0x17` and
the second one from `0x1f` to `0x20`

Thus the first size and data correspond to the encrypted file name, and the second one to the encrypted data.

We can also see that encrypted data is always exactly `0x10` bytes
larger that the plaintext. So it probably just adds a `0x10` bytes IV in front of it.

Looking back at the original archive, we can thus see that the
the filename is `0x8` bytes large (which matches the `flag.txt`
we found) and the data is also `0x8` bytes large, thus confirming
the really small flag. (see below for a reminder of the original
archive)

```console
$ xxd result.fcsc 
00000000: 0100 0000 0000 0000 21e2 ae0f b85f de7b  ........!...._.{
00000010: b246 ed90 194f 601e 041b 3c8a c6e9 37b1  .F...O`...<...7.
00000020: 878b d8e0 e796 a098 1800 0000 0000 0000  ................
00000030: d44a b96f ea76 8c55 73a0 7266 1a5e b5fd  .J.o.v.Us.rf.^..
00000040: c3bf cc29 8ed7 e925 1800 0000 0000 0000  ...)...%........
00000050: f96d be51 956d 9342 7e3d 1c0d bbef ad7a  .m.Q.m.B~=.....z
00000060: bc57 7bf0 f36a cb23                      .W{..j.#
```

## Figuring out the crypto

Now I will try to get a file as close as possible as the original
flag and see how the resulting archive behaves to small
input mutations:

```console
$ echo -n '12345678' > flag.txt
$ ./archiver.exe create password 12345678.db flag.txt 
$ echo -n '22345678' > flag.txt
$ ./archiver.exe create password 22345678.db flag.txt 
$ xxd 12345678.db 
00000000: 0100 0000 0000 0000 21e2 ae0f b85f de7b  ........!...._.{
00000010: b246 ed90 194f 601e 041b 3c8a c6e9 37b1  .F...O`...<...7.
00000020: 878b d8e0 e796 a098 1800 0000 0000 0000  ................
00000030: 8257 3ccc 2608 498d b6b7 5801 740f 2e4e  .W<.&.I...X.t..N
00000040: 8b36 0169 9273 2c91 1800 0000 0000 0000  .6.i.s,.........
00000050: d509 6e9f 3d4a 06c1 9daa bebe f6cb c23b  ..n.=J.........;
00000060: cf4e 3d32 2b68 09cf                      .N=2+h..
$ xxd 22345678.db 
00000000: 0100 0000 0000 0000 21e2 ae0f b85f de7b  ........!...._.{
00000010: b246 ed90 194f 601e 041b 3c8a c6e9 37b1  .F...O`...<...7.
00000020: 878b d8e0 e796 a098 1800 0000 0000 0000  ................
00000030: 8257 3ccc 2608 498d b6b7 5801 740f 2e4e  .W<.&.I...X.t..N
00000040: 8b36 0169 9273 2c91 1800 0000 0000 0000  .6.i.s,.........
00000050: d609 6e9f 3d4a 06c1 cc6e be60 dd5d 8214  ..n.=J...n.`.]..
00000060: 05bb cadc 0bf1 e4b8                      ........
```


Most part of the two archives are identical, as expected.

But maybe a little bit too much identical:

Look at the IV of the file data's cipher text (offset `0x50`)

The first 8 bytes are almost identical, only the first one
has been increased by one.

Could it be that the IV is generated with the clear text data ?

Let's try with an other data:

```console
$ echo -n '32345678' > flag.txt
$ ./archiver.exe create password 32345678.db flag.txt 
$ xxd 32345678.db 
00000000: 0100 0000 0000 0000 21e2 ae0f b85f de7b  ........!...._.{
00000010: b246 ed90 194f 601e 041b 3c8a c6e9 37b1  .F...O`...<...7.
00000020: 878b d8e0 e796 a098 1800 0000 0000 0000  ................
00000030: 8257 3ccc 2608 498d b6b7 5801 740f 2e4e  .W<.&.I...X.t..N
00000040: 8b36 0169 9273 2c91 1800 0000 0000 0000  .6.i.s,.........
00000050: d709 6e9f 3d4a 06c1 fcd2 be2a c42f bdf1  ..n.=J.....*./..
00000060: 43e8 9879 eb86 bf95                      C..y....
```

Again, patching slightly the `n`th byte of the clear text only
patched slightly the `n`th byte of the IV.

I played with some values and noticed that the operation performed
is actually a xor:

```console
>>> 0xd7 ^ ord('3')
228
>>> 0xd6 ^ ord('2')
228
>>> 0xd5 ^ ord('1')
228
```

So the clear text is xored with a key to generate the IV,
but I do not know the said key, which seems to be derived
from the archive password.

## Known plaintext

Or do I ?

Remember that I know that filename is `flag.txt`, and that I have
an associated ciphertext.

With a little bit of luck, the IV of the filename cipher text
is generated with the key:

```console
>>> 0x82 ^ ord('f')
228
```

Looks like it does.

Since I have a known plaintext, example cipher text.

I can simply, xor the plaintext with the filename IV to recover
the xor key.

Then apply the same key to the file data IV to recover the
plain text:


```python
#!/usr/bin/env python3
from pwn import *
filename = b'flag.txt'
IV = b'\xd4\x4a\xb9\x6f\xea\x76\x8c\x55'
c = b'\xf9\x6d\xbe\x51\x95\x6d\x93\x42'
key = xor(IV, filename)
flag = xor(c, key)
print('FCSC{' + flag.decode() + '}')
```

```console
$ ./solve.py 
FCSC{KKfYQogc}
```