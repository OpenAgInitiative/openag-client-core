from nose.tools import assert_equal
from openag_brain.software_modules.bool_direct_controller import BoolDirect

def test_bool_direct():
    bool_direct = BoolDirect()
    assert_equal(True, bool_direct.update(True))
    assert_equal(False, bool_direct.update(False))
