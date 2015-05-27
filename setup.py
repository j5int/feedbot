#!/usr/bin/env python
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
    'git+git://git.code.sf.net/p/pythonjabberbot/code#egg=0.15'
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
    packages=[
        'feedbot',
    ],
    package_dir={'feedbot':
                 'feedbot'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='feedbot',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
