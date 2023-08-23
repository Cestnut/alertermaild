CC=gcc
CFLAGS= -Wall

all: deb clean

compile:nanoalertmaild.c
	$(CC) $(CFLAGS) nanoalertmaild.c -o nanoalertmaild


deb: compile
	mkdir tmp
	mkdir -p tmp/opt/
	mkdir -p tmp/lib/systemd/system
	
	mkdir -p tmp/usr/bin

	cp -r alertmaild tmp/opt/
	cp alertmail.service tmp/lib/systemd/system
	cp nanoalertmaild tmp/usr/bin
	
	cp -r DEBIAN/ tmp/
	
	dpkg-deb --build tmp alertmaild.deb

clean:
	rm -r tmp
	rm nanoalertmaild