#!/usr/bin/python3

# Copyright (c) 2016,2017 Peter Lemenkov <lemenkov@gmail.com>
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

import argparse
import glob
import pybeam
import re
import rpm
import sys

from elftools.elf.elffile import ELFFile

# Globals
ERLLIBDIR = ""
ERLSHRDIR = "/usr/share/erlang/lib"

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

# fastest sort + uniq
# see http://www.peterbe.com/plog/uniqifiers-benchmark
def sort_and_uniq(List):
	return list(set(List))

def check_for_mfa(Path, Dict, MFA):
	(M, F, A) = MFA
	Provides = []
        #  First we try to find a (list of) module(s)...
	Beams = glob.glob("%s/%s.beam" % (Path, M))
	if Beams != []:
		# ...and we'll use a first match, e.g. Beams[0] (as Erlang VM will do).
                # But before parsing module let's check if we already parsed
                # it, and stored the results in a dict.
		Provides = Dict.get(Beams[0])
		if not Provides:
			# No, we have to parse beam-file for the first time.
			b = pybeam.BeamFile(Beams[0])
			Provides = b.exports
			# Note - there are two special cases:
			# * eunit_test - add "erlang(eunit_test:nonexisting_function/0)"
			# * wx - add "erlang(demo:start/0)"
			if M == "erlang":
				Provides += ErtsBIFProvides
			Dict[Beams[0]] = Provides

                # Now Provides contains module's M export table. Let's check if
                # this module M actually exports a required function F with
                # arity A.
		for (F0, A0, Idx) in Provides:
			if F0 == F and A0 == A:
				# Always return first match. See comment above.
				return Beams[0]

	return None

def inspect_so_library(library, export_name, dependency_name):
    with open(library, 'rb') as f:
        elffile = ELFFile(f)
        dynsym = elffile.get_section_by_name('.dynsym')
        for sym in dynsym.iter_symbols():
            if sym.name == export_name:
                ts = rpm.TransactionSet()
                mi = ts.dbMatch('providename', dependency_name)
                h = next(mi)
                ds = dict(map(lambda x: x[0].split(" ")[1::2], rpm.ds(h, "providename")))
                if dependency_name in ds:
                    f.close()
                    return "%s = %s" % (dependency_name, ds[dependency_name])

        f.close()
        return None


# Compatibility function for the upcoming RPM Python3 API
# See https://bugzilla.redhat.com/1693771
def b2s(data):
    if isinstance(data, bytes):
        return data.decode('utf-8')
    return data

def inspect_beam_file(ISA, filename):
    b = pybeam.BeamFile(filename)
    # [(M,F,A),...]
    BeamMFARequires = sort_and_uniq(b.imports)

    Dict = {}
    # Filter out locally provided Requires

    # dirname(filename) could be:
    # * '$BUILDROOT/elixir-1.4.2-1.fc26.noarch/usr/share/elixir/1.4.2/lib/mix/ebin'
    # * '$BUILDROOT/erlang-y-combinator-1.0-1.fc26.noarch/usr/lib/erlang/lib/y-1.0/ebin'
    # * '$BUILDROOT/erlang-emmap-0-0.18.git05ae1bb.fc26.x86_64/usr/lib64/erlang/lib/emmap-0/ebin'
    # WARNING - this won't work for files from ERLLIBDIR
    BeamMFARequires = list(filter(lambda X: check_for_mfa('/'.join(filename.split('/')[:-3] + ["*", "ebin"]), Dict, X) is None, BeamMFARequires))

    Dict = {}
    # TODO let's find modules which provides these requires
    for (M,F,A) in BeamMFARequires:
        # FIXME check in noarch Erlang dir also
        if not check_for_mfa("%s/*/ebin" % ERLLIBDIR, Dict, (M, F, A)) and not check_for_mfa("%s/*/ebin" % ERLSHRDIR, Dict, (M, F, A)):
            print("ERROR: Cant find %s:%s/%d while processing '%s'" % (M,F,A, filename), file=sys.stderr)
            # We shouldn't stop further processing here - let pretend this is just a warning
            #exit(1)

    BeamModRequires = sort_and_uniq(Dict.keys())

    # let's find RPM-packets to which these modules belongs
    # We return more than one match since there could be situations where the same
    # object belongs to more than one package.
    ts = rpm.TransactionSet()
    RPMRequires = [item for sublist in map(
            lambda x: [(b2s(h[rpm.RPMTAG_NAME]), b2s(h[rpm.RPMTAG_ARCH])) for h in ts.dbMatch('basenames', x)],
            BeamModRequires
        ) for item in sublist]

    Ret = []
    for (req, PkgISA) in sort_and_uniq(RPMRequires):
        # ISA == "" if rpmbuild invoked with --target noarch
        if ISA == "noarch" or ISA == "" or PkgISA == "noarch":
            # noarch package - we don't care about arch dependency
            # erlang-erts erlang-kernel ...
            Ret += ["%s" % req]
        else:
            # arch-dependent package - we will use exact arch of adependent packages
            # erlang-erts(x86-64) erlang-kernel(x86-64) ...
            Ret += ["%s(%s)" % (req, ISA)]

    return sorted(Ret)

if __name__ == "__main__":

    ##
    ## Begin
    ##

    parser = argparse.ArgumentParser()

    # Get package's ISA
    parser.add_argument("-i", "--isa", nargs='?')
    args = parser.parse_args()

    if args.isa:
        # Convert "(x86-64)" to "x86-64"
        ISA=args.isa[1:-1]
    else:
        ISA="noarch"

    # Get the main Erlang directory
    prog = re.compile("/usr/lib(64)?/erlang/lib")
    ERLLIBDIR = prog.match(glob.glob("/usr/lib*/erlang/lib/erts-*/ebin/erts.app")[0])[0]

    # All the Erlang files matched by erlang.attr specification from the
    # package. Modern RPM version passes files one by one (a list
    # containing one filename prefixed by '\n'. We do not support older RPM
    # versions.
    #
    # We read filename as a list with a single element from stdin, get the
    # first element in the list, strip off the prefix, and pass it into the
    # main function.
    filename = sys.stdin.readlines()[0].rstrip('\n')

    Ret = []
    if filename.endswith(".beam"):
        Ret = inspect_beam_file(ISA, filename)

    elif filename.endswith(".so"):
        Ret += [inspect_so_library(filename, 'nif_init', 'erlang(erl_nif_version)')]
        Ret += [inspect_so_library(filename, 'driver_init', 'erlang(erl_drv_version)')]

    elif filename.endswith(".app"):
        # TODO we don't know what to do with *.app files yet
        pass

    else:
        # Unknown type
        pass

    for StringDependency in Ret:
        if StringDependency != None:
            print(StringDependency)
