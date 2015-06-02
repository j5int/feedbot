Python-feedbot
==============

.. image:: https://img.shields.io/travis/liavkoren/feedbot.svg
        :target: https://travis-ci.org/liavkoren/feedbot

.. image:: https://img.shields.io/pypi/v/feedbot.svg
        :target: https://pypi.python.org/pypi/feedbot


A Python jabberbot project to monitor RSS feeds in  a chatroom.

* Free software: BSD license
* Documentation: https://feedbot.readthedocs.org.

Features
--------

* Feedbot is a Jabberbot based chatbot that will sit in your xmpppy chatroom and monitor RSS and Atom feeds for you. It currently provides a set of simple commands to blacklist terms from feeds, and a simple interface to add, remove and read feed stories.

Quickstart
----------

* `pip install feedbot`
* A minimal install requires setting up a script that will launch Feedbot with
the correct settings:

Eg:

```python
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
```

Settings
--------
FeedBot has a few user-definable settings. To override the default settings,
simply create a shell environment variable with the correct setting-key and value.

* FEED_HISTORY_QUEUE_LENGTH: Every feed stores a history of entries that have already been shown in the channel. This settings controls how many entries that queue holds. Default is 200.
* FEEDBOT_DATA_DIRECTORY: The location on disk where the FeedBot will save feeds data. Feed data is saved as human readable JSON. By default FeedBot will attempt to find the current user's home directory and create a ~/.feedbot directory there. If `$HOME` is not set, FeedBot will issue a warning and attempt to create a directory in /tmp/feedbot
* FEEDBOT_DATA_FILENAME: Name of the FeedBot data file. Default is `feedbot.conf`


Credits
-------

Built at VM Farms, by Liav Koren using Feedparser and Jabberbot. Tests are
built with pytest and mock. Packaging was done with Cookiecutter and Jeff Knupp's excellent walkthrough http://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/
