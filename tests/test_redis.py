"""Make sure the test suite never talks to a real Redis server."""

import fakeredis
import redis


def test_redis_is_faked():
    """A client pointed at an unreachable server still stores data."""
    client = redis.Redis.from_url("redis://127.0.0.1:1/0")

    assert isinstance(client, fakeredis.FakeStrictRedis)

    client.set("django", "pictures")
    assert client.get("django") == b"pictures"
