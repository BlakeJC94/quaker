from collections import deque

from pytest import fixture

from quaker.core.record_filter import Cache, RecordFilter


class TestCache:
    @fixture
    def cache_input(self):
        return ["aaa", "bbb", "ccc"]

    def test_cache_init(self, cache_input):
        cache = Cache(cache_input)
        assert cache.stash == deque(cache_input)
        assert cache.registry == set(cache_input)

    def test_cache_append(self, cache_input):
        cache = Cache(cache_input)
        new_item = "ddd"
        cache.append(new_item)
        assert new_item in cache

    def test_cache_append_maxlen(self, cache_input):
        maxlen = 3
        cache = Cache(cache_input, maxlen)
        new_item = "ddd"
        cache.append(new_item)
        assert new_item in cache
        assert not cache_input[0] in cache

    def test_cache_append_maxlen_duplicate(self, cache_input):
        maxlen = 3
        cache = Cache(cache_input, maxlen)
        new_item = cache_input.copy()[0]
        cache.append(new_item)
        assert new_item in cache
        assert cache_input[0] in cache

    def test_cache_pop(self, cache_input):
        cache = Cache(cache_input)
        removed = cache.pop()
        assert not removed in cache
        assert removed == cache_input[-1]


def test_record_filter():

