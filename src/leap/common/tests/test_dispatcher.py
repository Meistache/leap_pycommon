import unittest

from leap.common.events.dispatcher import EventDispatcher, Event, SOLEDAD_NEW_DATA_TO_SYNC
# from multiprocessing import Queue
from Queue import Queue


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
        EventDispatcher(Queue(), None)

    def test_add_callback(self):
        d = EventDispatcher(Queue(), None)

        d.register(SOLEDAD_NEW_DATA_TO_SYNC, lambda e: e)
        d.register(SOLEDAD_NEW_DATA_TO_SYNC, lambda e: e)

    def test_same_callback_can_not_be_added_twice(self):
        d = EventDispatcher(Queue(), None)

        def callback(event):
            pass

        d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback)

        self.assertRaises(ValueError, lambda: d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback))

    def test_emit(self):
        d = EventDispatcher(Queue(), None)

        self.called = False   # needs to be instance var
        def callback(event):
            self.called = True

        with running_dispatcher(d):
            d.register(SOLEDAD_NEW_DATA_TO_SYNC, callback)
            d.emit(Event(SOLEDAD_NEW_DATA_TO_SYNC, {'foo': 'bar'}))

        self.assertTrue(self.called)

