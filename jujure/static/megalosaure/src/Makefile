.PHONY: all run

all: ./solver

./simple: ./megalosaure.c simple.c
	gcc -Wno-overflow simple.c megalosaure.c -o simple -O3 -march=native -fno-pie -no-pie

./megalosaure.c: ./disasm.py
	./disasm.py

./solver: ./megalosaure.c main.c
	gcc -Wno-overflow main.c megalosaure.c -o solver -O3 -march=native -fno-pie -no-pie

run: all
	./solver
