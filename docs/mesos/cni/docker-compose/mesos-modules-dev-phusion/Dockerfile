FROM phusion/baseimage
MAINTAINER Mesosphere <support@mesosphere.io>

# Install Dependencies

RUN apt-get update -q --fix-missing
RUN apt-get -qy install software-properties-common # (for add-apt-repository)
RUN add-apt-repository ppa:george-edison55/cmake-3.x
RUN apt-get update -q
RUN apt-cache policy cmake
RUN apt-get -qy install \
  build-essential                         \
  autoconf                                \
  automake                                \
  cmake=3.2.2-2~ubuntu14.04.1~ppa1 \
  ca-certificates                         \
  gdb                                     \
  wget                                    \
  git-core                                \
  libcurl4-nss-dev                        \
  libsasl2-dev                            \
  libtool                                 \
  libsvn-dev                              \
  libapr1-dev                             \
  libgoogle-glog-dev                      \
  libboost-dev                            \
  protobuf-compiler                       \
  libprotobuf-dev                         \
  make                                    \
  python                                  \
  python2.7                               \
  libpython-dev                           \
  python-dev                              \
  python-protobuf                         \
  python-setuptools                       \
  heimdal-clients                         \
  libsasl2-modules-gssapi-heimdal         \
  unzip                                   \
  --no-install-recommends

# Install the picojson headers
RUN wget https://raw.githubusercontent.com/kazuho/picojson/v1.3.0/picojson.h -O /usr/local/include/picojson.h

# Prepare to build Mesos
RUN mkdir -p /mesos
RUN mkdir -p /tmp
RUN mkdir -p /usr/share/java/
RUN wget http://search.maven.org/remotecontent?filepath=com/google/protobuf/protobuf-java/2.5.0/protobuf-java-2.5.0.jar -O protobuf.jar
RUN mv protobuf.jar /usr/share/java/

WORKDIR /mesos

# Clone Mesos (master branch)
RUN git clone git://git.apache.org/mesos.git /mesos
RUN git checkout master
RUN git log -n 1

# Bootstrap
RUN ./bootstrap

# Configure
RUN mkdir build && cd build && ../configure --disable-java --disable-optimize --without-included-zookeeper

# Build Mesos
RUN cd build && make -j 2 install

# Install python eggs
RUN easy_install /mesos/build/src/python/dist/mesos.interface-*.egg
RUN easy_install /mesos/build/src/python/dist/mesos.executor-*.egg
RUN easy_install /mesos/build/src/python/dist/mesos.scheduler-*.egg
RUN easy_install /mesos/build/src/python/dist/mesos.native-*.egg
