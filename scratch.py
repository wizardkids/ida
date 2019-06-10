"""
scratch.py

Richard E. Rawson
2019-05-26

Program Description:

"""

import timeit
from pprint import pprint
import requests
import urlwatch
import re
import feedparser


def scratch():
    """
    This utility function uses no arguments, but can contain anything that needs to be tested and the function will be timed automatically, below.
    """
    pass


scratch()


# ======================== TIMEIT: DO NOT DELETE ========================
# set num to the number of times you want to run scratch(); NOTE: print statments will print in the terminal num times!
# num = 1000000
# t1 = timeit.Timer("scratch()", "from __main__ import scratch")
# # the printed number gives the total time; so time using num=10 will be ten times longer than num=1 unless you divide t1 by 10; using large numbers for num increases overhead time, apparently
# t = t1.timeit(number=num)
# print('\nscratch ran ', num, ' times in: ',
#       '{0:0.6f}'.format(t), " sec", sep='')
# print('\nscratch ran once on average in: ',
#       '{0:0.6f}'.format(t/num*1000000), ' microsec', sep='')
# ========================================================================

"""
https://www.geeksforgeeks.org/timeit-python-examples/

Note: Pay attention to the fact that the output is the execution time of number times iteration of the code snippet, not the single iteration. For a single iteration exec. time, divide the output time by number.
"""
