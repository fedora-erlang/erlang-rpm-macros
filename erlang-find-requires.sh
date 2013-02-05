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

# This script reads filenames from STDIN and outputs any relevant requires
# information that needs to be included in the package.

filelist=`sed "s/['\"]/\\\&/g"`

/usr/lib/rpm/rpmdeps --requires $filelist

# Check for possible Port- and NIF-libraries
sofiles==$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/priv/.*\.so$')
if [ "$sofiles" != "" ]
then
	ERL_DRV_MAJOR=`grep "^#define ERL_DRV_EXTENDED_MAJOR_VERSION" /usr/lib*/erlang/usr/include/erl_driver.h | cut -f 2`
	ERL_DRV_MINOR=`grep "^#define ERL_DRV_EXTENDED_MINOR_VERSION" /usr/lib*/erlang/usr/include/erl_driver.h | cut -f 2`
	echo "erlang(erl_drv_version) = $ERL_DRV_MAJOR.$ERL_DRV_MINOR"

	ERL_NIF_MAJOR=`grep "^#define ERL_NIF_MAJOR_VERSION" /usr/lib*/erlang/usr/include/erl_nif.h | cut -d " " -f 3`
	ERL_NIF_MINOR=`grep "^#define ERL_NIF_MINOR_VERSION" /usr/lib*/erlang/usr/include/erl_nif.h | cut -d " " -f 3`
	echo "erlang(erl_nif_version) = $ERL_NIF_MAJOR.$ERL_NIF_MINOR"
fi

# Get the list of built *.beam files
beamfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.beam$')
/usr/lib/rpm/erlang-find-requires.escript $beamfiles | sort | uniq

