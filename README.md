# erlang-rpm-macros

RPM macros and an automatic dependency generator for packaging Erlang/OTP
applications in Fedora.

* **Build macros** compile, test and install Erlang applications with
  rebar3, either as classic macros or as a declarative build system
  (`BuildSystem: rebar3`).
* **Automatic dependencies** are generated for every BEAM module and
  NIF/driver library in a package, so Erlang packages rarely need
  hand-written `Requires:`.

## Requirements

* **RPM 4.20** or newer, for the multifile dependency generator protocol and
  declarative build systems.
* **Erlang/OTP 26** or newer.
* For the dependency generator: **Python 3** with `python3-rpm`,
  `python3-pybeam` (0.8.1 or newer to read modules built by OTP 28) and
  `python3-pyelftools`.
* For the build macros: **rebar3** (`erlang-rebar3`).

## Usage

The application name is taken from whichever of `%realname`, `%srcname` or
`%erlappname` the spec defines (define only one of them). If none of them is
defined, it is the package name without its `erlang-` prefix, so
`Name: erlang-foo` builds and installs the application `foo`.

### Declarative build system

```spec
%global srcname foo

Name:           erlang-%{srcname}
Version:        1.0
Release:        %autorelease
Summary:        Foo application for Erlang
License:        MIT
Source:         %{srcname}-%{version}.tar.gz

BuildSystem:    rebar3
BuildRequires:  erlang-rebar3

%description
Foo application for Erlang.

%files
%license LICENSE
%{erlang_appdir}/

%changelog
%autochangelog
```

To skip the EUnit tests or the Common Test suites, pass `-e` or `-c` to the
`%check` section:

```spec
BuildOption(check): -c
```

### Generated BuildRequires

`%erlang_buildrequires` reads `rebar.config` (and `rebar.config.script`, as
rebar3 does) of the application and of any applications under `apps/`, and
prints a BuildRequires for every dependency and build plugin in the form
`(erlang(NAME) or erlang-NAME)`. It is opt-in: add a `%generate_buildrequires`
section, in a declarative spec as well:

```spec
%generate_buildrequires
%erlang_buildrequires -t -x eqwalizer_support
```

`-t` adds the dependencies of the `test` profile, and `-x NAME,...` skips
dependencies which aren't packaged (it may be repeated). Development plugins
(`project_plugins`) and `raw` dependencies are skipped.

### Classic macros

```spec
%build
%{erlang3_compile}

%install
%{erlang3_install}

%check
%{erlang3_test}
```

| Macro | What it does |
|---|---|
| `%erlang3_compile` | Creates a minimal `src/APP.app.src` if the application has no `.app` file or template, then runs `%rebar3_compile` and `%rebar3_doc` |
| `%erlang3_test` | Runs `%rebar3_eunit` and `%rebar3_ct`; `-e` skips the former, `-c` the latter |
| `%erlang_buildrequires` | Prints the BuildRequires of `rebar.config` for `%generate_buildrequires`, see above |
| `%erlang3_install` | Installs the `.app` file and BEAM modules built by rebar3, `include/*.hrl`, and `priv/*.so` and `priv/lib/*.so` into `%{erlang_appdir}` |
| `%erlang_install` | The same, for applications built into `./ebin` without rebar3 |
| `%rebar3_compile`, `%rebar3_eunit`, `%rebar3_ct`, `%rebar3_doc` | Run the corresponding rebar3 command with the distribution build flags |
| `%erlang_appdir` | The application directory, `%{_erllibdir}/APP-%{version}` |
| `%_erllibdir` | `%{_libdir}/erlang/lib`, or `%{_datadir}/erlang/lib` for noarch packages |

The rebar2 macros (`%rebar_compile`, `%rebar_ct`, `%rebar_doc`,
`%rebar_eunit`, `%erlang_compile`, `%erlang_test`) are deprecated: rebar2 is
no longer available, so they print a warning and use rebar3 instead.

## Automatic dependencies

`erlang.attr` hooks `erlang-find-provides` and `erlang-find-requires` into
rpmbuild.

Every installed **application** (`APP/ebin/NAME.app`) provides
`erlang(NAME) = VSN`, `VSN` being the `vsn` of the application, e.g.
`erlang(jsx) = 3.1.0`. A `-` in the version becomes `~`, so pre-releases sort
before the release as they do in semantic versioning.

The requires are:

* For a **BEAM module**, every imported function is looked up in the
  installed Erlang libraries (`%{_libdir}/erlang/lib` and
  `/usr/share/erlang/lib`), and the package owning the module that exports it
  becomes a requirement, e.g. `erlang-stdlib(x86-64)` (or plain
  `erlang-stdlib` for noarch packages). Functions provided by the package
  itself are skipped. Functions which can't be found anywhere are reported as
  a warning, without failing the build.
* For a **NIF or driver library** (`priv/**/*.so` exporting `nif_init` or
  `driver_init`), the NIF or driver API version of the installed Erlang runtime
  becomes a requirement, e.g. `erlang(erl_nif_version) = 2.17`.

The requires generator only sees what is installed in the build environment, so
everything an application calls has to be in its `BuildRequires:`.

## Testing

```sh
make check
```

This needs `erlang-erts`, `gcc`, `make`, `python3-pybeam`,
`python3-pyelftools` and `python3-rpm`.

## License

The macros, the dependency generator, its tests and this README are available
under the [MIT](LICENSES/MIT.txt) license. The rest (CI configuration, build
files and test fixtures) is under [CC0-1.0](LICENSES/CC0-1.0.txt). The
project follows the [REUSE](https://reuse.software/) specification: see the
SPDX headers of the files and `REUSE.toml`.
