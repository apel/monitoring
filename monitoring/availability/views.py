# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view()
def status(requst):
    return Response({"message": "OK"}, status=200, template_name="status.html")
