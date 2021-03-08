========
nova-api
========

-------------------------------------
Server for the OpenStack Compute APIs
-------------------------------------

:Author: openstack@lists.openstack.org
:Copyright: OpenStack Foundation
:Manual section: 1
:Manual group: cloud computing

Synopsis
========

::

  nova-api  [options]

Description
===========

:program:`nova-api` is a server daemon that serves the metadata and compute
APIs in separate greenthreads.

Options
=======

**General options**

Files
=====

* ``/etc/nova/nova.conf``
* ``/etc/nova/api-paste.ini``
* ``/etc/nova/policy.json``
* ``/etc/nova/rootwrap.conf``
* ``/etc/nova/rootwrap.d/``

See Also
========

* :nova-doc:`OpenStack Nova <>`
* :nova-doc:`Using WSGI with Nova <user/wsgi.html>`

Bugs
====

* Nova bugs are managed at `Launchpad <https://bugs.launchpad.net/nova>`__
