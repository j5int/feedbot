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
    'feedparser==5.1.3',
    'humanize==0.5.1',
    'pytz==2014.10',
    'xmpppy==0.5.0rc1',
    'jabberbot==0.15',
    'mock==1.0.1',
    'beautifulsoup4==4.3.2',
]

test_requirements = [
    'pytest==2.7.0',
    'pytest-cov==1.8.1',
    'mock==1.0.1',
    # 'beautifulsoup4==4.3.2',
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
    dependency_links=['git+git://git.code.sf.net/p/pythonjabberbot/code.git#egg=jabberbot-0.15', ],
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='feedbot',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications :: Chat',

    ],
    test_suite='feedbot.tests.test_feedbot.py',
    tests_require=test_requirements
)
