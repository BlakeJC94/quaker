from collections import deque


class Cache:
    """Container class with a deque and a set for fast append/pop/lookup operations"""
    def __init__(self, *args, **kwargs):
        self.stash = deque(*args, **kwargs)

        self.registry = set(self.stash)
        self.maxlen = getattr(self.stash, "maxlen")

    def append(self, value):
        if self.maxlen and len(self.stash) == self.maxlen:
            self.registry.pop(self.stash.popleft())

        self.stash.append(value)
        self.registry.append(value)

    def pop(self):
        value = self.stash.pop()
        self.registry.pop(value)
        return value

    def __contains__(self, value):
        return value in self.registry

    def __len__(self):
        return len(self.stash)

    def __repr__(self):
        name = self.__class__.__name__
        return repr(self.stash).replace("deque", name, 1)