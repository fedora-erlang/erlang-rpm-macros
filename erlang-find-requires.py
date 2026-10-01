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
                Pn = rpm.ds(h, "providename")
                Map = map(lambda x: x[0].split(" ")[1::2], Pn)
                # Filter out unversioned dependencies like "group(epmd)"
                Filter = filter(lambda x: len(x) == 2, Map)
                ds = dict(Filter)
                if dependency_name in ds:
                    f.close()
                    return "%s = %s" % (dependency_name, ds[dependency_name])

        f.close()
        return None


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
            lambda x: [(h[rpm.RPMTAG_NAME], h[rpm.RPMTAG_ARCH]) for h in ts.dbMatch('basenames', x)],
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
