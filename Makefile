dist:
	nuitka3 -j8 --onefile robotmicha

clean:
	rm -fr robotmicha.build robotmicha.dist robotmicha.bin