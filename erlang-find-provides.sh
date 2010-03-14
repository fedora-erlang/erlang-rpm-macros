#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant provides
# information that needs to be included in the package.

filelist=`sed "s/['\"]/\\\&/g"`

basedirs=$(echo $filelist | tr [:blank:] '\n' | awk -F '/erlang/lib/' '{print $2}'|cut -d '/' -f 1 | uniq )

for bd in $basedirs; do
    basename=`echo $bd | cut -d '-' -f 1`
    basever=`echo $bd | cut -d '-' -f 2`
    echo "erlang($basename) = $basever"
done
