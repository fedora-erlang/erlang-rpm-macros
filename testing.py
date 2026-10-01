import glob
import importlib.util
import os
import rpm
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "erlang-find-requires.py")

spec = importlib.util.spec_from_file_location("erlang_find_requires", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

LIBDIRS = [M.erlang_libdir(), M.ERLSHRDIR]
TEST_BEAM = os.path.join(HERE, "test.beam")

def erts_provides(capability):
    ts = rpm.TransactionSet()
    h = next(ts.dbMatch("name", "erlang-erts"))
    for dep in rpm.ds(h, "providename"):
        if dep.N() == capability:
            return "%s = %s" % (capability, dep.EVR())
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
        self.assertEqual(M.provider("%s/*/ebin" % M.erlang_libdir(), ('erlang', 'load_nif', 2)), filepath)
        self.assertIsNone(M.provider("%s/*/ebin" % M.erlang_libdir(), ('erlang', 'no_such_function', 0)))
        self.assertIsNone(M.provider("%s/*/ebin" % M.erlang_libdir(), ('no_such_module', 'f', 0)))

    def test_so_requires_nif(self):
        # This test requires erlang-crypto RPM package installed
        filepath = glob.glob("/usr/lib*/erlang/lib/crypto-*/priv/lib/crypto.so")[0]
        self.assertEqual(M.so_requires(filepath), [erts_provides("erlang(erl_nif_version)")])

    def test_so_requires_drv(self):
        # This test requires erlang-erlsyslog RPM package installed
        filepath = glob.glob("/usr/lib*/erlang/lib/erlsyslog-*/priv/erlsyslog_drv.so")[0]
        self.assertEqual(M.so_requires(filepath), [erts_provides("erlang(erl_drv_version)")])

    def test_beam_requires_arch(self):
        Deps = ['erlang-erts(x86-64)', 'erlang-kernel(x86-64)', 'erlang-stdlib(x86-64)']
        self.assertEqual(M.beam_requires('x86-64', LIBDIRS, TEST_BEAM), Deps)

    def test_beam_requires_noarch(self):
        Deps = ['erlang-erts', 'erlang-kernel', 'erlang-stdlib']
        self.assertEqual(M.beam_requires('noarch', LIBDIRS, TEST_BEAM), Deps)

    def test_multifile(self):
        # The way RPM 4.20+ runs the generator: all files at once, and a
        # ";<filename>" line before the requires of each file
        crypto = glob.glob("/usr/lib*/erlang/lib/crypto-*/priv/lib/crypto.so")[0]
        files = [TEST_BEAM, crypto, os.path.join(HERE, "README")]
        out = subprocess.run([sys.executable, SCRIPT, "-i", "(x86-64)"], input="".join(f + "\n" for f in files),
            capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.splitlines(), [
            ";" + TEST_BEAM, 'erlang-erts(x86-64)', 'erlang-kernel(x86-64)', 'erlang-stdlib(x86-64)',
            ";" + crypto, erts_provides("erlang(erl_nif_version)")])

    def test_multifile_noarch(self):
        # %{?_isa} is empty for noarch packages
        out = subprocess.run([sys.executable, SCRIPT, "-i"], input=TEST_BEAM + "\n",
            capture_output=True, text=True, check=True).stdout
        self.assertEqual(out.splitlines(), [";" + TEST_BEAM, 'erlang-erts', 'erlang-kernel', 'erlang-stdlib'])

    def test_check_for_absense_of_buildarch_macro(self):
        self.assertEqual(rpm.expandMacro("%{buildarch}"), "%{buildarch}")

    def test_check_for_target_cpu_macro(self):
        self.assertNotEqual(rpm.expandMacro("%{_target_cpu}"), "%{_target_cpu}")

if __name__ == "__main__":
    unittest.main()
