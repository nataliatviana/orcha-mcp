from orcha.config.load_config import get_enabled_servers


def test_disabled_server_is_filtered():
    config = {
        "mcps": {
            "server1": {"enabled": True},
            "server2": {"enabled": False},
        }
    }

    result = get_enabled_servers(config)

    assert "server1" in result
    assert "server2" not in result

def test_server_enabled_by_default():
    config = {
        "mcps": {
            "server1": {},
        }
    }

    result = get_enabled_servers(config)

    assert "server1" in result
