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
    -- display each RSS site and a list of its titles
    -- order the titles from newest to oldest
    -- load a title in a browser
    -- provide a mechanism for selecting a particular title to read
    -- mark a read title as "read"
    -- manually mark a feed title as read or unread
    -- automatically update all feeds when app starts update
    -- background mode updates feed in the background
    -- group feeds so they are easier to find
    -- import OPML
    -- export to...???
    -- list feeds by group/title

How to find RSS address for a website:
https://www.lifewire.com/what-is-an-rss-feed-4684568

How to use python to get RSS address from a website:
http://bluegalaxy.info/codewalk/2017/09/21/python-using-requests-to-get-web-page-source-text/
"""

import hashlib
import json
import re
import textwrap
import urllib.parse
import webbrowser
from datetime import datetime
from inspect import getfullargspec, getmembers, isfunction
from pprint import pprint
from sys import modules

import feedparser
import requests
import urlwatch
from bs4 import BeautifulSoup as bs4

# todo -- need a utility to delete a group, or edit its name

# todo -- modify functions so that error messages are posted right above input() statements so that the user can easily notice them.


# === DEVELOPER UTILITY FUNCTIONS ================

def get_feed_info(rss):
    """
    Utility function to print information about a news feed. USED ONLY BY THE DEVELOPER.
    """

    try:
        newsfeed = feedparser.parse(rss)
        # entries is the only dict in [newsfeed_keys]
        newsfeed_keys = ['feed', 'entries', 'bozo', 'headers', 'updated',
                         'updated_parsed', 'href', 'status', 'encoding', 'version', 'namespaces']

        # pprint(newsfeed, depth=1, width=40, indent=2)

        # pprint(newsfeed['headers'], width=40, indent=2)

        feed_keys = ['title', 'title_detail', 'links', 'link', 'subtitle', 'subtitle_detail', 'updated', 'updated_parsed',
                     'language', 'sy_updateperiod', 'sy_updatefrequency', 'generator_detail', 'generator', 'cloud', 'image']

        # pprint(newsfeed['feed'], depth=1, width=40, indent=2)

        entries_keys = ['title', 'title_detail', 'links', 'link', 'comments', 'published', 'published_parsed', 'authors', 'author',
                        'author_detail', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content', 'wfw_commentrss', 'slash_comments', 'media_content']

        # pprint(newsfeed['entries'], depth=4, width=40, indent=2)

        print('RSS ADDRESS:\n', rss, sep='')
        try:
            print('\nBlog name:', newsfeed['feed']['title'])
        except:
            print('\nNo feed title.')
        try:
            print('\nSubtitle:', newsfeed['feed']['subtitle'])
        except:
            print('\nNo feed subtitle.')
        try:
            print('\nSite RSS:', newsfeed['href'])
        except:
            print('\nNo RSS address.')
        try:
            print('\nSite link:', newsfeed['feed']['link'])
        except:
            print('\nNo link provided.')
        try:
            print('\nSite RSS address:', newsfeed['feed']['links'][0]['href'])
        except:
            print('\nNo address provided.')
        try:
            print('\nSite ETag:', newsfeed['feed']['ETag'])
        except:
            print('\nNo ETag.')
        try:
            print('\nSite modified:', newsfeed['feed']['modified'])
        except:
            print('\nNo modified datetime.')
        try:
            print('\nSite updated:', newsfeed['feed']['updated'])
        except:
            print('\nNo updated datetime.')
        try:
            print('\nLatest feed posts:')
            for ndx, i in enumerate(newsfeed['entries']):
                print(ndx+1, ': ', i['title'], sep='')
                print('   ', i['link'])
        except:
            print('\nNo entry link found.')

    except IndexError:
        print('Oops. Encountered an error!')

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


# === IMPORT OPML FILE ================

def import_OPML(myFeeds):
    """
    Parse an OPML file and put group names, feed titles, and feed addresses in {myFeeds} in the form {'Group name': [[title1, RSS1], [title2, RSS2], placeholder feed.ETag, feed.modified, feed.updated], [...]], ... }. If no filename is entered, process is aborted. If FileNotFoundError is generated, notify user and <continue>. With confirmation, this file is overwritten each time an OPML file is read.

    Output: {myFeeds} is written to myFeeds.json.
    """
    file = input('Name of OPML file to import: ')
    # file = 'feedly.opml'

    while True:
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
            myFeeds = {'Default': []}
            for ndx, line in enumerate(feedly):
                m_Feed_Group = re.search(rem_Feed_Group, line)
                m_Feed_Title = re.search(rem_title, line)
                m_RSS = re.search(rem_RSS, line)
                m_HTML = re.search(rem_HTML, line)
                if m_HTML:
                    this_URL = m_HTML.group('URL')[:-1]  # deletes the final "
                    # check to see if this is a valid URL
                    print('Checking validity of:', this_URL)
                    status_code = get_url_status(this_URL)
                    if status_code != 200:
                        continue
                if m_Feed_Group:
                    this_group = m_Feed_Group.group("Feed_Group")
                    myFeeds.update({this_group: []})
                if m_Feed_Title:
                    this_title = m_Feed_Title.group("Feed_Title")
                if m_RSS:
                    this_RSS = m_RSS.group('RSS')
                if m_Feed_Title and m_RSS and m_HTML:
                    # add placeholders for feed.ETag, feed.modified, feed.updated, feed.last_title, feed.last_link
                    new_feed = (this_title,
                                this_RSS,
                                this_URL,
                                '',
                                '',
                                '',
                                '',
                                '')
                    current_feed = myFeeds[this_group]
                    current_feed.append(new_feed)
                    myFeeds.update({this_group: current_feed})
            break
        else:
            print('Aborted.')
            return True, myFeeds

    for k, v in myFeeds.items():
        print('\n', k, sep='')
        for ndx, i in enumerate(v):
            print(' '*5, ndx+1, ': ', i, sep='')

    # with confirmation, write {myFeeds} to myFeeds.json
    r = input('Overwrite "myFeeds.json"? (YES/ABORT) ')
    if r.upper() == 'YES':
        with open('myFeeds.json', 'w+') as file:
            file.write(json.dumps(myFeeds, ensure_ascii=False))
        err = False
    else:
        print('Aborted.')
        err = True

    return err, myFeeds


def get_url_status(url):
    """
    Get the status code for a URL. This function is used during import of an OPML file to be sure each feed is accessible.
    """
    # set the headers like we are a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    # download the url and get its status, if any
    try:
        r = requests.get(url, headers=headers)
        status_code = r.status_code
    except:
        print('Cannot connect to', url)
        status_code = 404

    return status_code


# === FEED MANAGEMENT ================

def add_feed(myFeeds):
    """
    Allows user to add a feed to {myFeeds}, including an optional group.

    - enter URL of feed and optionally a group (new or existing)
    - go to the URL, get the RSS feed address

    # -- fill in the following fields in {myFeeds}
        # -- 0: feed title
        # -- 1: feed RSS
        # -- 2: feed URL
        # -- 3: feed.ETag (blank)
        # -- 4: feed.modified (blank)
        # -- 5: feed.updated (blank)
        # -- 6: hash of last entry posted on website (blank)
        # -- 7: link to last entry posted on website (blank)
    """
    print()
    # enter a URL, find the feed address, parse the feed
    f = input('Website address: ')
    try:
        result = findfeed(f)
        # check alternate RSS formats
        if not result:
            result = findfeed(f + '/feed')
        if not result:
            result = findfeed(f + '/?feed=rss')
        if not result:
            result = findfeed(f + '/feed/rss2')
        if not result:
            result = findfeed(f + '/blog/feed')
        if not result:
            result = findfeed(f + '/atom.xml')
        if not result:
            result = feedburner_rss(f)
        if not result:
            result = youtube_rss(f)
        if not result:
            result = feed_xml(f)
    except:
        print('='*30, '\nDid you forget "http://"?\n', '='*30, '\n', sep='')
        return myFeeds

    rss_address = ''
    if isinstance(result, list):
        for r in result:
            if 'comments' not in r:
                rss_address = r
    else:
        rss_address = result

    if rss_address:
        feed = feedparser.parse(rss_address)
    else:
        print('='*30, '\nNo RSS address found.\n', '='*30, '\n', sep='')
        rss_address = input("Enter RSS address manually: ")
        feed = feedparser.parse(rss_address)

        if not rss_address or not feed['entries']:
            print('='*30, '\nBad RSS address or no address found.\n',
                  '='*30, '\n', sep='')
            return myFeeds

    # add info into [new_feed]
    # https://www.youtube.com/feeds/videos.xml?channel_id=UCxAS_aK7sS2x_bqnlJHDSHw
    new_feed = []
    try:
        new_feed.append(feed['feed']['title'])
    except:
        new_feed.append('')
    try:
        new_feed.append(feed['href'])
    except:
        new_feed.append('')
    new_feed.append(f)
    new_feed.append('')
    new_feed.append('')
    new_feed.append('')
    new_feed.append('')
    try:
        new_feed.append(feed['entries'][0]['title'])
    except:
        new_feed.append('')
    try:
        new_feed.append(feed['entries'][0]['link'])
    except:
        new_feed.append('')

    # get the group that the feed should be added to...
    print('\nGroups:')
    cnt, kys = 0, list(myFeeds.keys())
    for grp_name in kys:
        cnt += 1
        print('  ', cnt, ': ', grp_name, sep='')

    print()

    while True:
        grp_name = input('Add new feed to which group (or enter new group)? ')
        if not grp_name:
            grp_name = 0
            break
        try:
            grp_name = int(grp_name)
            if grp_name < 1 or grp_name > len(kys):
                print('='*30, '\nEnter an integer between 1 and ',
                      len(kys), '\n', '='*30, '\n', sep='')
                continue
            else:
                break
        except:
            # if a non-integer was entered, assume it's a group name
            break

    # translate a group number into a group name so you can find it in myFeeds.keys()
    if isinstance(grp_name, int):
        if grp_name <= len(kys) and grp_name > 0:
            grp_name = kys[grp_name-1]
        elif (grp_name == 0) or (grp_name == len(kys) + 1):
            grp_name = 'Default'
        else:
            grp_name = ''

    # add [new_feed] to the appropriate group
    if isinstance(grp_name, str):
        if grp_name:
            # if the group already exists...
            if grp_name in myFeeds.keys():
                myFeeds[grp_name].append(new_feed)
            # otherwise, create a new group
            else:
                myFeeds.update({grp_name: [new_feed]})

    myFeeds = clean_feeds(myFeeds)

    return myFeeds


def move_feed(myFeeds):
    """
    Move a feed to a different group.
    """
    while True:
        # list feeds, by group, numbering the feeds
        feed_cnt, grp_cnt, feed_list = 0, 0, []

        for k, v in myFeeds.items():
            print(k, sep='')
            grp_cnt += 1
            for i in v:
                feed_cnt += 1
                feed_list.append(i)
                print('   ', feed_cnt, ': ', i[0], sep='')
        
        print()
        # enter the number of the feed to move
        feed_num = input('Number of feed to move: ')
        try:
            feed_num = int(feed_num)
            feed_name = feed_list[feed_num-1][0]
            # find the feed in {myFeeds}
            this_feed = ''
            for k, v in myFeeds.items():
                for ndx, i in enumerate(v):
                    if i[0] == feed_name:
                        this_feed = i
                        v.pop(ndx)
                    if this_feed: break
                if this_feed: break
        except:
            break

        # enter the name of the group to receive the moving feed
        group_name = input("Enter name of group receiving feed: ").strip()
        done = False
        try:  
            # find the group in {myFeeds}
            for k, v in myFeeds.items():
                if k.upper() == group_name.upper():
                    v.append(this_feed)
                    done = True
                    break
            # in case user entered a garbage group, feed is moved to "Default" group
            if not done:
                myFeeds['Default'].append(this_feed)
        except:
            break
        break

    return myFeeds


def clean_feeds(myFeeds):
    """
    Deletes feeds that are duplicates or that have no title. The latter can happen when a user deletes
    a feed: del_feed() sets the title to ''
    """
    # delete any feed with no title
    for k, v in myFeeds.items():
        for ndx, i in enumerate(v):
            if not i[0]:
                v.pop(ndx)

    # delete any duplicate feeds
    feed_urls = []
    for k, v in myFeeds.items():
        feed_tuples = set(tuple(x) for x in v)
        feed_list = [list(item) for item in feed_tuples]
        myFeeds.update({k: feed_list})

    return myFeeds


def del_feed(myFeeds):
    """
    Delete a feed.
    """

    # generate a list of feed names
    cnt, feed_names=0, []
    for k, v in myFeeds.items():
        for i in v:
            cnt += 1
            feed_names.append(i[0])
            print(cnt, '. ', i[0], sep = '')

    print()
    # get the name of the feed to delete
    while True:
        f=input('Number of feed to delete: ').lower()
        if not f:
            break
        try:
            f=int(f)
            if f < 1 or f > cnt:
                print('='*30, '\nEnter an integer between 1 and ',
                      cnt, '.\n', '='*30, sep = '')
                continue
            else:
                break
        except ValueError:
            print('='*30, '\nEnter an integer between 1 and ',
                  cnt, '.\n', '='*30, sep='')
            continue

    # find that name in {myFeeds} and set title to ''
    if f:
        this_feed = feed_names[f-1]
        for k, v in myFeeds.items():
            for i in v:
                if i[0] == this_feed:
                    i[0] = ''
                    break
            if not i[0]:
                break

    myFeeds = clean_feeds(myFeeds)

    print()

    return myFeeds


def edit_group(myFeeds):
    """
    Edit the name of a group.
    """
    pass


def feed_xml(f):
    """
    Find a feed when the blog uses an xml address.
    """
    feed = feedparser.parse(f)
    result = feed['href'] + 'index.xml'

    return result


def feedburner_rss(f):
    """
    Find a feed when the blogger is using feedburner.
    """
    feed = requests.get(f)
    txt = feed.content.decode('utf-8')

    rem_uri = re.compile(r"""
            (href=\"//feedburner.google.com/)(.*uri=)(?P<feed_uri>.*)(&amp)
            """, re.X)

    m_feed_uri = re.search(rem_uri, txt)

    if m_feed_uri:
        this_uri = m_feed_uri.group("feed_uri")
        result = 'http://feeds.feedburner.com/' + this_uri
    else:
        result = ''

    return result


def youtube_rss(f):
    """
    Find the feed for a youtube channel (not a single video!).

    
    """
    rem = re.compile("""
            (.*channel/)(?P<yt_channel>.*)"""
            , re.X)

    m_RSS = re.search(rem, f)
    if m_RSS:
        this_channel = m_RSS.group('yt_channel')
    else:
        this_channel = ''

    this_RSS = 'https://www.youtube.com/feeds/videos.xml?channel_id=' + this_channel

    return this_RSS


def findfeed(site):
    """
    Python 3 function for extracting RSS feeds from URLs.
    
    Source: https://gist.github.com/alexmill/9bc634240531d81c3abe
    Attribution: https://alex.miller.im/
    """
    raw = requests.get(site).text
    result = []
    possible_feeds = []
    html = bs4(raw, features="lxml")
    feed_urls = html.findAll("link", rel="alternate")
    if len(feed_urls) > 1:
        for f in feed_urls:
            t = f.get("type", None)
            if t:
                if "rss" in t or "xml" in t:
                    href = f.get("href", None)
                    if href:
                        possible_feeds.append(href)
    parsed_url = urllib.parse.urlparse(site)
    base = parsed_url.scheme+"://"+parsed_url.hostname
    atags = html.findAll("a")
    for a in atags:
        href = a.get("href", None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                possible_feeds.append(base+href)
    for url in list(set(possible_feeds)):
        f = feedparser.parse(url)
        if len(f.entries) > 0:
            if url not in result:
                result.append(url)

    return result


# === CHECK FEEDS FOR UPDATES ================

def find_all_changes(myFeeds):
    """
    Go through the RSS feeds in {myFeeds} and return a list of feeds that have changed since last access. Also return list of unreachable sites.
    """
    rss_list, updated_feeds, bad_feeds = [], [], []

    # not used unless you uncomment lines of code below
    # other_feeds, unchanged_feeds = [], []
    # site_200, site_301, site_302, site_303 = [], [], [], []
    # site_403, site_410 = [], []

    # iterate through {myFeeds} and get each RSS feed
    for group in myFeeds.values():
        # each group contains a list of websites for a given category.
        # so iterate through each item of each list
        for i in group:
            # in case group is empty
            try:
                rss_list.append([i[0], i[1], i[7]])
            except:
                break

    for rss_feed in rss_list:
        # [rss_feed] entering get_feed_status():
            # -- feed title
            # -- RSS address
            # -- link to the latest post

        myFeeds, updated_feeds, bad_feeds = get_feed_status(
            rss_feed, myFeeds, updated_feeds, bad_feeds)

        # for each rss_feed, [uptdate_feeds] returned by get_feed_status():
        # -- feed title
        # -- RSS address
        # -- the most recent post link
        # -- n items containing lists of [post-title, post-link]

        # if status == 200:               # 200 OK
        #     site_200.append(site)
        # elif status == 301:             # 301 Moved Permanently
        #     site_301.append(site)
        # elif status == 302:             # 302 Found
        #     site_302.append(site)
        # elif status == 303:             # 303 See Other
        #     site_303.append(site)
        # elif status == 304:             # 304 Not Modified
        #     unchanged_feeds.append(site)
        # elif status == 403:             # 403 Forbidden
        #     site_403.append(site)
        # elif status == 410:             # 410 Gone
        #     site_410.append(site)
        # else:
        #     other_feeds.append((status, site))

    # print('\updated_feeds\n', updated_feeds, sep='')
    # print('\nunchanged_feeds\n', unchanged_feeds, sep='')
    # print('\nbad_feeds\n', bad_feeds, sep='')
    # print('\nsite_301\n', site_301, sep='')
    # print('\nsite_302\n', site_302, sep='')
    # print('\nsite_303\n', site_303, sep='')
    # print('\nsite_403\n', site_403, sep='')
    # print('\nsite_410\n', site_410, sep='')
    # print('\nsite_200\n', site_200, sep='')
    # print('\nother_feeds\n', other_feeds, sep='')

    return updated_feeds, bad_feeds, myFeeds


def get_feed_status(rss_feed, myFeeds, updated_feeds, bad_feeds):
    """
    Access a feed. Compare the title of the most recent post to the title stored in {myFeeds}. If they are the same, then the feed has not been updated. If they are different, then add the feed info to [updated_feeds].

    arg rss_feed contains:
        feed title
        RSS address
        link to the latest post
    """
    # -- https://pythonhosted.org/feedparser/http-ETag.html
    # -- https://fishbowl.pastiche.org/2002/10/21/http_conditional_get_for_rss_hackers

    # if status is other than 304, then add this title to [updated_feeds]
        # -- [rss_feed] structure to be added to [updated_feeds]:
        # -- fed title
        # -- RSS address
        # -- the most recent post link
        # -- n items containing lists of [post-title, post-link]

    # get last article title and link that was read
    for k, v in myFeeds.items():
        for newsfeed in v:
            # in case group is empty
            try:
                if newsfeed[0] == rss_feed[0]:
                    last_title = newsfeed[6]
                    last_link = newsfeed[7]
            except:
                break

    feed_update = feedparser.parse(rss_feed[1])

    # get the link to the most recent post
    try:
        current_link = feed_update['entries'][0]['link']
    except IndexError:
        current_link = ''

    # get the title of the most recent post
    try:
        current_title = feed_update['entries'][0]['title']
    except:
        current_title = ''

    # if the last_title in {myFeeds} == the title of the most recent post, then the feed has not been updated
    if last_link == hash_a_string(current_link):
        status = 304
    # otherwise, store this feed's informtion in [rss]
    else:
        try:
            # add to [rss] all the titles and links available in ['entries'] for this particular feed
            for ndx, i in enumerate(feed_update['entries']):
                rss_feed.append([i['title'], i['link']])

            # put the link to the most recent post in rss_feed[2]
            rss_feed[2] = current_link
            updated_feeds.append(rss_feed)

        except:
            bad_feeds.append(rss_feed)

    return myFeeds, updated_feeds, bad_feeds


def list_updated_feeds(myFeeds, updated_feeds, titles_read, bad_feeds):
    """
    Create a list of your feeds. Let user select from that list one feed and then create a list of updated articles. Default to filtering out articles that have been read. Let user choose articles to read online.
    """
    # default for article list is to show only unread articles
    show_read = 'unread'
    show_bad = False

    sf = input('\nShow bad feeds? (Y/N)').lower()
    show_bad = True if sf == 'y' else False

    if show_bad:
        print()
        print('='*5, ' UNREACHABLE FEEDS ', '='*5, sep='')
        for i in bad_feeds:
            print(i)
        print('='*29, sep='')

    print()
    while True:
        if len(updated_feeds) == 0:
            print('\n', '='*30, '\nNone of your feeds have updated since last check.\n',
                  '='*30, '\n', sep='', end='')
            f = input('Press <ENTER> to continue...')
            break

        for ndx, i in enumerate(updated_feeds):
            print(ndx+1, '. ', i[0], sep='')
        print()

        while True:
            choice = input('Select feed: ')
            if not choice:
                break
            try:
                choice = int(choice)
                if choice < 1 or choice > len(updated_feeds):
                    print('='*30, '\nEnter an integer between 1 and ',
                          len(updated_feeds), '\n', '='*30, '\n', end='', sep='')
                    continue
                else:
                    break
            except ValueError:
                print('='*30, '\nEnter an integer between 1 and ',
                      len(updated_feeds), '\n', '='*30, '\n', end='', sep='')
                continue

        if not choice:
            break
        else:
            err = ''

            # have user choose which post to view
            while True:

                chosen_feed = updated_feeds[choice-1]

                # find the number of articles in updated_feeds that have already been read
                cnt_unread_articles = 0
                for i in range(3, len(chosen_feed)):
                    if hash_a_string(chosen_feed[i][1]) not in titles_read:
                        cnt_unread_articles += 1
                if cnt_unread_articles == 0:
                    print('\n', '='*30, '\nThis feed has not changed since last access.\n',
                          '='*30, '\n', sep='', end='')
                    m = input('\nUnread some articles? (Y/N) ').lower()
                    if m == 'y':
                        titles_read = set_post_to_unread(
                            titles_read, chosen_feed)
                    break

                # structure of [updated_feeds]
                # -- feed title
                # -- RSS address
                # -- the link to the most recent post
                # -- n items containing lists of [post-title, post-link]

                print()
                # print all the available posts, depending on show_read setting
                for cnt in range(3, len(chosen_feed)):
                    if hash_a_string(chosen_feed[cnt][1]) not in titles_read:
                        print(cnt-2, ': ', chosen_feed[cnt][0], sep='')
                    elif show_read == 'read':
                        print('*', cnt-2, ': ', chosen_feed[cnt][0], sep='')
                print()

                if err:
                    print(err)

                # print a menu
                post_menu = [
                    '<t>oggle showing read articles',
                    'post to set to <u>nread',
                    'post to set to <r>ead'
                ]
                for i in range(len(post_menu)):
                    print(post_menu[i])

                # get a specific article from this feed
                post = input(
                    '\nSelect from menu or a numbered article: ').lower().strip()
                if not post:
                    break

                if post in ['t', 'u', 'r']:
                    if post == 't':
                        show_read = toggle_show_read_articles(show_read)
                    elif post == 'u':
                        titles_read = set_post_to_unread(
                            titles_read, chosen_feed)
                    elif post == 'r':
                        titles_read = set_post_to_read(
                            titles_read, chosen_feed)
                else:
                    try:
                        post = int(post)
                        if post + 2 < 3 or post + 3 > len(chosen_feed):
                            err = '='*30 + '\nEnter an integer between 1 and ' + \
                                str(len(chosen_feed)-3) + \
                                ' or a menu item\n' + '='*30 + '\n'
                            continue
                    except ValueError:
                        err = '='*30 + '\nEnter an integer between 1 and ' + \
                            str(len(chosen_feed)-3) + \
                            ' or a menu item\n' + '='*30 + '\n'
                        continue

                    if post:
                        print('showing', chosen_feed[post+2][0])
                        # show_lastest_rss(chosen_feed[post+2][1])
                        current_link = hash_a_string(chosen_feed[post+2][1])
                        titles_read.append(current_link)
                        for k, v in myFeeds.items():
                            for feed in v:
                                if feed[0] == chosen_feed[0]:
                                    try:
                                        feed[6] = hash_a_string(current_link)
                                        # feed[7] = feed_update['entries'][0]['link']
                                    except:
                                        pass
                                    break
                    else:
                        break

            if cnt_unread_articles == 0:
                continue

            if not post:
                continue

    return myFeeds, updated_feeds, titles_read


def toggle_show_read_articles(show_read):
    """
    In list_updated_feeds(), toggle the listing of read articles.
    """
    show_read = 'read' if show_read == 'unread' else 'unread'
    return show_read 


def set_post_to_unread(titles_read, chosen_feed):
    """
    In list_updated_feeds(), set one or more read posts to unread.
    """
    print()
    while True:
        article_number = input("Number or range of post(s) to set to unread: ")
        print()

        # if the user enters a range of articles...
        if '-' in article_number:
            try:
                ndx = article_number.index('-')
                start_num = int(article_number[0:ndx])
                end_num = int(article_number[ndx+1:])+1
            except ValueError:
                print('='*30, '\nEnter a range of integers separated by a hyphen.\n', '='*30, sep='')
                return titles_read
            for i in range(start_num, end_num):
                titles_read = unread_one_article(i, chosen_feed, titles_read)
            break
        else:
            try:
                article_number = int(article_number)
            except:
                print('='*30, '\nEnter an integer between 1 and ', \
                    len(chosen_feed)-3, '\n', '='*30, '\n', sep='', end='')
                continue
            if not article_number:
                break
            else:
                titles_read = unread_one_article(article_number, chosen_feed, titles_read)
                break
    return titles_read


def set_post_to_read(titles_read, chosen_feed):
    """
    In list_updated_feeds(), set one or more unread posts to read.
    """
    print()
    while True:
        article_number = input("Number or range of post(s) to set to read: ")

        # if the user enters a range of articles...
        if '-' in article_number:
            try:
                ndx = article_number.index('-')
                start_num = int(article_number[0:ndx])
                end_num = int(article_number[ndx+1:])+1
            except ValueError:
                print(
                    '='*30, '\nEnter a range of integers separated by a hyphen.\n', '='*30, sep='')
                return titles_read
            for i in range(start_num, end_num):
                titles_read = set_to_read_one_article(i, chosen_feed, titles_read)
            break
        else:
            try:
                article_number = int(article_number)
            except:
                print('='*30, '\nEnter an integer between 1 and ',
                      len(chosen_feed)-3, '\n', '='*30, '\n', sep='', end='')
                continue
            if not article_number:
                break
            else:
                titles_read = unread_one_article(
                    article_number, chosen_feed, titles_read)
                break
    return titles_read


def set_to_read_one_article(article_number, chosen_feed, titles_read):
    """
    Utility function to set one article in a feed to 'read'.
    """
    title = hash_a_string(chosen_feed[article_number+2][1])

    titles_read.append(title)
    # strip out repeat titles
    titles_read = list(set(titles_read))
    print()

    return titles_read


def unread_one_article(article_number, chosen_feed, titles_read):
    """
    Utility function to unread one article in a feed.
    """
    try:
        title = hash_a_string(chosen_feed[article_number+2][1])
    # in case user chose a title that is unread...
        try:
            ndx = titles_read.index(title)
            titles_read.pop(ndx)
        except:
            print('='*30, '\nTitle is already marked unread.\n',
                    '='*30, '\n', sep='', end='')
    except:
        print('='*30, '\nEnter an integer between 1 and ',
              len(chosen_feed)-3, '\n', '='*30, '\n',  sep='', end='')

    return titles_read


def show_lastest_rss(rss):
    """
    Show a RSS feed in a browser window.
    """
    try:
        webbrowser.open(rss)
    except TypeError:
        pass
    return


# === STARTUP AND MISCELLANEOUS FUNCTIONS ================

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


def fold(txt):
    """
    Utility function that textwraps 'txt' 45 characters wide.
    """
    return textwrap.fill(txt, width=45)


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
    Create a hash value for a string (this_string). This utility is used to hash titles to speed up comparison of titles and reduce list storage space.
    """
    return str(int(hashlib.sha256(this_string.encode('utf-8')).hexdigest(), 16) % 10**8)


def load_myFeeds_dict():
    """
    Read myFeeds.json and return a dictionary of the RSS feeds. Each key is a group and each value is a list of RSS feeds in that group. Structure of {myFeeds}:

        # -- 0: feed title
        # -- 1: feed RSS
        # -- 2: feed URL
        # -- 3: feed.ETag
        # -- 4: feed.modified
        # -- 5: feed.updated
        # -- 6: hash of title of last entry posted on website
        # -- 7: link to last entry posted on website
    """
    try:
        with open("myFeeds.json", 'r') as file:
            myFeeds = json.load(file)
    except FileNotFoundError:
        # at a minimum, {myFeeds} contains a default group
        myFeeds = {"Default": [[]]}

    # for k, v in myFeeds.items():
    #     print(k)
    #     for i in v:
    #         print('   ', i[0])

    return myFeeds


# === MAIN MENU ================

def main_menu(myFeeds, titles_read):
    """
    Print the main menu on the screen and direct the user's choice.
    """
    menu = (
        '<c>heck feeds  ', '<a>dd feed     ', '<d>elete feed  ',
        '<m>ove feed    ', '               ', '               ',
        '<i>mport OPML  ', 'a<b>out        ', '<q>uit         ',
    )
    # 'e<x>port feeds '

    while True:
        print()
        for i in range(0, len(menu), 3):
            m = ''.join(menu[i:i+3])
            m = ''.join(menu[i:i+3])
            print(m)
        print()

        menu_choice = input('Choice: ')

        if menu_choice.upper() == 'Q':
            break

        elif menu_choice.upper() == 'A':
            myFeeds = add_feed(myFeeds)

        elif menu_choice.upper() == 'B':
            about()

        elif menu_choice.upper() == 'C':
            updated_feeds, bad_feeds, myFeeds = find_all_changes(myFeeds)
            myFeeds, updated_feeds, titles_read = list_updated_feeds(
                myFeeds, updated_feeds, titles_read, bad_feeds)

        elif menu_choice.upper() == 'D':
            myFeeds = del_feed(myFeeds)

        elif menu_choice.upper() == 'E':
            pass

        elif menu_choice.upper() == 'I':
            err, myFeeds = import_OPML(myFeeds)
            if err:
                print('Import failed or aborted.')
            else:
                print('OPML file successfully imported.')

        elif menu_choice.upper() == 'M':
            myFeeds = move_feed(myFeeds)

        elif menu_choice.upper() == 'X':
            pass

        else:
            print('*'*35)
            print('Enter a valid menu choice.')
            print('*'*35)
            continue

    return myFeeds, titles_read


def main():
    """
    The main program that organizes program flow.
    """

    # before starting the app, read [titles_read] and {myFeeds} from disk
    try:
        with open('titles_read.txt', 'r') as file:
            all_titles = file.readlines()
        titles_read = [line.strip('\n') for line in all_titles]
    except FileNotFoundError:
        titles_read = []

        # {myFeeds} structure:
        # -- 0: feed title
        # -- 1: feed RSS
        # -- 2: feed URL
        # -- 3: feed.ETag
        # -- 4: feed.modified
        # -- 5: feed.updated
        # -- 6: hash of last entry posted on website
        # -- 7: link to last entry posted on website
    myFeeds = load_myFeeds_dict()

    # display menu on screen
    myFeeds, titles_read = main_menu(myFeeds, titles_read)

    # before quitting the app save [titles_read] and {myFeeds}
    titles_read_set = set(titles_read)
    with open('titles_read.txt', 'w') as file:
        for i in titles_read_set:
            file.write(i + '\n')

    with open('myFeeds.json', 'w+') as file:
        file.write(json.dumps(myFeeds, ensure_ascii=False))

    return


if __name__ == '__main__':

    # get_revision_number()
    version_num = '1.0 rev17'
    print('ida ' + version_num[0:3] + ' - a small news feed reader')

    main()

    # ============ UTILITY FUNCTIONS FOR TESTING PURPOSES ============

    # -- print various attributes of a single RSS feed
    # get_feed_info('https://www.youtube.com/feeds/videos.xml?channel_id=UCxAS_aK7sS2x_bqnlJHDSHw')


    # -- print all the functions in this script
    # print_all_functions()
