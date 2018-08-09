"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='eposfederator.webapi',  # Required
    version='0.0.1',  # Required
    description='Epos federator REST API',  # Required
    long_description=long_description,  # Optional
    package_dir={'': 'src'},
    packages=find_packages('src'),
    namespace_packages=['eposfederator', 'eposfederator.plugins'],
    install_requires=['tornado', 'webargs>=3.0.1', 'eposfederator.libs', 'ruamel.yaml', 'marshmallow_jsonschema'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
