Dataset **HIT-UAV** can be downloaded in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format):

 [Download](https://assets.supervisely.com/supervisely-supervisely-assets-public/teams_storage/k/d/ru/0fXaeSmqq3nUNNXRaSj2aKGQSqrXIGKXiELxS2kOlF9MhGmKzlk1Nn0BNpNOBb6N2E0EiFAwD8g7wZ8WI5TgXUAqM7sDfZOEwAWcp6qLHYjT9bGqROHT1R0zOD29.tar)

As an alternative, it can be downloaded with *dataset-tools* package:
``` bash
pip install --upgrade dataset-tools
```

... using following python code:
``` python
import dataset_tools as dtools

dtools.download(dataset='HIT-UAV', dst_dir='~/dataset-ninja/')
```
Make sure not to overlook the [python code example](https://developer.supervisely.com/getting-started/python-sdk-tutorials/iterate-over-a-local-project) available on the Supervisely Developer Portal. It will give you a clear idea of how to effortlessly work with the downloaded dataset.

The data in original format can be [downloaded here](https://github.com/suojiashun/HIT-UAV-Infrared-Thermal-Dataset/releases/download/v1.2.1/HIT-UAV.zip).