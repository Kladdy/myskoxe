# Use the official Ubuntu image
FROM ubuntu:24.04

# Install packages
# Use Boost < 1.82 in order to allow for C++11 compatibility in Boost.Math
RUN apt-get update && apt-get install -y \
    nano \
    curl \
    wget \
    htop \
    git \
    build-essential \
    libboost1.74-all-dev \
    liblapack-dev \
    csh \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash", "-l"]