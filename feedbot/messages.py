""" Message strings that are sent to the chatroom. """

ADD_FILTER_HELP = '\n'.join([
    'To filter an RSS feed use: `/filter <name> not: <search term>`,',
    'where <name> is a currently monitored RSS feed name.',
    'Eg: `/filter woopList not: acme microsoft oogle`.',
    'will filter out articles with the phrase `acme microsoft oogle`',
    'from the `woopList` feed. Filters are case insensitive.'])

ADDED_FILTER = 'Added: {filter_type} `{filter_term}` filter to the {feed_name} feed.'

CURRENTLY_MONITORING = 'Currently monitoring: '

DATA_DIR_ERROR = "Could not find a $HOME env var, pleas set $FEEDBOT_DATA_DIRECTORY env var. Using /tmp/feedbot for now."

ENTRY_FIELD_TEMPLATE = '<b>{field_name} :</b>  {field_value}'

ENTRY_PUBLISHED_FIELD_TEMPLATE = ' -= About {publication_time} =- \n'

ENTRY_SEPERATOR = '----------\n\n'

FEED_ADD_HELP = '\n'.join([
    'To add an RSS feed for monitoring, call `/add_feed` with a `name` and URL.',
    'Eg: `/add_feed foobar http://foobar.org/rss/quux.rss`.'])

FEED_SCHEDULE_HELP = '\n'.join([
    'To schedule a RSS feed, call `/schedule_feed` with a `name` and a number of minutes.',
    'Eg: `/schedule_feed foobar 15`.'])

FEED_REMOVE_HELP = '\n'.join([
    'Sorry, couldn\'t find that feed.',
    'To remove an RSS feed call `/remove_feed` with <feed_name> or <feed_url>.',
    'Eg: `/remove_feed fooFeed` or `/remove_feed http://fooFeed.com/rss`'])


FEED_DATA_LOAD_ERROR = 'Error attempting to load feed data from: {path}'

FEED_EXISTS_ERROR = 'Already monitoring: {url} with name: {name}.'

FEED_PARSE_ERROR = 'There was a problem parsing that url. Feedparser returned with: {error}'

FEED_NOT_FOUND_ERROR = 'Sorry, couldn\'t find that RSS feed. You may want to use /list_feeds.'

FEED_SAVE_DATA_ERROR = '\n'.join([
    'Error attempting to save feed data to disc, encountered:',
    '`{error}`, when trying to save changes to `{data_path}` data file.'])


FEED_DELETED = 'You\'re dead to me, {feed_name}. Dead.'

FEED_HEADER = '<b>Stories from: <i>{feed_name}</i></b> \n\n'

FEEDS_DO_NOT_EXIST = '\n'.join([
    'Not currently monitoring any feeds. Add some with the `/add_feed` command!',
    '',
    '<The bot looks away and mutters `Feed me, Seymour.. feed me..`>'])


FEED_NAME_URL_TEMPLATE = '<b>{name}:</b>  {url}'

FEED_SEPERATOR = '===========\n\n'

FILTER_HEADER = '\tFilters in effect:\n'

FILTER_KEY_VALUE = '\t{key}:  {filter}'

OKAY = 'Okay!'

NEWLINE = ' \n'

NO_NEW_ENTRIES = '<b>No new entries for the <i>{feed_name}</i> feed.</b>'

SET_AGE_FILTER_HELP = '\n'.join([
    'Set the time_window for RSS stories to be displayed in minutes with: ',
    '`/set_age_filter <feed name> <n>` where n is the number of minutes.'])


REMOVE_FILTER_HELP = '\n'.join([
    'To remove a filter from FooFeed, call `/remove_filter FooFeed <filter id>`.',
    'Eg: `/remove_filter FooFeed 3`.'])

REMOVED_FILTER = 'Removed \'{filter}\' filter from {feed} feed.'

SORRY = 'Sorry?'

UNKNOWN_FILTER_ERROR = 'Unknown filter type.'
