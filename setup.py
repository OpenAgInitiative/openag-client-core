from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

# fetch values from package.xml
setup_args = generate_distutils_setup(
    packages=[
        'openag_brain',
        'openag_lib',
        'openag_lib.firmware',
        'openag_lib.firmware.plugins',
        'openag_lib.db_bootstrap'
    ],
    package_dir={'': 'src'},
)

setup(**setup_args)
