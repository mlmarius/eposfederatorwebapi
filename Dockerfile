FROM python:3.6.6-stretch
SHELL ["/bin/bash", "-c"]

# Add a non-root user to prevent files being created with root permissions on host machine.
ARG PUID=1000
ARG PGID=1000

RUN apt update &&\
    apt install -y python3-pip git libgeos-c1v5 libspatialindex-c4v5 &&\
    pip3 install virtualenv &&\
    groupadd -g ${PGID} epos &&\
    useradd -g epos --home-dir /home/epos epos && \
    mkdir -p /home/epos/app && \
    chown -R epos:epos /home/epos

WORKDIR /home/epos/app
USER epos
RUN python3 -m virtualenv --system-site-packages venv &&\
    source ./venv/bin/activate &&\
    pip install git+https://github.com/mlmarius/eposfederatorwebapi.git && \
    pip install git+https://github.com/mlmarius/eposfederatorradon.git

CMD ["/bin/bash", "-c", "source ./venv/bin/activate && python -m eposfederator.webapi run" ]
