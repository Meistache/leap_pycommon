import unittest

from .test_dispatcher import running_dispatcher
from multiprocessing import JoinableQueue
from Queue import Queue
from multiprocessing import Process
from threading import Thread
from leap.common.events.dispatcher import EventDispatcher, Event, SOLEDAD_NEW_DATA_TO_SYNC, Transport

from time import sleep, time


def wait_for(func, timeout=10.0):
    start = time()

    while time() < start + timeout:
        print 'checking'
        if func():
            return
        sleep(0.05)

class JoinableQueueTransport(Transport):

    def __init__(self, read_queue, write_queue):
        self._read_queue = read_queue
        self._write_queue = write_queue
        self._dispatchers = set()
        self._thread = Thread(target=self._loop)
        self._thread.setDaemon(True)
        self._thread.start()

    def _loop(self):
        while True:
            event = self._read_queue.get()
            for d in self._dispatchers:
                d.emit_from_transport(self, event)

    def register_event_dispatcher(self, dispatcher):
        self._dispatchers.add(dispatcher)

    def notify_for(self, event_type):
        pass

    def forward(self, dispatcher, event):
       self._write_queue.put(event)


class EventDispatcherIntegrationTest(unittest.TestCase):

    def test_multiprocessing_transport(self):
        self.called = False

        def sub_process(jq1, jq2):
            t = JoinableQueueTransport(jq1, jq2)
            d = EventDispatcher(Queue(), [t])
            received_events = []

            def sub_process_callback(event, d, received_events):
                d.emit(Event('pong', {'value': event['value']}))
                received_events.append(event)

            d.register('ping', lambda event: sub_process_callback(event, d, received_events))
            with running_dispatcher(d):
                wait_for(lambda: len(received_events) > 0)
                print 'sub: exit wait_for'
            print 'sub: exit context manager'

        def ping_callback(event):
            print 'main: ping called'

        def pong_callback(event):
            print 'pong called'
            self.called = True

        jq1 = JoinableQueue()
        jq2 = JoinableQueue()
        transport = JoinableQueueTransport(jq1, jq2)

        d = EventDispatcher(Queue(), [transport])

        p = Process(target=sub_process, args=(jq2,jq1))
        p.start()

        sleep(0.1)

        d.register('pong', pong_callback)
        d.register('ping', ping_callback)

        with running_dispatcher(d):
            d.emit(Event('ping', {'value': '1234'}))
            wait_for(lambda: self.called)
            print 'main: finished waiting'
        print 'main: finished context manager'

        p.join()

        self.assertTrue(self.called)
