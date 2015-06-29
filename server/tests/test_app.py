# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

import server.app
import server.db.models
import server.tests


class TestApp(server.tests.DCITestCase):
    @staticmethod
    def _extract_response(rv):
        return json.loads(rv.get_data().decode())

    def test_post_product_item(self):
        rv = self.admin_client(
            'post',
            '/api/products',
            data={'name': 'bob',
                  'data': {
                      'product_keys': {
                          'foo': ['bar1', 'bar2']}}})
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertTrue(response['id'])
        return response

    def test_post_version_item(self):
        product = self.test_post_product_item()
        rv = self.admin_client(
            'post',
            '/api/versions',
            data={'name': 'bob',
                  'product_id': product['id'],
                  'data': {
                      'version_keys': {
                          'foo': ['bar1', 'bar2']}}})
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertTrue(response['id'])
        return response

    def test_post_test_item(self):
        rv = self.admin_client(
            'post',
            '/api/tests',
            data={
                'name': 'bob',
                'data': {
                    'test_keys': {
                        'foo': ['bar1', 'bar2']}}})
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertTrue(response['id'])
        return response

    def test_post_testversion_item(self, test_id=None):
        if not test_id:
            test = self.test_post_test_item()
            test_id = test['id']
        version = self.test_post_version_item()
        rv = self.admin_client(
            'post',
            '/api/testversions',
            data={
                'test_id': test_id,
                'version_id': version['id']})
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertTrue(response['id'])
        return response

    def test_post_remoteci_item(self, test_id=None):
        if not test_id:
            test = self.test_post_test_item()
            test_id = test['id']
        rv = self.admin_client(
            'post',
            '/api/remotecis',
            data={
                'name': 'a_remoteci',
                'test_id': test_id,
                'data': {
                    'remoteci_keys': {
                        'foo': ['bar1', 'bar2']}}})
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertTrue(response['id'])
        return response

    def test_post_job_item_with_no_testversion_id(self):
        """testversion_id is missing, the server should pick a
        testversion that match the test_id of the remoteci.
        """
        test = self.test_post_test_item()
        remoteci = self.test_post_remoteci_item(test['id'])
        self.test_post_testversion_item(test['id'])
        rv = self.partner_client(
            'post',
            '/api/jobs',
            data={'remoteci_id': remoteci['id']})
        self.assertEqual(rv.status_code, 201)
        return self._extract_response(rv)

    def test_get_job_item(self):
        """GET /jobs should retrieve the item and feed the
        data key with the data section from the product, remoteci,
        test and version.
        """
        job = self.test_post_job_item_with_no_testversion_id()
        rv = self.partner_client('get', '/api/jobs/%s' % job['id'])
        self.assertEqual(rv.status_code, 200)
        response = self._extract_response(rv)
        self.assertEqual({'product_keys': {'foo': ['bar1', 'bar2']},
                          'remoteci_keys': {'foo': ['bar1', 'bar2']},
                          'test_keys': {'foo': ['bar1', 'bar2']},
                          'version_keys': {'foo': ['bar1', 'bar2']}},
                         response['data'])

    def test_get_versions_extra(self):
        # Create a test
        rv = self.admin_client(
            'post',
            '/api/tests',
            data={
                'name': 'bob',
                'data': {
                    'test_keys': {
                        'foo': ['bar1', 'bar2']}}})
        test_id = self._extract_response(rv)['id']

        # Create a product
        rv = self.admin_client(
            'post',
            '/api/products',
            data={'name': 'bob',
                  'data': {
                      'product_keys': {
                          'foo': ['bar1', 'bar2']}}})
        product_id = self._extract_response(rv)['id']

        # Create a version
        rv = self.admin_client(
            'post',
            '/api/versions',
            data={'name': 'bob',
                  'product_id': product_id,
                  'data': {
                      'version_keys': {
                          'foo': ['bar1', 'bar2']}}})
        version_id = self._extract_response(rv)['id']

        # Create a testversion
        self.admin_client(
            'post',
            '/api/testversions',
            data={
                'test_id': test_id,
                'version_id': version_id})

        # Get versions, should be empty
        rv = self.admin_client('get', '/api/versions?extra_data=1')
        self.assertEqual([], self._extract_response(rv)["_items"])
