from nose.tools import assert_equal
from openag_brain.software_modules.on_off_open_controller import OnOffOpen

def test_on_off():
    on_off_open = OnOffOpen()
    assert_equal(False, on_off_open.update(-1))
    assert_equal(False, on_off_open.update(0))
    assert_equal(True, on_off_open.update(0.1))

def test_threshold():
    on_off_open = OnOffOpen(threshold = 10)
    assert_equal(False, on_off_open.update(1))
    assert_equal(False, on_off_open.update(10))
    assert_equal(True, on_off_open.update(10.1))
    assert_equal(True, on_off_open.update(100))
    assert_equal(False, on_off_open.update(10))

def test_activate_below_threshold():
    on_off_open = OnOffOpen(activate_below_threshold = True)
    assert_equal(False, on_off_open.update(0))
    assert_equal(True, on_off_open.update(-0.1))
    assert_equal(True, on_off_open.update(-100))
    assert_equal(False, on_off_open.update(0.1))
    assert_equal(False, on_off_open.update(100))

def test_threshold_and_activate_below_threshold():
    on_off_open = OnOffOpen(threshold = 10, activate_below_threshold = True)
    assert_equal(True, on_off_open.update(0))
    assert_equal(True, on_off_open.update(9.9))
    assert_equal(False, on_off_open.update(10))
    assert_equal(False, on_off_open.update(100))
