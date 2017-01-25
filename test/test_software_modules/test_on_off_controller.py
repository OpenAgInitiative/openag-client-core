from nose.tools import assert_equal
from openag_brain.software_modules.on_off_controller import OnOff

def test_on_off():
    on_off = OnOff()
    on_off.set_point = 0
    # If Temperature is below the set point, turn the heater ON
    # If Water level is below the set point, turn the pump ON
    assert_equal(True, on_off.update(-1))
    # If Temperature is above the set point, turn the heater OFF
    # If Water level is above the set point, turn the pump OFF
    assert_equal(False, on_off.update(1))

def test_inverted_output():
    on_off = OnOff(inverted_output = True)
    on_off.set_point = 0
    # If Temperature is below the set point, turn the cooler OFF
    assert_equal(False, on_off.update(-1))
    # If Temperature is above the set point, turn the cooler ON
    assert_equal(True, on_off.update(1))

def test_hysteresis_width():
    on_off = OnOff(hysteresis_width = 2)
    on_off.set_point = 0
    assert_equal(on_off.update(-1.0), True)
    assert_equal(on_off.update(1.9), True)
    assert_equal(on_off.update(2.0), False)
    assert_equal(on_off.update(2.1), False)
    assert_equal(on_off.update(1.9), False)
    assert_equal(on_off.update(-1.9), False)
    assert_equal(on_off.update(-2.0), True)
    assert_equal(on_off.update(-2.1), True)
