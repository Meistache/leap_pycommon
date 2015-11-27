
from leap.common.events.catalog import EVENTS
import threading
from threading import Thread

class EventType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<EventType: %s>' % self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, EventType):
            return self.name == other.name
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, EventType):
            return self.name != other.name
        else:
            return NotImplemented

lcl = locals()
for event in EVENTS:
    lcl[event] = EventType(event)


class Event(object):
    def __init__(self, event_type, content):
        self.event_type = event_type
        self.content = content


TYPE_EVENT=1
TYPE_COMMAND=2


class EventDispatcher(object):
    def _event_dispatch_loop(self):
        running = True
        while running:
            entry_type, entry_value = self._queue.get()
            try:
                if TYPE_EVENT == entry_type:
                    self._dispatch_to_callbacks(entry_value)
                    pass  # we need to dispatch
                else:
                    running = False  # for now assume we are supposed to stop
            finally:
                self._queue.task_done()

    def __init__(self, queue, legacy_backends):
        self._legacy_backends = legacy_backends
        self._queue = queue
        self._callbacks = {}

    def start(self):
        self._thread = Thread(target=self._event_dispatch_loop)
        self._thread.start()

    def stop(self):
        self._queue.put((TYPE_COMMAND, "stop"))
        self._queue.join()

    def register(self, event_type, callback):
        self._add_callback(event_type, callback)

    def _add_callback(self, event_type, callback):
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []

        self._assert_callback_not_registered_for_type(event_type, callback)

        self._callbacks[event_type].append(callback)

    def _assert_callback_not_registered_for_type(self, event_type, callback):
        if callback in self._callbacks[event_type]:
            raise ValueError('Callback %s already registered for event %s' % (callback, event_type))

    def emit(self, event):
        self._queue.put((TYPE_EVENT, event))

    def _event_dispatch_loop(self):
        running = True
        while running:
            entry_type, entry_value = self._queue.get()
            try:
                if TYPE_EVENT == entry_type:
                    self._dispatch_to_callbacks(entry_value)
                    pass  # we need to dispatch
                else:
                    running = False  # for now assume we are supposed to stop
            finally:
                self._queue.task_done()

    def _dispatch_to_callbacks(self, event):
        callbacks = self._callbacks.get(event.event_type, [])

        for c in callbacks:
            c(event.content)
