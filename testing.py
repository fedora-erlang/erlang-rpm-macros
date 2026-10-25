# SPDX-FileCopyrightText: © 2017-2026 Peter Lemenkov
# SPDX-License-Identifier: MIT

import glob
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

import rpm

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "erlang-find-requires.py")

spec = importlib.util.spec_from_file_location("erlang_find_requires", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

BUILDREQUIRES = os.path.join(HERE, "erlang-buildrequires.escript")
PROVIDES = os.path.join(HERE, "erlang-find-provides.py")
spec = importlib.util.spec_from_file_location("erlang_find_provides", PROVIDES)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

LIBDIRS = [M.erlang_libdir(), M.ERLSHRDIR]
TEST_BEAM = os.path.join(HERE, "test.beam")
# Built by the Makefile
TEST_NIF = os.path.join(HERE, "test_nif.so")
TEST_DRV = os.path.join(HERE, "test_drv.so")
TEST_NODYNSYM = os.path.join(HERE, "test_nodynsym.so")

def erts_provides(capability):
    ts = rpm.TransactionSet()
    h = next(ts.dbMatch("name", "erlang-erts"))
    for dep in rpm.ds(h, "providename"):
        if dep.N() == capability:
            return f"{capability} = {dep.EVR()}"
    return None

class TestAllMethods(unittest.TestCase):
    def test_imports(self):
        imports = M.imports(TEST_BEAM)
        self.assertIn(("io", "format", 1), imports)
        self.assertIn(("lists", "reverse", 1), imports)
        self.assertIn(("application", "ensure_started", 1), imports)

    def test_exports(self):
        self.assertEqual(M.exports(TEST_BEAM), frozenset([("main", 0), ("module_info", 0), ("module_info", 1)]))

    def test_provider(self):
        # This test requires erlang-erts RPM package installed
        filepath = glob.glob('/usr/lib*/erlang/lib/erts-*/ebin/erlang.beam')[0]
        self.assertEqual(M.provider(f"{M.erlang_libdir()}/*/ebin", ('erlang', 'load_nif', 2)), filepath)
        self.assertIsNone(M.provider(f"{M.erlang_libdir()}/*/ebin", ('erlang', 'no_such_function', 0)))
        self.assertIsNone(M.provider(f"{M.erlang_libdir()}/*/ebin", ('no_such_module', 'f', 0)))

    def test_so_requires_nif(self):
        self.assertEqual(M.so_requires(TEST_NIF), [erts_provides("erlang(erl_nif_version)")])

    def test_so_requires_drv(self):
        self.assertEqual(M.so_requires(TEST_DRV), [erts_provides("erlang(erl_drv_version)")])

    def test_so_requires_nodynsym(self):
        self.assertEqual(M.so_requires(TEST_NODYNSYM), [])

    def test_beam_requires_arch(self):
        Deps = ['erlang-erts(x86-64)', 'erlang-kernel(x86-64)', 'erlang-stdlib(x86-64)']
        self.assertEqual(M.beam_requires('x86-64', LIBDIRS, TEST_BEAM), Deps)

    def test_beam_requires_noarch(self):
        Deps = ['erlang-erts', 'erlang-kernel', 'erlang-stdlib']
        self.assertEqual(M.beam_requires('noarch', LIBDIRS, TEST_BEAM), Deps)

    def test_multifile(self):
        # The way RPM 4.20+ runs the generator: all files at once, and a
        # ";<filename>" line before the requires of each file
        files = [TEST_BEAM, TEST_NIF, TEST_NODYNSYM, os.path.join(HERE, "README")]
        out = subprocess.run([sys.executable, SCRIPT, "-i", "(x86-64)"], input="".join(f + "\n" for f in files),
            capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.splitlines(), [
            ";" + TEST_BEAM, 'erlang-erts(x86-64)', 'erlang-kernel(x86-64)', 'erlang-stdlib(x86-64)',
            ";" + TEST_NIF, erts_provides("erlang(erl_nif_version)")])

    def test_multifile_noarch(self):
        # %{?_isa} is empty for noarch packages
        out = subprocess.run([sys.executable, SCRIPT, "-i"], input=TEST_BEAM + "\n",
            capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.splitlines(), [";" + TEST_BEAM, 'erlang-erts', 'erlang-kernel', 'erlang-stdlib'])

    def test_rpm_version(self):
        self.assertEqual(P.rpm_version("1.2.3"), "1.2.3")
        self.assertEqual(P.rpm_version("1.0.0-rc.1"), "1.0.0~rc.1")
        self.assertEqual(P.rpm_version("2.0+build.5"), "2.0+build.5")
        self.assertEqual(P.rpm_version("3.0 beta"), "3.0_beta")

    def test_app_provides(self):
        with tempfile.TemporaryDirectory() as d:
            ebin = os.path.join(d, "usr/share/erlang/lib/foo-1.2.3/ebin")
            os.makedirs(ebin)
            app = os.path.join(ebin, "foo.app")
            with open(app, "w") as f:
                f.write('{application,foo,\n    [{description,"Foo"},\n     {vsn,"1.2.3-rc1"},\n     {modules,[foo]}]}.\n')
            self.assertEqual(P.app_provides(app), ["erlang(foo) = 1.2.3~rc1"])
            novsn = os.path.join(ebin, "bar.app")
            with open(novsn, "w") as f:
                f.write("{application, bar, [{modules, []}]}.\n")
            self.assertEqual(P.app_provides(novsn), ["erlang(bar)"])
            # Only APP/ebin/NAME.app files are application resource files
            self.assertEqual(P.app_provides(os.path.join(d, "foo.app")), [])
            self.assertEqual(P.app_provides(os.path.join(ebin, "foo.beam")), [])

    def test_provides_multifile(self):
        # Every installed application provides erlang(NAME) = VSN
        app = sorted(glob.glob('/usr/lib*/erlang/lib/stdlib-*/ebin/stdlib.app'))[0]
        vsn = os.path.basename(os.path.dirname(os.path.dirname(app)))[len("stdlib-"):]
        out = subprocess.run([sys.executable, PROVIDES], input="".join(f + "\n" for f in [TEST_BEAM, app]),
            capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.splitlines(), [";" + app, f"erlang(stdlib) = {vsn}"])

    def buildrequires(self, files, *args):
        """Run the BuildRequires generator in a project made of the given files."""
        with tempfile.TemporaryDirectory() as d:
            for (name, text) in files.items():
                os.makedirs(os.path.dirname(os.path.join(d, name)), exist_ok=True)
                with open(os.path.join(d, name), "w") as f:
                    f.write(text)
            return subprocess.run(["escript", BUILDREQUIRES, *args], cwd=d, capture_output=True, text=True)

    def test_buildrequires(self):
        config = """
            {deps, [jsx, {cowboy, "2.10.0"}, {lager, {git, "https://example.com/lager", {tag, "3.9.2"}}},
                    {meck, ".*", {git, "https://example.com/meck"}, [raw]}]}.
            {plugins, [pc]}.
            {project_plugins, [rebar3_hex]}.
            {profiles, [{test, [{deps, [proper]}]}]}.
        """
        out = self.buildrequires({"rebar.config": config})
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.splitlines(), [f"(erlang({n}) or erlang-{n})" for n in ["cowboy", "jsx", "lager", "pc"]])
        out = self.buildrequires({"rebar.config": config}, "-t", "-x", "cowboy", "-x", "jsx,pc")
        self.assertEqual(out.stdout.splitlines(), [f"(erlang({n}) or erlang-{n})" for n in ["lager", "proper"]])

    def test_buildrequires_script_and_umbrella(self):
        files = {
            "rebar.config": "{deps, [jsx]}.\n",
            "rebar.config.script": "lists:keystore(deps, 1, CONFIG, {deps, [recon | proplists:get_value(deps, CONFIG)]}).\n",
            "apps/core/rebar.config": "{deps, [getopt, web]}.\n",
            "apps/web/rebar.config": "{deps, [core, cowboy]}.\n",
        }
        out = self.buildrequires(files)
        self.assertEqual(out.returncode, 0, out.stderr)
        # The applications of an umbrella project aren't dependencies
        self.assertEqual(out.stdout.splitlines(), [f"(erlang({n}) or erlang-{n})" for n in ["cowboy", "getopt", "jsx", "recon"]])

    def test_buildrequires_errors(self):
        self.assertEqual(self.buildrequires({}).stdout, "")
        out = self.buildrequires({"rebar.config": "{deps, [jsx]\n"})
        self.assertEqual(out.returncode, 1)
        self.assertIn("rebar.config", out.stderr)
        self.assertEqual(self.buildrequires({}, "-q").returncode, 1)

    def test_check_for_absense_of_buildarch_macro(self):
        self.assertEqual(rpm.expandMacro("%{buildarch}"), "%{buildarch}")

    def test_check_for_target_cpu_macro(self):
        self.assertNotEqual(rpm.expandMacro("%{_target_cpu}"), "%{_target_cpu}")

if __name__ == "__main__":
    unittest.main()
