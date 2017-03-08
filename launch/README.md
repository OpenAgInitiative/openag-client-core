openag\_launch
==============

A collection of ROS `.launch` files and parameter files for configuring the
runtime and flashing the OpenAg sensor firmware.

Use with [openag_python](https://github.com/openaginitiative/openag_python) as
a stand-alone flash tool, or with [openag_brain](https://github.com/openaginitiative/openag_brain) for runtime flashing.

Using with openag\_python
-------------------------

You can use `openag_python` as a stand-alone flash tool by using the `.yaml`
parameter files in this repository. First, install `openag_python` (>0.1.5):

    git clone https://github.com/openaginitiative/openag_python.git
    cd openag_python
    pip install -e .[flash]

Then:

    openag firmware flash -p ros -t upload -f openag_launch/personal_food_computer_v2.yaml
