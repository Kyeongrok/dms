FROM centos:7.2.1511

RUN yum -y install epel-release && \
    yum -y update && \
    yum -y install sudo \
                   tree \
                   python34-pip \
                   gcc \
                   python34-devel \
                   libyaml-devel \
                   rsync \
                   mdadm \
                   nfs-utils \
                   at \
                   psmisc && \
    yum -y clean all

RUN useradd -u 1000 jenkins --no-create-home
RUN echo "jenkins  ALL=(ALL)  NOPASSWD:ALL" >> /etc/sudoers

RUN localedef -c -f UTF-8 -i en_US en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
