"""
RSS_reader.py

Richard E. Rawson
2019-06-09

Program Description:
    A small, lightweight, RSS feed reader.

How to find RSS address for a website:
https://www.lifewire.com/what-is-an-rss-feed-4684568

How to use python to get RSS address from a website:
http://bluegalaxy.info/codewalk/2017/09/21/python-using-requests-to-get-web-page-source-text/

Simple news aggregator:
    https://newsapi.org/
    Source: https://www.youtube.com/watch?v=ZRlbf5P2iMA
"""

import hashlib
import json
import re
import textwrap
import urllib.parse
import webbrowser
from datetime import datetime
from inspect import getfullargspec, getmembers, isfunction
from sys import modules

import feedparser
import requests
from bs4 import BeautifulSoup as bs4

"""
=== DATA STRUCTURES ==============

myFeeds = {
    "Group": [
        {
            "feed title 1": [
                "0: feed RSS",
                "1: feed URL",
                "2: feed.ETag",
                "3: feed.modified",
                "4: changed/unchanged",
                "5: title of last entry posted on website",
                "6: link to last entry posted on website",
            ]
        },
        {"feed title 2": ["..."]},
    ]
}


updated_feeds = [{feed title: [
                        0: feed RSS
                        1: updated? (boolean)
                        2: [most recent post title, most recent post link]
                        3: [title, link]
                        4: ...
                        ]
                    }
                {feed title: [],}
            ]

=================================
"""


# === DEVELOPER UTILITY FUNCTIONS ================


def get_feed_info(rss):
    """
    Utility function to print information about a news feed. USED ONLY BY THE DEVELOPER.
    """

    if not rss:
        rss = input("RSS address: ")

    try:
        newsfeed = feedparser.parse(rss)
        # ['entries'] is the only dict in [newsfeed_keys]
        newsfeed_keys = [
            "feed",
            "entries",
            "bozo",
            "headers",
            "updated",
            "updated_parsed",
            "href",
            "status",
            "encoding",
            "version",
            "namespaces",
        ]

        feed_keys = [
            "title",
            "title_detail",
            "links",
            "link",
            "subtitle",
            "subtitle_detail",
            "updated",
            "updated_parsed",
            "language",
            "sy_updateperiod",
            "sy_updatefrequency",
            "generator_detail",
            "generator",
            "cloud",
            "image",
        ]

        entries_keys = [
            "title",
            "title_detail",
            "links",
            "link",
            "comments",
            "published",
            "published_parsed",
            "authors",
            "author",
            "author_detail",
            "tags",
            "id",
            "guidislink",
            "summary",
            "summary_detail",
            "content",
            "wfw_commentrss",
            "slash_comments",
            "media_content",
        ]

        print("RSS ADDRESS:\n", rss, sep="")
        try:
            print("\nBlog name:", newsfeed["feed"]["title"])
        except:
            print("\nNo feed title.")
        try:
            print("\nSubtitle:", newsfeed["feed"]["subtitle"])
        except:
            print("\nNo feed subtitle.")
        try:
            print("\nSite RSS:", newsfeed["href"])
        except:
            print("\nNo RSS address.")
        try:
            print("\nSite link:", newsfeed["feed"]["link"])
        except:
            print("\nNo link provided.")
        try:
            print("\nSite RSS address:", newsfeed["feed"]["links"][0]["href"])
        except:
            print("\nNo address provided.")
        try:
            print("\nSite ETag:", newsfeed["feed"]["ETag"])
        except:
            print("\nNo ETag.")
        try:
            print("\nSite modified:", newsfeed["feed"]["modified"])
        except:
            print("\nNo modified datetime.")
        try:
            print("\nSite updated:", newsfeed["feed"]["updated"])
        except:
            print("\nNo updated datetime.")
        try:
            print("\nLatest article posted:")
            print(newsfeed["entries"][0]["title"])
            print(newsfeed["entries"][0]["link"])
        except:
            print("\nNo entry link found.")

        g = input("List all entries? (Y/N) ").upper()
        if g == "Y":
            try:
                print("\nAll articles returned by feedparser():")
                for i in range(len(newsfeed["entries"])):
                    print(newsfeed["entries"][i]["title"])
                    print(newsfeed["entries"][i]["link"])
            except:
                print("\nNo entries found.")

    except IndexError:
        print("Oops. Encountered an error!")

    return


def print_all_functions():
    """
    Print all the functions, with their docStrings, used in this program. USED ONLY BY THE DEVELOPER.
    """
    module_functions = []

    func_name = ""
    func_list = []
    print("=" * 14, " ALL FUNCTIONS ", "=" * 14, sep="")
    line_width = 45

    for i in getmembers(
        modules[__name__],
        predicate=lambda f: isfunction(f) and f.__module__ == __name__,
    ):
        # i[0] is the function name
        # i[1] is the function itself

        # get the arguments for the i[1]
        v_args = getfullargspec(i[1])
        this_args = ""
        if v_args[0]:
            for j in range(len(v_args[0])):
                if this_args:
                    this_args = this_args + ", " + v_args[0][j]
                else:
                    this_args = v_args[0][j]

        print(i[0], "(", this_args, ")", sep="", end="")
        print(" " * 5, i[1].__doc__, sep="")

    return


# === IMPORT OPML FILE ================


def import_OPML(myFeeds):
    """
    Parse an OPML file and put group names, feed titles, and feed addresses in {myFeeds} in the form {'Group': [{feed title: [0: feed RSS, 1: feed URL, 2: feed.ETag, 3: feed.modified, 4: changed/unchanged, 5: title of last entry posted on website, 6: link to last entry posted on website]}]}. If no filename is entered, process is aborted. If FileNotFoundError is generated, notify user and <continue>. With confirmation, this file is overwritten each time an OPML file is read.

    Output: {myFeeds} is written to myFeeds.json.
    """

    while True:
        print()
        # get the name of the OPML file and put each line in a [list]
        file = input("Name of OPML file to import: ")
        if file:
            try:
                with open(file, "r") as f:
                    feedly = f.readlines()
            except FileNotFoundError:
                err = file + " not found."
                return err, myFeeds

            # extract group name from line
            rem_Feed_Group = re.compile(
                r"""
                        (.*<outline\stext=\")(?P<Feed_Group>\w*\s*\w*)
                        """,
                re.X,
            )
            # extract site title from the line
            rem_title = re.compile(
                r"""
                        (.*)(<outline.*text=\")(?P<Feed_Title>.*)(\"\stitle)
                        """,
                re.X,
            )

            # extract the RSS address from the line
            rem_RSS = re.compile(
                r"""
                            (.xmlUrl=\")(?P<RSS>.*)(\"\s)
                            """,
                re.X,
            )

            # extract HTML address from the line
            rem_HTML = re.compile(
                r"""
                            (.*htmlUrl=")(?P<URL>.*\")
                            """,
                re.X,
            )

            # put group, title, and RSS in {myFeeds}
            myFeeds = {"Default": {}}
            for ndx, line in enumerate(feedly):
                m_Feed_Group = re.search(rem_Feed_Group, line)
                m_Feed_Title = re.search(rem_title, line)
                m_RSS = re.search(rem_RSS, line)
                m_HTML = re.search(rem_HTML, line)
                if m_HTML:
                    this_URL = m_HTML.group("URL")[:-1]  # deletes the final "
                    # check to see if this is a valid URL
                    print("Checking if link is valid:", this_URL)
                    status_code = get_url_status(this_URL)
                    if status_code != 200:
                        continue
                if m_Feed_Group:
                    this_group = m_Feed_Group.group("Feed_Group")
                    myFeeds.update({this_group: {}})
                if m_Feed_Title:
                    this_title = m_Feed_Title.group("Feed_Title")
                if m_RSS:
                    this_RSS = m_RSS.group("RSS")
                if m_Feed_Title and m_RSS and m_HTML:
                    # add placeholders for feed.ETag, feed.modified, feed.updated, feed.last_title, feed.last_link
                    new_feed = {this_title: [
                        this_RSS, this_URL, "", "", "", "", ""]}

                    myFeeds[this_group].update(new_feed)
            break
        else:
            # if no file name was entered by user
            err = "Aborted."
            return err, myFeeds

    # with confirmation, write {myFeeds} to myFeeds.json
    r = input('Overwrite "myFeeds.json"? (YES/ABORT) ')
    if r.upper() == "YES":
        with open("myFeeds.json", "w+") as file:
            file.write(json.dumps(myFeeds, ensure_ascii=False))
        err = ""
    else:
        err = "Aborted."

    myFeeds = clean_feeds(myFeeds)

    return err, myFeeds


def get_url_status(url):
    """
    Get the status code for a URL. This function is used by import_OPML() to be sure each feed is accessible.
    """
    # set the headers like we are a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    }
    # download the url and get its status, if any
    try:
        r = requests.get(url, headers=headers)
        status_code = r.status_code
    except:
        print("Cannot connect to", url, "\nstatus code: ", status_code, sep="")
        status_code = 404

    return status_code


# === FEED MANAGEMENT ================


def add_feed(myFeeds):
    """
    Allows user to add a feed to {myFeeds}, including an optional group.

    - enter URL of feed and optionally a group (new or existing)
    - go to the URL, get the RSS feed address
    """
    err = ""
    print()
    # enter a URL, find the feed address, parse the feed
    f = input("Website address: ")

    try:
        print("\nLooking for RSS address...")
        result = findfeed(f)
        # check alternate RSS formats
        if not result:
            result = findfeed(f + "/feed")
        if not result:
            result = findfeed(f + "/?feed=rss")
        if not result:
            result = findfeed(f + "/feed/rss2")
        if not result:
            result = findfeed(f + "/blog/feed")
        if not result:
            result = findfeed(f + "/atom.xml")
        if not result:
            result = feedburner_rss(f)
        if not result and "youtube.com" in f:
            result = youtube_rss(f)
        if not result:
            result = feed_xml(f + "/index.xml")
        if not result:
            result = ""
    except:
        err = 'Did you forget "http://"?'
        return myFeeds, err

    if not result:
        print("\nFeed not found.")
        result = input("Enter RSS address manually: ")
        if not result:
            err = "Feed not added."
            return myFeeds, err

    rss_address = ""
    if isinstance(result, list):
        for r in result:
            if "comments" not in r:
                rss_address = r
    else:
        rss_address = result

    if rss_address:
        feed = feedparser.parse(rss_address)
    else:
        print("=" * 30, "\nNo RSS address found.\n", "=" * 30, "\n", sep="")
        rss_address = input("Enter RSS address manually: ")
        feed = feedparser.parse(rss_address)

        if not rss_address or not feed["entries"]:
            print(
                "=" * 30,
                "\nBad RSS address or no address found.\n",
                "=" * 30,
                "\n",
                sep="",
            )
            return myFeeds, err

    # add info into {ew_feed}
    """
    new_feed = {feed title: [
                        0: feed RSS
                        1: feed URL
                        2: feed.ETag
                        3: feed.modified
                        4: changed/unchanged
                        5: title of last entry posted on website
                        6: link to last entry posted on website
                        ]
                    }
    """
    new_feed = {}
    try:
        feed_title = feed["feed"]["title"]
    except:
        err = "No feed found."
        return myFeeds, err
    try:
        URL = feed["href"]
    except:
        URL = ""
    try:
        post_title = feed["entries"][0]["title"]
    except:
        post_title = ""
    try:
        post_link = feed["entries"][0]["link"]
    except:
        post_link = ""

    new_feed.update(
        {feed_title: [rss_address, URL, "", "",
                      "unchanged", post_title, post_link]}
    )

    # get the group that the feed should be added to...
    print("\nGroups:")
    cnt, kys = 0, list(myFeeds.keys())
    for grp_name in kys:
        cnt += 1
        print("  ", cnt, ": ", grp_name, sep="")

    print()

    while True:
        grp_name = input(
            "Add feed to which group number (or enter new group name)? ")
        if not grp_name:
            grp_name = 0
            break
        try:
            grp_name = int(grp_name)
            if grp_name < 1 or grp_name > len(kys):
                print(
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    len(kys),
                    "\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue
            else:
                break
        except:
            # if a non-integer was entered, assume it's a group name
            break

    # translate a group number into a group name so you can find it in myFeeds.keys()
    if isinstance(grp_name, int):
        if grp_name <= len(kys) and grp_name > 0:
            grp_name = kys[grp_name - 1]
        elif (grp_name == 0) or (grp_name == len(kys) + 1):
            grp_name = "Default"
        else:
            grp_name = ""

    # add {new_feed} to the appropriate group or create group if it doesn't exist
    if grp_name:
        try:
            # if the group already exists...
            myFeeds[grp_name].update(new_feed)
        except:
            myFeeds.update({grp_name: {}})
            myFeeds[grp_name].update(new_feed)

    myFeeds = clean_feeds(myFeeds)

    save_myFeeds(myFeeds)

    return myFeeds, err


def clean_feeds(myFeeds):
    """
    Deletes feeds that are duplicates or that have no RSS address. The latter can happen when a user deletes a feed: del_feed() sets the RSS address to ''
    """

    # delete any feed with no RSS address
    try:
        for group, feeds in myFeeds.items():
            for feed_title, feed_info in feeds.items():
                if not feed_info[0]:
                    feeds.pop(feed_title)
                    continue
    except:
        pass

    # find empty groups in {myFeeds} and delete them, excepting "Default"
    # this will only work for one empty group at a time
    for group, feeds in myFeeds.items():
        if group == "Default":
            continue
        elif not myFeeds[group]:
            myFeeds.pop(group)
            break
        else:
            pass

    save_myFeeds(myFeeds)

    return myFeeds


def del_feed(myFeeds, titles_read):
    """
    Delete a feed.
    """
    err = ""
    show_read = False

    feed_list, feed_cnt, grp_cnt = [], 0, 0

    # generate a list of feed names
    print()
    feed_cnt = print_feeds(myFeeds, show_read, titles_read)

    print()
    # get the number of the feed to delete
    while True:
        f = input("Number of feed to delete: ")
        if not f:
            break
        try:
            f = int(f)
            if f < 1 or f > feed_cnt:
                print(
                    "\n",
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    feed_cnt,
                    ".\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue
            else:
                break
        except ValueError:
            print(
                "\n",
                "=" * 30,
                "\nEnter an integer between 1 and ",
                feed_cnt,
                ".\n",
                "=" * 30,
                "\n",
                sep="",
            )
            continue

    # find that name in {myFeeds} and set link to ''
    ndx = 0
    for group, feeds in myFeeds.items():
        for feed_title, feed_info in feeds.items():
            ndx += 1
            if ndx == f:
                confirming = input("Delete " + feed_title + "? (Y/N)").upper()
                if confirming == 'Y':
                    myFeeds[group][feed_title][0] = ""

    print()

    myFeeds = clean_feeds(myFeeds)

    save_myFeeds(myFeeds)

    return myFeeds


def edit_RSS_address(myFeeds, titles_read):
    """
    Manually enter an RSS address for a feed.
    """
    show_read = False
    feed_cnt = print_feeds(myFeeds, show_read, titles_read)

    # get the number of the feed to edit
    while True:
        print()
        f = input("Enter number of feed to edit: ")
        if not f:
            break
        try:
            f = int(f)
            if f < 1 or f > feed_cnt:
                print(
                    "\n",
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    feed_cnt,
                    ".\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue
            else:
                break
        except ValueError:
            print(
                "\n",
                "=" * 30,
                "\nEnter an integer between 1 and ",
                feed_cnt,
                ".\n",
                "=" * 30,
                "\n",
                sep="",
            )
            continue

    while True:
        r = input("Enter an RSS address: ")
        if not r:
            break

        # find that name in {myFeeds} and set RSS_address to r
        ndx, done = 0, False
        for group, feeds in myFeeds.items():
            for feed_title, feed_info in feeds.items():
                ndx += 1
                if ndx == f:
                    print(
                        "\nSetting RSS address for ",
                        feed_title,
                        " to\n",
                        r,
                        "\n",
                        sep="",
                    )
                    ok = input("OK (Y/N)").upper()
                    if ok == "Y":
                        myFeeds[group][feed_title][0] = r
                        print(
                            "\n",
                            "=" * 30,
                            "\nRSS address for ",
                            feed_title,
                            "\nhas been set to:\n",
                            r,
                            "\n",
                            "=" * 30,
                            "\n",
                            sep="",
                        )
                    else:
                        print(
                            "\n",
                            "=" * 30,
                            "\nRSS address for ",
                            feed_title,
                            "\nhas not been changed.\n",
                            "=" * 30,
                            "\n",
                            sep="",
                        )
                    done = True
        if done:
            break

    myFeeds = clean_feeds(myFeeds)

    save_myFeeds(myFeeds)

    return myFeeds


def feed_xml(f):
    """
    Find a feed when the blog uses an xml address.
    """
    feed = feedparser.parse(f)
    href = feed["href"] + "/index.xml"
    result = href if "error" not in feed["href"] else ""
    return result


def feedburner_rss(f):
    """
    Find a feed when the blogger is using feedburner.
    """
    feed = requests.get(f)
    txt = feed.content.decode("utf-8")

    rem_uri = re.compile(
        r"""
            (href=\"//feedburner.google.com/)(.*uri=)(?P<feed_uri>.*)(&amp)
            """,
        re.X,
    )

    m_feed_uri = re.search(rem_uri, txt)

    if m_feed_uri:
        this_uri = m_feed_uri.group("feed_uri")
        result = "http://feeds.feedburner.com/" + this_uri
    else:
        result = ""

    return result


def findfeed(site):
    """
    Python 3 function for extracting RSS feeds from URLs.

    Source: https://gist.github.com/alexmill/9bc634240531d81c3abe
    Attribution: https://alex.miller.im/
    """
    raw = requests.get(site).text
    result = []
    possible_feeds = []
    try:
        html = bs4(raw, features="lxml")
    except:
        result = []
        return result
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
    base = parsed_url.scheme + "://" + parsed_url.hostname
    atags = html.findAll("a")
    for a in atags:
        href = a.get("href", None)
        if href:
            if "xml" in href or "rss" in href or "feed" in href:
                possible_feeds.append(base + href)
    for url in list(set(possible_feeds)):
        f = feedparser.parse(url)
        if len(f.entries) > 0:
            if url not in result:
                result.append(url)

    return result


def move_feed(myFeeds, titles_read):
    """
    Move a feed to a different group.
    """
    show_read = False

    while True:
        # list feeds, by group, numbering the feeds
        feed_cnt, grp_cnt, feed_list = 0, 0, []

        # generate a list of feed names
        print()
        feed_cnt = print_feeds(myFeeds, show_read, titles_read)

        print()
        # enter the number of the feed to move
        f = input("Number of feed to move: ")
        if not f:
            break
        try:
            f = int(f)
            if f < 1 or f > feed_cnt:
                print(
                    "\n",
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    feed_cnt,
                    ".\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue
            else:
                pass
        except ValueError:
            print(
                "\n",
                "=" * 30,
                "\nEnter an integer between 1 and ",
                feed_cnt,
                ".\n",
                "=" * 30,
                "\n",
                sep="",
            )
            continue

        # find that name in {myFeeds} and set title to ''
        ndx = 0
        for group, feeds in myFeeds.items():
            for fd_ttl, feed_info in feeds.items():
                ndx += 1
                if ndx == f:
                    print("  ", ndx, ": ", fd_ttl, sep="")
                    this_feed = myFeeds[group][fd_ttl]
                    feed_title = fd_ttl
                    myFeeds[group][fd_ttl][0] = ""
                    break

        # enter the name of the group to receive the moving feed
        group_name = input("Enter name of group receiving feed: ").strip()
        done = False

        # find that name in {myFeeds} and set title to ''
        ndx = 0
        for group, feeds in myFeeds.items():
            print(group)
            if group == group_name:
                try:
                    # if the group already exists...
                    myFeeds[group].update({feed_title: [this_feed]})
                except:
                    myFeeds.update({group_name: {}})
                    myFeeds[group_name].update({feed_title: [this_feed]})

        try:
            # find the group in {myFeeds}
            for k, v in myFeeds.items():
                if k.upper() == group_name.upper():
                    v.append(this_feed)
                    done = True
                    break
            # in case user entered a garbage group, feed is moved to "Default" group
            if not done:
                myFeeds["Default"].append(this_feed)
        except:
            break
        break

    myFeeds = clean_feeds(myFeeds)  # clean_feeds() also saves {myFeeds}

    return myFeeds


def rename_group(myFeeds):
    """
    Rename a group.
    """
    my_keys = []
    for ndx, k in enumerate(myFeeds.keys()):
        print(ndx + 1, ": ", k, sep="")
        my_keys.append(k)
    print()

    # get the name of the group to edit
    while True:
        ren = input("Number of group to rename or delete: ")
        if not ren:
            return myFeeds
        try:
            ren = int(ren)
            if ren == 1:
                print(
                    "\n",
                    "=" * 30,
                    '\nCannot rename or delete "Default" group',
                    "\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue
            elif (ren < 2) or (ren > len(myFeeds.keys())):
                print(
                    "\n",
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    len(myFeeds.keys()),
                    "\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue
            else:
                break
        except:
            print(
                "\n",
                "=" * 30,
                "\nEnter an integer between 1 and ",
                len(myFeeds.keys()),
                "\n",
                "=" * 30,
                "\n",
                sep="",
            )

    this_feed = my_keys[ren - 1]

    # get the new name for the group or enter DELETE to delete a group
    while True:
        new_name = input("Edited name (or type DELETE): ")
        for i in my_keys:
            if new_name.upper() == i.upper():
                print("That group already exists.")
                continue
            else:
                pass
        break

    if not new_name:
        return myFeeds
    elif new_name == "DELETE":
        if myFeeds[this_feed]:
            print(
                "\n",
                "=" * 30,
                "\nDelete all feeds in this group first.\n",
                "=" * 30,
                "\n",
                sep="",
            )
            y = ""
        else:
            y = input("Delete this group? (Y/N) ").upper()
            if y == "Y":
                y = "D"
            else:
                y = ""
    else:
        y = input("Change " + this_feed + " to " +
                  new_name + "? (Y/N) ").upper()

    if y == "Y":
        myFeeds[new_name] = myFeeds.pop(this_feed)
    elif y == "D":
        myFeeds.pop(this_feed)
    else:
        pass

    return myFeeds


def youtube_rss(f):
    """
    Find the feed for a youtube channel (not a single video!).


    """
    rem = re.compile(
        """
            (.*channel/)(?P<yt_channel>.*)""",
        re.X,
    )

    m_RSS = re.search(rem, f)
    if m_RSS:
        this_channel = m_RSS.group("yt_channel")
    else:
        this_channel = ""

    this_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=" + this_channel

    return this_RSS


def save_myFeeds(myFeeds):
    """
    Utility to save {myFeeds} to a file (myFeeds.json).
    """

    with open("myFeeds.json", "w+") as file:
        file.write(json.dumps(myFeeds, ensure_ascii=True))

    return None


# === CHECK FEEDS FOR UPDATES ================


def print_feeds(myFeeds, show_read, titles_read):
    """
    Print a numbered list of feeds, by group.
    Used by: del_feed(), edit_rss_address(), move_feed(), list_updated_feeds()
    """
    # retrieve history.json from disk; this file contains [updated_feeds] from the last time the user ran "<c>heck feeds" from the main menu
    try:
        with open("history.json", "r", encoding="utf-8") as file:
            updated_feeds = json.load(file)
    except FileNotFoundError:
        print('Run "<c>heck feeds" first.')
        updated_feeds = []
        return myFeeds, updated_feeds, titles_read

    ndx = 0
    for group, feeds in myFeeds.items():
        print(group)
        for feed_title, feed_info in feeds.items():
            # see if all articles in feed have been read
            for i in updated_feeds:
                all_read = False
                for k, v in i.items():
                    if k == feed_title:
                        cnt = 0
                        for a in range(2, len(v)):
                            cnt = (
                                cnt + 1
                                if hash_a_string(v[a][1]) in titles_read
                                else cnt
                            )
                        if cnt == len(v) - 2:
                            all_read = True
                        break
                if k == feed_title:
                    break
            ndx += 1
            if feed_info[4] == "unchanged" and not all_read:
                print(" *", ndx, ": ", feed_title, sep="")
            elif feed_info[4] == "unchanged":
                print("   ", ndx, ": ", feed_title, sep="")
            else:
                print(" *", ndx, ": ", feed_title, sep="")

    return ndx


def find_all_changes(myFeeds):
    """
    Go through the RSS feeds in {myFeeds} and return a list of feeds, with feeds being flagged that have changed since last access. Also return list of unreachable sites.
    """
    rss_list, updated_feeds, bad_feeds = [], [], []

    print("\nChecking RSS feeds for updates.\nThis may take a few seconds...\n", sep="")

    # iterate through {myFeeds} and get each RSS feed
    for group, feeds in myFeeds.items():
        # each group contains a list of websites for a given category.
        # so iterate through each item of each list
        for feed in feeds:
            # in case group is empty
            try:
                feed_info = feeds[feed]  # value of the key (feed title)
                rss_list.append([group, feed, feed_info[0]])
            except:
                break

    """
    rss_list = [
                [group, feed_title, rss_address]
                [...]
            ]
    """

    for rss_feed in rss_list:
        myFeeds, updated_feeds, bad_feeds = get_feed_status(
            rss_feed, myFeeds, updated_feeds, bad_feeds
        )

    with open("history.json", "w+", encoding="utf-8") as file:
        file.write(json.dumps(updated_feeds, ensure_ascii=False))

    print()
    return updated_feeds, bad_feeds, myFeeds


def get_feed_status(rss_feed, myFeeds, updated_feeds, bad_feeds):
    """
    Access a feed. Compare the title and link of the most recent post to the title and link stored in {myFeeds}. If they are the same, then the feed has not been updated. If they are different, then in [updated_feeds], flag the feed as having changed.

    https://pythonhosted.org/feedparser/http-ETag.html
    https://fishbowl.pastiche.org/2002/10/21/http_conditional_get_for_rss_hackers
    """

    group = rss_feed[0]
    feed_title = rss_feed[1]
    rss_address = rss_feed[2]

    feed_update = feedparser.parse(rss_address)

    # get the title of the most recent post on the website
    try:
        most_recent_title = feed_update["entries"][0]["title"]
    except:
        most_recent_title = ""

    # get the link to the most recent post on the website
    try:
        most_recent_link = feed_update["entries"][0]["link"]
    except IndexError:
        most_recent_link = ""

    if not most_recent_title or not most_recent_link:
        print(
            "\n",
            "=" * 30,
            "\nNo feed found for:\n",
            feed_title,
            "\n",
            "=" * 30,
            "\n",
            sep="",
        )

    try:
        last_title = myFeeds[group][feed_title][5]
    except:
        last_title = ""
    try:
        last_link = myFeeds[group][feed_title][6]
    except:
        last_link = ""

    """
    {this_feed} = {feed title: [
                        0: feed RSS
                        1: changed/unchanged
                        2: [most recent post title, most recent post link]
                        3: [title, link]
                        4: ...
                        ]
                    }
    """

    this_feed = {}

    # store information in {this_feed} for this feed
    try:
        this_feed.update(
            {feed_title: [rss_address, "", [
                most_recent_title, most_recent_link]]}
        )
        posts = []
        for i in feed_update["entries"]:
            posts.append([i["title"], i["link"]])

        this_feed[feed_title].extend(posts)

        # if the last_link or last_title in {myFeeds} != the most_recent_link or most_recent_title, then the feed has been updated, so update {myFeeds}
        if last_link != most_recent_link or last_title != most_recent_title:
            this_feed[feed_title][1] = "changed"
        else:
            this_feed[feed_title][1] = "unchanged"

        for group, feeds in myFeeds.items():
            for feed in feeds:
                if feed == feed_title:
                    # try:
                    if last_link != most_recent_link or last_title != most_recent_title:
                        feeds[feed_title][4] = "changed"
                        feeds[feed_title][5] = most_recent_title
                        feeds[feed_title][6] = most_recent_link
                    else:
                        feeds[feed_title][4] = "unchanged"
                # except:
                #     pass

        # finally, add {this_feed} to the list of feeds in [updated_feeds]
        updated_feeds.append(this_feed)
    except:
        # if feed_update['entries'] raises an exception, add [this_feed] to [bad_feeds]
        bad_feeds.append(this_feed)

    return myFeeds, updated_feeds, bad_feeds


def list_updated_feeds(myFeeds, titles_read=[], bad_feeds=[]):
    """
    Create a list of your feeds. Let user select from that list one feed and then create a list of updated articles for that feed. Default to filtering out articles that have been read. Let user choose articles to read online.
    """

    # retrieve history.json from disk; this file contains [updated_feeds] from the last time the user ran "<c>heck feeds" from the main menu
    try:
        with open("history.json", "r", encoding="utf-8") as file:
            updated_feeds = json.load(file)
    except FileNotFoundError:
        print('Run "<c>heck feeds" first.')
        updated_feeds = []
        return myFeeds, updated_feeds, titles_read

    # default for article list is to show only unread articles
    show_read = "unread"

    # =============================================================
    # ask if user wants to see a list of unreachable feeds...
    if len(bad_feeds) > 0:
        sf = input("\nShow bad feeds? (Y/N)").lower()
        show_bad = True if sf == "y" else False

        if show_bad:
            print()
            print("=" * 5, " UNREACHABLE FEEDS ", "=" * 5, sep="")
            for i in bad_feeds:
                print(i)
            print("=" * 29, sep="")
    # =============================================================

    print()
    while True:

        # list feeds, by group, numbering the feeds and flagging updated feeds
        feed_cnt = print_feeds(myFeeds, show_read, titles_read)

        # select a feed from the list of feeds
        while True:
            choice = input("\nSelect feed: ")
            if not choice:
                break
            try:
                choice = int(choice)
                if choice < 1 or choice > feed_cnt:
                    print(
                        "\n",
                        "=" * 30,
                        "\nEnter an integer between 1 and ",
                        len(updated_feeds),
                        "\n",
                        "=" * 30,
                        "\n",
                        sep="",
                    )
                    continue
                else:
                    break
            except ValueError:
                print(
                    "\n",
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    len(updated_feeds),
                    "\n",
                    "=" * 30,
                    "\n",
                    sep="",
                )
                continue

        # parse the choice of feeds that the user just made
        if not choice:
            break
        else:
            err = ""
            # [chosen_feed] is a list of attributes of a single feed
            chosen_feed = updated_feeds[choice - 1]
            feed_title = list(chosen_feed.keys())[0]

            # having chosen a feed, have user choose which post to view
            while True:
                """
                chosen_feed = {feed title: [
                                0: feed RSS
                                1: changed/unchanged
                                2: [most recent post title, most recent post link]
                                3: [title, link]
                                4: ...]
                            }
                """

                # find the number of articles in [chosen_feed] that have already been read
                cnt_unread_articles = 0
                for i in range(2, len(chosen_feed[feed_title])):
                    # hash the link and see if it's in [titles_read]
                    if hash_a_string(chosen_feed[feed_title][i][1]) not in titles_read:
                        cnt_unread_articles += 1
                if cnt_unread_articles == 0:
                    print(
                        "\n",
                        "=" * 30,
                        "\nAll articles have been read.\n",
                        "=" * 30,
                        "\n",
                        sep="",
                        end="",
                    )
                    m = input(
                        "\nUn-read some articles from this feed? (Y/N) ").lower()
                    print()
                    if m == "y":
                        titles_read = set_post_to_unread(
                            titles_read, chosen_feed)
                    else:
                        # set 'changed' in {myFeeds} for this feed to "unchanged"
                        # find the feed in {myFeeds}
                        ndx, done = 0, False
                        for group, feeds in myFeeds.items():
                            for this_title, feed_info in feeds.items():
                                if this_title == feed_title:
                                    myFeeds[group][feed_title][4] = "unchanged"
                                    done = True
                            if done:
                                break
                    break

                print()
                # print all the available posts in the [chosen_feed], depending on show_read setting
                # if show_read == "read", then print ALL posts, otherwise print only the unread posts
                for cnt in range(3, len(chosen_feed[feed_title])):
                    # if the article hasn't been read, flag it with "*"
                    if (
                        hash_a_string(chosen_feed[feed_title][cnt][1])
                        not in titles_read
                    ):
                        print(
                            "*", cnt - 2, ": ", chosen_feed[feed_title][cnt][0], sep=""
                        )

                    elif show_read == "read":
                        print(
                            " ", cnt - 2, ": ", chosen_feed[feed_title][cnt][0], sep=""
                        )

                print()

                if err:
                    print(err)

                # print a menu
                post_menu = [
                    "<t>oggle showing read articles",
                    "post to set to <u>nread",
                    "post to set to <r>ead",
                ]
                for i in range(len(post_menu)):
                    print(post_menu[i])
                print()

                # get a specific article from this feed
                post = (
                    input("\nSelect from menu or a numbered article: ").lower().strip()
                )
                if not post:
                    break

                if post in ["t", "u", "r"]:
                    if post == "t":
                        show_read = toggle_show_read_articles(show_read)
                    elif post == "u":
                        titles_read = set_post_to_unread(
                            titles_read, chosen_feed)
                    elif post == "r":
                        titles_read = set_post_to_read(
                            titles_read, chosen_feed)
                else:
                    try:
                        post = int(post)
                        # user should enter an integer between 1 and the number of entries in [chosen_feed]
                        if post < 0 or post + 1 > len(chosen_feed[feed_title]) - 2:
                            err = (
                                "=" * 30
                                + "\nEnter an integer between 1 and "
                                + str(len(chosen_feed) - 3)
                                + "\nor a menu item.\n"
                                + "=" * 30
                                + "\n"
                            )
                            continue
                    except ValueError:
                        err = (
                            "=" * 30
                            + "\nEnter an integer between 1 and "
                            + str(len(chosen_feed) - 2)
                            + "\nor a menu item.\n"
                            + "=" * 30
                            + "\n"
                        )
                        continue

                    if post:
                        this_link = chosen_feed[feed_title][post + 2][1]
                        # print('Showing...', chosen_feed[feed_title][post+2][0])
                        # print(this_link)
                        show_lastest_rss(this_link)

                        # hash link; put in [titles_read] so you know it's been read
                        titles_read.append(hash_a_string(this_link))
                        print()
                    else:
                        break

            print()

            if cnt_unread_articles == 0:
                continue
            elif not post:
                continue
            else:
                break

    print()

    return myFeeds, titles_read


def toggle_show_read_articles(show_read):
    """
    In list_updated_feeds(), toggle the listing of read articles.
    """
    show_read = "read" if show_read == "unread" else "unread"
    return show_read


def set_post_to_unread(titles_read, chosen_feed):
    """
    In list_updated_feeds(), set one or more read posts to unread.
    """
    feed_title = list(chosen_feed.keys())[0]

    print()
    while True:
        article_number = input("Number or range of post(s) to set to unread: ")
        print()

        # if the user enters a range of articles...
        if "-" in article_number:
            try:
                ndx = article_number.index("-")
                start_num = int(article_number[0:ndx])
                end_num = int(article_number[ndx + 1:]) + 1
            except ValueError:
                print(
                    "=" * 30,
                    "\nEnter a range of integers separated by a hyphen.\n",
                    "=" * 30,
                    sep="",
                )
                return titles_read
            for i in range(start_num, end_num):
                titles_read = set_to_unread_one_article(
                    i, chosen_feed, titles_read)
            break
        else:
            try:
                article_number = int(article_number)
            except:
                print(
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    len(chosen_feed[feed_title]) - 2,
                    "\n",
                    "=" * 30,
                    "\n",
                    sep="",
                    end="",
                )
                continue
            if not article_number:
                break
            else:
                titles_read = set_to_unread_one_article(
                    article_number, chosen_feed, titles_read
                )
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
        if "-" in article_number:
            try:
                ndx = article_number.index("-")
                start_num = int(article_number[0:ndx]) + 1
                end_num = int(article_number[ndx + 1:]) + 2
            except ValueError:
                print(
                    "=" * 30,
                    "\nEnter a range of integers separated by a hyphen.\n",
                    "=" * 30,
                    sep="",
                )
                return titles_read
            for i in range(start_num, end_num):
                titles_read = set_to_read_one_article(
                    i, chosen_feed, titles_read)
            break
        else:
            try:
                article_number = int(article_number)
            except:
                print(
                    "=" * 30,
                    "\nEnter an integer between 1 and ",
                    len(chosen_feed) - 3,
                    "\n",
                    "=" * 30,
                    "\n",
                    sep="",
                    end="",
                )
                continue
            if not article_number:
                break
            else:
                titles_read = set_to_read_one_article(
                    article_number + 1, chosen_feed, titles_read
                )
                break
    return titles_read


def set_to_read_one_article(article_number, chosen_feed, titles_read):
    """
    Utility function to set one article in a feed to 'read' status. Used by set_post_to_read().
    """
    feed_title = list(chosen_feed.keys())[0]

    link = hash_a_string(chosen_feed[feed_title][article_number + 1][1])

    titles_read.append(link)
    # strip out repeat titles
    titles_read = list(set(titles_read))

    return titles_read


def set_to_unread_one_article(article_number, chosen_feed, titles_read):
    """
    Utility function to set one article in a feed to 'unread' status. Used by set_post_to_unread().
    """
    feed_title = list(chosen_feed.keys())[0]

    try:
        link = hash_a_string(chosen_feed[feed_title][article_number + 2][1])
        # in case user chose a title that is unread...
        try:
            ndx = titles_read.index(link)
            titles_read.pop(ndx)
        except:
            print(
                "=" * 30,
                "\nTitle is already marked unread.\n",
                "=" * 30,
                "\n",
                sep="",
                end="",
            )
    except:
        print(
            "=" * 30,
            "\nEnter an integer between 1 and ",
            len(chosen_feed[feed_title]) - 3,
            "\n",
            "=" * 30,
            "\n",
            sep="",
            end="",
        )

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


def about(version_num, revision_number):
    """
    Information about the author and product.
    """
    print("=" * 45)

    txt1 = (
        "ida - a small news feed reader\n"
        + " version: "
        + str(version_num)
        + "\n"
        + "revision: "
        + str(revision_number)
        + "\n"
        + "  python: v3.7\n"
        + "  author: Richard E. Rawson\n\n"
    )

    txt2 = "ida is named after Ida B. Wells (July 16, 1862 to March 25, 1931), was an African-American journalist, abolitionist and feminist who led an anti-lynching crusade in the United States in the 1890s. She went on to found and become integral in groups striving for African-American justice."

    print("\n".join([fold(txt1) for txt1 in txt1.splitlines()]))
    print("\n".join([fold(txt2) for txt2 in txt2.splitlines()]))

    print("=" * 45)
    return


def fold(txt):
    """
    Utility function that textwraps 'txt' 45 characters wide.
    """
    return textwrap.fill(txt, width=45)


def hash_a_string(this_string):
    """
    Create a hash value for a string (this_string). This utility is used to hash links before storing the link in [titles_read]. Hashing saves disk space, speeds searching the [list], and, because of simplicity, reduces error.
    """
    return str(
        int(hashlib.sha256(this_string.encode("utf-8")).hexdigest(), 16) % 10 ** 8
    )


def load_myFeeds_dict():
    """
    Read myFeeds.json and return a dictionary of the RSS feeds. Each key is a group and each value is a list of RSS feeds in that group.
    """
    try:
        with open("myFeeds.json", "r") as file:
            myFeeds = json.load(file)
    except FileNotFoundError:
        # at a minimum, {myFeeds} contains a default group
        myFeeds = {"Default": []}

        myFeeds = load_myFeeds_dict()

    return myFeeds


# === MAIN MENU ================


def main_menu(myFeeds, titles_read, err):
    """
    Print the main menu on the screen and direct the user's choice.
    """
    menu = (
        "<i>mport OPML     ",
        "<c>heck feeds   ",
        "<a>dd feed    ",
        "<e>dit group      ",
        "<l>ist feeds    ",
        "<d>elete feed ",
        "edit <r>ss address",
        "                ",
        "<m>ove feed   ",
        "                  ",
        "a<b>out         ",
        "<q>uit        ",
    )

    while True:
        if err:
            print("\n", "=" * 30, "\n", err, "\n", "=" * 30, sep="")

        print()
        for i in range(0, len(menu), 3):
            m = "".join(menu[i: i + 3])
            m = "".join(menu[i: i + 3])
            print(m)
        print()

        menu_choice = input("Choice: ")

        if menu_choice.upper() == "Q":
            break

        elif menu_choice.upper() == "A":
            myFeeds, err = add_feed(myFeeds)

        elif menu_choice.upper() == "B":
            about(version_num, revision_number)

        elif menu_choice.upper() == "C":
            updated_feeds, bad_feeds, myFeeds = find_all_changes(myFeeds)
            myFeeds, titles_read = list_updated_feeds(
                myFeeds, titles_read, bad_feeds)

        elif menu_choice.upper() == "D":
            myFeeds = del_feed(myFeeds, titles_read)

        elif menu_choice.upper() == "E":
            myFeeds = rename_group(myFeeds)

        elif menu_choice.upper() == "G":
            get_feed_info("")

        elif menu_choice.upper() == "I":
            err, myFeeds = import_OPML(myFeeds)
            if err:
                print("Import failed or aborted.")
            else:
                print("OPML file successfully imported.")

        elif menu_choice.upper() == "L":
            myFeeds, titles_read = list_updated_feeds(myFeeds, titles_read)

        elif menu_choice.upper() == "M":
            myFeeds = move_feed(myFeeds, titles_read)

        elif menu_choice.upper() == "R":
            myFeeds = edit_RSS_address(myFeeds, titles_read)

        elif menu_choice.upper() == "X":
            pass

        else:
            print("*" * 35)
            print("Enter a valid menu choice.")
            print("*" * 35)
            continue

    return myFeeds, titles_read


def main():
    """
    The main program that organizes program flow.
    """

    # before starting the app, read [titles_read] and {myFeeds} from disk
    try:
        with open("titles_read.txt", "r") as file:
            all_titles = file.readlines()
        titles_read = [line.strip("\n") for line in all_titles]
    except FileNotFoundError:
        titles_read = []

    myFeeds = load_myFeeds_dict()

    # display menu on screen
    err = ""
    myFeeds, titles_read = main_menu(myFeeds, titles_read, err)

    # before quitting the app save [titles_read] and {myFeeds}
    titles_read_set = set(titles_read)
    with open("titles_read.txt", "w") as file:
        for i in titles_read_set:
            file.write(i + "\n")

    save_myFeeds(myFeeds)

    return


def get_revision_number():
    """
    Returns the revision number, which is the number of days since the initial coding of "ida" began on June, 10, 2019.
    """

    start_date = datetime(2019, 6, 10)
    tday = datetime.today()
    revision_delta = datetime.today() - start_date

    return revision_delta.days


if __name__ == "__main__":

    version_num = "1.0"
    revision_number = 30
    print("ida " + version_num + " - a small news feed reader")

    main()

    # ============ UTILITY FUNCTIONS FOR TESTING PURPOSES ============

    # -- print various attributes of a single RSS feed
    # get_feed_info('https://www.youtube.com/feeds/videos.xml?channel_id=UCxAS_aK7sS2x_bqnlJHDSHw')

    # -- print all the functions in this script
    # print_all_functions()

    # get revision number
    # rn = get_revision_number()
    # print(rn)
