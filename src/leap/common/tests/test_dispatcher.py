import unittest

from leap.common.events.dispatcher import EventDispatcher, Event, SOLEDAD_NEW_DATA_TO_SYNC
# from multiprocessing import Queue
from Queue import Queue
from mock import MagicMock

def running_dispatcher(d):
    class RunningDispatcher(object):
        def __init__(self, event_dispatcher):
            self._event_dispatcher = event_dispatcher

        def __enter__(self):
            self._event_dispatcher.start()

        def __exit__(self, exc_type, value, traceback):
            self._event_dispatcher.stop()

    return RunningDispatcher(d)


class EventDispatcherTest(unittest.TestCase):

    def test_create(self):
        EventDispatcher(Queue())

    def test_add_callback(self):
        d = EventDispatcher(Queue())

        d.register(SOLEDAD_NEW_DATA_TO_SYNC, lambda e: e)
        d.register(SOLEDAD_NEW_DATA_TO_SYNC, lambda e: e)

    def test_same_callback_can_not_be_added_twice(self):
        d = EventDispatcher(Queue())

        def callback(event):
            pass

        d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback)

        self.assertRaises(ValueError, lambda: d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback))

    def test_emit(self):
        d = EventDispatcher(Queue())

        self.called = False   # needs to be instance var
        def callback(event):
            self.called = True

        with running_dispatcher(d):
            d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback)
            d.emit(Event(SOLEDAD_NEW_DATA_TO_SYNC, {'foo': 'bar'}))

        self.assertTrue(self.called)

    def test_transport_can_be_provided(self):
        transports = [MagicMock()]
        d = EventDispatcher(Queue(), transports)

    def test_events_are_registered_at_transport(self):
        transport = MagicMock()
        d = EventDispatcher(Queue(), [transport])

        def callback(event):
            pass

        d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback)

        transport.notify_for.assert_called_once_with(SOLEDAD_NEW_DATA_TO_SYNC)


    def test_dispatcher_registers_at_transport(self):
        # when transport receives an event from external source
        # it needs to call the local listeners. For that to be possible
        # the distacher needs to make itself known to the transport as a callback

        transport = MagicMock()
        d = EventDispatcher(Queue(), [transport])

        transport.register_event_dispatcher.assert_called_once_with(d)


    def test_emit_from_transport(self):
        transport = MagicMock()
        d = EventDispatcher(Queue(), [transport])

        self.called = False
        def callback(event):
            self.called = True

        d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback)

        event = Event(SOLEDAD_NEW_DATA_TO_SYNC, {'foo': 'bar'})
        with running_dispatcher(d):
            d.emit_from_transport(transport, event)

        self.assertTrue(self.called)

    def test_emit_forwards_events_to_transports(self):
        transport = MagicMock()
        d = EventDispatcher(Queue(), [transport])

        event = Event(SOLEDAD_NEW_DATA_TO_SYNC, {'foo': 'bar'})

        with running_dispatcher(d):
            d.emit(event)

        transport.forward.assert_called_once_with(d, event)

