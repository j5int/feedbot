""" Feedbot Exceptions. """


class FeedbotError(Exception):
    """ Base class for all feedbot errors. """


class DeserializationError(FeedbotError):
    """ Raise if there is an error parsing a serialized Feed. """


class FeedDataError(FeedbotError):
    """ Raise if there was an error parsing a Feed. """


class UnknownFeedError(FeedbotError):
    """ Raise if client code asks for an unknown Feed. """
