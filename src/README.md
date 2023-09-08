`pzm-tools` is a script collection tailored for post-zygotic mutation (PZM) analysis; 
it is packaged as a Python package, Dockerized for containerization, 
and WDLized for workflow compatibility. 
You have multiple options for running it:

1. [**Local Installation:**](#local-installation)
   You can install it on your local machine as a Python package and 
   use it programmatically.

2. [**Command Line:**](#command-line)
   Run it directly from the command line by invoking its executable.

3. [**Docker Image:**](#docker-image) 
   Execute it within a Docker container, ensuring portability and isolation.

4. **Cloud Execution:** 
   These tools are WDLized, offering flexibility for execution:

   - [**Local Cromwell:**](#run-wdl-locally) 
     Run them on a local Cromwell engine without server or 
     deployment hassles, mainly for development purposes.

   - [**Cloud Cromwell Deployment:**](#cromwell-deployment) 
     Execute on a cloud-based Cromwell deployment, mainly for power users to test scalability.

   - [**Terra workspace:**](#terra) 
     Run within a Terra workspace, mainly for end-users.


## Local Installation

```shell
# Clone the repository
> git clone https://github.com/talkowski-lab/pzm 
> cd pzm

# Create a virtual environment and activate it.
> virtualenv .venv
> source .venv/bin/activate

# Install the package
> pip install src/pzm_tools 
```

## Command Line

First, install the package following the instructions given in the
[local installation](#local-installation) section, then you
may invoke it from the command line as the following.

```shell
> cd src
> pzm-tools label \ 
    test_data/rf_model.joblib \
    test_data/SS0012986.vcf.gz \
    --output-prefix test
```

You may run `pzm-tools --help` for more detailed documentation
on the subcommands and their arguments.

## Docker Image

For local development purposes, you may run and execute into the `pzm-tools` 
Docker image using the following command.

```shell
> TAG=us.gcr.io/broad-dsde-methods/vjalili/pzm:v0.1
> docker run -it --entrypoint /bin/bash $TAG
```

Once you run and exec into the Docker image, you may run the 
`pzm-tools` from [command line as this](#command-line). For example:

```shell
> docker run -it --entrypoint /bin/bash $TAG
root@65337f2018ce:/# pzm-tools
usage: pzm-tools [-h] {label} ...

Tools for studying PZM variants

optional arguments:
  -h, --help  show this help message and exit

subcommands:
  {label}
    label     Label the variants in a given VCF file as PZM or not-PZM
              using a trained random forest model.

```

### Building Docker Image

You may build the Docker image using the following command.

```shell
> cd pzm/src/
> TAG=us.gcr.io/broad-dsde-methods/vjalili/pzm:v0.1
> docker image build --no-cache --platform linux/amd64 --tag $TAG .
```

In order to use the Docker image in Terra, you would need to 
push the image to a container registry accessible to Terra.
Assuming the tag you specified in `TAG` refers to such registry, 
you may run the following to push the image. 

```shell
> docker push $TAG
```

## Run WDL locally

For development purposes, you may take the following steps to 
run the WDL locally---without needing a Cromwell deployment or Terra workspace. 

1. Download Cromwell from 
   [Cromwell releases page](https://github.com/broadinstitute/cromwell/releases).

2. Run the following command to execute the `Classifier` workflow.
   ```shell
   > cd src
   > java -jar cromwell-72.jar run \
      --inputs test_data/inputs.json \
      --options test_data/options.json \
      --metadata-output metadata.json \
      wdl/Classifier.wdl \ 
   ```


## Cromwell deployment

1. Install and configure [cromshell](https://github.com/broadinstitute/cromshell)
   to interface with a Cromwell server.

2. Create `inputs.json` and `options.json`. 
   You may use `test_data/inputs.json` and `test_data/options.json` as template, 
   ensure the files are stored on a Google cloud bucket that is accessible to the 
   cromwell server you are using.

3. Run the following command to submit the workflow to be executed on Cromshell.

   ```shell
   cromshell submit wdl/Classifier.wdl inputs.json options.json
   ```
   
4. You may check the status of your submission as the following.

   ```shell
   cromshell status
   ```

## Terra

The `Classifier` workflow is hosted on 
[this Dockstore](https://dockstore.org/my-workflows/github.com/talkowski-lab/pzm/Classifier)
page. You may follow 
[these steps](https://support.terra.bio/hc/en-us/articles/360038137292--How-to-import-a-workflow-and-its-parameter-file-from-Dockstore-into-Terra)
to import it into your Terra workspace.
