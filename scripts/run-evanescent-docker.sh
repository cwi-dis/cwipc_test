#!/bin/sh
docker pull jackjansen/ubuntu1804-vrtogether-evanescent:latest
docker run -p 9000:9000 -t jackjansen/ubuntu1804-vrtogether-evanescent:latest
