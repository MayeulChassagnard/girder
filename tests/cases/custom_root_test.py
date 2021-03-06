#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2014 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import os
import types

from .. import base


class CustomRootTestCase(base.TestCase):

    def setUp(self):
        self.mockPluginDir(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_plugins'))
        base.enabledPlugins.append('test_plugin')

        base.startServer()

        # Make sure our import semantics work as expected for plugins
        from girder.plugins import test_plugin
        self.assertIsInstance(test_plugin, types.ModuleType)

    def tearDown(self):
        base.stopServer()
        self.unmockPluginDir()

    def testCustomWebRoot(self):
        """
        Tests the ability of plugins to serve their own custom server roots.
        """
        # Root (/) should serve our custom route
        resp = self.request('/', prefix='', isJson=False)
        self.assertStatusOk(resp)
        self.assertEqual(self.getBody(resp), 'hello world')

        # Normal web client should now be served from /girder
        resp = self.request('/girder', prefix='', isJson=False)
        self.assertStatusOk(resp)
        self.assertIn('g-global-info-apiroot', self.getBody(resp))

        # Api should be served out of /api/v1
        resp = self.request('/api/v1', prefix='', isJson=False)
        self.assertStatusOk(resp)
        self.assertIn('Girder REST API Documentation', self.getBody(resp))

        # /api should redirect to /api/v1
        resp = self.request('/api', prefix='', isJson=False)
        self.assertStatus(resp, 303)
        self.assertIn('/api/v1', self.getBody(resp))

        # Our custom API augmentations should still work
        resp = self.request('/describe')
        self.assertStatusOk(resp)
        self.assertIn('paths', resp.json)
        self.assertIn('/other', resp.json['paths'])

        resp = self.request('/other')
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, ['custom REST route'])

        # Api should not be served out of /girder/api/v1
        resp = self.request('/girder/api/v1', prefix='', isJson=False)
        self.assertStatus(resp, 404)
        body = self.getBody(resp).lower()
        server = resp.headers['Server'].lower()
        self.assertNotIn('cherrypy', body)
        self.assertNotIn('cherrypy', server)
        self.assertIn('girder', body)
        self.assertIn('girder', server)

        # Test our staticFile method
        resp = self.request('/static_route', prefix='', isJson=False)
        self.assertEqual(self.getBody(resp), 'Hello world!\n')
