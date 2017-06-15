#!/usr/bin/env python
__all__ = [
    "Environment", "EnvironmentalDataPoint", "FirmwareModule",
    "FirmwareModuleType", "Recipe", "SoftwareModule", "SoftwareModuleType"
]

from openag_lib.firmware.categories import SENSORS, ACTUATORS, CALIBRATION, all_categories
from voluptuous import Schema, Required, Any, Extra, Optional, REMOVE_EXTRA

Environment = Schema({
    "name": Any(str, unicode),
}, extra=REMOVE_EXTRA)
Environment.__doc__ = """
An :class:`Environment` abstractly represents a single homogenous
climate-controlled volume within a system. A food computer usually consists of
a single :class:`Environment`, but larger systems will often contain more than
one :class:`Environment`.

.. py:attribute:: name

    (str) A human-readable name for the environment
"""

EnvironmentalDataPoint = Schema({
    Required("environment"): Any(str, unicode),
    Required("variable"): Any(str, unicode),
    Required("is_manual", default=False): bool,
    Required("is_desired"): bool,
    "value": object,
    Required("timestamp"): Any(float, int),
}, extra=REMOVE_EXTRA)
EnvironmentalDataPoint.__doc__ = """
An `EnvironmentalDataPoint` represents a single measurement or event in an
`Environment`, such as a single air temperature measurement or the start of a
recipe.

.. py:attribute:: environment

    (str, required) The ID of the environment for which this point was measured

.. py:attribute:: variable

    (str, required) The type of measurement of event this represents (e.g.
    "air_temperature"). The class
    :class:`~openag.var_types.EnvVar` contains all valid variable names.

.. py:attribute:: is_manual

    (bool) This should be true if the data point represents a manual reading
    performed by a user and false if it represents an automatic reading from a
    firmware or software module. Defaults to false.

.. py:attribute:: is_desired

    (bool, required) This should be true if the data point represents the
    desired state of the environment (e.g. the set points of a recipe) and
    false if it represents the measured state of the environment.

.. py:attribute:: value

    The value associated with the measurement or event. The exact use of this
    field may very depending on the `variable` field.

.. py:attribute:: timestamp

    (float, required) A UNIX timestamp reflecting when this data point was
    generated.
"""

Recipe = Schema({
    "name": Any(str, unicode),
    "description": Any(str, unicode),
    Required("format"): Any(str, unicode),
    Required("operations"): object
}, extra=REMOVE_EXTRA)
Recipe.__doc__ = """
In order to allow for recipes to evolve, we have developed a very generic
recipe model. The idea behind the model is that the system runs a recipe
handler module which declares some list of recipe formats that it supports.
Recipes also declare what format they are. Thus, to define a new recipe format,
you can write a custom recipe handler module type that understands that format,
write recipes in the new format, and then use the rest of the existing system
as is. See :ref:`writing-recipes` for information on existing recipe formats
and how to write recipes with them.

.. py:attribute:: name

    (str) A human-readable name for the recipe

.. py:attribute:: description

    (str) A description of the recipe and what it should be used for

.. py:attribute:: format

    (str, required) The format of the recipe

.. py:attribute:: operations

    (required) The actual content of the recipe, organized as specified for the
    format of this recipe
"""


FirmwareInput = Schema({
    "type": Any(str, unicode),
    "variable": Any(str, unicode),
    "categories": [ACTUATORS, CALIBRATION],
    "description": Any(str, unicode),
    "multiplier": Any(float, int),
    "deadband": Any(float, int)
})
FirmwareInput.__doc__ = """
A :class:`models.FirmwareInput` gives information about a single input
to a firmware module (a ROS topic to which the module subscribes). These
objects are only ever stored in the `input` attribute of a
:class:`models.FirmwareModuleType` or
:class:`models.FirmwareModule`.

.. py:attribute:: type

    (str) The name of the ROS message type expected for messages on the topic

.. py:attribute:: variable

    (str) The name of the environmental variable affected by this input. For
    example, for a heater, this should be "air_temperature". Defaults to the
    key for this object in the parent dictionary.

.. py:attribute:: categories

    (list) A list of categories to which this inputs belongs. Must be a subset
    of ["actuators", "calibration"]

.. py:attribute:: description

    (str) A short description of what the input is for

.. py:attribute:: multipler

    (float) A factor by which to multiply data points on this input before they
    reach the module itself. This should generally be used to specify the
    extent to which the module affects the variable. For example, for an input
    which represents the command to send to a chiller module, the input should
    have the variable "air_temperature" and should have a negative multiplier
    so that a negative output from the air temperature control loop turns the
    chiller on. Fractional multipliers are allowed and can be useful to
    balance things from the perspective of the control loop when an up actuator
    (e.g. heater) is more powerful than its corresponding down actuator (e.g.
    chiller) or vice versa. Defaults to 1.

.. py:attribute:: deadband

    (float) Data points sent to this input with an absolute value less than the
    deadband will be sent as zeros instead. This is expecially useful for
    boolean inputs. For example, if a control loop outputs a float that is
    being fed into a binary actuator, a deadband can be put on the input to the
    actuator to effectively set a threshold on the commanded control effect
    above which the acuator will turn on.
"""

FirmwareOutput = Schema({
    "type": Any(str, unicode),
    "variable": Any(str, unicode),
    "categories": [SENSORS, CALIBRATION],
    "description": Any(str, unicode),
    "accuracy": Any(float, int),
    "repeatability": Any(float, int),
})
FirmwareOutput.__doc__ = """
A :class:`models.FirmwareOutput` gives information about a single
outputs from a firmware module (a ROS topic to which the module publishes).
These objects are only ever stored in the `output` attribute of a
:class:`models.FirmwareModuleType` or
:class:`models.FirmwareModule`.

.. py:attribute:: type

    (str) The name of the ROS message type expected for messages on the topic

.. py:attribute:: variable

    (str) The name of the environmental variable represented by this output.
    Defaults to the key for this object in the parent dictionary.

.. py:attribute:: categories

    (list) A list of categories to which this output belongs. Must be a subset
    of ["sensors", "calibration"]

.. py:attribute:: description

    (str) A short description of what the output is for

.. py:attribute:: accuracy

    (float) The maximum error for measurements on this output. Used to decide
    how to round the values before they are presented to the user.

.. py:attribute:: repeatability

    (float) A value below which the absolute difference between two repeated
    readings on this output should be expected to lie with a probability of 95%
    assuming that the underlying environmental condition is constant between
    readings.
"""

FirmwareArgument = Schema({
    "name": Any(str, unicode),
    Required("type"): Any("int", "float", "bool", "str"),
    "description": Any(str, unicode),
    "default": object,
})
FirmwareArgument.__doc__ = """
A :class:`models.FirmwareArgument` gives information about a single
argument to a firmware module (an argument to the constructor for the Arduino
class for the module). These objects are only ever stored in the `arguments`
attribute of a :class:`models.FirmwareModuleType` or
:class:`models.FirmwareModule`.

.. py:attribute:: name

    (str) The name of the argument

.. py:attribute:: type

    (str, required) Must be one of "int", "float", "bool", and "str"

.. py:attribute:: description

    (str) A short description of what the argument is for

.. py:attribute:: default

    The value that should be used for the argument if the user doesn't specify
    one.
"""

PioRepo = Schema({
    Required("type"): "pio",
    Required("id"): int
})
GitRepo = Schema({
    Required("type"): "git",
    Required("url"): Any(str, unicode),
    Optional("branch"): Any(str, unicode)
})

FirmwareModuleType = Schema({
    Required("_id"): Any(str, unicode),
    "repository": Any(PioRepo, GitRepo),
    "header_file": Any(str, unicode),
    "class_name": Any(str, unicode),
    "description": Any(str, unicode),
    "categories": [SENSORS, ACTUATORS, CALIBRATION],
    "arguments": [FirmwareArgument],
    "inputs": {Extra: FirmwareInput},
    "outputs": {Extra: FirmwareOutput},
    "dependencies": [Any(PioRepo, GitRepo)],
    "status_codes": {Extra: Any(str, unicode)}
}, extra=REMOVE_EXTRA)
FirmwareModuleType.__doc__ = """
A :class:`models.FirmwareModuleType` represents a firmware library for
interfacing with a particular system peripheral. It is essentially a driver for
a sensor or actuator. The code can be either stored in a git repository or
registered with `PlatformIO <http://platformio.org>`_ and metadata about it
should be stored in the OpenAg database. See :ref:`writing-firmware-modules`
for information on how to write firmware modules.

.. py:attribute:: repository

    (dict) A dictionary that describes where the code for this module type is
    hosted. The dictionary must always have the field "type" which indicates
    what service hosts the code. For a module hosted by platformio, this
    dictionary should have a "type" of "pio" and an "id" which is the integer
    ID of the platformIO library. For a module hosted in a git repository, the
    dictionary should have a "type" of "git" and a "url" which is the URL of
    the git repository.

.. py:attribute:: header_file

    (str, required) The name of the header file containing the top-level class
    in the library

.. py:attribute:: class_name

    (str, required) The name of the top-level class in the library

.. py:attribute:: description

    (str) Description of the library

.. py:attribute:: categories

    (list) A list of categories to which this firmware module type belongs.
    Must be a subset of ["sensors", "actuators", "calibration"].

.. py:attribute:: arguments

    (list) A list of :class:`models.FirmwareArgument` objects
    representing the arguments to be passed to the constructor of the top-level
    class of this module. All arguments with a default value should be at the
    end of the list.

.. py:attribute:: inputs

    (dict) A nested dictionary mapping names of topics to which modules of this
    type subscribe to :class:`models.FirmwareInput` objects describing
    those inputs.

.. py:attribute:: outputs

    (dict) A nested dictionary mapping names of topics to which modules of this
    type publish to :class:`models.FirmwareOutput` objects describing
    those outputs.

.. py:attribute:: dependencies

    (dict) A list of libraries on which this module depends. In particular, it
    should be a list of dictionaries with the same structure as is required by
    the "repository" field.

.. py:attribute:: status_codes

    (dict) A dictionary mapping status codes (as 8-bit integers) for this
    module to strings describing the relevant status.
"""

FirmwareModule = Schema({
    Required("_id"): Any(str, unicode),
    Required("type"): Any(str, unicode),
    "environment": Any(str, unicode),
    "categories": [SENSORS, ACTUATORS, CALIBRATION],
    "arguments": [object],
    "inputs": {Extra: FirmwareInput},
    "outputs": {Extra: FirmwareOutput}
}, extra=REMOVE_EXTRA)
FirmwareModule.__doc__ = """
A :class:`models.FirmwareModule` is a single instance of a
:class:`models.FirmwareModuleType` usually configured to control a
single physical sensor or actuator.

.. py:attribute:: type

    (str, required) The ID of the :class:`models.FirmwareModuleType` of
    this object

.. py:attribute:: environment

    (str, required) The ID of the :class:`models.Environment` on which
    this peripheral acts

.. py:attribute:: categories

    (list) A list of categories to which this firmware module belongs. Must be
    a subset of ["sensors", "actuators", "calibration"]. If a value for this
    attribute is provided, it will overwrite the value from the
    :class:`models.FirmwareModuleType` for this module.

.. py:attribute:: arguments

    (list) A list of argument values to pass to the module. There should be
    at least as many items in this list as there are arguments in the
    :class:`models.FirmwareModuleType` for this module that don't have
    a default value.

.. py:attribute:: inputs

    (dict) A nested dictionary mapping names of topics to which this module
    subscribes to :class:`FirmwareInput` objects describing those inputs. The
    set of keys in this dictionary must be a subset of the keys in the `inputs`
    dictionary for the :class:`models.FirmwareModuleType` for this
    module. Values in this dictionary override values in the firmware module
    type.

.. py:attribute:: outputs

    (dict) A nested dictionary mapping names of topics to which this module
    publishes to :class:`FirmwareOutput` objects describing those outputs. The
    set of keys in this dictionary must be a subset of the keys in the
    `outputs` dictionary for the :class:`models.FirmwareModuleType` for
    this module. Values in this dictionary override values in the firmware
    module type.
"""

SoftwareInput = Schema({
    Required("type"): Any(str, unicode),
    "description": Any(str, unicode),
})
SoftwareOutput = Schema({
    Required("type"): Any(str, unicode),
    "description": Any(str, unicode),
})
SoftwareArgument = Schema({
    Required("name"): Any(str, unicode),
    "type": Any("int", "float", "bool", "str"),
    "description": Any(str, unicode),
    "default": object,
    Required("required", default=False): bool
})
Parameter = Schema({
    "type": Any("int", "float", "bool", "str"),
    "description": Any(str, unicode),
    "default": object,
    Required("required", default=False): bool
})
SoftwareModuleType = Schema({
    Required("package"): Any(str, unicode),
    Required("executable"): Any(str, unicode),
    "description": Any(str, unicode),
    "categories": all_categories,
    Required("arguments", default=[]): [SoftwareArgument],
    Required("parameters", default={}): {Extra: Parameter},
    Required("inputs", default={}): {Extra: SoftwareInput},
    Required("outputs", default={}): {Extra: SoftwareOutput}
}, extra=REMOVE_EXTRA)
SoftwareModuleType.__doc__ = """
A :class:`SoftwareModuleType` is a ROS node that can be run on the controller
for the farm (e.g. Raspberry Pi). It can listen to ROS topics, publish to ROS
topics, and advertize services.  Examples include the recipe handler and
individual control loops. Software module types are distributed as ROS
packages.

.. py:attribute:: package

    (str, required) The name of the ROS package containing the code for this
    object

.. py:attribute:: executable

    (str, required) The name of the executable for this object

.. py:attribute:: description

    (str) Description of the library

.. py:attribute:: categories

    (list) A list of categories to which this software module type belongs.
    Must be a subset of ["sensors", "actuators", "control", "calibration",
    "persistence"].

.. py:attribute:: arguments

    (array, required) An array of dictionaries describing the command line
    arguments to be passed to this module. The inner dictionaries must contain
    the field "name" (the name of the argument)  and can contain the fields
    "type" (one of "int", "float", "bool", and "str"), "description" (a short
    description of what the argument is for), "required" (a boolean indicating
    whether or not this argument is required to be passed to the module.
    defaults to False) and "default" (a default value for the argument in case
    no value is supplied).  An argument should only have a default value if it
    is required.

.. py:attribute:: parameters

    (dict, required) A nested dictionary mapping names of ROS parameters read
    by this module to dictionaries describing those parameters. The inner
    dictionaries can contain the fields "type" (one of "int", "float", "bool",
    and "str") "description" (a short description of what the parameter is
    for), "required" (a boolean indicating whether or not this parameter is
    required to be defined), and "default" (a default value for the parameter
    in case no value is supplied). A parameter should only have a default value
    if it is required.

.. py:attribute:: inputs

    (dict) A nested dictionary mapping names of topics to which this library
    subscribes to dictionaries containing information about those topics. The
    inner dictionaries must contain the field "type" (the ROS message type
    expected for messages on the topic) and can contain the field "description"
    (a short description of what the input is for).

.. py:attribute:: outputs

    (dict) A nested dictionary mapping names of topics to which this library
    publishes to dictionaries containing information about those topics. The
    inner dictionary must contain the field "type" (the ROS message type
    expected for messages on the topic) and can contain the field "description"
    (a short description of what the output is for).
"""

SoftwareModule = Schema({
    Required("type"): Any(str, unicode),
    "namespace": Any(str, unicode),
    "environment": Any(str, unicode),
    "categories": all_categories,
    "arguments": [object],
    "parameters": dict,
    "mappings": dict
}, extra=REMOVE_EXTRA)
SoftwareModule.__doc__ = """
A :class:`SoftwareModule` is a single instance of a
:class:`models.SoftwareModuleType`.

.. py:attribute:: type

    (str, required) The ID of the :class:`models.SoftwareModuleType` of
    this object

.. py:attribute:: namespace

    (str) The name of the ros namespace that should contain the ROS node for
    this software module. If no value is provided, the environment field is
    used instead. If no environment is provided, the module is placed in the
    global namespace.

.. py:attribute:: environment

    (str) The ID of the :class:`models.Environment` on which this
    :class:`SoftwareModule` acts.

.. py:attribute:: categories

    (list) A list of categories to which this software module belongs. Must be
    a subset of ["sensors", "actuators", "control", "calibration",
    "persistence"]. If a value for this attribute is provided, it will
    overwrite the value from the :class:`models.SoftwareModuleType` for
    this module.

.. py:attribute:: arguments

    (array) A list of argument values to pass to the module. there should be at
    least as many items in this list as there are arguments in the
    :class:`models.SoftwareModuleType` for this module that don't have
    a default value.

.. py:attribute:: parameters

    (dict) A dictionary mapping ROS parameter names to parameter values. These
    parameters will be defined in the roslaunch XML file under the node for
    this software module.

.. py:attribute:: mappings

    (dict) A dictionary mapping ROS names for topics or parameters to different
    ROS names. Keys are the names defined in the software module type and
    values are the names that should be used instead. This can be used, for
    example, to route the correct inputs into a control module with generic
    input names like `set_point` and `measured`.
"""

