FROM centos

ENV apppath /srv/wangwa
RUN mkdir ${apppath}

RUN yum -y install epel-release
RUN yum install -y python-devel libevent-devel python-pip gcc
RUN yum install -y supervisor

RUN mkdir /srv/supervisord.d/ -p

RUN sed -i 's/files =/&\/srv\/supervisord.d\/*.conf,/g' /etc/supervisord.conf

COPY ./ ${apppath}

RUN chmod +x ${apppath}/bi/build.sh

RUN ${apppath}/bi/build.sh

CMD sh ${apppath}/services_ctl.sh start

#change by peter
