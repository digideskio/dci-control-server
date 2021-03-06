# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import flask
from flask import json


api = flask.Blueprint('api_v1', __name__)


@api.route('/', strict_slashes=False)
def index():
    return flask.Response(json.dumps({'_status': 'OK',
                                      'message': 'Distributed CI.'}),
                          status=200,
                          content_type='application/json')


import dci.api.v1.audits  # noqa
import dci.api.v1.components  # noqa
import dci.api.v1.files  # noqa
import dci.api.v1.jobdefinitions  # noqa
import dci.api.v1.jobs  # noqa
import dci.api.v1.jobstates  # noqa
import dci.api.v1.remotecis  # noqa
import dci.api.v1.search  # noqa
import dci.api.v1.teams  # noqa
import dci.api.v1.tests  # noqa
import dci.api.v1.topics  # noqa
import dci.api.v1.users  # noqa
