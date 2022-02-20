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

On average these ip-finding functions take about half a second to run. Your results may vary.

Because whatismyip relies on online services, you always want to update to the latest version. This module uses [calendar versioning](https://calver.org/), such as version 2021.8.5 for the version released on August 5, 2021.

# How Does whatismyip Work?

There are several public STUN (Session Traversal Utilities for NAT) servers that return your IP address (as it appears to them). There are also several public websites that you can view in your browser:

* [https://ifconfig.co/ip](https://ifconfig.co/ip)
* [https://icanhazip.com](https://icanhazip.com)
* [https://ipinfo.io/ip](https://ipinfo.io/ip)
* [https://ipecho.net/plain](https://ipecho.net/plain)
* [https://ident.me](https://ident.me)
* [https://curlmyip.net](https://curlmyip.net)
* [https://api.ipify.org](https://api.ipify.org)
* [https://ipaddr.site](https://ipaddr.site)

The whatismyip module does not have any dependencies outside the Python standard library. It does not require Requests to be installed.


Support
-------

If you find this project helpful and would like to support its development, [consider donating to its creator on Patreon](https://www.patreon.com/AlSweigart).
