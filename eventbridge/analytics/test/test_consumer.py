import unittest
import mock
import time
import json
from moto import mock_iam, mock_events
import boto3

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from eventbridge.analytics.consumer import Consumer, MAX_MSG_SIZE
from eventbridge.analytics.request import APIError


@mock_iam
def create_user_with_all_permissions():
    client = boto3.client("iam", region_name="eu-west-1")
    client.create_user(UserName="test_user1")

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": ["events:*"],
                       "Resource": "*"}],
    }

    client.put_user_policy(
        UserName="test_user1",
        PolicyName="policy1",
        PolicyDocument=json.dumps(policy_document),
    )

    return client.create_access_key(UserName="test_user1")["AccessKey"]


@mock_events
@mock_iam
class TestConsumer(unittest.TestCase):

    _boto_client = None
    _bus_name = "test_bus_name"

    def setUp(self):
        # Create User
        user = create_user_with_all_permissions()
        self.boto_client = boto3.client(
            "events",
            aws_access_key_id=user["AccessKeyId"],
            aws_secret_access_key=user["SecretAccessKey"],
            region_name="eu-west-1"
        )
        self.boto_client.create_event_bus(Name=self._bus_name)

    def test_next(self):
        q = Queue()
        consumer = Consumer(q, '', self._bus_name, boto_client=self._boto_client)
        q.put(1)
        next = consumer.next()
        self.assertEqual(next, [1])

    def test_next_limit(self):
        q = Queue()
        upload_size = 10
        consumer = Consumer(q, '', self._bus_name, upload_size, boto_client=self._boto_client)
        for i in range(10000):
            q.put(i)
        next = consumer.next()
        self.assertEqual(next, list(range(upload_size)))

    def test_dropping_oversize_msg(self):
        q = Queue()
        consumer = Consumer(q, '', self._bus_name, boto_client=self._boto_client)
        oversize_msg = {'m': 'x' * MAX_MSG_SIZE}
        q.put(oversize_msg)
        next = consumer.next()
        self.assertEqual(next, [])
        self.assertTrue(q.empty())

    def test_upload(self):
        q = Queue()
        consumer = Consumer(q, 'test_app_id', self._bus_name, boto_client=self._boto_client)
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }

        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            q.put(track)
            success = consumer.upload()
            self.assertTrue(success)

    def test_upload_interval(self):
        # Put _n_ items in the queue, pausing a little bit more than
        # _upload_interval_ after each one.
        # The consumer should upload _n_ times.
        q = Queue()
        upload_interval = 0.3
        consumer = Consumer(q, 'test_app_id', self._bus_name, upload_size=10,
                            upload_interval=upload_interval, boto_client=self._boto_client)
        with mock.patch('eventbridge.analytics.consumer.post') as mock_post:
            consumer.start()
            for i in range(0, 3):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId'
                }
                q.put(track)
                time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 3)

    def test_multiple_uploads_per_interval(self):
        # Put _upload_size*2_ items in the queue at once, then pause for
        # _upload_interval_. The consumer should upload 2 times.
        q = Queue()
        upload_interval = 0.5
        upload_size = 10
        consumer = Consumer(q, 'test_app_id', self._bus_name, upload_size=upload_size,
                            upload_interval=upload_interval, boto_client=self._boto_client)
        with mock.patch('eventbridge.analytics.consumer.post') as mock_post:
            consumer.start()
            for i in range(0, upload_size * 2):
                track = {
                    'type': 'track',
                    'event': 'python event %d' % i,
                    'userId': 'userId'
                }
                q.put(track)
            time.sleep(upload_interval * 1.1)
            self.assertEqual(mock_post.call_count, 2)

    def test_request(self):
        consumer = Consumer(None, 'test_app_id', self._bus_name, boto_client=self._boto_client)
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }

        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            consumer.request([track])

    def _test_request_retry(self, consumer,
                            expected_exception, exception_count):

        def mock_post(*args, **kwargs):
            mock_post.call_count += 1
            if mock_post.call_count <= exception_count:
                raise expected_exception
        mock_post.call_count = 0

        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            track = {
                'type': 'track',
                'event': 'python event',
                'userId': 'userId'
            }
            # request() should succeed if the number of exceptions raised is
            # less than the retries parameter.
            if exception_count <= consumer.retries:
                consumer.request([track])
            else:
                # if exceptions are raised more times than the retries
                # parameter, we expect the exception to be returned to
                # the caller.
                try:
                    consumer.request([track])
                except type(expected_exception) as exc:
                    self.assertEqual(exc, expected_exception)
                else:
                    self.fail(
                        "request() should raise an exception if still failing "
                        "after %d retries" % consumer.retries)

    def test_request_retry(self):
        # we should retry on general errors
        consumer = Consumer(None, 'test_app_id', self._bus_name, boto_client=self._boto_client)
        self._test_request_retry(consumer, Exception('generic exception'), 2)

        # we should retry on server errors
        consumer = Consumer(None, 'test_app_id', self._bus_name, boto_client=self._boto_client)
        self._test_request_retry(consumer, APIError(
            2, '500', 'Internal Server Error'), 2)

        # we should retry on HTTP 429 errors
        consumer = Consumer(None, 'test_app_id', self._bus_name, boto_client=self._boto_client)
        self._test_request_retry(consumer, APIError(
            2, '429', 'Too Many Requests'), 2)

        # we should NOT retry on other client errors
        consumer = Consumer(None, 'test_app_id', self._bus_name, boto_client=self._boto_client)
        api_error = APIError(1, '400', 'Client Errors')
        try:
            self._test_request_retry(consumer, api_error, 1)
        except APIError:
            pass
        else:
            self.fail('request() should not retry on client errors')

        # test for number of exceptions raise > retries value
        consumer = Consumer(None, 'test_app_id', self._bus_name, boto_client=self._boto_client, retries=3)
        self._test_request_retry(consumer, APIError(
            3, '500', 'Internal Server Error'), 3)

    def test_pause(self):
        consumer = Consumer(None,'test_app_id', self._bus_name, boto_client=self._boto_client)
        consumer.pause()
        self.assertFalse(consumer.running)

    def test_max_batch_size(self):
        q = Queue()
        consumer = Consumer(
            q, 'test_app_id', self._bus_name, boto_client=self._boto_client, upload_size=950000, upload_interval=3)
        track = {
            'type': 'track',
            'event': 'python event',
            'userId': 'userId'
        }
        msg_size = len(json.dumps(track).encode())
        # number of messages in a maximum-size batch
        n_msgs = int(950000 / msg_size)

        def mock_post_fn(_, data, **kwargs):
            pass

        with mock.patch('eventbridge.analytics.consumer.post',
                        side_effect=mock_post_fn) as mock_post:
            consumer.start()
            for _ in range(0, n_msgs + 2):
                q.put(track)
            q.join()
            self.assertEqual(mock_post.call_count, 1533)
