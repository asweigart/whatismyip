# whatismyip
Fetch your public IP address from external sources with Python.

Install with `pip install whatismyip`

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

On average these ip-finding functions take about half a second to run. Your results may vary.

Because whatismyip relies on online services, you always want to update to the latest version. This module uses [calendar versioning](https://calver.org/), such as version 2024.2.20 for the version released on February 20, 2024.

# How Does whatismyip Work?

There are several public STUN (Session Traversal Utilities for NAT) servers (listed in the whatismip.STUN_SERVERS variable, listed in order of response speed) that return your IP address (as it appears to them). There are also several public websites that you can view in your browser (listed in the whatismyip.IP4_WEBSITES, whatismyip.IP6_WEBSITES, and whatismyip.IP_WEBSITES):

* [https://ifconfig.co/ip](https://ifconfig.co/ip)
* [https://icanhazip.com](https://icanhazip.com)
* [https://ipinfo.io/ip](https://ipinfo.io/ip)
* [https://ipecho.net/plain](https://ipecho.net/plain)
* [https://v6.ident.me](https://v6.ident.me)
* [https://v4.ident.me](https://v4.ident.me)
* [https://v6.tnedi.me](https://v6.tnedi.me)
* [https://v4.tnedi.me](https://v4.tnedi.me)
* [https://curlmyip.net](https://curlmyip.net)
* [https://api.ipify.org](https://api.ipify.org)
* [https://ipaddr.site](https://ipaddr.site)
* [https://ip.seeip.org](https://ip.seeip.org)

The whatismyip module does not have any dependencies outside the Python standard library. It does not require Requests to be installed.


Support
-------

If you find this project helpful and would like to support its development, [consider donating to its creator on Patreon](https://www.patreon.com/AlSweigart).
