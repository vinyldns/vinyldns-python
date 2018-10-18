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
