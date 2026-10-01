# SPDX-FileCopyrightText: © 2017-2026 Peter Lemenkov
# SPDX-License-Identifier: CC0-1.0

CC ?= cc

TEST_FILES = test.beam test_nif.so test_drv.so test_nodynsym.so

all: test

check: test

test: $(TEST_FILES)
	/usr/bin/python3 ./testing.py

test.beam: test.erl
	@erlc test.erl

# Only the entry point symbols matter to the requires generator
test_nif.so:
	@echo 'void *nif_init(void) { return 0; }' | $(CC) -shared -fPIC -x c -o $@ -

test_drv.so:
	@echo 'void *driver_init(void) { return 0; }' | $(CC) -shared -fPIC -x c -o $@ -

# A relocatable object has no .dynsym section
test_nodynsym.so:
	@echo 'void *nif_init(void) { return 0; }' | $(CC) -c -x c -o $@ -

clean:
	@rm -f $(TEST_FILES)
	@rm -f *~

.PHONY: all check test clean
