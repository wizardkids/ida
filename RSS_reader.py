"""
RSS_reader.py

Richard E. Rawson
2019-06-09

Program Description:

Features:
-- Add, edit, delete URLs
-- convert URL to RSS
-- name the feed with your own name
-- keep track of how frequently the feed is updated
-- keep track of last time the feed was updated
-- notify if a feed is unreachable
-- display each RSS site and a list of its titles
-- order the titles from newest to oldest
-- load a title in a browser
-- provide a mechanism for selecting a particular title to read
-- mark a read title as "read"
-- manually mark a feed title as read or unread
-- automatically update all feeds when app starts update
-- background mode updates feed in the background
-- group feeds so they are easier to find
-- import/export
-- list feeds by group/title
-- save a feed to OneNote

"""


import re
from pprint import pprint

import feedparser
import requests
import urlwatch
import webbrowser
import os
import textwrap


def get_rss_status(url):
    """
    Get the content from a URL.
    """
    # set the headers like we are a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    # download the url
    r = requests.get(url, headers=headers)
    # print(r.status_code, r.headers['content-type'], r.encoding)
    # print()
    # txt = r.text
    return r.status_code


def show_HTML_string(HTML_string):
    """
    Given a string, convert the string into an HTML file (temp.html) and display in a browser window.
    """
    path = os.path.abspath('temp.html')
    url = 'file://' + path

    with open(path, 'w') as f:
        f.write(HTML_string)
    webbrowser.open(url)
    return None


def get_latest_feed(rss):
    """
    Get a news feed.
    """
    try:
        newsfeed = feedparser.parse(rss)
        # entries is the only dict in [newsfeed_keys]
        newsfeed_keys = ['feed', 'entries', 'bozo', 'headers', 'updated',
                         'updated_parsed', 'href', 'status', 'encoding', 'version', 'namespaces']

        entries_keys = ['title', 'title_detail', 'links', 'link', 'comments', 'published', 'published_parsed', 'authors', 'author',
                        'author_detail', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'wfw_commentrss', 'slash_comments', 'media_content']

        # print site information
        # print('\n\n')
        # print('\nSite title:', newsfeed['feed']['title'])
        # print('\nSite link:', newsfeed['feed']['link'])
        # print('\nSite subtitle:', newsfeed['feed']['subtitle'])
        # print('\nSite updated:', newsfeed['feed']['updated'])

        # print page information
        # print('\n\n')
        # print('\nPage title:', newsfeed['entries'][0]['title'])
        # print('\nPage id:', newsfeed['entries'][0]['id'])
        # print('\nPage published:', newsfeed['entries'][0]['published'])

        # get the content for first item in [entries]
        c = '<html><body>' + \
            '<H1>' + newsfeed['entries'][0]['title'] + '</H1>' + \
            newsfeed['entries'][0]['content'][0]['value'] + '</body></html>'
    except IndexError:
        return rss

    return newsfeed['entries'][0]['link']


def show_lastest_rss(rss):
    """
    Show the most recent feed in a browser window.
    """
    try:
        webbrowser.open(rss)
    except TypeError:
        pass
    return


def import_OPML():
    """
    Parse an OPML file and put RSS addresses in [myFeeds]. If no file is entered, process is aborted. If FileNotFoundError is generated, notify user and <continue>. [myFeeds] is written to myFeeds.txt. This file is overwritten each time an OPML file is read.
    """
    while True:
        # file = input('Name of OPML file to import: ')
        file = 'feedly.opml'
        if file:
            try:
                with open(file, 'r') as f:
                    feedly = f.readlines()
            except FileNotFoundError:
                print('\n', file, ' not found.\n')
                continue

            # extract the RSS address from the line
            rem = re.compile(r"""
                            (.xmlUrl=\")(?P<RSS>.*)(\"\s)
                            """, re.X)

            myFeeds = []
            for ndx, line in enumerate(feedly):
                m = re.search(rem, line)
                if m:
                    # print(m.group('RSS'))
                    myFeeds.append(m.group('RSS'))
            break
        else:
            print('Aborted.')
            return

    # with confirmation, write myFeeds to a file of the same name
    r = input('Overwrite "myFeeds.txt"? (YES/ABORT) ')
    if r.upper() == 'YES':
        print('Writing to myFeeds.txt...')
        with open('myFeeds.txt', 'w') as f:
            for line in myFeeds:
                f.write(line + '\n')
    else:
        print('Aborted.')

    return


def fold(txt):
    """
    Textwraps 'txt' 45 characters wide.
    """
    return textwrap.fill(txt, width=45)


def about():
    """
    Information about the author and product.
    """
    print('='*45)

    txt1 = 'ida - a small news feed reader\n' + 'version: ' + \
        version_num[0:18] + '\n' + \
        ' python: v3.7\n' + ' author: Richard E. Rawson\n\n'

    txt2 = 'ida is named after Ida B. Wells (July 16, 1862 to March 25, 1931), was an African-American journalist, abolitionist and feminist who led an anti-lynching crusade in the United States in the 1890s. She went on to found and become integral in groups striving for African-American justice.'

    print('\n'.join([fold(txt1) for txt1 in txt1.splitlines()]))
    print('\n'.join([fold(txt2) for txt2 in txt2.splitlines()]))

    print('='*45)
    return


def get_revision_number():
    """
    Manually run this function to get a revision number by uncommenting the first line of code under "if __name__ == '__main__':"
    """
    from datetime import datetime

    start_date = datetime(2019, 6, 10)
    tday = datetime.today()
    revision_delta = datetime.today() - start_date

    print("\nREVISION NUMBER:", revision_delta.days)
    print('This is the number of days since ', start_date, '\n',
          'the date that the first version of this\n', 'calculator was launched.\n\n', sep='')
    return None


if __name__ == '__main__':

    # get_revision_number()
    version_num = '0.1 rev0'
    print('ida ' + version_num[0:3] + ' - a small news feed reader')

    # about this project
    about()

    # import OPML file and store RSS addresses in myFeeds.txt
    # import_OPML()

    # rss = get_latest_feed('https://hebendsdown.wordpress.com/feed/')

    # if get_rss_status(rss) == 200:
    #     show_lastest_rss(rss)
    # else:
    #     print('Sorry. We could not find ', rss, sep='')
