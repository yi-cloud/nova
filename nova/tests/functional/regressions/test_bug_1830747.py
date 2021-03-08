# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock

from nova import context as nova_context
from nova import objects
from nova.scheduler import weights
from nova import test
from nova.tests import fixtures as nova_fixtures
from nova.tests.functional import integrated_helpers
from nova.tests.unit.image import fake as fake_image


class HostNameWeigher(weights.BaseHostWeigher):
    # Prefer host1 over host2.
    weights = {'host1': 100, 'host2': 50}

    def _weigh_object(self, host_state, weight_properties):
        return self.weights.get(host_state.host, 0)


class MissingReqSpecInstanceGroupUUIDTestCase(
        test.TestCase, integrated_helpers.InstanceHelperMixin):
    """Regression recreate test for bug 1830747

    Before change I4244f7dd8fe74565180f73684678027067b4506e in Stein, when
    a cold migration would reschedule to conductor it would not send the
    RequestSpec, only the filter_properties. The filter_properties contain
    a primitive version of the instance group information from the RequestSpec
    for things like the group members, hosts and policies, but not the uuid.
    When conductor is trying to reschedule the cold migration without a
    RequestSpec, it builds a RequestSpec from the components it has, like the
    filter_properties. This results in a RequestSpec with an instance_group
    field set but with no uuid field in the RequestSpec.instance_group.
    That RequestSpec gets persisted and then because of change
    Ie70c77db753711e1449e99534d3b83669871943f, later attempts to load the
    RequestSpec from the database will fail because of the missing
    RequestSpec.instance_group.uuid.

    This test recreates the regression scenario by cold migrating a server
    to a host which fails and triggers a reschedule but without the RequestSpec
    so a RequestSpec is created/updated for the instance without the
    instance_group.uuid set which will lead to a failure loading the
    RequestSpec from the DB later.
    """

    def setUp(self):
        super(MissingReqSpecInstanceGroupUUIDTestCase, self).setUp()
        # Stub out external dependencies.
        self.useFixture(nova_fixtures.NeutronFixture(self))
        self.useFixture(nova_fixtures.PlacementFixture())
        fake_image.stub_out_image_service(self)
        self.addCleanup(fake_image.FakeImageService_reset)
        # Configure the API to allow resizing to the same host so we can keep
        # the number of computes down to two in the test.
        self.flags(allow_resize_to_same_host=True)
        # Start nova controller services.
        api_fixture = self.useFixture(nova_fixtures.OSAPIFixture(
            api_version='v2.1'))
        self.api = api_fixture.admin_api
        self.start_service('conductor')
        # Use our custom weigher defined above to make sure that we have
        # a predictable scheduling sort order.
        self.flags(weight_classes=[__name__ + '.HostNameWeigher'],
                   group='filter_scheduler')
        self.start_service('scheduler')
        # Start two computes, one where the server will be created and another
        # where we'll cold migrate it.
        self.computes = {}  # keep track of the compute services per host name
        for host in ('host1', 'host2'):
            compute_service = self.start_service('compute', host=host)
            self.computes[host] = compute_service

    def test_cold_migrate_reschedule(self):
        # Create an anti-affinity group for the server.
        body = {
            'server_group': {
                'name': 'test-group',
                'policies': ['anti-affinity']
            }
        }
        group_id = self.api.api_post(
            '/os-server-groups', body).body['server_group']['id']

        # Create a server in the group which should land on host1 due to our
        # custom weigher.
        server = self._build_minimal_create_server_request(
            self.api, 'test_cold_migrate_reschedule')
        body = dict(server=server)
        body['os:scheduler_hints'] = {'group': group_id}
        server = self.api.post_server(body)
        server = self._wait_for_state_change(self.api, server, 'ACTIVE')
        self.assertEqual('host1', server['OS-EXT-SRV-ATTR:host'])

        # Verify the group uuid is set in the request spec.
        ctxt = nova_context.get_admin_context()
        reqspec = objects.RequestSpec.get_by_instance_uuid(ctxt, server['id'])
        self.assertEqual(group_id, reqspec.instance_group.uuid)

        # Now cold migrate the server. Because of allow_resize_to_same_host and
        # the weigher, the scheduler will pick host1 first. The FakeDriver
        # actually allows migrating to the same host so we need to stub that
        # out so the compute will raise UnableToMigrateToSelf like when using
        # the libvirt driver.
        host1_driver = self.computes['host1'].driver
        with mock.patch.dict(host1_driver.capabilities,
                             supports_migrate_to_same_host=False):
            self.api.post_server_action(server['id'], {'migrate': None})
            server = self._wait_for_state_change(
                self.api, server, 'VERIFY_RESIZE')
            self.assertEqual('host2', server['OS-EXT-SRV-ATTR:host'])

        # The RequestSpec.instance_group.uuid should still be set.
        reqspec = objects.RequestSpec.get_by_instance_uuid(ctxt, server['id'])
        self.assertEqual(group_id, reqspec.instance_group.uuid)
