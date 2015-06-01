Python-feedbot
==============

.. image:: https://img.shields.io/travis/liavkoren/feedbot.svg :target:
https://travis-ci.org/liavkoren/feedbot

.. image:: https://img.shields.io/pypi/v/feedbot.svg :target:
https://pypi.python.org/pypi/feedbot

A Python jabberbot project to monitor RSS feeds in a chatroom.

-  Free software: BSD license
-  Documentation: https://feedbot.readthedocs.org.

Features
--------

-  Feedbot is a Jabberbot based chatbot that will sit in your xmpppy
   chatroom and monitor RSS and Atom feeds for you. It currently
   provides a set of simple commands to blacklist terms from feeds, and
   a simple interface to add, remove and read feed stories.

Quickstart
----------

-  ``pip install feedbot``
-  A minimal install requires setting up a script that will launch
   Feedbot with the correct settings:

Eg:

.. code:: python

    import logging
    from feedbot import bot
    from . import feedbot_settings as settings

    if __name__ == '__main__':
        logger = logging.getLogger(__name__)
        chatroom = settings.CHATROOMS['default']
        feedbot = FeedBot(
            chatroom,
            settings.BOT_USERNAME,
            settings.BOT_PASSWORD,
            server=settings.SERVER_IP,
            command_prefix=settings.COMMAND_PREFIX,
        )

        logger.info("RssBot is alive")
        feedbot.muc_join_room(chatroom, settings.BOT_NICKNAME)
        feedbot.serve_forever()
        logger.info("RssBot is dead")

Credits
-------

Built at VM Farms, by Liav Koren, using Feedparser and Jabberbot. Tests
are built with pytest and mock. Packaging was done with Cookiecutter and
Jeff Knupp's excellent walkthrough
http://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
