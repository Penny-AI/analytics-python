import os
import sys
from eventbridge.analytics.version import VERSION

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
# Don't import analytics-python module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                'eventbridge', 'analytics'))

long_description = '''
This is the unofficial python client that wraps the
AWS EventBridge PutEvents endpoint.

Documentation and more details at
https://github.com/Penny-AI/eventbridge-analytics-python
'''

install_requires = [
    "monotonic~=1.5",
    "backoff~=2.1",
    "python-dateutil~=2.2",
    "boto3~=1.17.0"
]

tests_require = [
    "mock==2.0.0",
    "pylint==2.8.0",
    "flake8==3.7.9",
]

setup(
    name='eventbridge-analytics-python',
    version=VERSION,
    url='https://github.com/Penny-AI/eventbridge-analytics-python',
    author='PennyAI',
    author_email='james.marcogliese@pennyapp.com',
    maintainer='PennyAI',
    maintainer_email='james.marcogliese@pennyapp.com',
    test_suite='analytics.test.all',
    packages=['eventbridge.analytics', 'analytics.test'],
    python_requires='>=3.6.0',
    license='MIT License',
    install_requires=install_requires,
    extras_require={
        'test': tests_require
    },
    description='A way to integrate analytics into AWS EventBridge.',
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
