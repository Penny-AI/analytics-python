import logging
from threading import Thread
import monotonic
import backoff
import json

from eventbridge.analytics.request import (
    APIError, DatetimeSerializer)

from queue import Empty

# https://docs.aws.amazon.com/eventbridge/latest/APIReference/API_PutEvents.html

# EventBridge imposes a 256kb limit on a single event entry. Here limit is set
# slightly lower to leave space for extra data that will be added later,
# eg. "sentAt".
MAX_MSG_SIZE = 243000

# EventBridge only accepts batches less than 1MB. Here limit is set slightly
# lower to leave space for extra data that will be added later, eg. "sentAt".
BATCH_SIZE_LIMIT = 950000

# EventBridge imposes a 10 event entry limit per batch.
MAX_BATCH_COUNT = 10


class Consumer(Thread):
    """Consumes the messages from the client's queue."""
    log = logging.getLogger('eventbridge.analytics')

    def __init__(self, queue, event_bridge_client,
                 upload_size=100, on_error=None, upload_interval=0.5,
                 retries=10):
        """Create a consumer thread."""
        Thread.__init__(self)
        # Make consumer a daemon thread so that it doesn't block program exit
        self.daemon = True
        self.upload_size = upload_size
        self.upload_interval = upload_interval
        self.on_error = on_error
        self.queue = queue
        self.event_bridge_client = event_bridge_client
        # It's important to set running in the constructor: if we are asked to
        # pause immediately after construction, we might set running to True in
        # run() *after* we set it to False in pause... and keep running
        # forever.
        self.running = True
        self.retries = retries

    def run(self):
        """Runs the consumer."""
        self.log.debug('consumer is running...')
        while self.running:
            self.upload()

        self.log.debug('consumer exited.')

    def pause(self):
        """Pause the consumer."""
        self.running = False

    def upload(self):
        """Upload the next batch of items, return whether successful."""
        success = False
        batch = self.next()
        if len(batch) == 0:
            return False

        try:
            self.request(batch)
            success = True
        except Exception as e:
            self.log.error('error uploading: %s', e)
            success = False
            if self.on_error:
                self.on_error(e, batch)
        finally:
            # mark items as acknowledged from queue
            for _ in batch:
                self.queue.task_done()
            return success

    def next(self):
        """Return the next batch of items to upload."""
        queue = self.queue
        items = []

        start_time = monotonic.monotonic()
        total_size = 0

        while len(items) < self.upload_size:
            elapsed = monotonic.monotonic() - start_time
            if elapsed >= self.upload_interval:
                break
            try:
                item = queue.get(
                    block=True, timeout=self.upload_interval - elapsed)
                item_size = len(json.dumps(
                    item, cls=DatetimeSerializer).encode())
                if item_size > MAX_MSG_SIZE:
                    self.log.error(
                        'Item exceeds 256kb limit, dropping. (%s)', str(item))
                    continue
                items.append(item)
                total_size += item_size
                if total_size >= BATCH_SIZE_LIMIT:
                    self.log.debug(
                        'hit batch size limit (size: %d)', total_size)
                    break
                if len(items) >= MAX_BATCH_COUNT:
                    self.log.debug(
                        'hit batch count limit (count: %d)', len(items))
                    break
            except Empty:
                break
            except Exception as e:
                self.log.exception('Exception: %s', e)

        return items

    def request(self, batch):
        """Attempt to upload the batch and retry before raising an error """

        def fatal_exception(exc):
            if isinstance(exc, APIError):
                # retry on server errors and client errors
                # with 429 status code (rate limited),
                # don't retry on other client errors
                return (400 <= int(exc.code) < 500) and int(exc.code) != 429
            else:
                # retry on all other errors (eg. network)
                return False

        @backoff.on_exception(
            backoff.expo,
            Exception,
            max_tries=self.retries + 1,
            giveup=fatal_exception)
        def send_request():
            self.event_bridge_client.post(batch=batch)

        send_request()
