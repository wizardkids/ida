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

How to find RSS address for a website:
https://www.lifewire.com/what-is-an-rss-feed-4684568

How to use python to get RSS address from a website:
http://bluegalaxy.info/codewalk/2017/09/21/python-using-requests-to-get-web-page-source-text/
"""

import hashlib
import json
import os
import re
import textwrap
import webbrowser
from datetime import datetime
from inspect import getfullargspec, getmembers, isfunction
from pprint import pprint
from sys import modules

import feedparser
import requests
import urlwatch


def get_feed_info(rss):
    """
    Utility function to print information about a news feed. USED ONLY BY THE DEVELOPER.
    """
    try:
        newsfeed = feedparser.parse(rss)
        # entries is the only dict in [newsfeed_keys]
        newsfeed_keys = ['feed', 'entries', 'bozo', 'headers', 'updated',
                         'updated_parsed', 'href', 'status', 'encoding', 'version', 'namespaces']

        feed_keys = ['title', 'title_detail', 'links', 'link', 'subtitle', 'subtitle_detail', 'updated', 'updated_parsed',
                     'language', 'sy_updateperiod', 'sy_updatefrequency', 'generator_detail', 'generator', 'cloud', 'image']

        entries_keys = ['title', 'title_detail', 'links', 'link', 'comments', 'published', 'published_parsed', 'authors', 'author',
                        'author_detail', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'wfw_commentrss', 'slash_comments', 'media_content']

        # print site information
        print('\nSite title:', newsfeed['feed']['title'])
        print('\nSite link:', newsfeed['feed']['link'])
        print('\nSite subtitle:', newsfeed['feed']['subtitle'])
        print('\nSite updated_parsed:', newsfeed['feed']['updated_parsed'])
        try:
            print('\nSite eTag:', newsfeed['feed']['eTag'])
        except:
            pass
        try:
            print('\nSite modified:', newsfeed['feed']['modified'])
        except:
            pass

        # print page information
        print('\nPage title:', newsfeed['entries'][0]['title'])
        print('\nPage id:', newsfeed['entries'][0]['id'])
        print('\nPage published:', newsfeed['entries'][0]['published'])
        try:
            print('\nPage content:',
                  newsfeed['entries'][0]['content']['value'])
            print('\nPage content type:', type(
                newsfeed['entries'][0]['content']['value']))
        except:
            print('\nPage summary:', newsfeed['entries'][0]['summary'])
            print('\nPage summary type:', type(
                newsfeed['entries'][0]['summary']))

        # get the content for first item in [entries]
        # c = newsfeed['entries'][0]['content']
        # print(c)
    except IndexError:
        pass

    return


def print_all_functions():
    """
    Print all the functions, with their docStrings, used in this program. USED ONLY BY THE DEVELOPER
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


def import_OPML():
    """
    Parse an OPML file and put group names, feed titles, and feed addresses in {myFeeds} in the form {'Group name': [[title1, RSS1], [title2, RSS2], placeholder feed.eTag, feed.modified, feed.updated_parsed], [...]], ... }. If no filename is entered, process is aborted. If FileNotFoundError is generated, notify user and <continue>. With confirmation, this file is overwritten each time an OPML file is read.

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
                    # add placeholder feed.eTag, feed.modified, feed.updated_parsed
                    new_feed = (this_title,
                                this_RSS,
                                this_URL,
                                '',
                                '',
                                '')
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


def load_myFeeds_dict():
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


def get_feed_status(rss, myFeeds):
    """
    Access a feed and return its status code.
    """
    # -- https://pythonhosted.org/feedparser/http-etag.html

    # todo -- update eTag, modified, or updated_parsed in {myFeeds}, changed or not
    # ? The basic concept is that a feed publisher may provide a special HTTP header, called an eTag, when it publishes a feed. You should send this eTag back to the server on subsequent requests. If the feed has not changed since the last time you requested it, the server will return a special HTTP status code (304) and no feed data.
    # ? see: https://fishbowl.pastiche.org/2002/10/21/http_conditional_get_for_rss_hackers
    # todo -- if the feed has changed, add the site info from {myFeeds} to a temporary list called [updated_feeds]
    # todo -- create a new function to create updated_feeds and to modify {myFeeds} with new eTag, modified, and updated_parsed

    # first request
    feed = feedparser.parse(rss[1])

    # store the etag, modified, updated_parsed; any or all may not exist!
    try:
        last_etag = feed.etag
    except AttributeError:
        last_etag = ''
    try:
        last_modified = feed.modified
    except AttributeError:
        last_modified = ''
    try:
        last_updated = feed.updated_parsed
    except AttributeError:
        last_updated = ''
    # check if new version exists by sending etag and modified back to the server:
    if last_etag and last_modified:
        feed_update = feedparser.parse(
            rss, etag=last_etag, modified=last_modified)
    elif last_etag and not last_modified:
        feed_update = feedparser.parse(rss, etag=last_etag)
    elif last_modified and not last_etag:
        feed_update = feedparser.parse(rss, modified=last_modified)
    elif last_updated:
        feed_update = feedparser.parse(rss, updated_parsed=last_updated)
    else:
        feed_update = feedparser.parse(rss)

    try:
        status = feed_update['status']
    except KeyError:
        status = 304

    # update {myFeeds} with last_etag, last_modified, and last_updated
    for k, v in myFeeds.items():
        print('\n', k, sep='')
        for ndx, i in enumerate(v):
            if i[0] == rss[0]:
                i[3] = last_etag
                i[4] = last_modified
                i[5] = last_updated
            for n in range(len(i)):
                print(' '*5, ndx+1, ': ', i[n], sep='')

    return status, myFeeds


def find_all_changes(myFeeds):
    """
    Go through the RSS feeds in {myFeeds} and return a list of feeds that have changed since last access. Also return list of unreachable sites.
    """
    rss_list, updated_sites, unchanged_sites = [], [], []
    other_sites, bad_sites = [], []
    site_200, site_301, site_302, site_303 = [], [], [], []
    site_403, site_410 = [], []

    # iterate through {myFeeds} and get each RSS feed
    for group in myFeeds.values():
        # each group contains a list of websites for a given category.
        # so iterate through each item of each list
        for i in group:
            rss_list.append((i[0], i[1]))

    for site in rss_list:
        try:
            status, myFeeds = get_feed_status(site, myFeeds)
        except AttributeError:
            bad_sites.append(site[1])

        # if status == 200:               # 200 OK
        #     site_200.append(site)
        # elif status == 301:             # 301 Moved Permanently
        #     site_301.append(site)
        # elif status == 302:             # 302 Found
        #     site_302.append(site)
        # elif status == 303:             # 303 See Other
        #     site_303.append(site)
        # elif status == 304:             # 304 Not Modified
        #     unchanged_sites.append(site)
        # elif status == 403:             # 403 Forbidden
        #     site_403.append(site)
        # elif status == 410:             # 410 Gone
        #     site_410.append(site)
        # else:
        #     other_sites.append((status, site))

        if status != 304:
            updated_sites.append(site)

    # print('\nchanged_sites\n', updated_sites, sep='')
    # print('\nunchanged_sites\n', unchanged_sites, sep='')
    # print('\nbad_sites\n', bad_sites, sep='')
    # print('\nsite_301\n', site_301, sep='')
    # print('\nsite_302\n', site_302, sep='')
    # print('\nsite_303\n', site_303, sep='')
    # print('\nsite_403\n', site_403, sep='')
    # print('\nsite_410\n', site_410, sep='')
    # print('\nsite_200\n', site_200, sep='')
    # print('\nother_sites\n', other_sites, sep='')

    return updated_sites, bad_sites


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


def last_ten(rss):
    """
    Return the titles of the latest ten articles for a website as a list of titles.
    """
    newsfeed = feedparser.parse(rss)
    num_entries = len(newsfeed['entries'])

    last_ten_titles = []
    for i in range(num_entries):
        last_ten_titles.append(newsfeed['entries'][i]['title'])

    return last_ten_titles


def show_lastest_rss(rss):
    """
    Show a RSS feed in a browser window.
    """
    try:
        webbrowser.open(rss)
    except TypeError:
        pass
    return


def pick_website():
    """
    From a list of feeds, pick one and return the feed's RSS address.
    """
    myFeeds = load_myFeeds_dict()

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


def hash_a_string(this_string):
    """
    Create a hash value for a string (this_string).
    """
    return str(int(hashlib.sha256(this_string.encode('utf-8')).hexdigest(), 16) % 10**8)


def main_menu(myFeeds):
    """
    Print the main menu on the screen and direct the user's choice.
    """
    menu = (
        '<c>heck feeds  ', '<e>dit feed    ', '<a>bout ',
        '<i>mport OPML  ', 'e<x>port feeds ', '<q>uit',
    )

    while True:
        print()
        for i in range(0, len(menu), 3):
            m = ''.join(menu[i:i+3])
            print(m)
        print()
        menu_choice = input('Choice: ')

        if menu_choice.upper() == 'Q':
            return
        elif menu_choice.upper() == 'A':
            about()
        elif menu_choice.upper() == 'C':
            changed_sites, bad_sites = find_all_changes(myFeeds)
            print(changed_sites)
        elif menu_choice.upper() == 'E':
            pass
        elif menu_choice.upper() == 'I':
            err = import_OPML()
            if err:
                print('Import failed or aborted.')
            else:
                print('OPML file successfully imported.')
        elif menu_choice.upper() == 'X':
            pass
        else:
            print('*'*35)
            print('Enter a valid menu choice.')
            print('*'*35)
            continue


def main(hash_titles):
    """
    The main program that organizes program flow.
    """

    # load {myFeeds} from myFeeds.json file
    myFeeds = load_myFeeds_dict()

    # display menu on screen
    menu_choice = main_menu(myFeeds)

    # before quitting the app, save hash_titles:
    hash_titles_set = set(hash_titles)
    with open('titles_read.txt', 'w') as file:
        for i in hash_titles_set:
            file.write(i + '\n')

    return


if __name__ == '__main__':

    # get_revision_number()
    version_num = '0.1 rev4'
    print('ida ' + version_num[0:3] + ' - a small news feed reader')

    # read titles_read.txt from disk
    try:
        with open('titles_read.txt', 'r') as file:
            all_titles = file.readlines()
        hash_titles = [line.strip('\n') for line in all_titles]
    except FileNotFoundError:
        hash_titles = []

    main(hash_titles)

    """
    FUNCTIONS NEEDED:
        create myFeeds.json where:
            - keys: feed groups
            - values: [list] of RSS feeds for each group:
                - feed.title, RSS, HTML, feed.etag, feed.modified, feed.updated_parsed
            - should contain a blank group for feeds that don't belong to a group
            -- import_OPML() 
                can create this file from an OPML file

        need functions that allow creating and editing of myFeeds.json
            1. get a HTML address
            2. fxn to read feed source content and use regex to get RSS address
            3. fields:
            ['Ignatian Spirituality', 'http://feeds.feedburner.com/dotMagis?format=xml', 'https://www.ignatianspirituality.com', '6c132-941-ad7e3080', 'Fri, 11 Jun 2012 23:00:34 GMT', 'time.struct_time(tm_year=2012, tm_mon=3, tm_mday=6, tm_hour=23, tm_min=00, tm_sec=34, tm_wday=6, tm_yday=66, tm_isdst=0)', hash the title for ['entries'][0]['title']]

            [Site title, RSS address, HTML address, eTag, modified, updated_parsed, hashed-title for top entry]

            4. put the new feed into an existing group, where the default is the blank group 
            5. fxn to add a new group
            6. fxn to edit or delete an existing group
            7. fxn to move a feed from one group to another

        create a menu:
            - import/export
            - add/edit/delete RSS feeds and groups
            - check all feeds for changes and display changed feeds



    WHEN THE APP STARTS:

        1. get {myFeeds} from myFeeds.json
            -- {myFeeds} = load_myFeeds_dict()

        2. access every RSS feed
            -- status, myFeeds, updated_feeds = get_feed_status(site, myFeeds)
            for each group in {myFeeds}
                for each feed site:
                    - access site using RSS
                    - determine if feed has changed:
                        -compare current feed.eTag and/or feed.modified or feed.updated_parsed with the same values stored in {myFeeds}
                        - hash the title for ['entries'][0] (the most recent page) and see if that hash exists in [hash_titles]; if not, then site has changed
                    - if site has changed (updated):
                        - store this feed (RSS) in [updated_feeds]
                        - update feed.eTag, feed.modified, feed.updated.parsed, and hash the title for ['entries'][0]['title'] in {myFeeds}

        3. from [updated_feeds]:
            - for each title, hash the title and then check in [hash_titles]. If it already exists, then don't list the title since you've already read it
            - print a list of feed['entries'][0]['content'][0]['value']: 
                Feed_Title
                    1. Article_title1 (feed['entries'][0]['title'])
                    2. Article_title2 (feed['entries'][1]['title'])
                    3. Article_title3 (feed['entries'][2]['title'])
                    4. Article_title4 (feed['entries'][3]['title'])
                    5. ...

        4. from the list, choose a number

        5. for the number chosen:
            (a) get RSS address: feed['entries'][i]['link'] from [updated_feeds]
                (a) display in browser 
                    -- show_lastest_rss(rss)

                ...OR...

                (b) display a page summary (feed['entries][i]['summary'])

            (b) create a hash of the title and store in [hash_titles]
                    -- hash = hash_a_string(this_string)

        6. after selecting a number and choosing (a) or (b) from step #5, loop back to step (3)



    before quitting the app, write [hash_titles] to file
    when restarting, reload [hash_titles] from file
 

    """

    # -- print various attributes of a single RSS feed
    # get_feed_info('https://hebendsdown.wordpress.com/feed/')

    # -- import OPML file and store RSS info in myFeeds.json; return True if successful
    # err = import_OPML()

    # -- retrieve all feeds from myFeeds.json and return {myFeeds} as a dict
    # myFeeds = load_myFeeds_dict()

    # -- get last ten RSS feeds from a single site, returned as a list
    # last_ten_titles = last_ten('https://hebendsdown.wordpress.com/feed/')

    # -- check to see if feed has changed; return status code
    #  -- status is 304 if no change
    # status, myFeeds = get_feed_status('https://hebendsdown.wordpress.com/feed/', myFeeds)
    # print(status)

    # -- pick one website from the list and return the URL (not RSS)
    # url = pick_website()

    # -- display an RSS address, if it exists, in a browser window
    # if get_url_status(url) == 200:
    #     show_lastest_rss(url)
    # else:
    #     print('Sorry. We could not find ', url, sep='')

    # -- go through the entire list of RSS addresses and return a list of changed sites
    # changed_sites, bad_sites = find_all_changes(myFeeds)
