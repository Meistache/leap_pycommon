
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
TYPE_TRANSPORT_EVENT=2
TYPE_COMMAND=3


class Transport(object):
    pass


class EventDispatcher(object):
    def __init__(self, queue, transports=[]):
        self._transports = transports
        self._queue = queue
        self._callbacks = {}

        self._register_with_transports()

    def _register_with_transports(self):
        for t in self._transports:
            t.register_event_dispatcher(self)

    def start(self):
        self._thread = Thread(target=self._event_dispatch_loop)
        self._thread.setDaemon(True)
        self._thread.start()

    def stop(self):
        self._queue.put((TYPE_COMMAND, "stop"))
        self._queue.join()

    def register(self, event_type, callback):
        self._add_callback(event_type, callback)
        self._transport_should_notify_us(event_type)

    def _add_callback(self, event_type, callback):
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []

        self._assert_callback_not_registered_for_type(event_type, callback)

        self._callbacks[event_type].append(callback)

    def _transport_should_notify_us(self, event_type):
        for t in self._transports:
            t.notify_for(event_type)

    def _assert_callback_not_registered_for_type(self, event_type, callback):
        if callback in self._callbacks[event_type]:
            raise ValueError('Callback %s already registered for event %s' % (callback, event_type))

    def emit(self, event):
        self._queue.put((TYPE_EVENT, event))

    def emit_from_transport(self, transport, event):
        self._queue.put((TYPE_TRANSPORT_EVENT, event))

    def _event_dispatch_loop(self):
        running = True
        while running:
            entry_type, entry_value = self._queue.get()
            try:
                if TYPE_EVENT == entry_type:
                    self._dispatch_to_callbacks(entry_value)
                    self._dispatch_to_transports(entry_value)
                    # option b, it would be asynchronous with client code (pulled from queue)
                elif TYPE_TRANSPORT_EVENT == entry_type:
                    self._dispatch_to_callbacks(entry_value)
                else:
                    running = False  # for now assume we are supposed to stop
            finally:
                self._queue.task_done()

    def _dispatch_to_callbacks(self, event):
        callbacks = self._callbacks.get(event.event_type, [])

        for c in callbacks:
            try:
                c(event.content)
            except Exception, e:
                #FIXME we should log this in the leap way
                pass


    def _dispatch_to_transports(self, event):
        for t in self._transports:
            try:
                t.forward(self, event)
            except Exception, e:
                #FIXME we should log this in the leap way
                pass

