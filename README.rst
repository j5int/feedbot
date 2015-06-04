feedbot
=======

.. image:: https://travis-ci.org/liavkoren/feedbot.svg?branch=app
    :target: https://travis-ci.org/liavkoren/feedbot

A Python jabberbot project to monitor RSS feeds in a chatroom.

-  Free software: BSD license
-  Documentation: https://feedbot.readthedocs.org.

Features
--------

-  Feedbot is a Jabberbot based chatbot that will sit in your xmpppy
   chatroom and monitor RSS and Atom feeds for you. It currently
   provides a set of simple commands to blacklist terms from feeds, and
   a simple interface to add, remove and read feed stories.

Installing
----------
Feedbot runs as an `application rather than a library`_  because it has concrete dependencies on versions of Jabberbot and xmpppy that are not available on the Cheeseshop.

.. _application rather than a library: https://caremad.io/2013/07/setup-vs-requirement/

Having said that, installation is still straightforward.

``$ git clone https://github.com/liavkoren/feedbot.git``

followed by

``$ python pip install -r requirements.txt``

If you would like to work on Feedbot, simply install the test_requirments from test_requirements.txt. Docs can be build from the ``doc/`` directory with

``$ make html``

Quickstart
----------

-  A minimal install requires setting up a script that will launch
   Feedbot with the correct settings:

Eg:

.. code:: python

    import logging
    from feedbot import bot

    BOT_NICKNAME = 'Feedbot'
    BOT_PASSWORD = 'l33t'
    BOT_USERNAME = 'feedbot@botbot.org'
    CHATROOM = 'bot-party@conference.bot.org'
    SERVER_IP = '0.0.0.0'

    if __name__ == '__main__':
        feedbot = bot.FeedBot(
            CHATROOM,
            BOT_USERNAME,
            BOT_PASSWORD,
            server=SERVER_IP,
        )

        logging.info("Feedbot is alive")
        feedbot.muc_join_room(CHATROOM, BOT_NICKNAME)
        feedbot.serve_forever()
        logging.info("Feedbot is dead")

Settings
--------

FeedBot has a few user-definable settings. To override the default
settings, simply create a shell environment variable with the correct
setting-key and value.

-  FEED\_HISTORY\_QUEUE\_LENGTH: Every feed stores a history of entries
   that have already been shown in the channel. This settings controls
   how many entries that queue holds. Default is 200.
-  FEEDBOT\_DATA\_DIRECTORY: The location on disk where the FeedBot will
   save feeds data. Feed data is saved as human readable JSON. By
   default FeedBot will attempt to find the current user's home
   directory and create a ~/.feedbot directory there. If ``$HOME`` is
   not set, FeedBot will issue a warning and attempt to create a
   directory in /tmp/feedbot
-  FEEDBOT\_DATA\_FILENAME: Name of the FeedBot data file. Default is
   ``feedbot.conf``

Credits
-------

Built at VM Farms, by Liav Koren using Feedparser and Jabberbot. Tests
are built with pytest and mock. Packaging was done with Cookiecutter and
Jeff Knupp's excellent walkthrough
http://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
