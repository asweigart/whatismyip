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
    >>> whatismyip.whatismylocalip()  # Returns local IPs of all network cards.
    ('192.168.189.1', '192.168.220.1', '192.168.56.1', '192.168.1.201')
    >>> whatismyip.whatismyhostname()
    'GIBSON'
"""

__version__ = '2024.2.20'

import re
import binascii
import random
import socket
import urllib.request

from typing import Optional, Pattern, Tuple, Sequence

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
IP4_WEBSITES = ('https://ifconfig.co/ip',
                'https://v4.ident.me',
                'https://v4.tnedi.me',
                'https://ipinfo.io/ip',
                'https://ipecho.net/plain',
                'https://api.ipify.org',
                'https://ipaddr.site',
                'https://ifconfig.me/ip',
                'https://checkip.amazonaws.com/',
                )

# Note: In the event that your system only has an IPv4 address and no IPv6 address,
# these websites will return your IPv4 address.
IP6_WEBSITES = ('https://icanhazip.com',
                'https://v6.ident.me',
                'https://v6.tnedi.me',
                'https://tnedi.me/',
                'https://curlmyip.net',
                #'https://ip.seeip.org',  # Tested on 2024/02/20, had an certificate that expired on 2023/10/03
                'https://wtfismyip.com/text',
                )

IP_WEBSITES = IP4_WEBSITES + IP6_WEBSITES

# TODO - add other websites that provide this info in a web page, along with a regex that can pull out the IP address.
# Example: http://checkip.dyndns.org

# Popular web servers to test if we are online. (2024/02/20 - youtube.com was removed since it is blocked in some countries)
ONLINE_WEB_SERVERS = ('google.com', 'facebook.com', 'yahoo.com', 'reddit.com', 'wikipedia.org', 'ebay.com', 'bing.com', 'netflix.com', 'office.com', 'twitch.com', 'cnn.com', 'linkedin.com')


# Responsive servers that responded in less than 0.3 seconds, in order of fastest response time. Re-test their speeds by calling _profile_stun_servers().

# Tested on 2023/04/27 from Houston, TX, USA:
#STUN_SERVERS = ('stun.epygi.com:3478', 'stun.l.google.com:19302', 'stun.l.google.com:3478', 'relay.webwormhole.io:3478', 'stun.ooma.com:3478', 'stun.usfamily.net:3478', 'stun.rackco.com:3478', 'stun.voip.blackberry.com:3478', 'stun.freeswitch.org:3478', 'stun.voip.aebc.com:3478', 'stun.callwithus.com:3478', 'stun.vivox.com:3478', 'stun.ippi.fr:3478', 'stun.12connect.com:3478', 'stun.12voip.com:3478', 'stun.acrobits.cz:3478', 'stun.actionvoip.com:3478', 'stun.aeta.com:3478', 'stun.voipzoom.com:3478', 'stun3.l.google.com:19302', 'stun.1und1.de:3478', 'stun.aeta-audio.com:3478', 'stun.jumblo.com:3478', 'stun1.l.google.com:19302', 'iphone-stun.strato-iphone.de:3478', 'stun.antisip.com:3478', 'stun.it1.hr:3478', 'stun.ivao.aero:3478', 'stun4.l.google.com:19302', 'stun.etoilediese.fr:3478', 'stun.voippro.com:3478', 'stun.voipstunt.com:3478', 'stun.altar.com.pl:3478', 'stun.voipbuster.com:3478', 'stun.voipwise.com:3478', 'stun.voys.nl:3478', 'stun.internetcalls.com:3478', 'stun.ipshka.com:3478', 'stun.powervoip.com:3478', 'stun.rynga.com:3478', 'stun2.l.google.com:19302', 'stun.callromania.ro:3478', 'stun.gmx.net:3478', 'stun.linphone.org:3478', 'stun.myvoiptraffic.com:3478', 'stun.mywatson.it:3478', 'stun.schlund.de:3478', 'stun.sipgate.net:10000', 'stun.zoiper.com:3478', 'stun.voip.eutelia.it:3478', 'stun.voipbusterpro.com:3478', 'stun.voipgate.com:3478', 'stun.gmx.de:3478', 'stun.annatel.net:3478', 'stun.sipnet.ru:3478', 'stun.t-online.de:3478', 'stun.cheapvoip.com:3478', 'stun.easyvoip.com:3478', 'stun.intervoip.com:3478', 'stun.lowratevoip.com:3478', 'stun.nonoh.net:3478', 'stun.siptraffic.com:3478', 'stun.smartvoip.com:3478', 'stun.telbo.com:3478', 'stun.voipblast.com:3478', 'stun.voipgain.com:3478', 'stun.voipinfocenter.com:3478', 'stun.webcalldirect.com:3478', 'stun.zadarma.com:3478', 'stun.nextcloud.com:443', 'stun.freecall.com:3478', 'stun.justvoip.com:3478', 'stun.netappel.com:3478', 'stun.bluesip.net:3478', 'stun.freevoipdeal.com:3478', 'stun.voicetrading.com:3478', 'stun.voipcheap.co.uk:3478', 'stun.voipcheap.com:3478', 'stun.voipraider.com:3478', 'stun.dcalling.de:3478', 'stun.liveo.fr:3478', 'stun.lundimatin.fr:3478', 'stun.poivy.com:3478', 'stun.ppdi.com:3478', 'stun.xtratelecom.es:3478', 'stun.hoiio.com:3478', 'stun.voztele.com:3478', 'stun.mit.de:3478', 'stun.tng.de:3478', 'stun.pjsip.org:3478', 'stun.sipnet.net:3478', 'stun.twt.it:3478', 'stun.solnet.ch:3478', 'stun.cope.es:3478', 'stun.dus.net:3478', 'stun.cablenet-as.net:3478', 'stun.sovtest.ru:3478', 'stun.uls.co.za:3478', 'stun.halonet.pl:3478', 'stun.demos.ru:3478', 'stun.siplogin.de:3478', 'stun.cloopen.com:3478', 'stun.hosteurope.de:3478', 'stun.rockenstein.de:3478', 'stun.easycall.pl:3478')
# Tested on 2024/02/20 from Brooklyn, NY, USA:
STUN_SERVERS = ('stun.freeswitch.org:3478', 'stun.l.google.com:19302', 'stun.l.google.com:3478', 'stun.voip.blackberry.com:3478', 'stun.vivox.com:3478', 'stun.usfamily.net:3478', 'stun.epygi.com:3478', 'stun.voipzoom.com:3478', 'stun.rynga.com:3478', 'stun2.l.google.com:19302', 'stun.voipbusterpro.com:3478', 'stun.cheapvoip.com:3478', 'stun.easyvoip.com:3478', 'stun.lowratevoip.com:3478', 'stun.nonoh.net:3478', 'stun.siptraffic.com:3478', 'stun.voipinfocenter.com:3478', 'stun.webcalldirect.com:3478', 'stun.freecall.com:3478', 'stun.justvoip.com:3478', 'stun.voicetrading.com:3478', 'stun.dcalling.de:3478', 'stun.liveo.fr:3478', 'stun.voip.aebc.com:3478', 'stun.ippi.fr:3478', 'stun.12voip.com:3478', 'stun3.l.google.com:19302', 'stun.jumblo.com:3478', 'stun.voipstunt.com:3478', 'stun.internetcalls.com:3478', 'stun.freevoipdeal.com:3478', 'stun.voipcheap.com:3478', 'stun.voipraider.com:3478', 'stun.actionvoip.com:3478', 'stun.powervoip.com:3478', 'stun.myvoiptraffic.com:3478', 'stun.intervoip.com:3478', 'stun.smartvoip.com:3478', 'stun.telbo.com:3478', 'stun.voipblast.com:3478', 'stun.voipgain.com:3478', 'stun.netappel.com:3478', 'stun.acrobits.cz:3478', 'stun.antisip.com:3478', 'stun.voipwise.com:3478', 'stun.voipgate.com:3478', 'stun.zadarma.com:3478', 'stun.twt.it:3478', 'stun.solnet.ch:3478', 'stun4.l.google.com:19302', 'stun.voippro.com:3478', 'stun.mywatson.it:3478', 'stun.t-online.de:3478', 'stun.ppdi.com:3478', 'stun.tng.de:3478', 'stun.siplogin.de:3478', 'stun.linphone.org:3478', 'stun.sipgate.net:10000', 'stun.gmx.de:3478', 'stun.voipcheap.co.uk:3478', 'stun.aeta.com:3478', 'stun.1und1.de:3478', 'stun.aeta-audio.com:3478', 'stun.callromania.ro:3478', 'stun.gmx.net:3478', 'stun.schlund.de:3478', 'stun.voip.eutelia.it:3478', 'stun.bluesip.net:3478', 'stun.voztele.com:3478', 'stun.rockenstein.de:3478', 'stun.voipbuster.com:3478', 'stun.it1.hr:3478', 'stun.12connect.com:3478', 'stun.zoiper.com:3478', 'stun.voys.nl:3478', 'stun.nextcloud.com:443', 'stun.dus.net:3478', 'stun.poivy.com:3478', 'stun.ipshka.com:3478', 'stun.halonet.pl:3478', 'stun1.l.google.com:19302', 'stun.cablenet-as.net:3478', 'stun.annatel.net:3478', 'stun.cope.es:3478', 'stun.hoiio.com:3478', 'stun.uls.co.za:3478')


# STUN attributes, in hex:
MAPPED_ADDRESS = '0001'
STUN_ATTR_LEN = 4

# STUN message types, in hex:
BIND_REQUEST_MSG = '0001'
BIND_RESPONSE_MSG = '0101'

# Note: Because this module is named whatismyip and it's a small module that likely people will only use for its
# whatismyip() function, I've kept the all lowercase, no underscore naming convention for the public functions.
# It would be too confusing to have whatismyip.what_is_my_ip(). Please don't complain about pep8 to me.

def whatismyip():
    # type: (Optional[Sequence[str]]) -> Optional[str]
    """Returns a str of your IP address, either IPv4 or IPv6. If offline or
    the IP address can't be determined, this returns None."""

    # Get ipv4 address from STUN servers first (they tend to be faster than the websites):
    # Note: STUN servers only return IPv4 addresses. This means that whatismyip() will almost
    # always return the IPv4 address of users who have both IPv4 and IPv6 addresses.
    # (TODO: Test this claim.)
    for i in range(3):  # Make 3 attempts, otherwise assume accessing STUN is blocked for some reason.
        ip = _get_ip_from_stun()  # Check a random STUN server.
        if ip is not None:
            return ip

    return _get_ip_from_https()


def whatismyipv4():
    # type: () -> Optional[str]
    """Returns a str of your IPv4 address. If offline or the IP address can't
    be determined, this returns None."""

    # Get ipv4 address from STUN servers first (they tend to be faster than the websites):
    # Note: STUN servers only return IPv4 addresses. (TODO: Test this claim.)
    for i in range(3):  # Make 3 attempts, otherwise assume accessing STUN is blocked for some reason.
        ip = _get_ip_from_stun()  # Check a random STUN server.
        if ip is not None:
            return ip

    return _get_ip_from_https(4)


def whatismyipv6():
    # type: () -> Optional[str]
    """Returns a str of your IPv6 address, or None if offline or you don't have an IPv6 address."""
    return _get_ip_from_https(6)


def whatismylocalip():
    return tuple(socket.gethostbyname_ex(socket.gethostname())[2])


def whatismyhostname():
    # type: () -> str
    return socket.gethostname()


def amionline(web_servers=None): # type: (Optional[List[str]]) -> bool
    """Return True if the system is currently on the internet, otherwise returns False.

    It determines this by attempting to connect to a popular web server in the `ONLINE_WEB_SERVERS` list.

    :param web_servers: A list of web server domain names to check for connectivity (or `ONLINE_WEB_SERVERS` if
        None), defaults to None.
    :type web_servers: list, optional
    :return: True if the system is online, False if not online.
    :rtype: bool
    """
    # If web_servers is not provided, use the default list of popular web servers.
    if web_servers is None:
        web_servers = list(ONLINE_WEB_SERVERS)

    # Shuffle the list of web servers to try a random sequence.
    random.shuffle(web_servers)

    # Try to connect to up to 3 randomly selected web servers.
    for i in range(3):
        try:
            # Attempt to get address information for the current web server.
            socket.getaddrinfo(web_servers[i], 'www')
            # If successful, return True to indicate that the system is online.
            return True
        except socket.gaierror:
            # If an error occurs, continue to the next server in the shuffled list.
            continue

    # If all three attempts have failed, return False to indicate that the system is offline.
    return False

# Note: Private functions will use snake_case.

def _get_ip_from_https(ip_version=None, web_servers=None):
    # type: (Optional[int], Optional[Sequence[str]]) -> Optional[str]
    """Returns a str of your IPv4 or IPv6 address from a "whatismyip" website.
    If offline or the IP address can't be determined, this returns None.

    :param ip_version: The IP address version you want: either 4, 6, or None
    for either.
    :type ip_version: The ints 4 or 6, or None.
    :param web_servers: Optional sequence of websites that return an IP address,
    similar to the ones in IP_WEBSITES."""

    if web_servers is None:
        # By default, we keep checking each website in IP_WEBSITES until
        # we get a valid response.
        ipWebsites = list(IP_WEBSITES)
    else:
        ipWebsites = list(web_servers)
    random.shuffle(ipWebsites)

    for ipWebsite in ipWebsites:  # Go through all ip website servers, return the first valid response.
        try:
            response = urllib.request.urlopen(ipWebsite)

            charsets = response.info().get_charsets()
            if len(charsets) == 0 or charsets[0] is None:
                charset = 'utf-8'  # Use utf-8 by default
            else:
                charset = charsets[0]

            userIp = response.read().decode(charset).strip()

            if ip_version == 4 and IPV4_REGEX.match(userIp):
                return userIp
            elif ip_version == 6 and IPV6_REGEX.match(userIp):
                return userIp
            elif ip_version is None and (IPV4_REGEX.match(userIp) or IPV6_REGEX.match(userIp)):
                return userIp
            else:
                # Either the ip_version argument is invalid or the ip website
                # returned some unexpected text that is not an IP address.
                # (Or the user asked for, say, ipv4 and got an ipv6 address.)
                continue
        except:
            pass  # Network error, just continue on to next website.

    # Either all of the websites are down or returned invalid response
    # (unlikely) or you are disconnected from the internet (likely).
    return None


def _b2hex(abytes):
    # type: (bytes) -> str
    """Converts bytes to an ascii string of hex digits, e.g. """
    return binascii.b2a_hex(abytes).decode('ascii')


def _get_ip_from_stun(stun_servers=None):
    # type: (Optional[str], Optional[int]) -> Optional[str]
    """Retrieves the IPv4 address from a STUN (Session Traversal Utilities for NAT) server. If stunHost and stunPort
    aren't specified, then a public STUN server is randomly selected from the STUN_SERVERS tuple."""
    SOURCE_IP = '0.0.0.0'
    SOURCE_PORT = 54320

    if stun_servers is None:
        # If a STUN server isn't provided, use a random one from the STUN_SERVERS:
        #stunHost, stunPortStr = random.choice(STUN_SERVERS).split(':')
        #stunPort = int(stunPortStr)
        stunServer = random.choice(STUN_SERVERS)
    else:
        # Pick a random STUN server from sources to use.
        stunServer = random.choice(stun_servers)

    # Turn the '0.0.0.0:54320' string in stunServer to '0.0.0.0' and 54320:
    stunHost, stunPortStr = stunServer.split(':')
    stunPort = int(stunPortStr)

    sockObj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockObj.settimeout(2)
    sockObj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sockObj.bind((SOURCE_IP, SOURCE_PORT))

    # STUN transaction IDs are arbitrary numbers:
    transID = ''.join(random.choice('0123456789ABCDEF') for i in range(32))

    data = binascii.a2b_hex(BIND_REQUEST_MSG + '0000' + transID)
    while True:
        attempts_remaining = 3
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
                attempts_remaining -= 1
                if attempts_remaining == 0:
                    return None  # Could not connect to the stun server.

        transIDMatch = transID.upper() == _b2hex(buf[4:20]).upper()
        if transIDMatch and _b2hex(buf[0:2]) == BIND_RESPONSE_MSG:
            message_remaining = int(_b2hex(buf[2:4]), 16)
            base = 20
            while message_remaining:
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
                message_remaining -= STUN_ATTR_LEN + stunAttributeLength
            break

    sockObj.close()
    return ip



def _profile_stun_servers():
    """Run this to get the response times of the STUN servers in STUN_SERVERS."""
    import time
    import pprint
    results = []
    for stunServer in STUN_SERVERS:
        elapsedTimes = []
        for i in range(3):  # Get the average of 3 timings.
            startTime = time.time()
            resultIp = _get_ip_from_stun([stunServer])
            elapsedTimes.append(round(time.time() - startTime, 2))
            time.sleep(0.1)  # Maybe this pause is not needed? I'm being superstitious.
        elapsedTime = sum(elapsedTimes) / 3
        print('DEBUG:', (stunServer, resultIp, elapsedTime))
        results.append((stunServer, resultIp, elapsedTime))
    results.sort(key=lambda x: x[2])
    pprint.pprint(results)
    results_for_STUN_SERVERS_constant = [i[0] for i in results if i[2] < 0.3 and i[1] is not None]  # 0.3 second max response time.
    return tuple(results_for_STUN_SERVERS_constant)


def _profile_https_servers():
    """Run this to get the response times of the HTTPS servers in IP_WEBSITES."""
    import time
    import pprint
    results = []
    for ipWebsite in IP_WEBSITES:

        startTime = time.time()
        resultIp = _get_ip_from_https(web_servers=[ipWebsite])
        elapsedTime = round(time.time() - startTime, 2)
        print('DEBUG:', (ipWebsite, resultIp, elapsedTime))
        results.append((ipWebsite, resultIp, elapsedTime))
    results.sort(key=lambda x: x[2])
    pprint.pprint(results)
    results_no_times = [(i[0], i[1]) for i in results if i[2] < 2.0]  # 2 second max response time.
    pprint.pprint(results_no_times)
    return results_no_times
