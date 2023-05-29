from datetime import date, datetime
import logging
import json
from dateutil.tz import tzutc
import boto3
from botocore.exceptions import ClientError


class EventBridge(object):

    def __init__(self,
                 source_id,
                 event_bus_name,
                 region_name=None,
                 access_key=None,
                 secret_access_key=None,
                 session_token=None):

        self.source_id = source_id
        self.event_bus_name = event_bus_name
        self.boto_client = boto3.client('events')

        if access_key is not None and secret_access_key is not None:
            self.boto_client = boto3.client('events',
                                            aws_access_key_id=access_key,
                                            aws_secret_access_key=secret_access_key,
                                            aws_session_token=session_token,
                                            region_name=region_name)

    def post(self, **kwargs):
        log = logging.getLogger('eventbridge.analytics')
        body = kwargs
        body["sentAt"] = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()

        data = json.dumps(body, cls=DatetimeSerializer)
        log.debug('making request: %s', data)

        entries = []
        for detail_data in body['batch']:
            detail_data_str = json.dumps(detail_data, cls=DatetimeSerializer)
            entries.append({
                    'Source': self.source_id,
                    'DetailType': 'eventbridge_analytics_python',
                    'Detail': detail_data_str,
                    'EventBusName': self.event_bus_name
            })

        try:
            res = self.boto_client.put_events(
                Entries=entries
            )
        except ClientError as e:
            log.debug('ClientError:  %s,  %s' % (e.response['Error']['Code'],
                                                 e.response['Error']['Message']))
            raise APIError(e.response['Error']['Code'], e.response['Error']['Message'])

        if res['FailedEntryCount'] == 0:
            log.debug('data uploaded successfully')
            return res

        try:
            log.debug('failed %s entries', res['FailedEntryCount'])
            for entry in res["Entries"]:
                if "ErrorCode" in entry and "ErrorMessage" in entry:
                    raise APIError(res['FailedEntryCount'],
                                   entry['ErrorCode'],
                                   entry['ErrorMessage'])

        except ValueError:
            raise APIError(res.status_code, 'unknown', res.text)


class APIError(Exception):

    def __init__(self, failed_count, code, message):
        self.message = message
        self.failed_count = failed_count
        self.code = code

    def __str__(self):
        msg = "[EventBridge] {0}: {1} ({2})"
        return msg.format(self.code, self.message, self.failed_count)


class DatetimeSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)
