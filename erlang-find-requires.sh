#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant requires
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

/usr/lib/rpm/rpmdeps --requires $filelist

# Get the list of *.app files
appfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.app$')

for f in $appfiles; do
	apps=`cat $f | tr -d [:space:] | grep -o -E '\{applications,\[.*[a-zA-Z0-9_]\]\}' | sed -e "s,.*\[,,g;s,\].*,,g;s.,. .g"`
	for a in $apps; do
		echo "erlang($a)"
	done
done

# Get include_lib directives
if [ -n "$BUILDDIR" ]
then
	erlfiles=$(echo $filelist | tr [:blank:] '\n' | grep '\.[eh]rl$')
	for f in `find $BUILDDIR -type f -name '*.[eh]rl'` ; do
		apps=`cat $f | tr -d [:blank:] | grep -o -E '^\-include_lib\(\".*\"\)' | sed -e "s,.*(\",,g;s,\/.*,,g"`
		for a in $apps; do
			echo "erlang($a)"
		done
	done | sort | uniq
fi

# Get the list of *.beam files
beamfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.beam$')

for beam in $beamfiles; do
	escript /usr/lib/rpm/erlang-find-requires.escript $beam
done

