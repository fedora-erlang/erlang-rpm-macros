#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant provides
# information that needs to be included in the package.

filelist=`sed "s/['\"]/\\\&/g"`

/usr/lib/rpm/rpmdeps --provides $filelist

# Get the list of *.app files
appfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.app$')

for f in $appfiles; do
	app=`cat $f | tr -d [:space:] | awk -F '{application,' '{print $2}'|cut -d , -f 1`
	ver=`cat $f | tr -d [:space:] | grep -o -E '\{vsn,\".*[0-9]\"\}' | sed -e "s,.vsn\,\",,g;s,\".,,g"`
	echo "erlang($app) = $ver"
done

# Create list of directories and try guessing by directory name
basedirs=$(echo $filelist | tr [:blank:] '\n' | grep -o -E 'erlang\/lib\/[a-zA-Z_0-9]*-[0-9.]*\/ebin' | cut -d \/ -f 3 | sort | uniq)
for bd in $basedirs; do
	basename=`echo $bd | cut -d \- -f 1`
	basever=`echo $bd | cut -d \- -f 2`
	if [ -n "$basever" ]
	then
		echo "erlang($basename) = $basever"
	fi
done

# Get the list of *.beam files
beamfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.beam$')

for beam in $appfiles; do
	escript /usr/lib/rpm/erlang-find-provides.escript $beam
done

