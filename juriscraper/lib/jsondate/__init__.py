"""
Copyright (c) 2012 Rick Harris

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# code taken from https://github.com/rconradharris/jsondate
# author email: rconradharris@gmail.com
import datetime
import json
import six

DATE_FMT = '%Y-%m-%d'
ISO8601_FMT = '%Y-%m-%dT%H:%M:%SZ'


def _datetime_encoder(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime(ISO8601_FMT)
    elif isinstance(obj, datetime.date):
        return obj.strftime(DATE_FMT)

    raise TypeError


def _datetime_decoder(dict_):
    for key, value in six.iteritems(dict_):
        # The built-in `json` library will `unicode` strings, except for empty
        # strings which are of type `str`. `jsondate` patches this for
        # consistency so that `unicode` is always returned.
        if value == '':
            dict_[key] = u''
            continue

        try:
            datetime_obj = datetime.datetime.strptime(value, ISO8601_FMT)
            dict_[key] = datetime_obj
        except (ValueError, TypeError):
            try:
                date_obj = datetime.datetime.strptime(value, DATE_FMT)
                dict_[key] = date_obj.date()
            except (ValueError, TypeError):
                continue

    return dict_


def dumps(*args, **kwargs):
    kwargs['default'] = _datetime_encoder
    return json.dumps(*args, **kwargs)


def dump(*args, **kwargs):
    kwargs['default'] = _datetime_encoder
    return json.dump(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs['object_hook'] = _datetime_decoder
    return json.loads(*args, **kwargs)


def load(*args, **kwargs):
    kwargs['object_hook'] = _datetime_decoder
    return json.load(*args, **kwargs)
