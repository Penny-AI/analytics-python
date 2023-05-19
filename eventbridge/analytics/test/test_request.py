from datetime import datetime, date
import unittest
import json
import boto3
from moto import mock_iam, mock_events

from eventbridge.analytics.request import post, DatetimeSerializer


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
class TestRequests(unittest.TestCase):

    _boto_client = None
    _bus_name = "test_bus_name"

    def setUp(self):
        # Create User
        user = create_user_with_all_permissions()
        self._boto_client = boto3.client(
            "events",
            aws_access_key_id=user["AccessKeyId"],
            aws_secret_access_key=user["SecretAccessKey"],
            region_name="eu-west-1"
        )
        self._boto_client.create_event_bus(Name=self._bus_name)

    def test_valid_request(self):
        res = post('app_id', self._bus_name, boto_client=self._boto_client, batch=[{
            'userId': 'userId',
            'event': 'python event',
            'type': 'track'
        }])
        self.assertEqual(res['FailedEntryCount'], 0)

    def test_datetime_serialization(self):
        data = {'created': datetime(2012, 3, 4, 5, 6, 7, 891011)}
        result = json.dumps(data, cls=DatetimeSerializer)
        self.assertEqual(result, '{"created": "2012-03-04T05:06:07.891011"}')

    def test_date_serialization(self):
        today = date.today()
        data = {'created': today}
        result = json.dumps(data, cls=DatetimeSerializer)
        expected = '{"created": "%s"}' % today.isoformat()
        self.assertEqual(result, expected)
