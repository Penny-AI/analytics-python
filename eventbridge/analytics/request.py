from datetime import date, datetime
import logging
import json
from dateutil.tz import tzutc
import boto3
import sys

# this is a pointer to the module object instance itself.
this = sys.modules[__name__]
this._boto_client = boto3.client('events')


def post(source_id, event_bus_name, boto_client=None, **kwargs):
    if boto_client is not None:
        this._boto_client = boto_client

    """Post the `kwargs` to the API"""
    log = logging.getLogger('segment')
    body = kwargs
    body["sentAt"] = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()

    data = json.dumps(body, cls=DatetimeSerializer)
    log.debug('making request: %s', data)

    entries = []
    for detail_data in body['batch']:
        detail_data_str = json.dumps(detail_data, cls=DatetimeSerializer)
        entries.append({
                'Source': source_id,
                'DetailType': 'eventbridge_analytics_python',
                'Detail': detail_data_str,
                'EventBusName': event_bus_name
        })

    res = this._boto_client.put_events(
        Entries=entries
    )

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
