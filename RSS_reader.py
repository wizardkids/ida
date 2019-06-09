"""
RSS_reader.py

Richard E. Rawson
2019-06-09

Program Description:

"""

from pprint import pprint
import pprint
import requests
import urlwatch
import feedparser


def get_url(url):
    """
    Get the content from a URL.
    """
    # set the headers like we are a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    # download the homepage
    r = requests.get(url, headers=headers)
    print(r.status_code, r.headers['content-type'], r.encoding)
    print()
    txt = r.text


def get_feed(rss):
    """
    Get a news feed.
    """
    newsfeed = feedparser.parse(rss)
    # entry = newsfeed.entries[1]

    for key in newsfeed["entries"]:
        print(key["title"])
        print()

    # dict_keys(['feed', 'entries', 'bozo', 'headers', 'etag', 'updated','updated_parsed', 'href', 'status', 'encoding', 'version', 'namespaces'])

    for k, v in newsfeed.items():
        x = input(k + ' press <enter>\n')
        print(k, v, '\n')

    # for k, v in entry.items():
    #     if k in ['published', 'published_parsed', 'updated', 'updated_parsed', 'tags', 'title']:
    #         print(k, v, '\n')


if __name__ == '__main__':
    # get_url('http://bushbabycolvin.blogspot.com/')
    get_feed('http://bushbabycolvin.blogspot.com/feeds/posts/default')
