from datetime import timedelta

from feedparser import FeedParserDict
from mock import (
    Mock,
    patch
)
import pytest

from .. import messages
from ..bot import (
    FeedBot,
    utc_now,
)
from ..feed import Feed
from ..filters import (
    AgeFilter,
    FilterBase,
    NotFilter,
)
from ..exceptions import FeedDataError

# Feedparser transforms many datetime strings into a tuple, see:
# http://pythonhosted.org//feedparser/date-parsing.html
now = utc_now()
NOW_TUPLE = (now.year, now.month, now.day, now.hour, now.minute, now.second)

GOOD_FEED_ENTRY = FeedParserDict({
    'summary': 'perfectly innocent test summary',
    'title': 'look, a title',
    'published_parsed': NOW_TUPLE,
})

FOOBAR_FEED_ENTRY = FeedParserDict({
    'summary': 'foobar',
    'title': 'a title',
    'published_parsed': NOW_TUPLE,
})

STALE_FEED_ENTRY = FeedParserDict({
    'summary': 'a valid summary',
    'title': 'a title',
    'published_parsed': (2000, 1, 1, 1, 1, 1),
})


class TestSetupMixin(object):
    """ Class to setup the fixture for Feedbot tests. """
    def setup(self):
        self.filter_term = 'foobar'
        self.not_filter = NotFilter(self.filter_term)

        self.age_filter_window = {'minutes': 25}
        self.age_filter = AgeFilter(**self.age_filter_window)

        self.filters = [self.age_filter, self.not_filter]
        self.feed_name = 'Test-Feed'
        self.feed_url = 'http://test.org/fake/rss/feed/url.xml'
        self.feed = Feed(self.feed_name, self.feed_url, filters=self.filters)


class TestFilters(TestSetupMixin, object):
    """ Tests for the feedbot Filters. """
    def test_not_filter(self):
        """ Assert that NotFilters discard entries correctly. """
        assert self.not_filter.discard_entry(FOOBAR_FEED_ENTRY) is True
        assert self.not_filter.discard_entry(GOOD_FEED_ENTRY) is False


class TestFeed(TestSetupMixin, object):
    """ Tests for the feedbot Feed class. """
    def test_accept_entry(self):
        """ Assert that the Feed._accept_entry method works. """
        assert self.feed._accept_entry(GOOD_FEED_ENTRY) is True
        assert self.feed._accept_entry(FOOBAR_FEED_ENTRY) is False
        assert self.feed._accept_entry(STALE_FEED_ENTRY) is False

    @patch('feedbot.bot.Feed.get_raw_feed')
    def test_get_filtered_stream(self, feed):
        """ Assert that feed returns a filtered stream. """
        feed.return_value = FeedParserDict({'entries': [GOOD_FEED_ENTRY, FOOBAR_FEED_ENTRY, STALE_FEED_ENTRY]})
        assert self.feed.get_filtered_feed() == [GOOD_FEED_ENTRY]

    @patch('feedbot.bot.Feed.get_raw_feed')
    def test_get_filtered_stream_raises_stream_error(self, feed):
        """ Assert FeedDataError is raised if there are no entries. """
        feed.return_value = FeedParserDict()
        with pytest.raises(FeedDataError):
            self.feed.get_filtered_feed()

    def test_add_filter(self):
        """ Assert that new Filters are added to the Feed. """
        number_of_filters = len(self.feed.get_filters())
        new_filter = NotFilter("bad juju")
        self.feed.add_filter(new_filter)

        assert len(self.feed.get_filters()) == number_of_filters + 1
        assert new_filter in self.feed.get_filters()

    def test_remove_filter(self):
        """ Assert that Filters can be removed from the Feed. """
        number_of_filters = len(self.feed.get_filters())
        self.feed.remove_filter(self.age_filter)

        assert self.age_filter not in self.feed.get_filters()
        assert len(self.feed.get_filters()) == number_of_filters - 1
        assert self.not_filter in self.feed.get_filters()

    def test_get_filters(self):
        """ Assert that Feed returns a list of its filters. """
        assert self.feed.get_filters() == self.filters

    def test_get_filter_by_key(self):
        """ Assert that Feeds return a specific filter. """
        for index, feed_filter in enumerate(self.filters):
            assert self.feed.get_filter_by_key(index) == feed_filter


class TestFeedBot(object):
    """ Tests for the FeedBot class. """
    @patch('feedbot.bot.FeedBot._init_data_dir')  # prevents tests from writing files.
    @patch('feedbot.bot.FeedBot._load_feed_data')
    @patch('feedbot.bot.FeedBot.connect')
    def setup(self, Jabberbot, load_data, touch_file_system):
        load_data.return_value = {}
        self.bot = FeedBot('test chatroom', 'test bot name', 'test bot password', )
        assert not self.bot.feeds, 'Feedbot tests may be accessing real saved data. Exiting!'

        self.first_feed = Feed('First-test-Feed', 'http://test.org/fake/rss/feed/url.xml')
        self.not_filter = NotFilter('foobar')
        self.first_feed.add_filter(self.not_filter)

        self.second_feed = Feed('Second-test-Feed', 'http://another_test_fake.com/fake/rss/feed/url.xml')
        self.feeds = {feed.name: feed for feed in [self.first_feed, self.second_feed]}
        self.bot.feeds = self.feeds

    def test_get_feed_urls(self):
        """ Assert that we can get feed URLs from the bot. """
        assert len(self.bot.get_feed_urls()) == 2
        assert self.first_feed.url in self.bot.get_feed_urls()
        assert self.second_feed.url in self.bot.get_feed_urls()

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_feed_existing_name(self, send_to_channel):
        """ Assert that the bot enforces unique feed names. """
        feed_name = self.first_feed.name
        feed_url = self.first_feed.url
        bot_command = "{name} {url}".format(name=feed_name, url=feed_url)
        self.bot.add_feed("", bot_command)

        EXPECTED_MESSAGE = messages.FEED_EXISTS_ERROR.format(name=feed_name, url=feed_url)
        send_to_channel.assert_called_with(EXPECTED_MESSAGE)

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_feed_existing_url(self, send_to_channel):
        """ Assert that the bot enforces unqiue URLs. """
        feed_name = "a-unique-feed-name"
        feed_url = self.first_feed.url
        bot_command = "{name} {url}".format(name=feed_name, url=feed_url)
        self.bot.add_feed("", bot_command)

        EXPECTED_MESSAGE = messages.FEED_EXISTS_ERROR.format(name=feed_name, url=feed_url)
        send_to_channel.assert_called_with(EXPECTED_MESSAGE)

    @patch('feedbot.bot.Feed')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_bad_feed(self, send_to_channel, Feed):
        """ Assert that the channel is alerted if there's a feed error. """
        mock_feed = Mock()
        EXCEPTION_MESSAGE = "foobar"
        mock_feed.get_raw_feed.side_effect = FeedDataError(EXCEPTION_MESSAGE)
        Feed.return_value = mock_feed
        self.bot.add_feed("", "unique-name http://www.valid.url.com")

        EXPECTED_MESSAGE = messages.FEED_PARSE_ERROR.format(error=EXCEPTION_MESSAGE)
        send_to_channel.assert_called_with(EXPECTED_MESSAGE)

    @patch('feedbot.bot.Feed')
    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_feed_succeeds(self, send_to_channel, save_data, Feed):
        """ Assert that valid args add a feed to the bot. """
        EXPECTED_FEED_NAME = "unique-name"
        EXPECTED_FEED_URL = "http://www.valid.url.com"
        Feed.return_value = Mock(name=EXPECTED_FEED_NAME, url=EXPECTED_FEED_URL)
        self.bot.add_feed("", "unique-name http://www.valid.url.com")

        assert EXPECTED_FEED_NAME in self.bot.feeds
        assert EXPECTED_FEED_URL in self.bot.get_feed_urls()
        send_to_channel.assert_called_with(messages.OKAY)

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_list_feeds(self, send_to_channel):
        """ Assert that list filters sends the right messages to the channel. """
        self.bot.list_feeds("", "")

        feeds = [self.first_feed, self.second_feed]
        for feed in feeds:
            send_to_channel.assert_any_call(messages.FEED_NAME_URL_TEMPLATE.format(name=feed.name, url=feed.url))
            for key, _filter in enumerate(feed.filters):
                send_to_channel.assert_any_call(messages.FILTER_KEY_VALUE.format(key=key, filter=_filter))

    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_feed_by_name(self, send_to_channel, _save_feed_data):
        """ Assert that feeds can be removed by name. """
        name = str(self.first_feed.name)
        self.bot.remove_feed("", name)

        send_to_channel.assert_called_with(messages.FEED_DELETED.format(feed_name=name))
        assert self.first_feed not in self.bot.feeds

    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_feed_by_url(self, send_to_channel, _save_feed_data):
        """ Assert that feeds can be removed by url. """
        url = str(self.first_feed.url)
        name = str(self.first_feed.name)
        self.bot.remove_feed("", url)

        send_to_channel.assert_called_with(messages.FEED_DELETED.format(feed_name=name))
        assert self.first_feed not in self.bot.feeds

    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_unknown_feed(self, send_to_channel, _save_feed_data):
        """ Assert that remove_feed errors trigger the help message. """
        self.bot.remove_feed("", "")

        send_to_channel.assert_called_with(messages.FEED_REMOVE_HELP)

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_filter_invalid(self, send_to_channel):
        """ Assert that help message is sent. """
        self.bot.add_filter("", "foobar'd-command")
        send_to_channel.assert_called_with(messages.ADD_FILTER_HELP)

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_filter_unknown_type(self, send_to_channel):
        """ Assert that an invalid filter type is handled. """
        add_filter_command = "{feed_name} {filter_type}: {terms}"

        self.bot.add_filter("", add_filter_command.format(feed_name=self.first_feed.name, filter_type="quuxFilter", terms="bar baz"))
        send_to_channel.assert_called_with(messages.UNKNOWN_FILTER_ERROR)

    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_add_not_filter(self, send_to_channel, _save_feed_data):
        """ Assert that a filter can be added to a field. """
        FILTER_TERM = "bar baz"
        add_not_filter_command = "{filter_name} not: {term}".format(filter_name=self.second_feed.name, term=FILTER_TERM)
        number_of_filters = len(self.second_feed.filters)
        self.bot.add_filter("", add_not_filter_command)
        EXPECTED_MESSAGE = messages.ADDED_FILTER.format(filter_type='not', filter_term=FILTER_TERM, feed_name=self.second_feed.name)

        send_to_channel.assert_called_with(EXPECTED_MESSAGE)
        assert number_of_filters + 1 == len(self.second_feed.filters)

    def test_get_feeds(self):
        """ Assert that we can get the feed instances. """
        assert self.bot.get_feeds() == self.feeds.values()

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_filter_invalid(self, send_to_channel):
        """ Assert that a help message is sent for removing a filter. """
        self.bot.remove_filter("", "")
        send_to_channel.assert_called_with(messages.REMOVE_FILTER_HELP)

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_filter_bad_name(self, send_to_channel):
        """ Assert that a help message is sent when there's an unrecognized feed. """
        self.bot.remove_filter("", "fooFeed 3")
        send_to_channel.assert_called_with(messages.REMOVE_FILTER_HELP)

    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_filter_bad_index(self, send_to_channel):
        """ Assert that a help message is sent when there's a bad index. """
        # We are going to do two calls, one with a negative index and one with an
        # index that is two large.
        remove_filter_command = "{feed_name} {feed_index}".format(feed_name=self.first_feed.name, feed_index=-1)
        self.bot.remove_filter("", remove_filter_command)

        filter_index = len(self.first_feed.get_filters())
        remove_filter_command = "{feed_name} {feed_index}".format(feed_name=self.first_feed.name, feed_index=filter_index+1)
        self.bot.remove_filter("", remove_filter_command)

        send_to_channel.assert_called_with(messages.REMOVE_FILTER_HELP)
        assert len(send_to_channel.mock_calls) == 2

    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_remove_filter(self, send_to_channel, _save_feed_data):
        """ Assert that a filter can be removed. """
        feed_index = len(self.first_feed.get_filters())
        remove_filter_command = "{feed_name} {feed_index}".format(feed_name=self.first_feed.name, feed_index=feed_index-1)
        EXPECTED_MESSAGE = messages.REMOVED_FILTER.format(filter=self.not_filter, feed=self.first_feed.name)
        self.bot.remove_filter("", remove_filter_command)

        assert feed_index-1 == len(self.first_feed.get_filters())
        assert self.not_filter not in self.first_feed.get_filters()
        send_to_channel.assert_called_with(EXPECTED_MESSAGE)

    @patch('feedbot.bot.FeedBot._save_feed_data')
    @patch('feedbot.bot.FeedBot.send_groupchat_message')
    def test_set_age_filter(self, send_to_channel, _save_feed_data):
        """ Assert that we can set the AgeFilter. """
        MINUTES = 20
        set_age_filter_command = "{feed_name} {minutes}".format(feed_name=self.second_feed.name, minutes=MINUTES)
        self.bot.set_age_filter("", set_age_filter_command)
        expected_age_filter = [_filter for _filter in self.second_feed.filters if type(_filter) == AgeFilter]

        assert len(expected_age_filter) == 1
        assert expected_age_filter[0].get_window() == MINUTES


def filter_list_sorter(feed_filter):
    """ Provide a key to sort a list of feed filters. """
    return feed_filter['class']


class TestSerialization(TestSetupMixin, object):
    """ Tests that exercise the to_dict/from_dict methods. """
    def test_abstract_filter_to_dict(self):
        """ Assert that the FilterBase returns the correct class name. """
        test_filter = FilterBase('')
        assert test_filter.to_dict() == {'class': 'FilterBase'}

    def test_get_filter_class(self):
        """ Assert that FilterBase returns a class given a class name. """
        assert FilterBase._get_filter_class('NotFilter') is NotFilter
        assert FilterBase._get_filter_class('AgeFilter') is AgeFilter

    def test_notfilter_from_dict(self):
        """ Assert that a NotFilter can be reconstructed from a dict. """
        filter_dict = {'class': 'NotFilter', 'args': [self.filter_term]}
        not_filter = FilterBase.from_dict(filter_dict)
        assert type(not_filter) is NotFilter
        assert not_filter.terms == self.filter_term

    def test_notfilter_to_dict(self):
        """ Assert that a NotFilter can be serialized to a dict. """
        expected_dict = {'class': 'NotFilter', 'args': [self.filter_term]}
        assert expected_dict == self.not_filter.to_dict()

    def test_agefilter_from_dict(self):
        """ Assert that an AgeFilter can be reconstructed from a dict. """
        filter_dict = {'class': 'AgeFilter', 'kwargs': self.age_filter_window}
        age_filter = FilterBase.from_dict(filter_dict)
        assert type(age_filter) is AgeFilter
        assert age_filter.window == timedelta(**self.age_filter_window)

    def test_agefilter_to_dict(self):
        """ Assert that an AgeFilter can be serialized to a dict. """
        expected_dict = {'class': 'AgeFilter', 'kwargs': self.age_filter_window}
        assert expected_dict == self.age_filter.to_dict()

    def test_feed_to_dict(self):
        """ Assert that a Feed can be serialized to a dict. """
        # Serializing a Feed to dict returns a list of serialized filters. This
        # fixture sorts the serialized filters by class name, to prevent false
        # failures.
        filters = [self.not_filter.to_dict(), self.age_filter.to_dict()]
        sorted_filters = sorted(filters, key=filter_list_sorter)
        expected_dict = {
            'class': 'Feed',
            'name': self.feed_name,
            'url': self.feed_url,
            'filters': sorted_filters
        }
        actual_dict = self.feed.to_dict()
        actual_filters = actual_dict['filters']
        sorted_actual_filters = sorted(actual_filters, key=filter_list_sorter)
        actual_dict['filters'] = sorted_actual_filters

        assert expected_dict == actual_dict

    def test_feed_from_dict(self):
        """ Assert that a Feed can be reconstructed from a dict. """
        feed_dict = {
            'class': 'Feed',
            'name': self.feed_name,
            'url': self.feed_url,
            'filters': [self.not_filter.to_dict(), self.age_filter.to_dict()]
        }
        feed = Feed.from_dict(feed_dict)
        assert feed.name == self.feed_name
        assert feed.url == self.feed_url
        assert len(feed.filters) == 2

        actual_feed_filters = feed.filters
        assert NotFilter in [type(feed_filter) for feed_filter in actual_feed_filters]
        assert AgeFilter in [type(feed_filter) for feed_filter in actual_feed_filters]
