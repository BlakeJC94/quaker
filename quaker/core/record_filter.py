import logging
from collections import deque

logger = logging.getLogger(__name__)

# TODO Test RecordFilter
# - [ ] filtered input, retained IDs
# - [ ] check events are retained up to maxlen

class Cache:
    """Container class with a deque and a set for fast append/pop/lookup operations"""

    def __init__(self, *args, **kwargs):
        self.stash = deque(*args, **kwargs)

        self.registry = set(self.stash)
        self.maxlen = getattr(self.stash, "maxlen")

    def append(self, value):
        if self.maxlen and len(self.stash) == self.maxlen:
            self.registry.remove(self.stash.popleft())

        self.stash.append(value)
        self.registry.add(value)

    def pop(self):
        value = self.stash.pop()
        self.registry.remove(value)
        return value

    def __contains__(self, value):
        return value in self.registry

    def __len__(self):
        return len(self.stash)

    def __repr__(self):
        name = self.__class__.__name__
        return repr(self.stash).replace("deque", name, 1)

class RecordFilter(Cache):
    def __call__(self, records, event_ids):
        body = []
        duplicate_events = 0
        for event_id, line in zip(event_ids, records):
            if event_id in self:
                duplicate_events += 1
            else:
                body.append(line)
                self.append(event_id)

        if duplicate_events > 0:
            logger.warning(f"{duplicate_events=}")
        return body
