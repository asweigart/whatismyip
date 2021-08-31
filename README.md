# whatismyip
Fetch your public IP address from external sources with Python.

Install with `pip install whatismyip`

    >>> import whatismyip
    >>> whatismyip.whatismyip()
    '52.250.42.157'

Because whatismyip relies on online services, you always want to update to the latest version. This module uses [calendar versioning](https://calver.org/), such as version 2021.8.5 for the version released on August 5, 2021.

2021/08/26 TODO: This documentation is currently incomplete.

# How Does whatismyip Work?

There are several public websites that return your IP address (as it appears to them):

* [https://ifconfig.co/ip](https://ifconfig.co/ip)
* [https://icanhazip.com](https://icanhazip.com)
* [https://ipinfo.io/ip](https://ipinfo.io/ip)
* [https://ipecho.net/plain](https://ipecho.net/plain)
* [https://ident.me](https://ident.me)
* [https://curlmyip.net](https://curlmyip.net)
* [https://api.ipify.org](https://api.ipify.org)
* [https://ipaddr.site](https://ipaddr.site)

The whatismyip module uses [the Requests module](https://docs.python-requests.org/en/master/index.html) to make connections to these sites, then returns the IPv4 or IPv6 address the give.


# Road Map of Future Features

The whatismyip module is meant to be simple and small, so not many future features are planned. I might add something to grab geolocation information as well, but that's about it.