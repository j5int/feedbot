========
Usage
========

A minimal install of Feedbot needs to instantiate an instance, join a chat
room and call the `serve_forever()` method. For example, inside `test_bot.py`::

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


In order to launch feedbot from a shell prompt simply call::

    $ python test_bot.py

