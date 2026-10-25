# Notes for contributors and coding agents

## Workflow

* Branch off `master`, push the branch to your fork and open a pull request
  against `fedora-erlang/erlang-rpm-macros`. Merge it only when every check is
  green.
* One change per commit: a bugfix, a feature, an optimization, a refactoring
  or a cosmetic change, never a mix of them. Documentation goes with the change
  it documents.
* Order of work: bugfixes first, then features, then optimizations, then
  refactoring and compatible improvements, cosmetic changes last.
* Keep the existing macros, switches and parameters working (`-C`, `-e` and
  `-c` of `%erlang3_test`, `%realname`/`%srcname`/`%erlappname`, the deprecated
  rebar2 macros). New behaviour which could break existing packages is opt-in.
* Sign off every commit (`git commit -s`).
* Tags, releases and the Fedora package are done by the maintainer.

## Baseline

Erlang/OTP 26 and RPM 4.20 (multifile dependency generators, declarative
`BuildSystem`). Don't add compatibility code for anything older, and check
macro changes on both RPM 4.20 and the current release.

## Testing

`make check` runs the unit tests of the generators. Macros are checked by
expanding them with `rpm --load macros.erlang --eval ...`, and the generators
end to end with `rpmbuild` of a small package. A generator script which isn't
executable is skipped by RPM without a warning.

## Licensing

The project follows [REUSE](https://reuse.software/) 3.3, checked by CI. Code
and documentation are MIT, boilerplate (CI configuration, `Makefile`,
`REUSE.toml`, test data) is CC0-1.0. New files start with

```
# SPDX-FileCopyrightText: © YEAR Peter Lemenkov
# SPDX-FileCopyrightText: erlang-rpm-macros contributors
# SPDX-License-Identifier: MIT
```

(the contributors line only when others contributed), with no blank comment
line in between. Markdown files are annotated in `REUSE.toml` instead.
