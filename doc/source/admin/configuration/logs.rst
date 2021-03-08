=================
Compute log files
=================

The corresponding log file of each Compute service is stored in the
``/var/log/nova/`` directory of the host on which each service runs.

.. list-table:: Log files used by Compute services
   :widths: 35 35 30
   :header-rows: 1

   * - Log file
     - Service name (CentOS/Fedora/openSUSE/Red Hat Enterprise
       Linux/SUSE Linux Enterprise)
     - Service name (Ubuntu/Debian)
   * - ``nova-api.log``
     - ``openstack-nova-api``
     - ``nova-api``
   * - ``nova-compute.log``
     - ``openstack-nova-compute``
     - ``nova-compute``
   * - ``nova-conductor.log``
     - ``openstack-nova-conductor``
     - ``nova-conductor``
   * - ``nova-consoleauth.log``
     - ``openstack-nova-consoleauth``
     - ``nova-consoleauth``
   * - ``nova-network.log`` [#a]_
     - ``openstack-nova-network``
     - ``nova-network``
   * - ``nova-manage.log``
     - ``nova-manage``
     - ``nova-manage``
   * - ``nova-scheduler.log``
     - ``openstack-nova-scheduler``
     - ``nova-scheduler``

.. rubric:: Footnotes

.. [#a] The ``nova`` network service (``openstack-nova-network``/
         ``nova-network``) only runs in deployments that are not configured
         to use the Networking service (``neutron``).
