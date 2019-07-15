FROM continuumio/miniconda3

RUN conda create -n env python=3.6
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash
ENV CONTAINER_USER ikerlan
ENV CONTAINER_UID 1000
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Install Python 3 packages
RUN conda install --yes \
    pandas \
    psycopg2 \
    sqlalchemy \
    && conda clean -yt

ENV USER=root

ADD Simulation_Generator_Agent.py /home/$CONTAINER_USER/simulator/Simulation_Generator_Agent.py
ADD Config_Loader.py /home/$CONTAINER_USER/simulator/Config_Loader.py
ADD DB_Manager.py /home/$CONTAINER_USER/simulator/DB_Manager.py

RUN mkdir /home/$CONTAINER_USER/simulator/data/

# Configure container startup as root
WORKDIR /home/$CONTAINER_USER/simulator/
#ENTRYPOINT ["/sbin/tini", "--"]
