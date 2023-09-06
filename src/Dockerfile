FROM python:3.9.18

COPY . /opt/pzm_filter

RUN pip install --no-cache-dir --upgrade pip \
    && python -m pip install /opt/pzm_filter
#     && pip install -e /opt/pzm_filter

# Clean up.
RUN rm -rf /opt/pzm_filter

# To assert if the package is correctly installed.
RUN pzm-filter --help
