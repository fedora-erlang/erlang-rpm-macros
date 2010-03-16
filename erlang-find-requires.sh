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

# Get the list of *.app files
appfiles=$(echo $filelist | tr [:blank:] '\n' | grep '/ebin/' | grep '\.app$')

for f in $appfiles; do
	apps=`cat $f | tr -d '\n' |tr -d [:blank:]|awk -F '{applications,' '{print $2}'|awk -F '}' '{print $1}'|sed -e "s,.,,;s,.$,,;s.,. .g;"`
	for a in $apps; do
		echo "erlang($a)"
	done
done

# Get include_lib directives
if [ -n "$BUILDDIR" ]
then
	erlfiles=$(echo $filelist | tr [:blank:] '\n' | grep '\.[eh]rl$')
	for f in `find $BUILDDIR -type f -name '*.[eh]rl'` ; do
		apps=`cat $f | tr -d [:blank:] | grep '^\-include_lib' | cut -d \" -f 2|cut -d \/ -f 1`
		for a in $apps; do
			echo "erlang($a)"
		done
	done | sort | uniq
fi
