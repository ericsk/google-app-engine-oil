#!/usr/bin/env python

""" GAEO Utility methods."""
import re
from datetime import tzinfo, timedelta

def select_trusy(x, y):
    """Select the trusy value.

    TODO: document this function.

    Args:
        x:
        y:
    
    Returns:
    """
    return x if x else y

def bbcode(value):    
    """Convert the bbcodes to their HTML counterparts.

    Args:
        value: the input string that may contain bbcodes.

    Returns:
        The string with bbcodes converted to HTML.
    """
    bbdata = [
        (r'\[url\](.+?)\[/url\]', r'<a href="\1">\1</a>'),
        (r'\[url=(.+?)\](.+?)\[/url\]', r'<a href="\1">\2</a>'),
        (r'\[email\](.+?)\[/email\]', r'<a href="mailto:\1">\1</a>'),
        (r'\[email=(.+?)\](.+?)\[/email\]', r'<a href="mailto:\1">\2</a>'),
        (r'\[img\](.+?)\[/img\]', r'<img src="\1">'),
        (r'\[img=(.+?)\](.+?)\[/img\]', r'<img src="\1" alt="\2">'),
        (r'\[b\](.+?)\[/b\]', r'<b>\1</b>'),
        (r'\[i\](.+?)\[/i\]', r'<i>\1</i>'),
        (r'\[u\](.+?)\[/u\]', r'<u>\1</u>'),
        (r'\[quote\](.+?)\[/quote\]', r'<blockquote class="content-quote">\1</blockquote>'),
        (r'\[center\](.+?)\[/center\]', r'<div align="center">\1</div>'),
        (r'\[code\]\s?(.+?)\[/code\]', r'<blockquote class="code-segment"><code><pre>\1</pre></code></blockquote>'),
        (r'\[big\](.+?)\[/big\]', r'<big>\1</big>'),
        (r'\[small\](.+?)\[/small\]', r'<small>\1</small>'),
        ]

    for bbset in bbdata:
        p = re.compile(bbset[0], re.DOTALL)
        value = p.sub(bbset[1], value)

    #The following two code parts handle the more complex list statements
    temp = ''
    p = re.compile(r'\[list\](.+?)\[/list\]', re.DOTALL)
    m = p.search(value)
    if m:
        items = re.split(re.escape('[*]'), m.group(1))
        for i in items[1:]:
            temp = temp + '<li>' + i + '</li>'
        value = p.sub(r'<ul>'+temp+'</ul>', value)

    temp = ''
    p = re.compile(r'\[list=(.)\](.+?)\[/list\]', re.DOTALL)
    m = p.search(value)
    if m:
        items = re.split(re.escape('[*]'), m.group(2))
        for i in items[1:]:
            temp = temp + '<li>' + i + '</li>'
        value = p.sub(r'<ol type=\1>'+temp+'</ol>', value)

    return value


def safeout(value):
    """Converts the input string to an HTML segment.

    This function does 3 things:
     1. replaces angle brackets of HTML tags with &lt; and &gt;,
     2. converts the bbcodes to HTML tags,
     3. replaces newlines with <br> tags.

    Args:
        value: the input string to be escape-encoded.

    Returns:
        The escape-encoded string.
    """
    # strip tags
    pat = re.compile(r'<([^>]*?)>', re.DOTALL | re.M)
    value = re.sub(pat, '&lt;\\1&gt;', value)
    # apply bbcode
    value =  bbcode(value)
    # apply nl2br
    return re.sub(r'\n', '<br>', value)


class TaiwanTimeZone(tzinfo):
    """The tzinfo class for Taiwan's timezone."""
    ZERO = timedelta(0)
    PLUS_8 = timedelta(minutes=8*60)
    def utcoffset(self, dt):
        return self.PLUS_8

    def tzname(self, dt):
        return "CST"

    def dst(self, dt):
        return self.ZERO

