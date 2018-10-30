# vinyldns-python (WORK IN PROGRESS)

Python client library for [VinylDNS](https://www.vinyldns.io/)

This project is a work in progress! If you would like to help us get this where it needs to be,
please reach out to us in [gitter](https://gitter.im/vinyldns/Lobby).

To run, `pip install vinyldns-python` and then:

```python
>>> from vinyldns_python import *
>>> local_client = client.VinylDNSClient("ApiEndpoint", "UserAccessKey", "UserSecretKey")
>>> local_client.list_zones()
```

## Local Development
See the [quickstart](https://github.com/vinyldns/vinyldns/blob/master/README.md#quickstart) in the
VinylDNS api for details on how to start up a local instance of the api in docker. With that
running, you can make requests with the following client details:
```python
local_client = client.VinylDNSClient("http://localhost:9000", "okAccessKey", "okSecretKey")
``` 
