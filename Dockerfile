FROM centos

ENV apppath /srv/wangwa
RUN mkdir ${apppath}

RUN curl https://bootstrap.pypa.io/get-pip.py
RUN ls -l /etc/yum.repos.d/
RUN yum install -y python-devel libevent-devel python-pip gcc
RUN pip install supervisor

COPY ./ ${apppath}

RUN chmod +x ${apppath}/bi/build.sh

RUN ${apppath}/bi/build.sh

CMD sh ${apppath}/services_ctl.sh start
