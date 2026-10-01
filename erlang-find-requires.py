#!/usr/bin/python3

# SPDX-FileCopyrightText: © 2016-2026 Peter Lemenkov
# SPDX-FileCopyrightText: erlang-rpm-macros contributors
# SPDX-License-Identifier: MIT

# RPM dependency generator for Erlang, using the multifile protocol (RPM 4.20+).
# It reads the names of all matching files from STDIN and prints, for every
# file which has any, a ";<filename>" line followed by its requires:
#
# * for BEAM files, the packages providing the functions the module calls,
#   except those provided by the package itself;
# * for NIF and driver libraries, the NIF and driver API versions.

import argparse
import functools
import glob
import os
import struct
import sys
import zlib

import rpm
from elftools.elf.elffile import ELFFile
from pybeam.schema.beam.chunks import Atom, AtU8, ExpT, ImpT

ERLSHRDIR = "/usr/share/erlang/lib"

def erlang_libdir():
	# /usr/lib64/erlang/lib or /usr/lib/erlang/lib, depending on the arch
	erts = sorted(glob.glob("/usr/lib*/erlang/lib/erts-*/ebin/erts.app"))
	return os.path.dirname(os.path.dirname(os.path.dirname(erts[0]))) if erts else None

def read_chunks(filename, names):
	"""Return the raw contents of the given chunks of a BEAM file.

	Only the chunks needed are decoded afterwards, which is much faster
	than letting pybeam.BeamFile parse the whole file."""
	with open(filename, "rb") as f:
		data = f.read()
	if data[:2] == b'\x1f\x8b':
		data = zlib.decompress(data, 31)
	chunks = {}
	pos = 12
	while pos + 8 <= len(data):
		name = data[pos:pos + 4]
		size = struct.unpack(">I", data[pos + 4:pos + 8])[0]
		if name in names:
			chunks[name] = data[pos + 8:pos + 8 + size]
		pos += 8 + ((size + 3) & ~3)
	return chunks

def atoms(chunks):
	if b"AtU8" in chunks:
		return AtU8.parse(chunks[b"AtU8"])
	return Atom.parse(chunks[b"Atom"])

@functools.cache
def exports(filename):
	"""The set of (Function, Arity) exported by a module."""
	chunks = read_chunks(filename, (b"AtU8", b"Atom", b"ExpT"))
	a = atoms(chunks)
	return frozenset((a[e.function - 1], e.arity) for e in ExpT.parse(chunks[b"ExpT"]).entry)

def imports(filename):
	"""The set of (Module, Function, Arity) called by a module."""
	chunks = read_chunks(filename, (b"AtU8", b"Atom", b"ImpT"))
	a = atoms(chunks)
	return {(a[e.module - 1], a[e.function - 1], e.arity) for e in ImpT.parse(chunks[b"ImpT"]).entry}

@functools.cache
def find_module(pattern, module):
	beams = sorted(glob.glob(f"{pattern}/{module}.beam"))
	return beams[0] if beams else None

def provider(pattern, mfa):
	"""The BEAM file under pattern which exports mfa, or None.

	Like the Erlang VM, only the first module with the right name counts."""
	(m, f, a) = mfa
	beam = find_module(pattern, m)
	return beam if beam and (f, a) in exports(beam) else None

@functools.cache
def transaction_set():
	return rpm.TransactionSet()

@functools.cache
def owners(filename):
	"""(Name, Arch) of the installed packages which own a file."""
	return tuple((h[rpm.RPMTAG_NAME], h[rpm.RPMTAG_ARCH])
		for h in transaction_set().dbMatch("basenames", filename))

def beam_requires(isa, libdirs, filename):
	# The directory of the BEAM file could be:
	# * '$BUILDROOT/usr/share/elixir/1.4.2/lib/mix/ebin'
	# * '$BUILDROOT/usr/lib/erlang/lib/y-1.0/ebin'
	# * '$BUILDROOT/usr/lib64/erlang/lib/emmap-0/ebin'
	# so the applications of the package itself are found at ../../*/ebin.
	local = "/".join(filename.split("/")[:-3] + ["*", "ebin"])
	modules = set()
	for mfa in sorted(imports(filename)):
		if provider(local, mfa):
			continue
		beam = next((b for b in (provider(f"{d}/*/ebin", mfa) for d in libdirs) if b), None)
		if beam:
			modules.add(beam)
		else:
			# Not fatal: the function might be loaded at runtime from elsewhere
			(m, f, a) = mfa
			print(f"ERROR: Can't find {m}:{f}/{a} while processing '{filename}'", file=sys.stderr)

	requires = set()
	for beam in modules:
		for (name, arch) in owners(beam):
			# isa is "noarch" when building a noarch package
			if isa == "noarch" or arch == "noarch":
				requires.add(name)
			else:
				requires.add(f"{name}({isa})")
	return sorted(requires)

@functools.cache
def provided_version(capability):
	"""'capability = version' as provided by an installed package, or None."""
	for h in transaction_set().dbMatch("providename", capability):
		for dep in rpm.ds(h, "providename"):
			if dep.N() == capability and dep.EVR():
				return f"{capability} = {dep.EVR()}"
	return None

# Entry points of NIF and driver libraries, and the API versions they need
SO_ENTRY_POINTS = (
	("nif_init", "erlang(erl_nif_version)"),
	("driver_init", "erlang(erl_drv_version)"),
)

def so_requires(filename):
	with open(filename, "rb") as f:
		dynsym = ELFFile(f).get_section_by_name(".dynsym")
		if dynsym is None:
			return []
		found = [cap for (sym, cap) in SO_ENTRY_POINTS if dynsym.get_symbol_by_name(sym)]
	return [dep for dep in map(provided_version, found) if dep]

def main(argv=None):
	parser = argparse.ArgumentParser(description="RPM requires generator for Erlang")
	parser.add_argument("-i", "--isa", nargs="?", default="",
		help="the package ISA as in %%{_isa}, e.g. (x86-64); empty for noarch")
	args = parser.parse_args(argv)
	isa = (args.isa or "").strip("()") or "noarch"
	libdirs = [d for d in (erlang_libdir(), ERLSHRDIR) if d]

	for line in sys.stdin:
		filename = line.rstrip("\n")
		if filename.endswith(".beam"):
			requires = beam_requires(isa, libdirs, filename)
		elif filename.endswith(".so"):
			requires = so_requires(filename)
		else:
			continue
		if requires:
			print(";" + filename)
			for dep in requires:
				print(dep)

if __name__ == "__main__":
	main()
