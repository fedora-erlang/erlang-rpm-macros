#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant provides
# information that needs to be included in the package.

filelist=`sed "s/['\"]/\\\&/g"`

/usr/lib/rpm/rpmdeps --provides $filelist

# Get the list of *.app files
appfiles=$(echo $filelist | tr [:blank:] '\n' | grep '/ebin/' | grep '\.app$')

for f in $appfiles; do
	app=`cat $f | tr -d '\n' | tr -d [:blank:] | awk -F '{application,' '{print $2}'|cut -d , -f 1`
	ver=`cat $f | tr -d '\n' | tr -d [:blank:] | awk -F '{vsn,"' '{print $2}'|cut -d \" -f 1`
	echo "erlang($app) = $ver"
done

# Create list of directories and try guessing by directory name
basedirs=$(echo $filelist | tr [:blank:] '\n' | awk -F '/erlang/lib/' '{print $2}'|cut -d '/' -f 1 | uniq )
for bd in $basedirs; do
	basename=`echo $bd | cut -d '-' -f 1`
	basever=`echo $bd | cut -d '-' -f 2`
	if [ -n "$basever" ]
	then
		echo "erlang($basename) = $basever"
	fi
done
