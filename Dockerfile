FROM ubuntu:14.04.5
MAINTAINER ODL DevOps <mitx-devops@mit.edu>

WORKDIR /tmp

# Install base packages
COPY apt.txt /tmp/apt.txt
RUN apt-get update &&\
    apt-get install -y $(grep -vE "^\s*#" apt.txt  | tr "\n" " ")

# node
RUN curl --silent --location https://deb.nodesource.com/setup_4.x | bash -
RUN apt-get install nodejs -y

# pip
RUN curl --silent --location https://bootstrap.pypa.io/get-pip.py | python3 -

# Add, and run as, non-root user.
RUN mkdir /src
RUN adduser --disabled-password --gecos "" mitodl

# Install project packages
COPY requirements.txt /tmp/requirements.txt
COPY test_requirements.txt /tmp/test_requirements.txt
RUN pip install -r requirements.txt &&\
    pip install -r test_requirements.txt

# Add project
COPY . /src
WORKDIR /src
RUN chown -R mitodl:mitodl /src

# Gather static
RUN ./manage.py collectstatic --noinput
RUN apt-get clean && apt-get purge
USER mitodl

# Set pip cache folder, as it is breaking pip when it is on a shared volume
ENV XDG_CACHE_HOME /tmp/.cache

# Set and expose port for uwsgi config
EXPOSE 8071
ENV PORT 8071
CMD uwsgi uwsgi.ini
