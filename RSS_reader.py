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

# todo -- add ability to UNREAD a post
# todo -- figure out how to spead up get_feed_status(). What is the best way of determining if a feed post has been read? Is ETag, modified, etc. required? They may not be for many blogs, but what about Nature?


def get_feed_info(rss):
    """
    Utility function to print information about a news feed. USED ONLY BY THE DEVELOPER.
    """
    rss = 'https://leashoflonging.wordpress.com/feed/'
    rss = 'https://hebendsdown.wordpress.com/feed/'
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

        try:
            print('\nSite RSS:', newsfeed['href'])
        except:
            print('\nNo RSS address.')
        try:
            print('\nSite link:', newsfeed['feed']['link'])
        except:
            print('\nNo link provided.')
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
            myFeeds = {}
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


def get_feed_status(rss, updated_feeds, bad_feeds, myFeeds):
    """
    Access a feed and return its status code.

    arg rss contains:
        feed title
        RSS address
        link to the latest post
    """
    # -- https://pythonhosted.org/feedparser/http-ETag.html

    # ? The basic concept is that a feed publisher may provide a special HTTP header, called an ETag, when it publishes a feed. You should send this ETag back to the server on subsequent requests. If the feed has not changed since the last time you requested it, the server will return a special HTTP status code (304) and no feed data.
    # ? see: https://fishbowl.pastiche.org/2002/10/21/http_conditional_get_for_rss_hackers

    # get the most recent ETag, Last-Modified, updated, and hashed title from {myFeeds} by finding the correct list within {myFeeds} using rss[0]
    for k, v in myFeeds.items():
        for newsfeed in v:
            if newsfeed[0] == rss[0]:
                last_ETag = newsfeed[3]
                last_modified = newsfeed[4]
                last_updated = newsfeed[5]
                last_title = newsfeed[6]
                last_link = newsfeed[7]

    # check if new version exists by sending last_ETag, last_modified, and last_updated back to the server:

    feed_update = feedparser.parse(rss[1])
    try:
        current_link = feed_update['entries'][0]['link']
    except IndexError:
        current_link = ''

    if last_ETag and last_modified:
        feed_update = feedparser.parse(
            rss, etag=last_ETag, modified=last_modified)
    elif last_ETag and not last_modified:
        feed_update = feedparser.parse(rss, etag=last_ETag)
    elif last_modified and not last_ETag:
        feed_update = feedparser.parse(rss, modified=last_modified)
    elif last_updated:
        feed_update = feedparser.parse(rss, updated=last_updated)
    else:
        # use the hashed title to determine if a change has happened
        feed_update = feedparser.parse(rss[1])
        current_title = ''
        try:
            current_title = feed_update['entries'][0]['title']
        except:
            pass
        if last_title == hash_a_string(current_title):
            status = 304
        else:
            pass

    # then... get the status reported by the server
    try:
        status = feed_update['status']
    except KeyError:
        status = 304

    # if status is other than 304, then add this title to [updated_feeds]
    # -- [rss] structure to be added to [updated_feeds]:
        # -- fed title
        # -- RSS address
        # -- the most recent post link
        # -- n items containing lists of [post-title, post-link]
    try:
        if status != 304:
            for ndx, i in enumerate(feed_update['entries']):
                rss.append([i['title'], i['link']])
            
            rss[2] = current_link
            updated_feeds.append(rss)
            for k, v in myFeeds.items():
                for feed in v:
                    if feed[0] == rss[0]:
                        try:
                            feed[6] = hash_a_string(current_title)
                            feed[7] = feed_update['entries'][0]['link']
                        except:
                            pass
                        break
    except:
        bad_feeds.append(rss)

    return updated_feeds, bad_feeds, myFeeds


def find_all_changes(myFeeds):
    """
    Go through the RSS feeds in {myFeeds} and return a list of feeds that have changed since last access. Also return list of unreachable sites.
    """
    rss_list, updated_feeds, unchanged_feeds = [], [], []
    other_feeds, bad_feeds = [], []
    site_200, site_301, site_302, site_303 = [], [], [], []
    site_403, site_410 = [], []

    # iterate through {myFeeds} and get each RSS feed
    for group in myFeeds.values():
        # each group contains a list of websites for a given category.
        # so iterate through each item of each list
        for i in group:
            rss_list.append([i[0], i[1], i[7]])

    for rss in rss_list:
        # [rss] entering get_feed_status():
            # -- feed title
            # -- RSS address
            # -- link to the latest post

        updated_feeds, bad_feeds, myFeeds = get_feed_status(
            rss, updated_feeds, bad_feeds, myFeeds)

        # for each rss feed, [uptdate_feeds] returned by get_feed_status():
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


def get_url_status(url):
    """
    Get the status code for a URL.
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
    Return the latest articles for a website as a list of titles.
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


def list_updated_feeds(updated_feeds, titles_read):
    """
    Create a list of updated feeds from which the user can choose a feed to visit.
    """
    print()
    while True:
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
                     print('Enter an integer between 1 and ',len(updated_feeds),  sep='')
                     continue
                else:
                    break
            except ValueError:
                print('Enter an integer between 1 and ',
                      len(updated_feeds), sep='')
                continue

        if not choice:
            break
        else:
            err = ''

            # have user choose which post to view
            while True:
                # structure of [updated_feeds]
                # -- feed title
                # -- RSS address
                # -- the link to the most recent post
                # -- n items containing lists of [post-title, post-link]
                chosen_feed = updated_feeds[choice-1]
                # pprint(chosen_feed)
                print()
                for cnt in range(3, len(chosen_feed)):
                    if hash_a_string(chosen_feed[cnt][0]) not in titles_read:
                        print(cnt-2, ': ', chosen_feed[cnt][0], sep='')
                    else:
                        print('*', cnt-2, ': ', chosen_feed[cnt][0], sep='')

                print()

                if err:
                    print(err)
                post = input('Read which post? ')
                if not post:
                    break

                try:
                    post = int(post)
                    if post + 2 < 3 or post + 3 > len(chosen_feed):
                        err = 'Enter an integer between 1 and ' + str(len(chosen_feed)-3)
                        continue
                except ValueError:
                    err = 'Enter an integer between 1 and ' + str(len(chosen_feed)-3)
                    continue

                if post:
                    # print('showing', chosen_feed[post+2][0])
                    show_lastest_rss(chosen_feed[post+2][1])
                    current_title = hash_a_string(chosen_feed[post+2][0])
                    titles_read.append(current_title)
                else:
                    break

            if not post:
                continue

    return titles_read


def main_menu(myFeeds, titles_read):
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
            break
        elif menu_choice.upper() == 'A':
            about()
        elif menu_choice.upper() == 'C':
            updated_feeds, bad_feeds, myFeeds = find_all_changes(myFeeds)
            # updated_feeds:
            # [('Ignatian Spirituality', 'http://feeds.feedburner.com/dotMagis?format=xml'), ...]
            titles_read = list_updated_feeds(updated_feeds, titles_read)


        elif menu_choice.upper() == 'E':
            pass
        elif menu_choice.upper() == 'I':
            err, myFeeds = import_OPML(myFeeds)
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

    get_revision_number()
    version_num = '0.1 rev11'
    print('ida ' + version_num[0:3] + ' - a small news feed reader')

    main()

    """
    FUNCTIONS NEEDED:
        create myFeeds.json where:
            - keys: feed groups
            - values: [list] of RSS feeds for each group:
                - feed.title, RSS, HTML, feed.ETag, feed.modified, feed.updated
            - should contain a blank group for feeds that don't belong to a group
            -- import_OPML() 
                can create this file from an OPML file

        need functions that allow creating and editing of myFeeds.json
            1. get a HTML address
            2. fxn to read feed source content and use regex to get RSS address
            3. fields:
            ['Ignatian Spirituality', 'http://feeds.feedburner.com/dotMagis?format=xml', 'https://www.ignatianspirituality.com', '6c132-941-ad7e3080', 'Fri, 11 Jun 2012 23:00:34 GMT', 'time.struct_time(tm_year=2012, tm_mon=3, tm_mday=6, tm_hour=23, tm_min=00, tm_sec=34, tm_wday=6, tm_yday=66, tm_isdst=0)', hash the title for ['entries'][0]['title']]

            [Site title, RSS address, HTML address, ETag, modified, updated, hashed-title for top entry]

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
                        -compare current feed.ETag and/or feed.modified or feed.updated with the same values stored in {myFeeds}
                        - hash the title for ['entries'][0] (the most recent page) and see if that hash exists in [titles_read]; if not, then site has changed
                    - if site has changed (updated):
                        - store this feed (RSS) in [updated_feeds]
                        - update feed.ETag, feed.modified, feed.updated.parsed, and hash the title for ['entries'][0]['title'] in {myFeeds}

        3. from [updated_feeds]:
            - for each title, hash the title and then check in [titles_read]. If it already exists, then don't list the title since you've already read it
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

            (b) create a hash of the title and store in [titles_read]
                    -- hash = hash_a_string(this_string)

        6. after selecting a number and choosing (a) or (b) from step #5, loop back to step (3)



    before quitting the app, write [titles_read] to file
    when restarting, reload [titles_read] from file
 

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
    # changed_sites, bad_feeds = find_all_changes(myFeeds)

    # -- print all the functions in this script
    # print_all_functions()
