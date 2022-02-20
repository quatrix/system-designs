FROM python:3.9

RUN mkdir -p app/src

ADD src/requirements.txt app/src
RUN pip install -r app/src/requirements.txt

ADD src app/src

WORKDIR app

CMD /bin/bash
