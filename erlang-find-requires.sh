#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant requires
# information that needs to be included in the package.

filelist=`sed "s/['\"]/\\\&/g"`


# Get the list of *.app files
appfiles=$(echo $filelist | tr [:blank:] '\n' | grep '/ebin/' | grep '\.app$')

for f in $appfiles; do
	apps=`cat $f | tr -d '\n' |tr -d [:blank:]|awk -F '{applications,' '{print $2}'|awk -F '}' '{print $1}'|sed -e "s,.,,;s,.$,,;s.,. .g;"`
	for a in $apps; do
		echo "erlang($a)"
	done
done

# TODO
# Get include_lib directives
#erlfiles=$(echo $filelist | tr [:blank:] '\n' | grep '\.[eh]rl$')
#for f in $erlfiles ; do
#	apps=`cat $f | tr -d [:blank:] | grep '^\-include_lib' | cut -d \" -f 2|cut -d \/ -f 1`
#	for a in $apps; do
#		echo "erlang($a)"
#	done
#done


