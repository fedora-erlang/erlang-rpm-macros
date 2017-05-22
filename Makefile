all: test

check: test

test: test.beam
	/usr/bin/python3 ./testing.py

test.beam: clean
	@erlc test.erl

clean:
	@rm -f test.beam
	@rm -f *~
