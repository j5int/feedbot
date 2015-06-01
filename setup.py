#!/usr/bin/env python
from setuptools import find_packages

import feedbot

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'jabberbot==0.15',
    'beautifulsoup4==4.3.2',
    'feedparser==5.1.3',
    'humanize==0.5.1',
    'docutils==0.12',
    'Jinja2==2.7.3',
    'MarkupSafe==0.23',
    'pockets==0.2.4',
    'Pygments==2.0.2',
    'pytz==2014.10',
    'six==1.9.0',
    'Sphinx==1.2.3',
    'sphinxcontrib-napoleon==0.3.6',
    'wheel==0.24.0',
    'xmpppy==0.5.2',
]

test_requirements = [
    'pytest==2.7.0',
    'pytest-cov==1.8.1',
    'mock==1.0.1',
]

setup(
    name='feedbot',
    version=feedbot.__version__,
    description="A Python Jabberbot project to monitor RSS feeds in a chatroom.",
    long_description=readme + '\n\n' + history,
    author="Liav Koren",
    author_email='liav@vmfamrms.com',
    url='https://github.com/vmfarms/feedbot',
    packages=find_packages(),
    include_package_data=True,
    setup_requires=["setuptools_git >= 0.3"],
    dependency_links=[
        'git+git://git.code.sf.net/p/pythonjabberbot/code.git#egg=jabberbot-0.15',
        'git+https://github.com/ArchipelProject/xmpppy.git#egg=xmpppy-0.5.2'
        ],
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='feedbot',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',

    ],
    test_suite='feedbot.tests.test_feedbot.py',
    tests_require=test_requirements
)
