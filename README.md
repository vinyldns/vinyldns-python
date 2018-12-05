# vinyldns-python (WORK IN PROGRESS)

Python client library for [VinylDNS](https://www.vinyldns.io/)

This project is a work in progress! If you would like to help us get this where it needs to be,
please reach out to us in [gitter](https://gitter.im/vinyldns/Lobby).

To run, `pip install vinyldns-python` and then:

```python
>>> from vinyldns.client import VinylDNSClient
>>> local_client = VinylDNSClient("ApiEndpoint", "UserAccessKey", "UserSecretKey")
>>> local_client.list_zones()
>>>
>>> # If all of the following environments are set
>>> # - VINYLDNS_API_URL
>>> # - VINYLDNS_ACCESS_KEY_ID
>>> # - VINYLDNS_SECRET_ACCESS_KEY
>>> from vinyldns.client import VinylDNSClient
>>> local_client = VinylDNSClient.from_env()
>>> local_client.list_zones()
```

## Contributing

**Requirements**

* `python3`
* `pip`
* `virtualenv`

To get started, you will want to setup your virtual environment.

1. Ensure that you have `virtualenv` installed `> pip install virtualenv`
1. Run `./bootstrap.sh` to setup your environment (unless you really want all these dependencies to be installed locally, which we do not recommend).
1. Activate your virtual environment `> source .virtualenv/bin/activate` and you will be ready to go!

**Unit Tests**
Unit tests are developed using [pytest](https://docs.pytest.org/en/latest/).  We use
[Responses](https://github.com/getsentry/responses), which allows for simple mocking of HTTP endpoints.

To run unit tests, you can simply run `python3 setup.py test`.  To target a specific test, you can
run `python3 setup.py test -a "-k my_test"`

**Functional Tests**
Functional tests are also developed with pytest. These tests run against a local instance of VinylDNS. Note that for now
they are not tied into our travis build, so they must be run locally for validation.

To run the func tests, first startup a local VinylDNS api instance with `./docker/docker-up-vinyldns.sh`. Then from
your virtualenv, run `python3 setup.py test -a "func_tests"`.

After testing is complete, you should clean up the running VinylDNS api with `./docker/remove-vinyl-containers.sh `.

**Running a full build**
When you are finished writing your code you will want to run everything including linters.  The
simplest way to do this is to run `tox -e check,py36`, which will run static checks and run unit tests.

If you see any failures / warnings, correct them until `tox` runs successfully.

If you do not have `tox` in your environment, `pip install tox` to add it.  For more information you can
read the [tox docs](https://tox.readthedocs.io/en/latest/index.html).

## Local Development
See the [quickstart](https://github.com/vinyldns/vinyldns/blob/master/README.md#quickstart) in the
VinylDNS api for details on how to start up a local instance of the api in docker. With that
running, you can make requests with the following client details:
```python
local_client = VinylDNSClient("http://localhost:9000", "okAccessKey", "okSecretKey")
``` 
