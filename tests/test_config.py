from orcha.config import load_config


def test_environment_field_loaded() -> None:
    config = load_config("orcha.json")

    server = config.mcp_servers["filesystem"]

    assert server.environment is not None
    assert server.environment["TEST_ENV"] == "hello"