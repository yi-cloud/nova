===========
nova-manage
===========

-------------------------------------------
Control and manage cloud computer instances
-------------------------------------------

:Author: openstack@lists.openstack.org
:Copyright: OpenStack Foundation
:Manual section: 1
:Manual group: cloud computing

Synopsis
========

::

  nova-manage <category> <action> [<args>]

Description
===========

:program:`nova-manage` controls cloud computing instances by managing various
admin-only aspects of Nova.

Options
=======

The standard pattern for executing a nova-manage command is::

  nova-manage <category> <command> [<args>]

Run without arguments to see a list of available command categories::

  nova-manage

You can also run with a category argument such as user to see a list of all
commands in that category::

  nova-manage db

These sections describe the available categories and arguments for nova-manage.

Nova Database
~~~~~~~~~~~~~

``nova-manage db version``
    Print the current main database version.

``nova-manage db sync [--version <version>] [--local_cell]``
    Upgrade the main database schema up to the most recent version or
    ``--version`` if specified. By default, this command will also attempt to
    upgrade the schema for the cell0 database if it is mapped (see the
    ``map_cell0`` or ``simple_cell_setup`` commands for more details on mapping
    the cell0 database). If ``--local_cell`` is specified, then only the main
    database in the current cell is upgraded. The local database connection is
    determined by ``[database]/connection`` in the configuration file passed to
    nova-manage.

``nova-manage db archive_deleted_rows [--max_rows <number>] [--verbose] [--until-complete] [--purge]``
    Move deleted rows from production tables to shadow tables. Note that the
    corresponding rows in the instance_mappings and request_specs tables of the
    API database are purged when instance records are archived and thus,
    CONF.api_database.connection is required in the config file. Specifying
    --verbose will print the results of the archive operation for any tables that
    were changed. Specifying --until-complete will make the command run
    continuously until all deleted rows are archived. Use the --max_rows option,
    which defaults to 1000, as a batch size for each iteration. Specifying --purge
    will cause a `full` DB purge to be completed after archival. If a date range
    is desired for the purge, then run ``nova-manage db purge --before
    <date>`` manually after archiving is complete.

``nova-manage db purge [--all] [--before <date>] [--verbose] [--all-cells]``
    Delete rows from shadow tables. Specifying --all will delete all data from
    all shadow tables. Specifying --before will delete data from all shadow tables
    that is older than the date provided. Date strings may be fuzzy, such as
    ``Oct 21 2015``. Specifying --verbose will cause information to be printed about
    purged records. Specifying --all-cells will cause the purge to be applied against
    all cell databases. For --all-cells to work, the api database connection
    information must be configured. Returns exit code 0 if rows were deleted, 1 if
    required arguments are not provided, 2 if an invalid date is provided, 3 if no
    data was deleted, 4 if the list of cells cannot be obtained.

``nova-manage db null_instance_uuid_scan [--delete]``
    Lists and optionally deletes database records where instance_uuid is NULL.

``nova-manage db online_data_migrations [--max-count]``
   Perform data migration to update all live data.

   ``--max-count`` controls the maximum number of objects to migrate in a given
   call. If not specified, migration will occur in batches of 50 until fully
   complete.

   Returns exit code 0 if no (further) updates are possible, 1 if the ``--max-count``
   option was used and some updates were completed successfully (even if others generated
   errors), 2 if some updates generated errors and no other migrations were able to take
   effect in the last batch attempted, or 127 if invalid input is provided (e.g.
   non-numeric max-count).

   This command should be called after upgrading database schema and nova services on
   all controller nodes. If it exits with partial updates (exit status 1) it should
   be called again, even if some updates initially generated errors, because some updates
   may depend on others having completed. If it exits with status 2, intervention is
   required to resolve the issue causing remaining updates to fail. It should be
   considered successfully completed only when the exit status is 0.

``nova-manage db ironic_flavor_migration [--all] [--host] [--node] [--resource_class]``
   Perform the ironic flavor migration process against the database
   while services are offline. This is `not recommended` for most
   people. The ironic compute driver will do this online and as
   necessary if run normally. This routine is provided only for
   advanced users that may be skipping the 16.0.0 Pike release, never
   able to run services normally at the Pike level. Since this utility
   is for use when all services (including ironic) are down, you must
   pass the resource class set on your node(s) with the
   ``--resource_class`` parameter.

   To migrate a specific host and node, provide the hostname and node uuid with
   ``--host $hostname --node $uuid``. To migrate all instances on nodes managed
   by a single host, provide only ``--host``. To iterate over all nodes in the
   system in a single pass, use ``--all``. Note that this process is not lightweight,
   so it should not be run frequently without cause, although it is not harmful
   to do so. If you have multiple cellsv2 cells, you should run this once per cell
   with the corresponding cell config for each (i.e. this does not iterate cells
   automatically).

   Note that this is not recommended unless you need to run this
   specific data migration offline, and it should be used with care as
   the work done is non-trivial. Running smaller and more targeted batches (such as
   specific nodes) is recommended.

Nova API Database
~~~~~~~~~~~~~~~~~

``nova-manage api_db version``
    Print the current API database version.

``nova-manage api_db sync [VERSION]``
    Upgrade the API database schema up to the most recent version or
    ``[VERSION]`` if specified. This command does not create the API
    database, it runs schema migration scripts. The API database connection is
    determined by ``[api_database]/connection`` in the configuration file
    passed to nova-manage.

    Starting in the 18.0.0 Rocky release, this command will also upgrade the
    optional placement database if ``[placement_database]/connection`` is
    configured.

.. _man-page-cells-v2:

Nova Cells v2
~~~~~~~~~~~~~

``nova-manage cell_v2 simple_cell_setup [--transport-url <transport_url>]``
    Setup a fresh cells v2 environment; this should not be used if you
    currently have a cells v1 environment. If a transport_url is not
    specified, it will use the one defined by ``[DEFAULT]/transport_url``
    in the configuration file. Returns 0 if setup is completed
    (or has already been done), 1 if no hosts are reporting (and cannot be
    mapped), 1 if the transport url is missing or invalid, and 2 if run in a
    cells v1 environment.

``nova-manage cell_v2 map_cell0 [--database_connection <database_connection>]``
    Create a cell mapping to the database connection for the cell0 database.
    If a database_connection is not specified, it will use the one defined by
    ``[database]/connection`` in the configuration file passed to nova-manage.
    The cell0 database is used for instances that have not been scheduled to
    any cell. This generally applies to instances that have encountered an
    error before they have been scheduled. Returns 0 if cell0 is created
    successfully or already setup.

``nova-manage cell_v2 map_instances --cell_uuid <cell_uuid> [--max-count <max_count>] [--reset]``
    Map instances to the provided cell. Instances in the nova database will
    be queried from oldest to newest and mapped to the provided cell. A
    max_count can be set on the number of instance to map in a single run.
    Repeated runs of the command will start from where the last run finished
    so it is not necessary to increase max-count to finish. A reset option
    can be passed which will reset the marker, thus making the command start
    from the beginning as opposed to the default behavior of starting from
    where the last run finished. Returns 0 if all instances have been mapped,
    and 1 if there are still instances to be mapped.

    If ``--max-count`` is not specified, all instances in the cell will be
    mapped in batches of 50. If you have a large number of instances, consider
    specifying a custom value and run the command until it exits with 0.

``nova-manage cell_v2 map_cell_and_hosts [--name <cell_name>] [--transport-url <transport_url>] [--verbose]``
    Create a cell mapping to the database connection and message queue
    transport url, and map hosts to that cell. The database connection
    comes from the ``[database]/connection`` defined in the configuration
    file passed to nova-manage. If a transport_url is not specified, it will
    use the one defined by ``[DEFAULT]/transport_url`` in the configuration
    file. This command is idempotent (can be run multiple times), and the
    verbose option will print out the resulting cell mapping uuid. Returns 0
    on successful completion, and 1 if the transport url is missing or invalid.

``nova-manage cell_v2 verify_instance --uuid <instance_uuid> [--quiet]``
    Verify instance mapping to a cell. This command is useful to determine if
    the cells v2 environment is properly setup, specifically in terms of the
    cell, host, and instance mapping records required. Returns 0 when the
    instance is successfully mapped to a cell, 1 if the instance is not
    mapped to a cell (see the ``map_instances`` command), 2 if the cell
    mapping is missing (see the ``map_cell_and_hosts`` command if you are
    upgrading from a cells v1 environment, and the ``simple_cell_setup`` if
    you are upgrading from a non-cells v1 environment), 3 if it is a deleted
    instance which has instance mapping, and 4 if it is an archived instance
    which still has an instance mapping.

``nova-manage cell_v2 create_cell [--name <cell_name>] [--transport-url <transport_url>] [--database_connection <database_connection>] [--verbose] [--disabled]``
    Create a cell mapping to the database connection and message queue
    transport url. If a database_connection is not specified, it will use the
    one defined by ``[database]/connection`` in the configuration file passed
    to nova-manage. If a transport_url is not specified, it will use the one
    defined by ``[DEFAULT]/transport_url`` in the configuration file. The
    verbose option will print out the resulting cell mapping uuid. All the
    cells created are by default enabled. However passing the ``--disabled`` option
    can create a pre-disabled cell, meaning no scheduling will happen to this
    cell. The meaning of the various exit codes returned by this command are
    explained below:

    * Returns 0 if the cell mapping was successfully created.
    * Returns 1 if the transport url or database connection was missing
      or invalid.
    * Returns 2 if another cell is already using that transport url and/or
      database connection combination.

``nova-manage cell_v2 discover_hosts [--cell_uuid <cell_uuid>] [--verbose] [--strict] [--by-service]``
    Searches cells, or a single cell, and maps found hosts. This command will
    check the database for each cell (or a single one if passed in) and map any
    hosts which are not currently mapped. If a host is already mapped nothing
    will be done. You need to re-run this command each time you add more
    compute hosts to a cell (otherwise the scheduler will never place instances
    there and the API will not list the new hosts). If the strict option is
    provided the command will only be considered successful if an unmapped host
    is discovered (exit code 0). Any other case is considered a failure (exit
    code 1). If --by-service is specified, this command will look in the
    appropriate cell(s) for any nova-compute services and ensure there are host
    mappings for them. This is less efficient and is only necessary when using
    compute drivers that may manage zero or more actual compute nodes at any
    given time (currently only ironic).

``nova-manage cell_v2 list_cells [--verbose]``
    By default the cell name, uuid, disabled state, masked transport URL and
    database connection details are shown. Use the --verbose option to see
    transport URL and database connection with their sensitive details.

``nova-manage cell_v2 delete_cell [--force] --cell_uuid <cell_uuid>``
    Delete a cell by the given uuid. Returns 0 if the empty cell is found and
    deleted successfully or the cell that has hosts is found and the cell, hosts
    and the instance_mappings are deleted successfully with ``--force`` option
    (this happens if there are no living instances), 1 if a cell with that uuid
    could not be found, 2 if host mappings were found for the cell (cell not empty)
    without ``--force`` option, 3 if there are instances mapped to the cell
    (cell not empty) irrespective of the ``--force`` option, and 4 if there are
    instance mappings to the cell but all instances have been deleted in the cell,
    again without the ``--force`` option.

``nova-manage cell_v2 list_hosts [--cell_uuid <cell_uuid>]``
    Lists the hosts in one or all v2 cells. By default hosts in all v2 cells
    are listed. Use the --cell_uuid option to list hosts in a specific cell.
    If the cell is not found by uuid, this command will return an exit code
    of 1. Otherwise, the exit code will be 0.

``nova-manage cell_v2 update_cell --cell_uuid <cell_uuid> [--name <cell_name>] [--transport-url <transport_url>] [--database_connection <database_connection>] [--disable] [--enable]``
    Updates the properties of a cell by the given uuid. If a
    database_connection is not specified, it will attempt to use the one
    defined by ``[database]/connection`` in the configuration file. If a
    transport_url is not specified, it will attempt to use the one defined by
    ``[DEFAULT]/transport_url`` in the configuration file. The meaning of the
    various exit codes returned by this command are explained below:

    * If successful, it will return 0.
    * If the cell is not found by the provided uuid, it will return 1.
    * If the properties cannot be set, it will return 2.
    * If the provided transport_url or/and database_connection is/are same as
      another cell, it will return 3.
    * If an attempt is made to disable and enable a cell at the same time, it
      will return 4.
    * If an attempt is made to disable or enable cell0 it will return 5.

    .. note::

      Updating the ``transport_url`` or ``database_connection`` fields on a
      running system will NOT result in all nodes immediately using the new
      values.  Use caution when changing these values.

      The scheduler will not notice that a cell has been enabled/disabled until
      it is restarted or sent the SIGHUP signal.

``nova-manage cell_v2 delete_host --cell_uuid <cell_uuid> --host <host>``
    Delete a host by the given host name and the given cell uuid. Returns 0
    if the empty host is found and deleted successfully, 1 if a cell with
    that uuid could not be found, 2 if a host with that name could not be
    found, 3 if a host with that name is not in a cell with that uuid, 4 if
    a host with that name has instances (host not empty).


Placement
~~~~~~~~~

``nova-manage placement heal_allocations [--max-count <max_count>] [--verbose] [--dry-run] [--instance <instance_uuid>]``
    Iterates over non-cell0 cells looking for instances which do not have
    allocations in the Placement service and which are not undergoing a task
    state transition. For each instance found, allocations are created against
    the compute node resource provider for that instance based on the flavor
    associated with the instance.

    There is also a special case handled for instances that *do* have
    allocations created before Placement API microversion 1.8 where project_id
    and user_id values were required. For those types of allocations, the
    project_id and user_id are updated using the values from the instance.

    Specify ``--max-count`` to control the maximum number of instances to
    process. If not specified, all instances in each cell will be mapped in
    batches of 50. If you have a large number of instances, consider
    specifying a custom value and run the command until it exits with 0 or 4.

    Specify ``--verbose`` to get detailed progress output during execution.

    Specify ``--dry-run`` to print output but not commit any changes. The
    return code should be 4.

    Specify ``--instance`` to process a specific instance given its UUID. If
    specified the ``--max-count`` option has no effect.

    This command requires that the ``[api_database]/connection`` and
    ``[placement]`` configuration options are set. Placement API >= 1.28 is
    required.

    Return codes:

    * 0: Command completed successfully and allocations were created.
    * 1: --max-count was reached and there are more instances to process.
    * 2: Unable to find a compute node record for a given instance.
    * 3: Unable to create (or update) allocations for an instance against its
      compute node resource provider.
    * 4: Command completed successfully but no allocations were created.
    * 127: Invalid input.

``nova-manage placement sync_aggregates [--verbose]``
    Mirrors compute host aggregates to resource provider aggregates
    in the Placement service. Requires the ``[api_database]`` and
    ``[placement]`` sections of the nova configuration file to be
    populated.

    Specify ``--verbose`` to get detailed progress output during execution.

    .. note:: Depending on the size of your deployment and the number of
        compute hosts in aggregates, this command could cause a non-negligible
        amount of traffic to the placement service and therefore is
        recommended to be run during maintenance windows.

    .. versionadded:: Rocky

    Return codes:

    * 0: Successful run
    * 1: A host was found with more than one matching compute node record
    * 2: An unexpected error occurred while working with the placement API
    * 3: Failed updating provider aggregates in placement
    * 4: Host mappings not found for one or more host aggregate members
    * 5: Compute node records not found for one or more hosts
    * 6: Resource provider not found by uuid for a given host


See Also
========

* :nova-doc:`OpenStack Nova <>`

Bugs
====

* Nova bugs are managed at `Launchpad <https://bugs.launchpad.net/nova>`__
