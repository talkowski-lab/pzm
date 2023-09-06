
# Docker Image

You may build the Docker image using the following command.

```shell
> cd pzm/src/
> TAG=pzm:v0.1
> docker image build --no-cache --platform linux/amd64 --tag $TAG .
```

For local development purposes, you may run and execute into the created 
Docker image using the following command.

```shell
> docker run -it --entrypoint /bin/bash $TAG
```