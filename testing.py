import glob
import rpm
import unittest

M = None
ErlDrvDep = ""
ErlNifDep = ""

class TestAllMethods(unittest.TestCase):
    def test_sort_and_uniq(self):
        self.assertEqual(M.sort_and_uniq([1,2,2,2,2,4,3,2,1]), [1,2,3,4])

    def test_check_for_mfa(self):
        # This test requires erlang-erts RPM package installed
        ERLLIBDIR = glob.glob("/usr/lib*/erlang/lib")[0]
        filepath = glob.glob('/usr/lib*/erlang/lib/erts-*/ebin/erlang.beam')[0]
        self.assertEqual(M.check_for_mfa("%s/*/ebin" % ERLLIBDIR, {}, ('erlang', 'load_nif', 2)), filepath)

    def test_inspect_so_library_nif(self):
        # This test requires erlang-crypto RPM package installed
        filepath = glob.glob("/usr/lib*/erlang/lib/crypto-*/priv/lib/crypto.so")[0]
        self.assertEqual(M.inspect_so_library(filepath, 'nif_init', 'erlang(erl_nif_version)'), ErlNifDep)

    def test_inspect_so_library_drv(self):
        # This test requires erlang-erlsyslog RPM package installed
        filepath = glob.glob("/usr/lib*/erlang/lib/erlsyslog-*/priv/erlsyslog_drv.so")[0]
        self.assertEqual(M.inspect_so_library(filepath, 'driver_init', 'erlang(erl_drv_version)'), ErlDrvDep)

    def test_inspect_beam_file_arch(self):
        Deps = ['erlang-erts(x86-64)', 'erlang-kernel(x86-64)', 'erlang-stdlib(x86-64)']
        self.assertEqual(M.inspect_beam_file('x86-64', "./test.beam"), Deps)

    def test_inspect_beam_file_noarch(self):
        Deps = ['erlang-erts', 'erlang-kernel', 'erlang-stdlib']
        self.assertEqual(M.inspect_beam_file('noarch', "./test.beam"), Deps)

    def test_check_for_absense_of_buildarch_macro(self):
        self.assertEqual(rpm.expandMacro("%{buildarch}"), "%{buildarch}")

    def test_check_for_target_cpu_macro(self):
        self.assertNotEqual(rpm.expandMacro("%{_target_cpu}"), "%{_target_cpu}")

if __name__ == "__main__":
    M = __import__("erlang-find-requires")

    ts = rpm.TransactionSet()
    mi = ts.dbMatch('name', "erlang-erts")
    h = next(mi)
    ds = dict(map(lambda x: x[0].split(" ")[1::2], h.dsFromHeader('providename')))
    ErlDrvDep = "erlang(erl_drv_version) = %s" % ds['erlang(erl_drv_version)']
    ErlNifDep = "erlang(erl_nif_version) = %s" % ds['erlang(erl_nif_version)']

    unittest.main()
