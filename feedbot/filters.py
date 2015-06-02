""" Contains the Filter classes. """

from __future__ import absolute_import
from abc import abstractmethod
from datetime import timedelta
import sys

from bs4 import BeautifulSoup


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
        from .bot import struct_to_datetime, utc_now

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
