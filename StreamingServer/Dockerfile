FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
ENV CWIPCDEB=https://github.com/cwi-dis/cwipc/releases/download/nightly/cwipc-ubuntu2204-nightly.deb
ENV PATH=/bin:/usr/bin:/usr/local/bin:
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install apt-file curl

RUN curl --output cwipc.deb --location $CWIPCDEB
RUN apt install -y ./cwipc.deb
CMD cd /cwipc_test/StreamingServer && sh forward-depth7.sh