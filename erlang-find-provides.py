#!/usr/bin/python3

# SPDX-FileCopyrightText: © 2026 Peter Lemenkov
# SPDX-FileCopyrightText: erlang-rpm-macros contributors
# SPDX-License-Identifier: MIT

# RPM provides generator for Erlang, using the multifile protocol (RPM 4.20+).
# It reads the names of all matching files from STDIN and prints, for every
# application resource file APP/ebin/NAME.app, a ";<filename>" line followed
# by "erlang(NAME) = VSN", VSN being the application version.

import re
import sys

VSN = re.compile(r'\{\s*vsn\s*,\s*"([^"]*)"\s*\}')

def rpm_version(vsn):
	"""An application version as an RPM version.

	'-' starts a pre-release in semantic versioning and '~' sorts the same
	way in RPM; other characters RPM doesn't allow become '_'."""
	return re.sub(r"[^A-Za-z0-9._+~^]", "_", vsn.replace("-", "~"))

def app_provides(filename):
	parts = filename.split("/")
	if len(parts) < 3 or parts[-2] != "ebin" or not parts[-1].endswith(".app"):
		return []
	name = parts[-1][:-len(".app")]
	try:
		with open(filename, encoding="utf-8", errors="replace") as f:
			m = VSN.search(f.read())
	except OSError:
		return []
	vsn = rpm_version(m.group(1)) if m else ""
	return [f"erlang({name}) = {vsn}" if vsn else f"erlang({name})"]

def main():
	for line in sys.stdin:
		filename = line.rstrip("\n")
		provides = app_provides(filename)
		if provides:
			print(";" + filename)
			for dep in provides:
				print(dep)

if __name__ == "__main__":
	main()
