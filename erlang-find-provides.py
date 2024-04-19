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

# This script reads filenames from STDIN and outputs any relevant provides
# information that needs to be included in the package.

import getopt
import pybeam
import re
import sys

BUILDDIR=""

opts, args = getopt.getopt(sys.argv[1:],"b:",["builddir="])

for opt, arg in opts:
	if opt in ("-b", "--builddir"):
		BUILDDIR=arg

# All the files and directories from the package mentioned in erlang.attr as
# %__erlang_path
rawcontent = sys.stdin.readlines()

# See $BUILDDIR/erts/emulator/*/erl_bif_list.h
ErtsBIFProvides = [
	"erlang(erlang:*/2)",
	"erlang(erlang:++/2)",
	"erlang(erlang:+/1)",
	"erlang(erlang:+/2)",
	"erlang(erlang:--/2)",
	"erlang(erlang:-/1)",
	"erlang(erlang:-/2)",
	"erlang(erlang://2)",
	"erlang(erlang:/=/2)",
	"erlang(erlang:</2)",
	"erlang(erlang:=/=/2)",
	"erlang(erlang:=:=/2)",
	"erlang(erlang:=</2)",
	"erlang(erlang:==/2)",
	"erlang(erlang:>/2)",
	"erlang(erlang:>=/2)",
	"erlang(erlang:and/2)",
	"erlang(erlang:band/2)",
	"erlang(erlang:bnot/1)",
	"erlang(erlang:bor/2)",
	"erlang(erlang:bsl/2)",
	"erlang(erlang:bsr/2)",
	"erlang(erlang:bxor/2)",
	"erlang(erlang:div/2)",
	"erlang(erlang:not/1)",
	"erlang(erlang:or/2)",
	"erlang(erlang:rem/2)",
	"erlang(erlang:xor/2)"
]
HipeBIFprovides = [
	"erlang(hipe_bifs:add_ref/2)",
	"erlang(hipe_bifs:alloc_data/2)",
	"erlang(hipe_bifs:array/2)",
	"erlang(hipe_bifs:array_length/1)",
	"erlang(hipe_bifs:array_sub/2)",
	"erlang(hipe_bifs:array_update/3)",
	"erlang(hipe_bifs:atom_to_word/1)",
	"erlang(hipe_bifs:bif_address/3)",
	"erlang(hipe_bifs:bitarray/2)",
	"erlang(hipe_bifs:bitarray_sub/2)",
	"erlang(hipe_bifs:bitarray_update/3)",
	"erlang(hipe_bifs:bytearray/2)",
	"erlang(hipe_bifs:bytearray_sub/2)",
	"erlang(hipe_bifs:bytearray_update/3)",
	"erlang(hipe_bifs:call_count_clear/1)",
	"erlang(hipe_bifs:call_count_get/1)",
	"erlang(hipe_bifs:call_count_off/1)",
	"erlang(hipe_bifs:call_count_on/1)",
	"erlang(hipe_bifs:check_crc/1)",
	"erlang(hipe_bifs:code_size/1)",
	"erlang(hipe_bifs:constants_size/0)",
	"erlang(hipe_bifs:debug_native_called/2)",
	"erlang(hipe_bifs:enter_code/2)",
	"erlang(hipe_bifs:enter_sdesc/1)",
	"erlang(hipe_bifs:find_na_or_make_stub/2)",
	"erlang(hipe_bifs:fun_to_address/1)",
	"erlang(hipe_bifs:gc_info/0)",
	"erlang(hipe_bifs:gc_info_clear/0)",
	"erlang(hipe_bifs:gc_timer/0)",
	"erlang(hipe_bifs:gc_timer_clear/0)",
	"erlang(hipe_bifs:get_fe/2)",
	"erlang(hipe_bifs:get_hrvtime/0)",
	"erlang(hipe_bifs:get_rts_param/1)",
	"erlang(hipe_bifs:incremental_gc_info/0)",
	"erlang(hipe_bifs:invalidate_funinfo_native_addresses/1)",
	"erlang(hipe_bifs:in_native/0)",
	"erlang(hipe_bifs:llvm_fix_pinned_regs/0)",
	"erlang(hipe_bifs:mark_referred_from/1)",
	"erlang(hipe_bifs:merge_term/1)",
	"erlang(hipe_bifs:message_info/0)",
	"erlang(hipe_bifs:message_info_clear/0)",
	"erlang(hipe_bifs:message_sizes/0)",
	"erlang(hipe_bifs:misc_timer/0)",
	"erlang(hipe_bifs:misc_timer_clear/0)",
	"erlang(hipe_bifs:modeswitch_debug_off/0)",
	"erlang(hipe_bifs:modeswitch_debug_on/0)",
	"erlang(hipe_bifs:nstack_used_size/0)",
	"erlang(hipe_bifs:patch_call/3)",
	"erlang(hipe_bifs:patch_insn/3)",
	"erlang(hipe_bifs:pause_times/0)",
	"erlang(hipe_bifs:primop_address/1)",
	"erlang(hipe_bifs:process_info/0)",
	"erlang(hipe_bifs:process_info_clear/0)",
	"erlang(hipe_bifs:redirect_referred_from/1)",
	"erlang(hipe_bifs:ref/1)",
	"erlang(hipe_bifs:ref_get/1)",
	"erlang(hipe_bifs:ref_set/2)",
	"erlang(hipe_bifs:remove_refs_from/1)",
	"erlang(hipe_bifs:send_timer/0)",
	"erlang(hipe_bifs:send_timer_clear/0)",
	"erlang(hipe_bifs:set_funinfo_native_address/3)",
	"erlang(hipe_bifs:set_native_address/3)",
	"erlang(hipe_bifs:set_native_address_in_fe/2)",
	"erlang(hipe_bifs:shared_gc_info/0)",
	"erlang(hipe_bifs:shared_gc_timer/0)",
	"erlang(hipe_bifs:show_estack/1)",
	"erlang(hipe_bifs:show_heap/1)",
	"erlang(hipe_bifs:show_nstack/1)",
	"erlang(hipe_bifs:show_pcb/1)",
	"erlang(hipe_bifs:show_term/1)",
	"erlang(hipe_bifs:stop_hrvtime/0)",
	"erlang(hipe_bifs:system_crc/0)",
	"erlang(hipe_bifs:system_timer/0)",
	"erlang(hipe_bifs:system_timer_clear/0)",
	"erlang(hipe_bifs:term_to_word/1)",
	"erlang(hipe_bifs:trap_count_clear/0)",
	"erlang(hipe_bifs:trap_count_get/0)",
	"erlang(hipe_bifs:update_code_size/3)",
	"erlang(hipe_bifs:write_u32/2)",
	"erlang(hipe_bifs:write_u64/2)",
	"erlang(hipe_bifs:write_u8/2)"
]

Provides = []

rawcontent = list(map(lambda x: x.rstrip('\n'), rawcontent))

# Check for a specific cases
appmask = re.compile(".*/ebin/.*\.app")
# There should be only one app-file or none
for appfile in sorted([p for p in rawcontent if appmask.match(p)]):
	f = open(appfile, 'r')
	appcontents = f.read()
	f.close()
	# module erlang-erts (Erlang VM)
	if appcontents.split(",")[1].lstrip().rstrip() == "erts":
		# Export DRV version
		f = open("%s/erts/emulator/beam/erl_driver.h" % BUILDDIR, 'r')
		ERL_DRV_EXTENDED_MAJOR_VERSION = None
		ERL_DRV_EXTENDED_MINOR_VERSION = None
		for line in f:
			ms = re.search("(?<=^#define\sERL_DRV_EXTENDED_MAJOR_VERSION\s)[0-9]+(?=$)", line)
			if ms:
				ERL_DRV_EXTENDED_MAJOR_VERSION = ms.group(0)
		for line in f:
			ms = re.search("(?<=^#define\sERL_DRV_EXTENDED_MINOR_VERSION\s)[0-9]+(?=$)", line)
			if ms:
				ERL_DRV_EXTENDED_MINOR_VERSION = ms.group(0)
		# FIXME die here if ERL_DRV_EXTENDED_MAJOR_VERSION or ERL_DRV_EXTENDED_MINOR_VERSION is None
		Provides += "erlang(erl_drv_version) = %s.%s" % (ERL_DRV_EXTENDED_MAJOR_VERSION, ERL_DRV_EXTENDED_MINOR_VERSION)
		f.close()

		# Export NIF version
		f = open("%s/erts/emulator/beam/erl_nif.h" % BUILDDIR, 'r')
		ERL_NIF_MAJOR_VERSION = None
		ERL_NIF_MINOR_VERSION = None
		for line in f:
			ms = re.search("(?<=^#define\sERL_NIF_MAJOR_VERSION\s)[0-9]+(?=$)", line)
			if ms:
				ERL_NIF_MAJOR_VERSION = ms.group(0)
		for line in f:
			ms = re.search("(?<=^#define\sERL_NIF_MINOR_VERSION\s)[0-9]+(?=$)", line)
			if ms:
				ERL_NIF_MINOR_VERSION = ms.group(0)
		# FIXME die here if ERL_NIF_MAJOR_VERSION or ERL_NIF_MINOR_VERSION is None
		Provides += "erlang(erl_drv_version) = %s.%s" % (ERL_NIF_MAJOR_VERSION, ERL_NIF_MINOR_VERSION)
		f.close()

		# Add BIFs for erlang:F/A
		Provides += ErtsBIFProvides

	# module erlang-hipe
	if appcontents.split(",")[1].lstrip().rstrip() == "hipe":
		# Add BIFs for hipe_bifs:F/A
		Provides += HipeBIFprovides

# Iterate over all BEAM-files
beammask = re.compile(".*/ebin/.*\.beam")
for package in sorted([p for p in rawcontent if beammask.match(p)]):
        b = pybeam.BeamFile(package)
	# Two special cases:
	# * eunit_test - add "erlang(eunit_test:nonexisting_function/0)"
	# * wx - add "erlang(demo:start/0)"
	Provides += list(map(lambda x: 'erlang(%s:%s/%d)' % (b.modulename,x[0],x[1]), b.exports))

for prov in sorted(Provides):
	print(prov)
