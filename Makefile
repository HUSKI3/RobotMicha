dist:
	nuitka3 --static-libpython=yes -j8 --onefile robotmicha

clean:
	rm -fr robotmicha.build robotmicha.dist robotmicha.bin