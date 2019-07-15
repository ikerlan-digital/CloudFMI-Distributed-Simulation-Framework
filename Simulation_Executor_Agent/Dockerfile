FROM alpine:latest

# Inspired by :
# * https://github.com/jupyter/docker-stacks
# * https://github.com/CognitiveScale/alpine-miniconda
# * https://github.com/show0k/alpine-jupyter-docker

# Install glibc and useful packages
# mesa-gl and fortran used by modellica
RUN echo "@testing http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
    && apk --update add \
    bash \
    curl \
    ca-certificates \
    libstdc++ \
    glib \
    libgfortran \
    mesa-gl \
    tini@testing \
    && curl "https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub" -o /etc/apk/keys/sgerrand.rsa.pub \
    && curl -L "https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.23-r3/glibc-2.23-r3.apk" -o glibc.apk \
    && apk add glibc.apk \
    && curl -L "https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.23-r3/glibc-bin-2.23-r3.apk" -o glibc-bin.apk \
    && apk add glibc-bin.apk \
    && curl -L "https://github.com/andyshinn/alpine-pkg-glibc/releases/download/2.25-r0/glibc-i18n-2.25-r0.apk" -o glibc-i18n.apk \
    && apk add --allow-untrusted glibc-i18n.apk \
    && /usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8 \
    && /usr/glibc-compat/sbin/ldconfig /lib /usr/glibc/usr/lib \
    && rm -rf glibc*apk /var/cache/apk/*


# Configure environment
ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash
ENV CONTAINER_USER ikerlan
ENV CONTAINER_UID 1000
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Configure Miniconda
#ENV MINICONDA_VER 4.5.1
ENV MINICONDA_VER 4.5.11
ENV MINICONDA Miniconda3-$MINICONDA_VER-Linux-x86_64.sh
ENV MINICONDA_URL https://repo.continuum.io/miniconda/$MINICONDA
ENV MINICONDA_MD5_SUM e1045ee415162f944b6aebfe560b8fee

# Install conda
RUN cd /tmp && \
    mkdir -p $CONDA_DIR && \
    curl -L $MINICONDA_URL  -o miniconda.sh && \
    echo "$MINICONDA_MD5_SUM  miniconda.sh" | md5sum -c - && \
    /bin/bash miniconda.sh -f -b -p $CONDA_DIR && \
    rm miniconda.sh && \
    $CONDA_DIR/bin/conda install --yes conda==$MINICONDA_VER

RUN conda upgrade -y pip && \
    conda config --add channels conda-forge && \
    conda clean --all

# Install Python 3 packages
RUN conda install --yes \
    anaconda python \
    anaconda pandas \
    pyfmi \
    anaconda psycopg2 \
    && conda clean -yt

ENV USER=root

ADD Simulation_Executor_Agent.py /home/$CONTAINER_USER/simulator/Simulation_Executor_Agent.py
ADD Model_executor.py /home/$CONTAINER_USER/simulator/Model_executor.py
ADD Config_Loader.py /home/$CONTAINER_USER/simulator/Config_Loader.py
ADD DB_Manager.py /home/$CONTAINER_USER/simulator/DB_Manager.py

RUN mkdir /home/$CONTAINER_USER/simulator/model/


# Configure container startup as root
WORKDIR /home/$CONTAINER_USER/simulator/
ENTRYPOINT ["/sbin/tini", "--"]
