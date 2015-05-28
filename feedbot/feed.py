""" Contains the Feed class. """

from __future__ import absolute_import
import repr

import feedparser

from . import exceptions
from .filters import (
    AgeFilter,
    FilterBase,
)


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
