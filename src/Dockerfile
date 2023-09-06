FROM python:3.9.18

COPY ./pzm_tools /opt/pzm_tools

RUN pip install --no-cache-dir --upgrade pip \
    && python -m pip install /opt/pzm_tools

# Clean up.
RUN rm -rf /opt/pzm_tools

# To assert if the package is correctly installed.
RUN pzm-tools --help
