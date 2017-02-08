# -*- coding: utf-8 -*-
from requests.models import Request, Response
from requests.exceptions import ConnectionError


class MockRequest(Request):
    def __init__(self, url=None):
        super(Request, self).__init__()
        self.url = url
        #: Resulting :class:`HTTPError` of request, if one occurred.
        self.error = None

        #: Encoding to decode with when accessing r.content.
        self.encoding = None

        #: The :class:`Request <Request>` that created the Response.
        self.request = self

    def get(self):
        r = Response()
        try:
            with open(self.url, mode='rb') as stream:
                r._content = stream.read()
                #: Integer Code of responded HTTP Status.
                r.status_code = 200
                if self.url.endswith('json'):
                    r.headers['content-type'] = 'application/json'
        except IOError as e:
            r.status_code = 404
            raise ConnectionError(e)

        r._content_consumed = True

        #: Final URL location of Response.
        r.url = self.url

        # Return the response.
        return r
