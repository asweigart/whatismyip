from __future__ import division, print_function
import pytest
import whatismyip


def test_basic():
    # This is a fake web page I set up on my inventwithpython.com website.
    assert whatismyip.whatismyip(sources=('https://inventwithpython.com/whatismyip/',)) == '99.99.99.99'

    # Check that these don't cause exceptions:
    assert whatismyip.whatismyip()
    assert whatismyip.whatismyipv4()
    assert whatismyip.whatismyipv6()
    assert whatismyip.whatismylocalip()
    assert whatismyip.whatismyhostname()
    assert whatismyip.amionline()
    assert whatismyip.amionline(web_servers=whatismyip.ONLINE_WEB_SERVERS)

def test_can_connect_to_whatismyip_websites():
    for server in whatismyip.IP4_WEBSITES:
        pass
    for server in whatismyip.IP6_WEBSITES:
        pass

def test_can_connect_to_stun_servers():
    for server in whatismyip.STUN_SERVERS:
        pass

def test_can_connect_to_connectivity_websites():
    for server in whatismyip.ONLINE_WEB_SERVERS:
        pass


if __name__ == "__main__":
    pytest.main()
