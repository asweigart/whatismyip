"""WhatIsMyIP
By Al Sweigart al@inventwithpython.com

Fetch your public IP address from external sources."""

__version__ = '2020.8.5'

import re
import threading
import requests

# From https://stackoverflow.com/a/5284410/1893164
IPV4_REGEX = re.compile(r"""((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}""")  # type: Pattern

# From https://stackoverflow.com/a/17871737/1893164
IPV6_REGEX = re.compile(
    r"""(
([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|          # 1:2:3:4:5:6:7:8
([0-9a-fA-F]{1,4}:){1,7}:|                         # 1::                              1:2:3:4:5:6:7::
([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|         # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|  # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|  # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|  # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|  # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|       # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8
:((:[0-9a-fA-F]{1,4}){1,7}|:)|                     # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::
fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|     # fe80::7:8%eth0   fe80::7:8%1     (link-local IPv6 addresses with zone index)
::(ffff(:0{1,4}){0,1}:){0,1}
((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}
(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|          # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255  (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
([0-9a-fA-F]{1,4}:){1,4}:
((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}
(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])           # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)""",
    re.VERBOSE,
)  # type: Pattern


# Fake the user-agent because some services aren't friendly to bots.
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'}

# TODO - add type hints!

# TODO - more testing is required, especially if some/all of the sources are down.

SOURCES = ('https://ifconfig.co/ip',
           'https://icanhazip.com',
           'https://ipinfo.io/ip',
           'https://ipecho.net/plain',
           'https://ident.me',
           'http://curlmyip.net',
           'https://api.ipify.org',
           'https://ipaddr.site')


def whatismyip(minSources=3, timeout=1, numVerification=2):
    allResults = whataremyips(minSources, timeout, numVerification)
    resultsSet = frozenset(allResults.values())

    if len(resultsSet) == 1:
        return tuple(resultsSet)[0]
    else:
        # TODO - figure out how to handle when multiple IPs are returned, esp ipv4 and ipv6.
        # For now, just return one of them at random
        # Probably should do a count and go by that, since 9 sources giving one ip and 1 source giving another shouldn't be confusing.
        return tuple(resultsSet)[0]



def whataremyips(minSources=3, timeout=1, numVerification=2):
    results = {}
    allThreads = []
    for source in SOURCES:
        t = threading.Thread(target=_requestIpSourceWebsite, args=(source, results, timeout))
        t.start()
        allThreads.append(t)

    for t in allThreads:
        t.join()

    return results



def whatismyipv4(minSources=3, timeout=1, numVerification=2):
    pass


def whatismyipv6(minSources=3, timeout=1, numVerification=2):
    pass


def _requestIpSourceWebsite(ipUrl, resultsDict, timeout=1):
    try:
        response = requests.get(ipUrl, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        resultsDict[ipUrl] = response.text.strip()
    except:
        pass  # If something happened, just skip it. TODO - fix this

