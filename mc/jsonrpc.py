#
# Copyright (c) 2009, Ben Wilber (benwilber@gmail.com)
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License. You should have
# received a copy of the GPL license along with this program; if you
# did not, you can find it at http://www.gnu.org/
#

import json
from django.http import HttpResponse
from django.conf import settings as django_settings

class publicmethod(object):

    def __init__(self, method):
        self.method = method
        self.__public__ = True

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)

    def get_args(self):
        from inspect import getargspec
        method = self.method
        while hasattr(method, 'method'):
            method = method.method
        return [ a for a in getargspec(method).args if a != "self" ]


class JsonRpc(object):

    def __init__(self, instance, allow_errors=True, report_methods=True):
        self.instance = instance
        self.allow_errors = allow_errors
        self.report_methods = report_methods
        if not hasattr(self.instance, "url"):
            raise Exception("'url' not present in supplied instance")

    def get_public_methods(self):
        return [
            m for m in dir(self.instance) if \
            getattr(self.instance, m).__class__.__name__ == "publicmethod" and \
            getattr(self.instance, m).__public__ == True
        ]

    def generate_smd(self):
        smd = {
            "serviceType": "JSON-RPC",
            "serviceURL": self.instance.url,
            "methods": []
        }
        if self.report_methods:
            smd["methods"] = [
                {"name": method, "parameters": getattr(self.instance, method).get_args()} \
                for method in self.get_public_methods()
            ]
        return json.dumps(smd)

    def dispatch(self, method, params):
        if hasattr(self.instance, "dispatch") and \
            callable(self.instance.dispatch):
            return self.instance.dispatch(method, params)
        elif method in self.get_public_methods():
            return getattr(self.instance, method)(self.instance, *params)
        else:
            return "no such method"

    def serialize(self, raw_post_data):
        raw_request    = json.loads(raw_post_data)
        request_id     = raw_request.get("id", 0)
        request_method = raw_request.get("method")
        request_params = raw_request.get("params", [])

        response = {"id": request_id}

        try:
            response["result"] = self.dispatch(request_method, request_params)
        except:
            if self.allow_errors:
                import sys
                import traceback
                exc_type, exc_value, exc_tb = sys.exc_info()
                print >> sys.stderr, exc_value, exc_type
                traceback.print_tb(exc_tb)
                response["error"] = "%s: %s" % (exc_type, exc_value)
            else:
                response["error"] = "error"

        return json.dumps(response)

    def handle_request(self, request):
        response = None
        if request.method == "POST" and \
            len(request.body) > 0:
            response = self.serialize(request.body)
        else:
            response = self.generate_smd()
        return HttpResponse(response, content_type='application/json; charset=' + django_settings.DEFAULT_CHARSET)
