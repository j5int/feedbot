"""
Contains the FeedBot class.

Note:
    This documentation isn't in the body of the FeedBot class because Jabberbot
    turns docstrings into chatroom help-text.

FeedBot is a JabberBot which sits in a chatroom and monitors RSS/Atom feeds for
you.

Args:
    chatroom (string): the chatroom name and server, formatted '<name>@<server>',
        eg: 'test_chatroom@acme.industries.com'
    bot_name (string): the username for the bot
    bot_password (string): the password the bot should use with the chat server.

In order for the FeedBot to have persistence it saves feed/filter data to a
local flat-file via Pickle. You must define this path with the
FEEDBOT_DATAFILE_PATH, setting or suffer the consequences! (The consequences
are you'll lose your feeds when the bot exits.)

 """

from __future__ import absolute_import
from collections import deque
from datetime import datetime
import json
import logging
import os

import humanize
from jabberbot import (
    JabberBot,
    botcmd
)
from pytz import utc

from . import exceptions
from . import messages
from .feed import Feed
from .filters import (
    ALLOWED_FILTER_TYPES,
    AgeFilter,
    NotFilter,
)

logger = logging.getLogger(__name__)


class FeedBot(JabberBot):
    """ A JabberBot to monitor RSS/Atom feeds. """
    def __init__(self, chatroom, bot_name, bot_password, *args, **kwargs):
        self.chatroom = chatroom
        self.bot_name = bot_name
        self.bot_password = bot_password
        if 'command_prefix' not in kwargs:
            kwargs['command_prefix'] = '/'
        super(FeedBot, self).__init__(bot_name, bot_password, *args, **kwargs)
        self._init_data_dir()
        self.feeds = self._load_feed_data()
        queue_length = int(os.getenv('FEED_HISTORY_QUEUE_LENGTH', 200))
        self.entry_history = deque(maxlen=queue_length)

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, self.chatroom, self.bot_name)

    def _add_entry_to_history(self, entry):
        """ Track an entry that has already been displayed. """
        if entry.link not in self.entry_history:
            self.entry_history.append(entry.link)

    def _seen_entry(self, entry):
        """ Has an entry been displayed? """
        return entry.link in self.entry_history

    def _load_feed_data(self):
        """
        Attempt to load the feed data from a storage file and unpickle it.

        Note:
            If any exceptions are raised in this method they are caught, a standard
            error message is sent to the channel, and the bot initializes itself
            without restoring any saved state.
        """
        feeds = {}
        try:
            with open(self.data_file, 'r') as data_file:
                serialized_feed_data = json.load(data_file)
                for feed_data in serialized_feed_data:
                    deserialized_feed = Feed.from_dict(feed_data)
                    feeds[deserialized_feed.name] = deserialized_feed
        except:  # We never want to blow up on instantiating the bot.
            message = messages.FEED_DATA_LOAD_ERROR.format(path=self.data_file)
            self.send_groupchat_message(message)
        return feeds

    def _init_data_dir(self):
        """ Ensure the data directory exists and set self.data_file. """
        user_defined_data_dir = os.getenv('FEEDBOT_DATA_DIRECTORY')
        if user_defined_data_dir:
            self._create_data_file(user_defined_data_dir)
        else:
            home_dir = os.getenv('HOME')
            if home_dir:
                data_dir = os.path.join(home_dir, '.feedbot')
                self._create_data_file(data_dir)
            else:
                self.send_groupchat_message(messages.DATA_DIR_ERROR)
                self._create_data_file('/tmp/feedbot')

    def _create_data_file(self, feedbot_data_dir):
        """ Given a path string, ensure that the feedbot data file exists. """
        if not os.path.exists(feedbot_data_dir):
            os.makedirs(feedbot_data_dir)
        data_file = os.path.join(feedbot_data_dir, os.getenv('FEEDBOT_DATA_FILENAME', 'feedbot.conf'))
        if not os.path.exists(data_file):
            open(data_file, 'a').close()
        self.data_file = data_file

    def _save_feed_data(self):
        """
        Attempt to pickle and save the feed data to a storage file.

        Note:
            If any exceptions are raised in this method they are caught, a standard
            error message is sent to the channel, and an IOError is raised.
        """
        try:
            feed_data = [feed.to_dict() for feed in self.feeds.values()]
            with open(self.data_file, 'r+') as data_file:
                data_file.write(json.dumps(feed_data))
                return True
        except Exception as exception:
            error = getattr(exception, 'message', '')
            message = messages.FEED_SAVE_DATA_ERROR.format(
                error=error,
                data_path=self.data_file
            )
            self.send_groupchat_message(message)
            raise IOError()

    def get_feed_urls(self):
        """ Return URLs of Feeds. """
        return [feed.url for feed in self.feeds.values()]

    @botcmd
    def add_feed(self, msg, args):
        """
        Add a Feed for monitoring.

        Feed name should not contain whitespace and URLs must be unique.
        example usage: '/add_feed seclist http://www.seclist.org/rss/list.rss'
        Feeds are checked at the time they are added to make sure they are valid.

        Raises:
            FeedDataError: If there is an error parsing the feed.
        """
        try:
            try:
                name, url = clean_args(args)
            except ValueError:
                # If the user omits 'http://' from the url, jabberbot passes
                # three args rather than two, we don't care about the third one.
                name, url, _ = clean_args(args)
                url = 'http://' + url

            valid_name_url = not (name in self.feeds or url in self.get_feed_urls())
            if valid_name_url:
                date_filter = AgeFilter(minutes=90)
                feed = Feed(name=name, url=url, filters=[date_filter])
                # get the unfiltered feed once to make sure it's good:
                feed.get_raw_feed()
                self.feeds[name] = feed
                self._save_feed_data()
                self.send_groupchat_message(messages.OKAY)
            else:
                message = messages.FEED_EXISTS_ERROR.format(name=name, url=url)
                self.send_groupchat_message(message)
        except ValueError:
            self.send_groupchat_message(messages.FEED_ADD_HELP)
        except IOError:
            pass
        except exceptions.FeedDataError as e:
            message = messages.FEED_PARSE_ERROR.format(error=e.message)
            self.send_groupchat_message(message)

    @botcmd
    def list_feeds(self, msg, args):
        """ Display the monitored feeds along their filters. """
        if self.feeds:
            self.send_groupchat_message(messages.CURRENTLY_MONITORING)
            # Inform the channel of the name and URL of this feed:
            for feed in self.feeds.values():
                message = messages.FEED_NAME_URL_TEMPLATE.format(name=feed.name, url=feed.url)
                self.send_groupchat_message(message)
                # If there are filters on this feed, inform the channel:
                if not feed.get_filters():
                    continue

                self.send_groupchat_message(messages.FILTER_HEADER)
                for key, feed_filter in enumerate(feed.get_filters()):
                    message = messages.FILTER_KEY_VALUE.format(key=key, filter=str(feed_filter))
                    self.send_groupchat_message(message)
        else:
            self.send_groupchat_message(messages.FEEDS_DO_NOT_EXIST)

    def _url2name(self, url):
        """ Given a URL return the name of the Feed. """
        for name, feed in self.feeds.items():
            if feed.url == url:
                return name

    @botcmd
    def remove_feed(self, msg, args):
        """
        Stop monitoring a feed.

        Feeds can be removed by specifying either the `name` or `url` of the
        feed.
        """
        feed = args.strip()

        if feed in self.feeds:
            del self.feeds[feed]
            message = messages.FEED_DELETED.format(feed_name=feed)
        elif feed in self.get_feed_urls():
            feed_name = self._url2name(feed)
            del self.feeds[feed_name]
            message = messages.FEED_DELETED.format(feed_name=feed_name)
        else:
            # this is an unrecognized feed
            self.send_groupchat_message(messages.FEED_REMOVE_HELP)
            return
        try:
            self._save_feed_data()
            self.send_groupchat_message(message)
        except IOError:
            pass

    @botcmd
    def add_filter(self, msg, args):
        """
        Add a filter to a news Feed: `/add_filter <feed name> not: <search term>`.

        Filters are case-insensitive and applied against the summary and title
        of a feed entries.
        """
        try:
            command, filter_term = args.split(':')
            feed_name, filter_type = command.split(" ")
            filter_type = filter_type.lower()
            filter_term = filter_term.lower().strip()
            valid_filter = filter_type in ALLOWED_FILTER_TYPES
            feed = self.get_feed_by_name(feed_name)

            if valid_filter:
                new_filter = NotFilter(filter_term)
                feed.add_filter(new_filter)
                message = messages.ADDED_FILTER.format(
                    filter_type=filter_type,
                    filter_term=filter_term,
                    feed_name=feed_name)
                self._save_feed_data()
                self.send_groupchat_message(message)
            else:
                self.send_groupchat_message(messages.UNKNOWN_FILTER_ERROR)

        except IOError:
            pass
        except ValueError:
            self.send_groupchat_message(messages.ADD_FILTER_HELP)
        except exceptions.UnknownFeedError:
            self.send_groupchat_message(messages.FEED_NOT_FOUND_ERROR)

    def get_feeds(self):
        """ Return the URLs of all Feeds. """
        return self.feeds.values()

    def get_feed_by_name(self, name):
        """
        Given the name of a feed, returns the feed.

        Raises:
            UnknownFeedError
        """
        try:
            return self.feeds[name]
        except KeyError:
            raise exceptions.UnknownFeedError()

    @botcmd
    def remove_filter(self, msg, args):
        """ Given a feed_name and a filter, remove it. Eg: `/remove_filter fooList 3`. """
        try:
            feed_name, filter_index = clean_args(args)
            filter_index = int(filter_index)
            feed = self.feeds[feed_name]
            valid_filter = all([0 <= filter_index, filter_index < len(feed.get_filters())])

            if valid_filter:
                feed_filter = feed.get_filter_by_key(filter_index)
                feed.remove_filter(feed_filter)
                self._save_feed_data()
                message = messages.REMOVED_FILTER.format(filter=feed_filter, feed=feed.name)
                del(feed_filter)
                self.send_groupchat_message(message)
            else:
                self.send_groupchat_message(messages.REMOVE_FILTER_HELP)
        except (ValueError, KeyError):
            self.send_groupchat_message(messages.REMOVE_FILTER_HELP)
        except IOError:
            pass

    @botcmd
    def dump_feed(self, msg, args):
        """
        Dump the specified filtered feed into the channel.

        Use '/get_stories <feed_name> [n]' to get the first 3 or n stories.
        FeedBot does not display entries that have already been shown in channel.
        """
        args = clean_args(args)
        try:
            if len(args) == 2:
                feed_name, entries_limit = args
                entries_limit = int(entries_limit)
            elif len(args) == 1:
                feed_name, = args
                entries_limit = int(os.environ.get('FEEDBOT_STORY_LIMIT', 5))

            feed = self.feeds[feed_name]
            feed_entries = feed.get_filtered_feed()
            entries_limit = min(len(feed_entries), entries_limit)
            feed_entries = feed_entries[:entries_limit]
            unseen_entries = [entry for entry in feed_entries if not self._seen_entry(entry)]

            if unseen_entries:
                self._print_feed(feed.name, unseen_entries)
            else:
                self.send_groupchat_message(messages.NO_NEW_ENTRIES.format(feed_name=feed.name))

        except ValueError:
            self.send_groupchat_message(messages.SORRY)
        except KeyError:
            self.send_groupchat_message(messages.FEED_NOT_FOUND_ERROR)

    def _print_feed(self, feed_name, entries):
        """ Print a Feed to the channel. """
        self.send_groupchat_message(messages.FEED_HEADER.format(feed_name=feed_name))
        for entry in entries:
            if self._seen_entry(entry):
                continue
            self._add_entry_to_history(entry)
            self._print_entry(entry)
            self.send_groupchat_message(messages.ENTRY_SEPERATOR)

    def _print_entry(self, entry):
        """ Print a Feed entry to the channel. """
        fields = ['title', 'published', 'authors', 'link', 'summary']
        for field in fields:
            if field in entry:
                if entry[field] == [{}]:
                    continue
                try:
                    field_string = messages.ENTRY_FIELD_TEMPLATE.format(
                        field_name=unicode(field.capitalize()),
                        field_value=unicode(entry[field])
                    )
                except UnicodeEncodeError:
                    continue
                if field == 'published':
                    time_string = pub_time_to_string(entry.published_parsed)
                    field_string += messages.ENTRY_PUBLISHED_FIELD_TEMPLATE.format(publication_time=time_string)
                else:
                    field_string += messages.NEWLINE
                self.send_groupchat_message(field_string)

    @botcmd
    def dump_all(self, msg, args):
        """ Dump all filtered feeds into the channel. """
        for feed in self.get_feeds():
            self.dump_feed("", feed.name)
            self.send_groupchat_message(messages.FEED_SEPERATOR)

    @botcmd
    def set_age_filter(self, mess, args):
        """
        Set the cut-off age for an age-filter.

        Call with '/set_age_filter <feed name> <n>'. The window is set in minutes.
        Stories older than the window will not be shown.
        """
        try:
            feed_name, age_filter_setting = clean_args(args)
            feed = self.get_feed_by_name(feed_name)
            feed.set_age_filter(int(age_filter_setting))
            self._save_feed_data()
            self.send_groupchat_message(messages.OKAY)
        except IOError:
            pass
        except (ValueError, exceptions.UnknownFeedError):
            self.send_groupchat_message(messages.SET_AGE_FILTER_HELP)

    def send_groupchat_message(self, text):
        """ Send a message to the chatroom. """
        self.send(self.chatroom, text, message_type='groupchat')


def clean_args(args):
    """ Utility function that removes jabberbot formatting. """
    return str(args).strip().split()


def utc_now():
    """
    Return a timezone-aware datetime object, representing this instant in time.

    The timezone of the object will be UTC.
    """
    return utc.localize(datetime.now())


def struct_to_datetime(time_struct):
    """
    Given a time.struct_time instance, return a datetime.datetime instance.

    See Also:
        http://stackoverflow.com/a/1697838/2557196
        https://docs.python.org/2/library/time.html#time.struct_time
    """
    return utc.localize(datetime(*time_struct[:6]))


def time_delta_from_now(prev_time):
    """ Given a time `then`, returns the difference between `now` and `then`. """
    return utc_now() - prev_time


def pub_time_to_string(time_struct):
    """ Given a time_struct, return a humanized string representing the elapsed time. """
    publication_time = struct_to_datetime(time_struct)
    delta = time_delta_from_now(publication_time)
    return humanize.naturaltime(delta).capitalize()
