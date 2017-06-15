import os
import json
import re
from importlib import import_module
from ..util import parent_dirname
from .categories import all_categories, ACTUATORS, SENSORS
from .plugins import plugin_map

def find_manifest_paths(lib_path):
    """
    Find manifest files below ``lib_path``.
    Returns a generator of file paths.
    """
    dir_names = os.listdir(lib_path)
    manifest_paths = (
        os.path.join(lib_path, dir_name, 'module.json')
        for dir_name in dir_names
    )
    # Filter down to module files that actually exist.
    valid_manifest_paths = (
        path for path in manifest_paths
        if os.path.isfile(path)
    )
    return valid_manifest_paths


def load_manifest(manifest_path):
    with open(manifest_path) as f:
        doc = json.load(f)
        # Patch in id if id isn't present
        if not doc.get("_id"):
            doc["_id"] = parent_dirname(manifest_path)
    return doc


def load_firmware_type_manifests(lib_path):
    """Load firmware module type definitions from manifest files"""
    # Firmware modules can define a ``module.json`` manifest file that acts as a
    # firmware module type definition for that module.
    # Check for manifest files within each firmware module.
    manifest_paths = find_manifest_paths(lib_path)
    manifests = (
        load_manifest(manifest_path)
        for manifest_path in manifest_paths
    )
    return manifests


def load_plugin(plugin_name):
    """
    Given a plugin name, load plugin cls from plugin directory.
    Will throw an exception if no plugin can be found.
    """
    plugin_cls = plugin_map.get(plugin_name, None)
    if not plugin_cls:
        plugin_module_name, plugin_cls_name = plugin_name.split(":")
        plugin_module = import_module(plugin_module_name)
        plugin_cls = getattr(plugin_module, plugin_cls_name)
    return plugin_cls


def synthesize_firmware_module_info(modules, module_types):
    """
    Modules are allowed to define attributes on their inputs and outputs that
    override the values defined in their respective module types. This function
    takes as input a dictionary of `modules` (mapping module IDs to
    :class:`models.FirmwareModule` objects) and a dictionary of
    `module_types` (mapping module type IDs to
    :class:`models.FirmwareModuleType` objects). For each module, it
    synthesizes the information in that module and the corresponding module
    type and returns all the results in a dictionary keyed on the ID of the
    module
    """
    res = {}
    for mod_id, mod_info in modules.items():
        mod_info = dict(mod_info)
        mod_type = module_types[mod_info["type"]]
        # Directly copy any fields only defined on the type
        if "repository" in mod_type:
            mod_info["repository"] = mod_type["repository"]
        mod_info["header_file"] = mod_type["header_file"]
        mod_info["class_name"] = mod_type["class_name"]
        if "dependencies" in mod_type:
            mod_info["dependencies"] = mod_type["dependencies"]
        if "status_codes" in mod_type:
            mod_info["status_codes"] = mod_type["status_codes"]
        # Update the arguments
        mod_info["arguments"] = process_args(
            mod_id, mod_info.get("arguments", []),
            mod_type.get("arguments", [])
        )
        # Update the categories
        if not "categories" in mod_info:
            mod_info["categories"] = mod_type.get(
                "categories", all_categories
            )
        # Update the inputs
        mod_inputs = mod_info.get("inputs", {})
        for input_name, type_input_info in mod_type.get("inputs", {}).items():
            mod_input_info = dict(type_input_info)
            mod_input_info.update(mod_inputs.get(input_name, {}))
            mod_input_info["variable"] = mod_input_info.get(
                "variable", input_name
            )
            mod_input_info["categories"] = mod_input_info.get(
                "categories", [ACTUATORS]
            )
            mod_inputs[input_name] = mod_input_info
        mod_info["inputs"] = mod_inputs
        # Update the outputs
        mod_outputs = mod_info.get("outputs", {})
        for output_name, type_output_info in mod_type.get("outputs", {}).items():
            mod_output_info = dict(type_output_info)
            mod_output_info.update(mod_outputs.get(output_name, {}))
            mod_output_info["variable"] = mod_output_info.get(
                "variable", output_name
            )
            mod_output_info["categories"] = mod_output_info.get(
                "categories", [SENSORS]
            )
            mod_outputs[output_name] = mod_output_info
        mod_info["outputs"] = mod_outputs
        res[mod_id] = mod_info
    return res


def process_args(mod_id, args, type_args):
    """
    Takes as input a list of arguments defined on a module and the information
    about the required arguments defined on the corresponding module type.
    Validates that the number of supplied arguments is valid and fills any
    missing arguments with their default values from the module type
    """
    res = list(args)
    if len(args) > len(type_args):
        raise ValueError(
            'Too many arguments specified for module "{}" (Got {}, expected '
            '{})'.format(mod_id, len(args), len(type_args))
        )
    for i in range(len(args), len(type_args)):
        arg_info = type_args[i]
        if "default" in arg_info:
            args.append(arg_info["default"])
        else:
            raise ValueError(
                'Not enough module arguments supplied for module "{}" (Got '
                '{}, expecting {})'.format(
                    mod_id, len(args), len(type_args)
                )
            )
    return args


def prune_unspecified_categories(modules, categories):
    """
    Removes unspecified module categories.
    Mutates dictionary and returns it.
    """
    res = {}
    for mod_name, mod_info in modules.items():
        mod_categories = mod_info.get("categories", all_categories)
        for category in categories:
            if category in mod_categories:
                break
        else:
            continue
        for input_name, input_info in mod_info["inputs"].items():
            for c in input_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["inputs"][input_name]
        for output_name, output_info in mod_info["outputs"].items():
            for c in output_info["categories"]:
                if c in categories:
                    break
            else:
                del mod_info["outputs"][output_name]
        res[mod_name] = mod_info
    return res


 
