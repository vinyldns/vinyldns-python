# vinyldns-python (WORK IN PROGRESS)

Python client library for [VinylDNS](https://www.vinyldns.io/)

This project is a work in progress! If you would like to help us get this where it needs to be,
please reach out to us in [gitter](https://gitter.im/vinyldns/Lobby).

To run, `pip install vinyldns-python` and then:

```python
>>> from vinyldns_python import *
>>> local_client = client.VinylDNSClient("ApiEndpoint", "UserAccessKey", "UserSecretKey")
>>> local_client.list_zones()
>>>
>>> # If all of the following environments are set
>>> # - VINYLDNS_API_URL
>>> # - VINYLDNS_ACCESS_KEY_ID
>>> # - VINYLDNS_SECRET_ACCESS_KEY
>>> from vinyldns_python import *
>>> local_client = client.VinylDNSClient.from_env()
>>> local_client.list_zones()
```

## Contributing

**Requirements**

* `python3`
* `pip`
* `virtualenv`

To get started, you will want to setup your virtual environment.  Ensure that you have `virtualenv`
installed `>pip install virtualenv`.  Then, simply run `./bootstrap.sh` to setup your environment (unless
you really want all these dependencies to be installed locally, which we do not recommend).

Activate your virtual environment `>.virtualenv/bin/activate` and you will be ready to go!

**Unit Tests**
Unit tests are developed using [pytest](https://docs.pytest.org/en/latest/).  We use
[Responses](https://github.com/getsentry/responses), which allows for simple mocking of HTTP endpoints.

To run unit tests, you can simply run `python3 setup.py test`.  To target a specific test, you can
run `python3 setup.pyt test -a "-k my_test"`

**Running a full build**
When you are finished writing your code, you will want to run everything, including linters.  The
simplest way to do this is to run `tox -e py36`, which will run everything only against python 3.6.

If you see any failures / warnings, correct them until `tox` runs successfully.

## Local Development
See the [quickstart](https://github.com/vinyldns/vinyldns/blob/master/README.md#quickstart) in the
VinylDNS api for details on how to start up a local instance of the api in docker. With that
running, you can make requests with the following client details:
```python
local_client = client.VinylDNSClient("http://localhost:9000", "okAccessKey", "okSecretKey")
``` 
