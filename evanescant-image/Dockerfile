FROM ubuntu:bionic
MAINTAINER Jack Jansen <Jack.Jansen@cwi.nl>

ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH=/evanescent/installed/gnu

RUN apt-get update
WORKDIR /evanescent
COPY tmp/installed/ installed/

CMD /evanescent/installed/gnu/evanescent.exe

