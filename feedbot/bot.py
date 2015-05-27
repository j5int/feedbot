""" Contains the FeedBot class.  """

from __future__ import absolute_import
from abc import abstractmethod
from collections import deque
from datetime import (
    datetime,
    timedelta,
)
import json
import logging
import repr
import sys

from bs4 import BeautifulSoup
import feedparser
import humanize
from jabberbot import (
    JabberBot,
    botcmd
)
from pytz import utc

# TODO: rename to exceptions
from . import bot_exceptions as exceptions
from . import messages
from . import settings


logger = logging.getLogger(__name__)


class Feed(object):
    """
    A Feed provides a filtered stream of story entries.

    Feeds use the Universal Feed Parser module to download and parse syndicated
    feeds. Feeds must be initialized with a `name` and `URL` where the name is a
    human- readable label which will be displayed in channel and the url points
    to resource the Feed Parser will consume.

    The FeedBot will create Feed instances in response to channel activity.

    Args:
        name (string): A human readable name for this feed, to display in the
        chat channel.
        url (string): The URL this feed will be parsing.
        filters: An iterable container of `feedbot.filters`.

    See Also:

        Universal Feed Parser
            http://pythonhosted.org//feedparser/introduction.html
    """
    def __init__(self, name, url, filters=None):
        self.name = name
        self.url = url
        if not filters:
            filters = []
        self.filters = filters

    def __repr__(self):
        components = repr.repr(self.filters)
        return '{0}(name={1}, url={2}, filters={3})'.format(type(self).__name__, self.name, self.url, components)

    def _accept_entry(self, entry):
        """ Given an RSS entry returns True if it passes all the Feed's filters. """
        return all([feed_filter.discard_entry(entry) is False for feed_filter in self.filters])

    def to_dict(self):
        """ Serialize a Feed instance and its Filters to a dict. """
        data_dict = {
            'class': 'Feed',
            'name': self.name,
            'url': self.url,
            'filters': [feed_filter.to_dict() for feed_filter in self.filters]}
        return data_dict

    @classmethod
    def from_dict(cls, data_dict):
        """
        Given a data_dict, attempts to construct and return a Feed instance.

        Args:
            data_dict: a serialization dictionary.

        Raises:
            DeserializationError.
        """
        try:
            assert data_dict['class'] == 'Feed'
            feed_filters = []
            for serialized_filter in data_dict['filters']:
                filter_instance = FilterBase.from_dict(serialized_filter)
                feed_filters.append(filter_instance)
            return Feed(data_dict['name'], data_dict['url'], filters=feed_filters)
        except (KeyError, ValueError, AssertionError):
            raise exceptions.DeserializationError("Error parsing Filter json data.")

    def get_raw_feed(self):
        """
        Return the unfiltered feed.

        Raises:
            BadFeedData: If Feed Parser detects a feed error.
        """
        feed = feedparser.parse(self.url)
        # feed.bozo indicates that the feed's XML data is malformed
        # See: http://pythonhosted.org//feedparser/bozo.html
        if not feed.bozo:
            return feed
        raise exceptions.FeedDataError(feed.bozo_exception.message)

    def get_filtered_feed(self):
        """
        Return a list of filtered entries.

        Raises:
            FeedDataError: If there are no entries in the steam.
        """
        stream = self.get_raw_feed()
        if 'entries' in stream:
            return [entry for entry in stream.entries if self._accept_entry(entry)]
        raise exceptions.FeedDataError("Could not find entries in this stream.")

    def add_filter(self, feed_filter):
        """ Given a filter, add it to the feed. """
        self.filters.append(feed_filter)

    def remove_filter(self, feed_filter):
        """ Remove a filter, remove it from the feed. """
        if feed_filter == getattr(self, 'age_filter', None):
            self.age_filter = None
        self.filters.remove(feed_filter)

    def get_filters(self):
        """ Return a list of this Feed's filters. """
        return [feed_filter for feed_filter in self.filters]

    def get_filter_by_key(self, filter_index):
        return self.filters[filter_index]

    def set_age_filter(self, time_period):
        """
        Set the time period for an AgeFilter. Adds a filter if necessary.

        Note:
            This should be the main entry point for creating/setting AgeFilters,
            because it usually makes sense to only have one AgeFilter per Feed.
        """
        if getattr(self, 'age_filter', None):
            self.age_filter.set_window(time_period)
        else:
            self.age_filter = AgeFilter(time_period)
        self.filters.append(self.age_filter)


class FilterBase(object):
    """ Base class for filters."""
    def __init__(self, terms):
        self.terms = terms.lower()

    @abstractmethod
    def discard_entry(self, entry):
        """ Given an entry, return False if we don't want to display it. """

    def to_dict(self):
        return {'class': type(self).__name__}

    @staticmethod
    def from_dict(serialization_dict):
        """ Given a dictionary of args, kwargs and the class name, returns a filter.

        Args:
            serialization_dict (dict): Should contain the arguments and keyword
            arguments needed to construct the specific filter desired, along with
            that filter's name.

            The exact structure should be:
            {
                'class': <filter class name>,
                'args': <list of filter arguments>,
                'kwargs': <dict of keyword arguments>
            }

        Example:
            >>> FilterBase.from_dict({'class': 'NotFilter', 'args': ['foobar quuxquux']})
            >>> NotFilter('foobar quuxquux')
        """
        args = serialization_dict.get('args', [])
        kwargs = serialization_dict.get('kwargs', {})
        cls = FilterBase._get_filter_class(serialization_dict.get('class'))
        try:
            return cls(*args, **kwargs)
        except TypeError:
            raise ValueError("Bad args, kwargs or class name.")

    @staticmethod
    def _get_filter_class(filter_class_name):
        """ Given the name of a filter class, attempts to return it. """
        feedbot_module = sys.modules[__name__]
        return getattr(feedbot_module, filter_class_name)


# Change name to ExcludeFilter
class NotFilter(FilterBase):
    """
    Blacklists a term from the Feed.

    Initialize NotFilter with a string. If the string is present in an entry's
    summary or title, it will remove it from the Feed.
    """
    def __repr__(self):
        return "{0}('{1}')".format(type(self).__name__, self.terms)

    def discard_entry(self, entry):
        """ Given an entry, returns True if the blacklisted string is in the entry. """
        string = "%s %s " % (entry.summary.lower(), entry.title.lower())
        return self.terms in BeautifulSoup(string).get_text()

    def to_dict(self):
        """ Serialize the filter to a dict. """
        serialized_data = super(NotFilter, self).to_dict()
        serialized_data['args'] = [self.terms]
        return serialized_data


class AgeFilter(FilterBase):
    """
    Blacklists entries that are older than the AgeFilter's minutes.

    Initialize an AgeFilter with a dictionary of {minutes: <int>}.
    """
    def __init__(self, minutes=None):
        self.window = timedelta(minutes=minutes or 5)

    def __repr__(self):
        return "{0}({1})".format(type(self).__name__, self.window)

    def discard_entry(self, entry, fail_closed=False):
        """
        Return if the entry was published before the filter's age cutoff.

        If the entry has no `published_parsed` attribute, the filter can either
        fail-open (allow the entry to continue through) or fail-closed (discard
        the entry). This behavior is specified by the fail_closed kwarg, which
        defaults to False.
        """
        if 'published_parsed' in entry:
            published_time = struct_to_datetime(entry['published_parsed'])
            return utc_now() - published_time >= self.window
        return fail_closed

    def to_dict(self):
        """ Serialize the filter to a dict. """
        serialized_data = super(AgeFilter, self).to_dict()
        serialized_data['kwargs'] = {'minutes': self.get_window()}
        return serialized_data

    def set_window(self, minutes):
        """ Set the time window in minutes. """
        self.window = timedelta(minutes=minutes)
        return True

    def get_window(self):
        """ Get the time window in minutes. """
        return self.window.seconds/60.0


ALLOWED_FILTER_TYPES = ['not', 'age']


# Implement __iter__ and __getitem__ on FeedBot to make it dict-like?
class FeedBot(JabberBot):
    """ A Jabberbot for monitoring RSS/Atom feeds. """

    """
    (This second docstring is to prevent jabberbot from adding the rest of the
     documentation in the channel when there's a `/help` command.)

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
    def __init__(self, chatroom, bot_name, bot_password, *args, **kwargs):
        self.chatroom = chatroom
        self.bot_name = bot_name
        self.bot_password = bot_password
        # self.server = kwargs.pop('server')
        super(FeedBot, self).__init__(bot_name, bot_password, *args, **kwargs)
        self._rss_data_file_path = settings.FEEDBOT_DATAFILE_PATH
        self.feeds = self._load_feed_data()
        self.entry_history = deque(maxlen=settings.FEED_HISTORY_QUEUE_LENGTH)

    def __repr__(self):
        return "{0}({1}, {2})".format(type(self).__name__, self.chatroom, self.bot_name)

    def _add_entry_to_history(self, entry):
        if entry.link not in self.entry_history:
            self.entry_history.append(entry.link)

    def _seen_entry(self, entry):
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
            with open(settings.FEEDBOT_DATAFILE_PATH, 'r') as file:
                serialized_feed_data = json.load(file)
                for feed_data in serialized_feed_data:
                    deserialized_feed = Feed.from_dict(feed_data)
                    feeds[deserialized_feed.name] = deserialized_feed
        except:
            message = messages.FEED_DATA_LOAD_ERROR.format(path=settings.FEEDBOT_DATAFILE_PATH)
            self.send_groupchat_message(message)
        return feeds

    def _save_feed_data(self):
        """
        Attempt to pickle and save the feed data to a storage file.

        Note:
            If any exceptions are raised in this method they are caught, a standard
            error message is sent to the channel, and an IOError is raised.
        """
        try:
            feed_data = [feed.to_dict() for feed in self.feeds.values()]
            with open(settings.FEEDBOT_DATAFILE_PATH, 'r+') as file:
                file.write(json.dumps(feed_data))
                return True
        except Exception as e:
            error = getattr(e, 'message', '')
            message = messages.FEED_SAVE_DATA_ERROR.format(
                error=error,
                data_path=settings.FEEDBOT_DATAFILE_PATH
            )
            self.send_groupchat_message(message)
            raise IOError()

    def get_feed_urls(self):
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
            del(self.feeds[feed])
            message = messages.FEED_DELETED.format(feed_name=feed)
        elif feed in self.get_feed_urls():
            feed_name = self._url2name(feed)
            del(self.feeds[feed_name])
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
                message = messages.ADDED_FILTER.format(filter_type=filter_type, filter_term=filter_term, feed_name=feed_name)
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
                entries_limit = settings.DEFAULT_STORY_LIMIT

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
        self.send_groupchat_message(messages.FEED_HEADER.format(feed_name=feed_name))
        for entry in entries:
            if self._seen_entry(entry):
                continue
            self._add_entry_to_history(entry)
            self._print_entry(entry)
            self.send_groupchat_message(messages.ENTRY_SEPERATOR)

    def _print_entry(self, entry):
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

if __name__ == '__main__':
    chatroom = settings.CHATROOMS['default']
    rssbot = FeedBot(
        chatroom,
        settings.BOT_USERNAME,
        settings.BOT_PASSWORD,
        server=settings.SERVER_IP,
        command_prefix=settings.COMMAND_PREFIX,
    )

    logger.info("RssBot is alive")
    rssbot.muc_join_room(chatroom, settings.BOT_NICKNAME)
    rssbot.serve_forever()
    logger.info("RssBot is dead")
