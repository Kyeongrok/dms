#!/usr/bin/env python
import dmsclient

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools

    use_setuptools()
    from setuptools import setup, find_packages


def read(relative):
    """
    Read file contents and return a list of lines.
    ie, read the VERSION file
    """
    contents = open(relative, 'r').read()
    return [l for l in contents.split('\n') if l != '']


with open('README.rst', 'r') as f:
    readme = f.read()

setup(
    name='dmsclient',
    url='https://github.com/EMCECS/volvo',
    keywords=['dms', 'metadata', 'volvo', 'adac'],
    long_description=readme,
    version=dmsclient.__version__,
    description="A helper library for interacting with the Data Management System (DMS) in the scope Volvo/Zenuity "
                "ADAC project",
    author='Dell EMC',
    author_email='dell@dell.com',
    tests_require=read('./test-requirements.txt'),
    install_requires=read('./requirements.txt'),
    test_suite='nose.collector',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup']),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
