from nose.tools import assert_equal
from openag_brain.software_modules.direct_controller import Direct

def test_direct_controller():
    direct = Direct()
    assert_equal(1, direct.update(1))
    assert_equal(-1, direct.update(-1))
