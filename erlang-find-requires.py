#!/usr/bin/python3

# Copyright (c) 2016 Peter Lemenkov <lemenkov@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This script reads filenames from STDIN and outputs any relevant requires
# information that needs to be included in the package.

import getopt
import glob
import pybeam
import re
import rpm
import sys

# See $BUILDROOT/erts/emulator/*/erl_bif_list.h
# erlang:F/A
ErtsBIFProvides = [
	("*", 2, 0),
	("++", 2, 0),
	("+", 1, 0),
	("+", 2, 0),
	("--", 2, 0),
	("-", 1, 0),
	("-", 2, 0),
	("/", 2, 0),
	("/=", 2, 0),
	("<", 2, 0),
	("=/=", 2, 0),
	("=:=", 2, 0),
	("=<", 2, 0),
	("==", 2, 0),
	(">", 2, 0),
	(">=", 2, 0),
	("and", 2, 0),
	("band", 2, 0),
	("bnot", 1, 0),
	("bor", 2, 0),
	("bsl", 2, 0),
	("bsr", 2, 0),
	("bxor", 2, 0),
	("div", 2, 0),
	("not", 1, 0),
	("or", 2, 0),
	("rem", 2, 0),
	("xor", 2, 0)
]

# See $BUILDROOT/erts/emulator/*/erl_bif_list.h
# hipe_bifs:F/A
HipeBIFSprovides = [
	("add_ref", 2, 0),
	("alloc_data", 2, 0),
	("array", 2, 0),
	("array_length", 1, 0),
	("array_sub", 2, 0),
	("array_update", 3, 0),
	("atom_to_word", 1, 0),
	("bif_address", 3, 0),
	("bitarray", 2, 0),
	("bitarray_sub", 2, 0),
	("bitarray_update", 3, 0),
	("bytearray", 2, 0),
	("bytearray_sub", 2, 0),
	("bytearray_update", 3, 0),
	("call_count_clear", 1, 0),
	("call_count_get", 1, 0),
	("call_count_off", 1, 0),
	("call_count_on", 1, 0),
	("check_crc", 1, 0),
	("code_size", 1, 0),
	("constants_size", 0, 0),
	("debug_native_called", 2, 0),
	("enter_code", 2, 0),
	("enter_sdesc", 1, 0),
	("find_na_or_make_stub", 2, 0),
	("fun_to_address", 1, 0),
	("gc_info", 0, 0),
	("gc_info_clear", 0, 0),
	("gc_timer", 0, 0),
	("gc_timer_clear", 0, 0),
	("get_fe", 2, 0),
	("get_hrvtime", 0, 0),
	("get_rts_param", 1, 0),
	("incremental_gc_info", 0, 0),
	("invalidate_funinfo_native_addresses", 1, 0),
	("in_native", 0, 0),
	("llvm_fix_pinned_regs", 0, 0),
	("mark_referred_from", 1, 0),
	("merge_term", 1, 0),
	("message_info", 0, 0),
	("message_info_clear", 0, 0),
	("message_sizes", 0, 0),
	("misc_timer", 0, 0),
	("misc_timer_clear", 0, 0),
	("modeswitch_debug_off", 0, 0),
	("modeswitch_debug_on", 0, 0),
	("nstack_used_size", 0, 0),
	("patch_call", 3, 0),
	("patch_insn", 3, 0),
	("pause_times", 0, 0),
	("primop_address", 1, 0),
	("process_info", 0, 0),
	("process_info_clear", 0, 0),
	("redirect_referred_from", 1, 0),
	("ref", 1, 0),
	("ref_get", 1, 0),
	("ref_set", 2, 0),
	("remove_refs_from", 1, 0),
	("send_timer", 0, 0),
	("send_timer_clear", 0, 0),
	("set_funinfo_native_address", 3, 0),
	("set_native_address", 3, 0),
	("set_native_address_in_fe", 2, 0),
	("shared_gc_info", 0, 0),
	("shared_gc_timer", 0, 0),
	("show_estack", 1, 0),
	("show_heap", 1, 0),
	("show_nstack", 1, 0),
	("show_pcb", 1, 0),
	("show_term", 1, 0),
	("stop_hrvtime", 0, 0),
	("system_crc", 0, 0),
	("system_timer", 0, 0),
	("system_timer_clear", 0, 0),
	("term_to_word", 1, 0),
	("trap_count_clear", 0, 0),
	("trap_count_get", 0, 0),
	("update_code_size", 3, 0),
	("write_u32", 2, 0),
	("write_u64", 2, 0),
	("write_u8", 2, 0)
]

# sort + uniq
# see http://www.peterbe.com/plog/uniqifiers-benchmark
def sort_and_uniq(List):
	return list(set(List))

def check_for_mfa(Path, Dict, MFA):
	(M, F, A) = MFA
	Provides = []
	Beams = glob.glob("%s/erlang/lib/*/ebin/%s.beam" % (Path, M))
	if Beams != []:
		Provides = Dict.get(Beams[0])
		if not Provides:
			# Check if a module actually has required function
			b = pybeam.BeamFile(Beams[0])
			# Two special cases:
			# * eunit_test - add "erlang(eunit_test:nonexisting_function/0)"
			# * wx - add "erlang(demo:start/0)"
			Provides = b.exports
			if M == "erlang":
				Provides += ErtsBIFProvides
			Dict[Beams[0]] = Provides

		for (F0, A0, Idx) in Provides:
			if F0 == F and A0 == A:
				# Always return first match
				return Beams[0]

	return None

# We return more than one match since there could be situations where the same
# object belongs to more that one package.
def get_rpms_by_path(Path):
	Packages = []
	ts = rpm.TransactionSet()
	mi = ts.dbMatch('basenames', Path)
	for h in mi:
		Packages += [h[rpm.RPMTAG_NAME].decode("utf-8")]

	return Packages

BUILDROOT=""
ISA=""
LIBDIR=""

opts, args = getopt.getopt(sys.argv[1:],"b:i:l:",["builddir=", "isa=", "libdir="])

for opt, arg in opts:
	if opt in ("-b", "--builddir"):
		BUILDROOT=arg
	if opt in ("-i", "--isa"):
		ISA=arg
	if opt in ("-l", "--libdir"):
		LIBDIR=arg

# All the files and directories from the package (including %docs and %license)
# Modern RPM version passes files one by one, while older version create a list
# of files and pass the entire list
rawcontent = sys.stdin.readlines()

Requires = []

rawcontent = list(map(lambda x: x.rstrip('\n'), rawcontent))

# Iterate over all BEAM-files
# See note above regarding list of beam-fuiles vs. one beam-file
beammask = re.compile(".*/ebin/.*\.beam")
rawcontent = sorted([p for p in rawcontent if beammask.match(p)])
for package in rawcontent:
	b = pybeam.BeamFile(package)
	# [(M,F,A),...]
	Requires += b.imports

Requires = list(set(Requires))

Dict = {}
# Filter out locally provided Requires
Requires = list(filter(lambda X: check_for_mfa("%s/%s" % (BUILDROOT, LIBDIR), Dict, X) is None, Requires))

Dict = {}
# TODO let's find modules which provides these requires
for (M,F,A) in Requires:
	if not check_for_mfa(LIBDIR, Dict, (M, F, A)):
		print("ERROR: Cant find %s:%s/%d while processing '%s'" % (M,F,A, rawcontent[0]))
		# We shouldn't stop further processing here - let pretend this is just a warning
		#exit(1)

Requires = list(Dict.keys())

# let's find RPM-packets to which these modules belongs
Requires = [item for sublist in map(get_rpms_by_path, sort_and_uniq(Requires)) for item in sublist]


for req in sort_and_uniq(Requires):
	# erlang-erts(x86-64) erlang-kernel(x86-64) ...
	print("%s%s" % (req, ISA))
