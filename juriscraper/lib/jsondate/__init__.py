from __future__ import absolute_import
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
