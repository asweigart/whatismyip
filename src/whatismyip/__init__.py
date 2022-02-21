"""WhatIsMyIP by Al Sweigart al@inventwithpython.com

Fetch your public IP address from external sources.

Example:
    >>> import whatismyip
    >>> whatismyip.amionline()
    True
    >>> whatismyip.whatismyip()
    '69.89.31.226'
    >>> whatismyip.whatismyipv4()
    '69.89.31.226'
    >>> whatismyip.whatismyipv6()
    '2345:0425:2CA1:0000:0000:0567:5673:23b5'
"""

__version__ = '2022.2.20'

import re
import binascii
import random
import socket
import urllib.request

from typing import Optional, Pattern
from collections.abc import Sequence

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


# If you have an IPv4 *and* IPv6 address, these websites give you your IPv4 address.
# (I haven't tested what they do if you only have an IPv6 address.)
IP4_WEBSITES = (#'https://ifconfig.co/ip',  # This is down as of 2022/02/19
           'https://ipinfo.io/ip',
           'https://ipecho.net/plain',
           'https://api.ipify.org',
           'https://ipaddr.site',)

IP6_WEBSITES = ('https://icanhazip.com',
            'https://ident.me',
            'https://curlmyip.net',
            'https://ip.seeip.org',)

IP_WEBSITES = IP4_WEBSITES + IP6_WEBSITES

# Popular web servers to test if we are online.
ONLINE_WEB_SERVERS = ('google.com', 'youtube.com', 'facebook.com', 'yahoo.com', 'reddit.com', 'wikipedia.org', 'ebay.com', 'bing.com', 'netflix.com', 'office.com', 'twitch.com', 'cnn.com', 'linkedin.com')


# Responsive servers that responded in less than 1.0 seconds, in order of fastest response time. Tested on 2022/02/19
STUN_SERVERS = ('stun.epygi.com:3478', 'stun.l.google.com:19302', 'stun.l.google.com:3478', 'relay.webwormhole.io:3478', 'stun.ooma.com:3478', 'stun.usfamily.net:3478', 'stun.rackco.com:3478', 'stun.voip.blackberry.com:3478', 'stun.freeswitch.org:3478', 'stun.voip.aebc.com:3478', 'stun.callwithus.com:3478', 'stun.vivox.com:3478', 'stun.ippi.fr:3478', 'stun.12connect.com:3478', 'stun.12voip.com:3478', 'stun.acrobits.cz:3478', 'stun.actionvoip.com:3478', 'stun.aeta.com:3478', 'stun.voipzoom.com:3478', 'stun3.l.google.com:19302', 'stun.1und1.de:3478', 'stun.aeta-audio.com:3478', 'stun.jumblo.com:3478', 'stun1.l.google.com:19302', 'iphone-stun.strato-iphone.de:3478', 'stun.antisip.com:3478', 'stun.it1.hr:3478', 'stun.ivao.aero:3478', 'stun4.l.google.com:19302', 'stun.etoilediese.fr:3478', 'stun.voippro.com:3478', 'stun.voipstunt.com:3478', 'stun.altar.com.pl:3478', 'stun.voipbuster.com:3478', 'stun.voipwise.com:3478', 'stun.voys.nl:3478', 'stun.internetcalls.com:3478', 'stun.ipshka.com:3478', 'stun.powervoip.com:3478', 'stun.rynga.com:3478', 'stun2.l.google.com:19302', 'stun.callromania.ro:3478', 'stun.gmx.net:3478', 'stun.linphone.org:3478', 'stun.myvoiptraffic.com:3478', 'stun.mywatson.it:3478', 'stun.schlund.de:3478', 'stun.sipgate.net:10000', 'stun.zoiper.com:3478', 'stun.voip.eutelia.it:3478', 'stun.voipbusterpro.com:3478', 'stun.voipgate.com:3478', 'stun.gmx.de:3478', 'stun.annatel.net:3478', 'stun.sipnet.ru:3478', 'stun.t-online.de:3478', 'stun.cheapvoip.com:3478', 'stun.easyvoip.com:3478', 'stun.intervoip.com:3478', 'stun.lowratevoip.com:3478', 'stun.nonoh.net:3478', 'stun.siptraffic.com:3478', 'stun.smartvoip.com:3478', 'stun.telbo.com:3478', 'stun.voipblast.com:3478', 'stun.voipgain.com:3478', 'stun.voipinfocenter.com:3478', 'stun.webcalldirect.com:3478', 'stun.zadarma.com:3478', 'stun.nextcloud.com:443', 'stun.freecall.com:3478', 'stun.justvoip.com:3478', 'stun.netappel.com:3478', 'stun.bluesip.net:3478', 'stun.freevoipdeal.com:3478', 'stun.voicetrading.com:3478', 'stun.voipcheap.co.uk:3478', 'stun.voipcheap.com:3478', 'stun.voipraider.com:3478', 'stun.dcalling.de:3478', 'stun.liveo.fr:3478', 'stun.lundimatin.fr:3478', 'stun.poivy.com:3478', 'stun.ppdi.com:3478', 'stun.xtratelecom.es:3478', 'stun.hoiio.com:3478', 'stun.voztele.com:3478', 'stun.mit.de:3478', 'stun.tng.de:3478', 'stun.pjsip.org:3478', 'stun.sipnet.net:3478', 'stun.twt.it:3478', 'stun.solnet.ch:3478', 'stun.cope.es:3478', 'stun.dus.net:3478', 'stun.cablenet-as.net:3478', 'stun.sovtest.ru:3478', 'stun.uls.co.za:3478', 'stun.halonet.pl:3478', 'stun.demos.ru:3478', 'stun.siplogin.de:3478', 'stun.cloopen.com:3478', 'stun.hosteurope.de:3478', 'stun.rockenstein.de:3478', 'stun.easycall.pl:3478')

# STUN attributes, in hex:
MAPPED_ADDRESS = '0001'
STUN_ATTR_LEN = 4

# STUN message types, in hex:
BIND_REQUEST_MSG = '0001'
BIND_RESPONSE_MSG = '0101'



def whatismyip():
    # type: () -> Optional[str]
    """Returns a str of your IP address, either IPv4 or IPv6. If offline or
    the IP address can't be determined, this returns None."""

    # Get ipv4 address from STUN servers first (they tend to be faster than the websites):
    # Note: STUN servers only return IPv4 addresses. This means that whatismyip() will almost
    # always return the IPv4 address of users who have both IPv4 and IPv6 addresses.
    # (TODO: Test this claim.)
    for i in range(3): # Make 3 attempts, otherwise assume accessing STUN is blocked for some reason.
        ip = _getIpFromSTUN()
        if ip is not None:
            return ip

    return _getIpFromHTTPS()


def whatismyipv4():
    # type: () -> Optional[str]
    """Returns a str of your IPv4 address. If offline or the IP address can't
    be determined, this returns None."""

    # Get ipv4 address from STUN servers first (they tend to be faster than the websites):
    # Note: STUN servers only return IPv4 addresses. (TODO: Test this claim.)
    for i in range(3): # Make 3 attempts, otherwise assume accessing STUN is blocked for some reason.
        ip = _getIpFromSTUN()
        if ip is not None:
            return ip

    return _getIpFromHTTPS(4)


def whatismyipv6():
    # type: () -> Optional[str]
    """Returns a str of your IPv6 address. If offline or the IP address can't
    be determined, this returns None."""
    return _getIpFromHTTPS(6)


def amionline():
    # type: () -> bool
    """Returns True if the system is currently on the internet, otherwise returns False. It determines this by
    attempting to connect to a popular web server in the ONLINE_WEB_SERVRS list."""
    servers = list(ONLINE_WEB_SERVERS)
    random.shuffle(servers)

    for i in range(3):
        try:
            socket.getaddrinfo(servers[i], 'www')
            return True
        except socket.gaierror:
            continue  # Retry with the next server.
    return False


def _getIpFromHTTPS(ipVersion=None, sources=None):
    # type: (Optional[int], Optional[Sequence[str]]) -> Optional[str]
    """Returns a str of your IPv4 or IPv6 address from a "whatismyip" website.
    If offline or the IP address can't be determined, this returns None.

    :param ipVersion: The IP address version you want: either 4, 6, or None
    for either.
    :type ipVersion: The ints 4 or 6, or None.
    :param sources: Optional sequence of websites that return an IP address,
    similar to the ones in IP_WEBSITES."""

    if sources is None:
        # By default, we keep checking each website in IP_WEBSITES until
        # we get a valid response.
        ipWebsites = list(IP_WEBSITES)
    else:
        ipWebsites = list(sources)
    random.shuffle(ipWebsites)

    for ipWebsite in ipWebsites:
        try:
            response = urllib.request.urlopen(ipWebsite)

            charsets = response.info().get_charsets()
            if len(charsets) == 0 or charsets[0] is None:
                charset = 'utf-8'  # Use utf-8 by default
            else:
                charset = charsets[0]

            userIp = response.read().decode(charset).strip()

            if ipVersion == 4 and IPV4_REGEX.match(userIp):
                return userIp
            elif ipVersion == 6 and IPV6_REGEX.match(userIp):
                return userIp
            elif ipVersion is None and (IPV4_REGEX.match(userIp) or IPV6_REGEX.match(userIp)):
                return userIp
            else:
                # Either the ipVersion argument is invalid or the ip website
                # returned some unexpected text that is not an IP address.
                continue
        except:
            pass  # Network error, just continue on to next website.

    # Either all of the websites are down or returned invalid response
    # (unlikely) or you are disconnected from the internet.
    return None


def _b2hex(abytes):
    # type: (bytes) -> str
    """Converts bytes to an ascii string of hex digits, e.g. """
    return binascii.b2a_hex(abytes).decode('ascii')


def _getIpFromSTUN(stunHost=None, stunPort=None):
    # type: (Optional[str], Optional[int]) -> Optional[str]
    """Retrieves the IPv4 address from a STUN (Session Traversal Utilities for NAT) server. If stunHost and stunPort
    aren't specified, then a public STUN server is randomly selected from the STUN_SERVERS tuple."""
    SOURCE_IP = '0.0.0.0'
    SOURCE_PORT = 54320

    if stunHost is None and stunPort is None:
        # If a STUN server isn't provided, use a random one from the STUN_SERVERS:
        stunHost, stunPortStr = random.choice(STUN_SERVERS).split(':')
        stunPort = int(stunPortStr)


    sockObj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockObj.settimeout(2)
    sockObj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sockObj.bind((SOURCE_IP, SOURCE_PORT))

    # STUN transaction IDs are arbitrary numbers:
    transID = ''.join(random.choice('0123456789ABCDEF') for i in range(32))

    data = binascii.a2b_hex(BIND_REQUEST_MSG + '0000' + transID)
    while True:
        attemptsRemaining = 3
        while True:
            # Loop until we get a response or run out of retry attempts.
            try:
                sockObj.sendto(data, (stunHost, stunPort))
            except socket.gaierror:
                # Most likely you are offline.
                return None

            try:
                buf, addr = sockObj.recvfrom(2048)
                break
            except Exception:
                attemptsRemaining -= 1
                if attemptsRemaining == 0:
                    return None  # Could not connect to the stun server.

        transIDMatch = transID.upper() == _b2hex(buf[4:20]).upper()
        if transIDMatch and _b2hex(buf[0:2]) == BIND_RESPONSE_MSG:
            messageRemaining = int(_b2hex(buf[2:4]), 16)
            base = 20
            while messageRemaining:
                stunAttribute = _b2hex(buf[base:(base + 2)])
                stunAttributeLength = int(_b2hex(buf[(base + 2):(base + 4)]), 16)

                ip = '.'.join([
                    str(int(_b2hex(buf[base + 8:base + 9]), 16)),
                    str(int(_b2hex(buf[base + 9:base + 10]), 16)),
                    str(int(_b2hex(buf[base + 10:base + 11]), 16)),
                    str(int(_b2hex(buf[base + 11:base + 12]), 16))
                ])

                if stunAttribute == MAPPED_ADDRESS:
                    # There are several IP addresses in the STUN response, but only MAPPED_ADDRESS is our user's IP.
                    return ip
                else:
                    pass # We ignore all the other stun attributes.

                base += STUN_ATTR_LEN + stunAttributeLength
                messageRemaining -= STUN_ATTR_LEN + stunAttributeLength
            break

    sockObj.close()
    return ip



def _profileStunServers():
    """Run this to get the response times of the STUN servers in STUN_SERVERS."""
    import time, pprint
    results = []
    for stunServer in STUN_SERVERS:
        stunHost = stunServer.split(':')[0]
        stunPort = int(stunServer.split(':')[1])

        startTime = time.time()
        resultIp = _getIpFromSTUN(stunHost, stunPort)
        elapsedTime = round(time.time() - startTime, 2)
        results.append((stunServer, resultIp, elapsedTime))
    pprint.pprint(results)
    return results


def _profileHttpsServers():
    """Run this to get the response times of the STUN servers in STUN_SERVERS."""
    import time, pprint
    results = []
    for ipWebsite in IP_WEBSITES:

        startTime = time.time()
        resultIp = _getIpFromHTTPS(sources=[ipWebsite])
        elapsedTime = round(time.time() - startTime, 2)
        results.append((ipWebsite, resultIp, elapsedTime))
    pprint.pprint(results)
    return results
