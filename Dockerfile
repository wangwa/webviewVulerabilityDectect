FROM centos

ENV apppath /srv/wangwa
RUN mkdir ${apppath}

RUN yum install supervisor

COPY ./ ${apppath}

RUN chmod +x ${apppath}/bi/build.sh

RUN ${apppath}/bi/build.sh

CMD sh ${apppath}/services_ctl.sh start
