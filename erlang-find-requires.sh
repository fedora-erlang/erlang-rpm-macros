#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant requires
# information that needs to be included in the package.

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

# Get the list of *.beam files
beamfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.beam$')
/usr/lib/rpm/erlang-find-requires.escript $beamfiles | sort | uniq

