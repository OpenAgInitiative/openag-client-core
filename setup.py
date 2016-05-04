from os import path
from codecs import open
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='openag-brain',
    version='0.0.1',
    description='Framework for software modules in an OpenAg food computer',
    long_description=long_description,
    url='https://github.com/OpenAgInitiative/openag-brain',
    author='Open Agriculture Initiative',
    author_email='mitopenag@gmail.com',
    license='GPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Framework :: Flask',
        'Intended Audience :: Developers,',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(),
    namespace_packages=['openag', 'openag.brain', 'openag.brain.modules'],
    include_package_data=True,
    install_requires=[
        'couchdb>=1.0.1',
        'flask>=0.10.1',
        'gevent>=1.1.1',
    ]
)
