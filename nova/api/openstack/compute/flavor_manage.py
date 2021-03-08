#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import webob

from nova.api.openstack import api_version_request
from nova.api.openstack.compute.schemas import flavor_manage
from nova.api.openstack.compute.views import flavors as flavors_view
from nova.api.openstack import wsgi
from nova.api import validation
from nova.compute import flavors
from nova import exception
from nova import objects
from nova.policies import base
from nova.policies import flavor_extra_specs as fes_policies
from nova.policies import flavor_manage as fm_policies
from nova import policy


ALIAS = "os-flavor-manage"


class FlavorManageController(wsgi.Controller):
    """The Flavor Lifecycle API controller for the OpenStack API."""
    _view_builder_class = flavors_view.ViewBuilder

    def __init__(self):
        super(FlavorManageController, self).__init__()

    # NOTE(oomichi): Return 202 for backwards compatibility but should be
    # 204 as this operation complete the deletion of aggregate resource and
    # return no response body.
    @wsgi.response(202)
    @wsgi.expected_errors((404))
    @wsgi.action("delete")
    def _delete(self, req, id):
        context = req.environ['nova.context']
        # TODO(rb560u): remove this check in future release
        using_old_action = \
            policy.verify_deprecated_policy(fm_policies.BASE_POLICY_NAME,
                fm_policies.POLICY_ROOT % 'delete',
                base.RULE_ADMIN_API,
                context)

        if not using_old_action:
            context.can(fm_policies.POLICY_ROOT % 'delete')

        flavor = objects.Flavor(context=context, flavorid=id)
        try:
            flavor.destroy()
        except exception.FlavorNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

    # NOTE(oomichi): Return 200 for backwards compatibility but should be 201
    # as this operation complete the creation of flavor resource.
    @wsgi.action("create")
    @wsgi.expected_errors((400, 409))
    @validation.schema(flavor_manage.create_v20, '2.0', '2.0')
    @validation.schema(flavor_manage.create, '2.1', '2.54')
    @validation.schema(flavor_manage.create_v2_55,
                       flavors_view.FLAVOR_DESCRIPTION_MICROVERSION)
    def _create(self, req, body):
        context = req.environ['nova.context']
        # TODO(rb560u): remove this check in future release
        using_old_action = \
            policy.verify_deprecated_policy(fm_policies.BASE_POLICY_NAME,
                fm_policies.POLICY_ROOT % 'create',
                base.RULE_ADMIN_API,
                context)

        if not using_old_action:
            context.can(fm_policies.POLICY_ROOT % 'create')

        vals = body['flavor']

        name = vals['name']
        flavorid = vals.get('id')
        memory = vals['ram']
        vcpus = vals['vcpus']
        root_gb = vals['disk']
        ephemeral_gb = vals.get('OS-FLV-EXT-DATA:ephemeral', 0)
        swap = vals.get('swap', 0)
        rxtx_factor = vals.get('rxtx_factor', 1.0)
        is_public = vals.get('os-flavor-access:is_public', True)

        # The user can specify a description starting with microversion 2.55.
        include_description = api_version_request.is_supported(
            req, flavors_view.FLAVOR_DESCRIPTION_MICROVERSION)
        description = vals.get('description') if include_description else None

        try:
            flavor = flavors.create(name, memory, vcpus, root_gb,
                                    ephemeral_gb=ephemeral_gb,
                                    flavorid=flavorid, swap=swap,
                                    rxtx_factor=rxtx_factor,
                                    is_public=is_public,
                                    description=description)
            # NOTE(gmann): For backward compatibility, non public flavor
            # access is not being added for created tenant. Ref -bug/1209101
            req.cache_db_flavor(flavor)
        except (exception.FlavorExists,
                exception.FlavorIdExists) as err:
            raise webob.exc.HTTPConflict(explanation=err.format_message())

        include_extra_specs = False
        if api_version_request.is_supported(
                req, flavors_view.FLAVOR_EXTRA_SPECS_MICROVERSION):
            include_extra_specs = context.can(
                fes_policies.POLICY_ROOT % 'index', fatal=False)
            # NOTE(yikun): This empty extra_spec only for keeping consistent
            # with other related flavor api.
            flavor.extra_specs = {}

        return self._view_builder.show(req, flavor, include_description,
                                       include_extra_specs=include_extra_specs)

    @wsgi.Controller.api_version(flavors_view.FLAVOR_DESCRIPTION_MICROVERSION)
    @wsgi.action('update')
    @wsgi.expected_errors((400, 404))
    @validation.schema(flavor_manage.update_v2_55,
                       flavors_view.FLAVOR_DESCRIPTION_MICROVERSION)
    def _update(self, req, id, body):
        # Validate the policy.
        context = req.environ['nova.context']
        context.can(fm_policies.POLICY_ROOT % 'update')

        # Get the flavor and update the description.
        try:
            flavor = objects.Flavor.get_by_flavor_id(context, id)
            flavor.description = body['flavor']['description']
            flavor.save()
        except exception.FlavorNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        # Cache the flavor so the flavor_access and flavor_rxtx extensions
        # can add stuff to the response.
        req.cache_db_flavor(flavor)
        include_extra_specs = False
        if api_version_request.is_supported(
                req, flavors_view.FLAVOR_EXTRA_SPECS_MICROVERSION):
            include_extra_specs = context.can(
                fes_policies.POLICY_ROOT % 'index', fatal=False)
        return self._view_builder.show(req, flavor, include_description=True,
                                       include_extra_specs=include_extra_specs)
