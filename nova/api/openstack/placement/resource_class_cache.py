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

from oslo_concurrency import lockutils
import sqlalchemy as sa

from nova.api.openstack.placement import db_api
from nova.api.openstack.placement import exception
from nova.db.sqlalchemy import api_models as models
from nova import rc_fields as fields

_RC_TBL = models.ResourceClass.__table__
_LOCKNAME = 'rc_cache'


@db_api.placement_context_manager.reader
def _refresh_from_db(ctx, cache):
    """Grabs all custom resource classes from the DB table and populates the
    supplied cache object's internal integer and string identifier dicts.

    :param cache: ResourceClassCache object to refresh.
    """
    with db_api.placement_context_manager.reader.connection.using(ctx) as conn:
        sel = sa.select([_RC_TBL.c.id, _RC_TBL.c.name, _RC_TBL.c.updated_at,
                         _RC_TBL.c.created_at])
        res = conn.execute(sel).fetchall()
        cache.id_cache = {r[1]: r[0] for r in res}
        cache.str_cache = {r[0]: r[1] for r in res}
        cache.all_cache = {r[1]: r for r in res}


class ResourceClassCache(object):
    """A cache of integer and string lookup values for resource classes."""

    # List of dict of all standard resource classes, where every list item
    # have a form {'id': <ID>, 'name': <NAME>}
    STANDARDS = [{'id': fields.ResourceClass.STANDARD.index(s), 'name': s,
                  'updated_at': None, 'created_at': None}
                 for s in fields.ResourceClass.STANDARD]

    def __init__(self, ctx):
        """Initialize the cache of resource class identifiers.

        :param ctx: `nova.context.RequestContext` from which we can grab a
                    `SQLAlchemy.Connection` object to use for any DB lookups.
        """
        self.ctx = ctx
        self.id_cache = {}
        self.str_cache = {}
        self.all_cache = {}

    def clear(self):
        with lockutils.lock(_LOCKNAME):
            self.id_cache = {}
            self.str_cache = {}
            self.all_cache = {}

    def id_from_string(self, rc_str):
        """Given a string representation of a resource class -- e.g. "DISK_GB"
        or "IRON_SILVER" -- return the integer code for the resource class. For
        standard resource classes, this integer code will match the list of
        resource classes on the fields.ResourceClass field type. Other custom
        resource classes will cause a DB lookup into the resource_classes
        table, however the results of these DB lookups are cached since the
        lookups are so frequent.

        :param rc_str: The string representation of the resource class to look
                       up a numeric identifier for.
        :returns integer identifier for the resource class, or None, if no such
                 resource class was found in the list of standard resource
                 classes or the resource_classes database table.
        :raises `exception.ResourceClassNotFound` if rc_str cannot be found in
                either the standard classes or the DB.
        """
        # First check the standard resource classes
        if rc_str in fields.ResourceClass.STANDARD:
            return fields.ResourceClass.STANDARD.index(rc_str)

        with lockutils.lock(_LOCKNAME):
            if rc_str in self.id_cache:
                return self.id_cache[rc_str]
            # Otherwise, check the database table
            _refresh_from_db(self.ctx, self)
            if rc_str in self.id_cache:
                return self.id_cache[rc_str]
            raise exception.ResourceClassNotFound(resource_class=rc_str)

    def all_from_string(self, rc_str):
        """Given a string representation of a resource class -- e.g. "DISK_GB"
        or "CUSTOM_IRON_SILVER" -- return all the resource class info.

        :param rc_str: The string representation of the resource class for
                       which to look up a resource_class.
        :returns: dict representing the resource class fields, if the
                  resource class was found in the list of standard
                  resource classes or the resource_classes database table.
        :raises: `exception.ResourceClassNotFound` if rc_str cannot be found in
                 either the standard classes or the DB.
        """
        # First check the standard resource classes
        if rc_str in fields.ResourceClass.STANDARD:
            return {'id': fields.ResourceClass.STANDARD.index(rc_str),
                    'name': rc_str,
                    'updated_at': None,
                    'created_at': None}

        with lockutils.lock(_LOCKNAME):
            if rc_str in self.all_cache:
                return self.all_cache[rc_str]
            # Otherwise, check the database table
            _refresh_from_db(self.ctx, self)
            if rc_str in self.all_cache:
                return self.all_cache[rc_str]
            raise exception.ResourceClassNotFound(resource_class=rc_str)

    def string_from_id(self, rc_id):
        """The reverse of the id_from_string() method. Given a supplied numeric
        identifier for a resource class, we look up the corresponding string
        representation, either in the list of standard resource classes or via
        a DB lookup. The results of these DB lookups are cached since the
        lookups are so frequent.

        :param rc_id: The numeric representation of the resource class to look
                      up a string identifier for.
        :returns: string identifier for the resource class, or None, if no such
                 resource class was found in the list of standard resource
                 classes or the resource_classes database table.
        :raises `exception.ResourceClassNotFound` if rc_id cannot be found in
                either the standard classes or the DB.
        """
        # First check the fields.ResourceClass.STANDARD values
        try:
            return fields.ResourceClass.STANDARD[rc_id]
        except IndexError:
            pass

        with lockutils.lock(_LOCKNAME):
            if rc_id in self.str_cache:
                return self.str_cache[rc_id]

            # Otherwise, check the database table
            _refresh_from_db(self.ctx, self)
            if rc_id in self.str_cache:
                return self.str_cache[rc_id]
            raise exception.ResourceClassNotFound(resource_class=rc_id)
