"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django-automated-logging',
    version='3.0.0a1',
    description='Django model based logging - solved and done right.',
    long_description=long_description,
    url='https://github.com/indietyp/django-automated-logging',
    author='Bilal Mahmoud',
    author_email='opensource@indietyp.com',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
	'Framework :: Django :: 1.10'
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
	'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='django automation tools backend',
    packages=find_packages(exclude=(['logtest', 'test*'])),
    install_requires=['Django>1.10'],
    zip_safe=False
)
