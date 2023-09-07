
# Docker Image

1. You may build the Docker image using the following command.

```shell
> cd pzm/src/
> TAG=us.gcr.io/broad-dsde-methods/vjalili/pzm:v0.1
> docker image build --no-cache --platform linux/amd64 --tag $TAG .
```

2. For local development purposes, you may run and execute into the created 
Docker image using the following command.

```shell
> docker run -it --entrypoint /bin/bash $TAG
```

3. In order to use the Docker image in Terra, you would need to 
push the image to a container registry accessible to Terra.
Assuming the tag you specified in `TAG` refers to such registry, 
you may run the following to push the image. 

```shell
> docker push $TAG
```

# Run WDL locally

For development purposes, you may take the following steps to 
run the WDL locally---without needing a Cromwell deployment or Terra workspace. 

1. Download Cromwell from 
   [Cromwell releases page](https://github.com/broadinstitute/cromwell/releases).

2. Run the following command to execute the `Filter` workflow.
   ```shell
   > cd src
   > java -jar cromwell-72.jar run \
      --inputs test_data/inputs.json \
      --options test_data/options.json \
      --metadata-output metadata.json \
      wdl/Classifier.wdl \ 
   ```
