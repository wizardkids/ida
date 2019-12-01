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
Installation could not be easier. **_ida_** requires only one file: `ida.py`.

If you have python 3.7+ installed, you can download `ida.py` and, assuming python.exe is in your PATH, run:

    `python ida.py`


To _download_ one file, click on the file name. On the next screen, click the "Download" button.

## **Usage**
- The program is menu driven, and includes only essential capabilities as noted under *Features*. There are no options or preferences.
- See *Recommended setup* below for creating a shortcut.
- for easiest usage, python 3 must be in the PATH environment variable.

## **Recommended setup**
If you want to run "ida" from your desktop, here is what you need to do:
1. Put all of the files in this repository in a directory of your choice.
2. Modify ida.bat as noted within the .bat file.
3. Create a shortcut on your desktop.
4. In the properties dialog for the shortcut
   - change "TARGET" to the full path, including the filename, for ida.bat.
   - change "START IN" to the path for the directory that holds ida.bat

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
