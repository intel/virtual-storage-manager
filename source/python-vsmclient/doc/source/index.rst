Python API
==========
In order to use the python api directly, you must first obtain an auth token and identify which endpoint you wish to speak to. Once you have done so, you can use the API like so::

    >>> from vsmclient import client
    >>> vsm = client.Client('1', $OS_USER_NAME, $OS_PASSWORD, $OS_TENANT_NAME, $OS_AUTH_URL)
    >>> vsm.volumes.list()
    []
    >>> myvol = vsm.volumes.create(display_name="test-vol", size=1)
    >>> myvol.id
    ce06d0a8-5c1b-4e2c-81d2-39eca6bbfb70
    >>> vsm.volumes.list()
    [<Volume: ce06d0a8-5c1b-4e2c-81d2-39eca6bbfb70>]
    >>>myvol.delete

Command-line Tool
=================
In order to use the CLI, you must provide your OpenStack username, password, tenant, and auth endpoint. Use the corresponding configuration options (``--os-username``, ``--os-password``, ``--os-tenant-id``, and ``--os-auth-url``) or set them in environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_TENANT_ID=b363706f891f48019483f8bd6503c54b
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

Once you've configured your authentication parameters, you can run ``vsm help`` to see a complete listing of available commands.
