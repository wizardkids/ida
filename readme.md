# **_ida_ - a command-line RSS feed reader**

## **Why a home-grown feed reader?**
Google Reader was wonderful and then it went away. Others followed and died. I currently use Feedly and it's great (mostly) but for how long?

**_ida_** is designed to be lightweight. It does nothing in the background; it does not monitor websites continuously. Consequently, checking websites can be relatively slow: **_ida_** can update 20 feeds in 14 seconds, which is a whole lot faster than you can manually perform the same task. **_AND_**, it will never be sunset!

## **Features:**
- import OPML files
- add feeds by entering a URL; ida finds the RSS address automatically (most of the time!); if it can't, **_ida_** will ask you for the feed address
- delete feeds
- group similar feeds together
- rename or delete groups
- move feeds between groups
- manually edit an RSS address for a feed
- check all feeds for updates since last check
- notify if a feed is unreachable
- read a selected title from a feed in your browser
- set status of a title or range of titles to "unread"
- set status of a title or range of titles to "read"

## **Installation:**
Installation could not be easier. **_ida_** requires only one file: either `ida.py` or `ida.exe`.

1. If you have python 3.7+ installed, you can download `ida.py` and, assuming python.exe is in your PATH, run:

    `python ida.py`

2. Download `ida.exe` and run the executable. No other files are needed.

3. Download `ida.py` and use [pyinstaller](https://www.pyinstaller.org/) (or equivalent) to build your own executable.

To _download_ one file, click on the file name. On the next screen, click the "Download" button.

## **Required python modules:**
- bs4
- datetime
- feedparser
- hashlib
- inspect
- json
- re
- requests
- sys
- textwrap
- urllib.parse
- webbrowser
