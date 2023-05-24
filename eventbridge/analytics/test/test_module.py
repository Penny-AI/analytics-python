import unittest
import mock

import eventbridge.analytics as analytics


class TestModule(unittest.TestCase):

    # def failed(self):
    #     self.failed = True
    _boto_client = None
    _bus_name = "test_bus_name"

    def setUp(self):
        self.failed = False
        analytics.source_id = 'test_source_id'
        analytics.event_bus_name = self._bus_name
        analytics.on_error = self.failed

    def test_no_source_id(self):
        analytics.source_id = None
        analytics.event_bus_name = "test_bus_name"
        self.assertRaises(Exception, analytics.track)

    def test_no_event_bus_name(self):
        analytics.source_id = "test"
        analytics.event_bus_name = None
        self.assertRaises(Exception, analytics.track)

    def test_track(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.track('userId', 'python module event')
            analytics.flush()

    def test_identify(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.identify('userId', {'email': 'user@email.com'})
            analytics.flush()

    def test_group(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.group('userId', 'groupId')
            analytics.flush()

    def test_alias(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.alias('previousId', 'userId')
            analytics.flush()

    def test_page(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.page('userId')
            analytics.flush()

    def test_screen(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.screen('userId')
            analytics.flush()

    def test_flush(self):
        def mock_post(*args, **kwargs):
            pass
        with mock.patch('eventbridge.analytics.consumer.post',
                        mock.Mock(side_effect=mock_post)):
            analytics.flush()
