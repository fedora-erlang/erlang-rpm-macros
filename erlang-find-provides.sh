#!/bin/bash

# Copyright (c) 2009,2010 Peter Lemenkov <lemenkov@gmail.com>
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

BUILDDIR=

while true; do
	case "$1" in
		-b) BUILDDIR="$2"; shift 2;;
		--) shift; break;;
		*) echo "$0: option error at $1"; exit 1;;
	esac
done

filelist=`sed "s/['\"]/\\\&/g"`

/usr/lib/rpm/rpmdeps --provides $filelist

# Get the list of *.app files
appfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.app$')

for f in $appfiles; do
	app=`cat $f | tr -d [:space:] | awk -F '{application,' '{print $2}'|cut -d , -f 1`
	ver=`cat $f | tr -d [:space:] | grep -o -E '\{vsn,\".*[0-9]\"\}' | sed -e "s,.vsn\,\",,g;s,\".*,,g"`

	# HiPE module is different from others
	if [ "$app" == "hipe" ] ;
	then
		# Hardcoded minimal set of HiPE exported functions
		echo "erlang(hipe_amd64_main:rtl_to_amd64/3)"
		echo "erlang(hipe_arm_main:rtl_to_arm/3)"
		echo "erlang(hipe:c/1)"
		echo "erlang(hipe:compile/4)"
		echo "erlang(hipe_data_pp:pp/4)"
		echo "erlang(hipe_icode2rtl:translate/2)"
		echo "erlang(hipe_icode_heap_test:cfg/1)"
		echo "erlang(hipe_ppc_main:rtl_to_ppc/3)"
		echo "erlang(hipe_rtl_arch:endianess/0)"
		echo "erlang(hipe_rtl_arch:nr_of_return_regs/0)"
		echo "erlang(hipe_rtl_arch:word_size/0)"
		echo "erlang(hipe_rtl_cfg:init/1)"
		echo "erlang(hipe_rtl_cfg:linearize/1)"
		echo "erlang(hipe_rtl_cfg:pp/1)"
		echo "erlang(hipe_rtl_cfg:remove_trivial_bbs/1)"
		echo "erlang(hipe_rtl_cfg:remove_unreachable_code/1)"
		echo "erlang(hipe_rtl_cleanup_const:cleanup/1)"
		echo "erlang(hipe_rtl_lcm:rtl_lcm/2)"
		echo "erlang(hipe_rtl_ssa_avail_expr:cfg/1)"
		echo "erlang(hipe_rtl_ssa:check/1)"
		echo "erlang(hipe_rtl_ssa_const_prop:propagate/1)"
		echo "erlang(hipe_rtl_ssa:convert/1)"
		echo "erlang(hipe_rtl_ssapre:rtl_ssapre/2)"
		echo "erlang(hipe_rtl_ssa:remove_dead_code/1)"
		echo "erlang(hipe_rtl_ssa:unconvert/1)"
		echo "erlang(hipe_rtl_symbolic:expand/1)"
		echo "erlang(hipe_sparc_main:rtl_to_sparc/3)"
		echo "erlang(hipe_tagscheme:fixnum_val/1)"
		echo "erlang(hipe_tagscheme:is_fixnum/1)"
		echo "erlang(hipe_x86_main:rtl_to_x86/3)"
	fi

	echo "erlang($app) = $ver"
done

# Check for two special cases by inspecting path to ebin directory
basedirs=$(echo $filelist | tr [:blank:] '\n' | grep -o -E 'erlang\/lib\/[a-zA-Z_0-9]*-[0-9.]*\/ebin' | cut -d \/ -f 3 | sort | uniq)
for bd in $basedirs; do
	basename=`echo $bd | cut -d \- -f 1`
	basever=`echo $bd | cut -d \- -f 2`
	case $basename in
		"erts")
			echo "erlang($basename) = $basever"

			# BIFs from erts - this module is very specific
			cat $BUILDDIR/erts/emulator/*/erl_bif_list.h 2>/dev/null |\
				grep -v am__AtomAlias |\
				grep -o -E 'am_.*\,am_.*\,.\,' |\
				sed s,am_,,g |\
				sed -e "s,Plus,+,g;s,Minus,-,g;s,Neqeq,=\/=,g;s,Neq,\/=,g;s,Div,\/,g;s,Eqeq,=\:=,g;s,Eq,==,g;s,Ge,>=,g;s,Gt,>,g;s,Le,=<,g;s,Lt,<,g;s,Times,*,g;s,subtract,--,g;s,append\,,++\,,g" |\
				awk -F \, '{print "erlang(" $1 ":" $2 "/" $3 ")" }'

			# Add BIFs for HiPE
			grep "bif " $BUILDDIR/erts/emulator/hipe/*.tab | awk -F "bif " '{print "erlang(" $2 ")"}'

			ERL_DRV_MAJOR=`grep "^#define ERL_DRV_EXTENDED_MAJOR_VERSION" erts/emulator/beam/erl_driver.h | cut -f 2`
			ERL_DRV_MINOR=`grep "^#define ERL_DRV_EXTENDED_MINOR_VERSION" erts/emulator/beam/erl_driver.h | cut -f 2`
			echo "erlang(erl_drv_version) = $ERL_DRV_MAJOR.$ERL_DRV_MINOR"

			ERL_NIF_MAJOR=`grep "^#define ERL_NIF_MAJOR_VERSION" erts/emulator/beam/erl_nif.h | cut -d " " -f 3`
			ERL_NIF_MINOR=`grep "^#define ERL_NIF_MINOR_VERSION" erts/emulator/beam/erl_nif.h | cut -d " " -f 3`
			echo "erlang(erl_nif_version) = $ERL_NIF_MAJOR.$ERL_NIF_MINOR"
			;;
		"wx")
			# wx module doesn't contain app-file.
			echo "erlang($basename) = $basever"
			;;
		*)
			;;
	esac
done

# Get the list of *.beam files
beamfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.beam$')
/usr/lib/rpm/erlang-find-provides.escript $beamfiles | sed s,\',,g

