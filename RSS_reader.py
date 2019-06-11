"""
RSS_reader.py

Richard E. Rawson
2019-06-09

Program Description:
    A small, lightweight, RSS feed reader.

Features:
-- Add, edit, delete URLs
-- convert URL to RSS
-- name the feed with your own name
-- keep track of how frequently the feed is updated
-- keep track of last time the feed was updated
-- notify if a feed is unreachable
√-- display each RSS site and a list of its titles
-- order the titles from newest to oldest
√-- load a title in a browser
-- provide a mechanism for selecting a particular title to read
-- mark a read title as "read"
-- manually mark a feed title as read or unread
-- automatically update all feeds when app starts update
-- background mode updates feed in the background
√-- group feeds so they are easier to find
√-- import OPML
-- export
√-- list feeds by group/title
-- save a feed to OneNote

"""


import json
import os
from datetime import datetime
from inspect import getfullargspec, getmembers, isfunction
from pprint import pprint
from sys import modules

import feedparser
import requests

import feedparser
import requests
import urlwatch
import urlwatch


def print_all_functions():
    """
    Print all the functions, with their docStrings, used in this program. This function is not used, except by the developer.
    """
    module_functions = []

    func_name = ''
    func_list = []
    print('='*14, ' ALL FUNCTIONS ', '='*14, sep='')
    line_width = 45

    for i in getmembers(modules[__name__],
                        predicate=lambda f: isfunction(f) and f.__module__ == __name__):
        # i[0] is the function name
        # i[1] is the function itself

        # get the arguments for the i[1]
        v_args = getfullargspec(i[1])
        this_args = ''
        if v_args[0]:
            for j in range(len(v_args[0])):
                if this_args:
                    this_args = this_args + ', ' + v_args[0][j]
                else:
                    this_args = v_args[0][j]

        print(i[0], '(', this_args, ')', sep='', end='')
        print(' '*5, i[1].__doc__, sep='')

    return


def retrieve_myFeeds():
    """
    Read myFeeds.json and return a dictionary of the RSS feeds. Each key is a group and each value is a list of RSS feeds in that group. Each feed in 'value' contains two elements: title and RSS address.
    """
    try:
        with open("myFeeds.json", 'r') as file:
            myFeeds = json.load(file)
    except FileNotFoundError:
        myFeeds = {}

    # for k, v in myFeeds.items():
        # print('\n', k, sep='')
        # for ndx, i in enumerate(v):
        # print(' '*5, ndx+1, ': ', i[0], sep='')
        # print(' '*5, ndx+1, ': ', i[0], '\n', ' '*10, i[1], sep='')
        # x = input('PRESS <ENTER> TO CONTINUE...')

    return myFeeds


def inquire_feed(rss):
    """
    Access a feed and return its status code.
    """
    # -- https://pythonhosted.org/feedparser/http-etag.html

    # first request
    feed = feedparser.parse(rss)

    # store the etag and modified; either or both may not exist!
    try:
        last_etag = feed.etag
    except AttributeError:
        last_etag = ''
    try:
        last_modified = feed.modified
    except AttributeError:
        last_modified = ''

    # check if new version exists by sending etag and modified back to the server
    if last_etag and last_modified:
        feed_update = feedparser.parse(
            rss, etag=last_etag, modified=last_modified)
    elif last_etag and not last_modified:
        feed_update = feedparser.parse(rss, etag=last_etag)
    elif last_modified and not last_etag:
        feed_update = feedparser.parse(rss, modified=last_modified)
    else:
        feed_update = feedparser.parse(rss)

    return feed_update.status


def find_all_changes(myFeeds):
    """
    Go through the RSS feeds in {myFeeds} and return a list of feeds that have changed since last access. Also return lists of changed sites, as well as lists of sites by status code.
    """
    rss_list, changed_sites, unchanged_sites = [], [], []
    other_sites, bad_sites = [], []
    site_200, site_301, site_302, site_303 = [], [], [], []
    site_403, site_410 = [], []

    # iterate through {myFeeds} and get each RSS feed
    for group in myFeeds.values():
        # each group contains a list of websites for a given category.
        # so iterate through each item of each list
        for i in group:
            rss_list.append(i[1])

    for site in rss_list:
        try:
            status = inquire_feed(site)
        except AttributeError:
            bad_sites.append(site)
        if status == 200:               # 200 OK
            site_200.append(site)
        elif status == 301:             # 301 Moved Permanently
            site_301.append(site)
        elif status == 302:             # 302 Found
            site_302.append(site)
        elif status == 303:             # 303 See Other
            site_303.append(site)
        elif status == 304:             # 304 Not Modified
            unchanged_sites.append(site)
        elif status == 403:             # 403 Forbidden
            site_403.append(site)
        elif status == 410:             # 410 Gone
            site_410.append(site)
        else:
            other_sites.append((status, site))

        if status != 304:
            changed_sites.append(site)

    return changed_sites, unchanged_sites, other_sites, bad_sites, site_200, site_301, site_302, site_303, site_403, site_410


def get_url_status(url):
    """
    Get the status code for a URL.
    """
    # set the headers like we are a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    # download the url
    r = requests.get(url, headers=headers)

    return r.status_code


# ? def show_HTML_string(HTML_string):
# ?     """
# ?     Given a string, convert the string into an HTML file (temp.html) and  ?display in a browser window.
# ?     """
# ?     path = os.path.abspath('temp.html')
# ?     url = 'file://' + path

# ?     with open(path, 'w') as f:
# ?         f.write(HTML_string)
# ?     webbrowser.open(url)
# ?     return None


def get_latest_feed(rss):
    """
    Utility function to print information about a news feed. Used only by the developer.
    """
    try:
        newsfeed = feedparser.parse(rss)
        # entries is the only dict in [newsfeed_keys]
        newsfeed_keys = ['feed', 'entries', 'bozo', 'headers', 'updated',
                         'updated_parsed', 'href', 'status', 'encoding', 'version', 'namespaces']

        entries_keys = ['title', 'title_detail', 'links', 'link', 'comments', 'published', 'published_parsed', 'authors', 'author',
                        'author_detail', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'wfw_commentrss', 'slash_comments', 'media_content']

        # print site information
        print('\nSite title:', newsfeed['feed']['title'])
        print('\nSite link:', newsfeed['feed']['link'])
        print('\nSite subtitle:', newsfeed['feed']['subtitle'])
        print('\nSite updated:', newsfeed['feed']['updated'])

        # print page information
        print('\nPage title:', newsfeed['entries'][0]['title'])
        print('\nPage id:', newsfeed['entries'][0]['id'])
        print('\nPage published:', newsfeed['entries'][0]['published'])

        # get the content for first item in [entries]
        c = newsfeed['entries'][0]['content'][0]['value']
        # print(c)
    except IndexError:
        pass

    return


def last_ten(rss):
    """
    Return the titles of the latest ten pages for a website as a list of titles.
    """
    newsfeed = feedparser.parse(rss)
    num_entries = len(newsfeed['entries'])

    last_ten_titles = []
    for i in range(num_entries):
        last_ten_titles.append(newsfeed['entries'][i]['title'])

    return last_ten_titles


def show_lastest_rss(rss):
    """
    Show an RSS website in a browser window.
    """
    try:
        webbrowser.open(rss)
    except TypeError:
        pass
    return


def import_OPML():
    """
    Parse an OPML file and put group names, RSS titles, and RSS addresses in {myFeeds} in the form {'Group name': [[title1, RSS1], [title2, RSS2]]}. If no filename is entered, process is aborted. If FileNotFoundError is generated, notify user and <continue>. With confirmation, this file is overwritten each time an OPML file is read.

    Output: {myFeeds} is written to myFeeds.json.
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

            # extract group name from line
            rem_Feed_Group = re.compile(r"""
                        (.*<outline\stext=\")(?P<Feed_Group>\w*\s*\w*)
                        """, re.X)
            # extract site title from the line
            rem_title = re.compile(r"""
                        (.*)(<outline.*text=\")(?P<Feed_Title>.*)(\"\stitle)
                        """, re.X)

            # extract the RSS address from the line
            rem_RSS = re.compile(r"""
                            (.xmlUrl=\")(?P<RSS>.*)(\"\s)
                            """, re.X)

            # extract HTML address from the line
            rem_HTML = re.compile(r"""
                            (.*htmlUrl=")(?P<URL>.*\")
                            """, re.X)

            # put Group, title, and RSS in {myFeeds}
            myFeeds = {}
            for ndx, line in enumerate(feedly):
                m_Feed_Group = re.search(rem_Feed_Group, line)
                m_Feed_Title = re.search(rem_title, line)
                m_RSS = re.search(rem_RSS, line)
                m_HTML = re.search(rem_HTML, line)
                if m_Feed_Group:
                    this_group = m_Feed_Group.group("Feed_Group")
                    myFeeds.update({this_group: []})
                if m_Feed_Title:
                    this_title = m_Feed_Title.group("Feed_Title")
                if m_RSS:
                    this_RSS = m_RSS.group('RSS')
                if m_HTML:
                    this_URL = m_HTML.group('URL')[:-1]  # deletes the final "
                if m_Feed_Title and m_RSS and m_HTML:
                    marked = False
                    new_feed = (this_title, this_RSS, this_URL, marked)
                    current_feed = myFeeds[this_group]
                    current_feed.append(new_feed)
                    myFeeds.update({this_group: current_feed})
            break
        else:
            print('Aborted.')
            return

    # for k, v in myFeeds.items():
    #     print('\n', k, sep='')
    #     for ndx, i in enumerate(v):
    #         print(' '*5, ndx+1, ': ', i[0], sep='')

    # with confirmation, write {myFeeds} to myFeeds.json
    r = input('Overwrite "myFeeds.txt"? (YES/ABORT) ')
    if r.upper() == 'YES':
        with open('myFeeds.json', 'w+') as file:
            file.write(json.dumps(myFeeds, ensure_ascii=False))
        err = False
    else:
        print('Aborted.')
        err = True

    return err


def pick_website():
    """
    From a list of feeds, pick one and return the RSS address.
    """
    myFeeds = retrieve_myFeeds()

    cnt, the_titles = 0, []
    for k, v in myFeeds.items():
        print('\n', k, sep='')
        for ndx, i in enumerate(v):
            print(' '*5, cnt+1, ': ', i[0], sep='')
            the_titles.append(i[0])
            cnt += 1

    while True:
        site_num = input('Which site? ')
        if not site_num.strip():
            break
        try:
            site_num = int(site_num)
            if site_num > 0 and site_num <= cnt:
                break
            else:
                print("Enter a number between 1 and ", cnt, sep='')
                continue
        except:
            print('Enter only an integer.')
            continue

    site_name = the_titles[site_num-1]

    # find the site name in {myFeeds}
    rss = ''
    for group in myFeeds.values():
        for site in group:
            if site[0] == site_name:
                rss = site[2]
                return rss

    return rss


def fold(txt):
    """
    Utility function that textwraps 'txt' 45 characters wide.
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

    start_date = datetime(2019, 6, 10)
    tday = datetime.today()
    revision_delta = datetime.today() - start_date

    print("\nREVISION NUMBER:", revision_delta.days)
    print('This is the number of days since ', start_date, '\n',
          'the date that the first version of "ida" was launched.\n\n', sep='')
    return None


if __name__ == '__main__':

    # get_revision_number()
    version_num = '0.1 rev1'
    print('ida ' + version_num[0:3] + ' - a small news feed reader')

    # print_all_functions()

    # -- about this project
    # about()

    # -- print various attributes of a single RSS feed
    # get_latest_feed('https://hebendsdown.wordpress.com/feed/')

    # -- import OPML file and store RSS info in myFeeds.json; return True if successful
    # err = import_OPML()

    # -- retrieve all feeds from myFeeds.json and return {myFeeds} as a dict
    # myFeeds = retrieve_myFeeds()

    # -- get last ten RSS feeds from a single site, returned as a list
    # last_ten_titles = last_ten('https://hebendsdown.wordpress.com/feed/')

    # -- check to see if feed has changed; return status code
    #  -- status is 304 if no change
    # status = inquire_feed('https://hebendsdown.wordpress.com/feed/')
    # print(status)

    # -- pick one website from the list and return the URL (not RSS)
    # url = pick_website()

    # -- display an RSS address, if it exists, in a browser window
    # if get_url_status(url) == 200:
    #     show_lastest_rss(url)
    # else:
    #     print('Sorry. We could not find ', url, sep='')

    # -- go through the entire list of RSS addresses and return a list of changed sites
    # changed_sites, unchanged_sites, other_sites, bad_sites, site_200, site_301, site_302, site_303, site_403, site_410 = find_all_changes(
    #     myFeeds)

    # print('\nchanged_sites\n', changed_sites, sep='')
    # print('\nunchanged_sites\n', unchanged_sites, sep='')
    # print('\nbad_sites\n', bad_sites, sep='')
    # print('\nsite_301\n', site_301, sep='')
    # print('\nsite_302\n', site_302, sep='')
    # print('\nsite_303\n', site_303, sep='')
    # print('\nsite_403\n', site_403, sep='')
    # print('\nsite_410\n', site_410, sep='')
    # print('\nsite_200\n', site_200, sep='')
    # print('\nother_sites\n', other_sites, sep='')
