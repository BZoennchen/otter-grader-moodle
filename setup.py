# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
    ['ograder']

install_requires = ['pyyaml', 'fica', 'nbformat', 'click']

package_data = \
    {'': ['*']}

keywords = ['otter', 'grader', 'moodle', 'education', 'autograding']

setup_kwargs = {
    'name': 'ograder',
    'version': '0.0.1',
    'description': 'Tool that helps to autograde otter assignments without Gradescope',
    'author': 'Benedikt Zoennchen',
    'author_email': 'benedikt.zoennchen@web.de',
    'maintainer': 'BZoennchen',
    'maintainer_email': 'benedikt.zoennchen@web.de',
    'url': 'https://github.com/BZoennchen/otter-grader-moodle',
    'entry_points':'''
        [console_scripts]
        ograder=ograder.cli:cli
    ''',
    'packages': packages,
    'install_requires': install_requires,
    'python_requires': '>=3.7.0,<4.0.0',
    'keywords': keywords
}

setup(**setup_kwargs)