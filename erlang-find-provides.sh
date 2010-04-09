#!/bin/bash

# This script reads filenames from STDIN and outputs any relevant provides
# information that needs to be included in the package.

BUILDDIR=
ERLMODULENAME=

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
	ver=`cat $f | tr -d [:space:] | grep -o -E '\{vsn,\".*[0-9]\"\}' | sed -e "s,.vsn\,\",,g;s,\".,,g"`
	echo "erlang($app) = $ver"
done

# Create list of directories and try guessing by directory name
basedirs=$(echo $filelist | tr [:blank:] '\n' | grep -o -E 'erlang\/lib\/[a-zA-Z_0-9]*-[0-9.]*\/ebin' | cut -d \/ -f 3 | sort | uniq)
for bd in $basedirs; do
	basename=`echo $bd | cut -d \- -f 1`
	basever=`echo $bd | cut -d \- -f 2`
	if [ -n "$basever" ] ;
	then
		# Notify us if it is an erts
		if [ "$basename" == "erts" ] ;
		then
			ERLMODULENAME="erlang-erts"
		fi
		echo "erlang($basename) = $basever"
	fi
done

# Get the list of *.beam files
beamfiles=$(echo $filelist | tr [:blank:] '\n' | grep -o -E '.*/ebin/.*\.beam$')
/usr/lib/rpm/erlang-find-provides.escript $beamfiles | sed s,\',,g

# BIFs from erts - this module is very specific
if [ "$ERLMODULENAME" == "erlang-erts" ] ;
then
	cat $BUILDDIR/erts/emulator/*/erl_bif_list.h 2>/dev/null |\
		grep -v am__AtomAlias |\
		grep -o -E 'am_.*\,am_.*\,.\,' |\
		sed s,am_,,g |\
		sed -e "s,Plus,+,g;s,Minus,-,g;s,Neqeq,=\/=,g;s,Neq,\/=,g;s,Div,\/,g;s,Eqeq,=\:=,g;s,Eq,==,g;s,Ge,>=,g;s,Gt,>,g;s,Le,=<,g;s,Lt,<,g;s,Times,*,g;s,subtract,--,g;s,append\,,++\,,g" |\
		awk -F \, '{print "erlang(" $1 ":" $2 "/" $3 ")" }'
fi

