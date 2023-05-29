eventbridge-analytics-python
==============

eventbridge-analytics-python is a python client for [AWS EventBridge](https://aws.amazon.com/eventbridge) using the [Segment](https://segment.com) spec.

## 👨‍💻 Getting Started

Install `eventbridge-analytics-python` using pip:

```bash
pip3 install eventbridge-analytics-python
```

or you can clone this repo:
```bash
git clone https://github.com/Penny-AI/eventbridge-analytics-python.git

cd eventbridge-analytics-python

sudo python3 setup.py install
```

Now inside your app, you'll want to **set your** `source_id` and `event_bus_name` before making any analytics calls:

```python
import eventbridge.analytics as analytics

analytics.source_id = 'YOU_SOURCE_IDENTIFIER'
analytics.event_bus_name = 'YOUR_EVENT_BUS_NAME'
```
**Note** If you need to send data to multiple EventBridge buses, you can initialize a new Client for each `source_id` and `event_bus_name`

## Documentation

Documentation on the Segment spec is available at [https://segment.com/libraries/python](https://segment.com/libraries/python).

## License

```
WWWWWW||WWWWWW
 W W W||W W W
      ||
    ( OO )__________
     /  |           \
    /o o|    MIT     \
    \___/||_||__||_|| *
         || ||  || ||
        _||_|| _||_||
       (__|__|(__|__|
```

(The MIT License)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

![built-by-salty-dogs](https://github.com/Penny-AI/eventbridge-analytics-python/assets/8539492/a4b11bf0-b82a-4b10-87a0-60fafcdaa964)
