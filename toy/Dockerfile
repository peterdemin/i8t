ARG  FROM=python:3.12
FROM ${FROM}

WORKDIR /i8t
ADD requirements /i8t/requirements
RUN python -m pip install -r requirements/toy.txt

ADD . /i8t/
RUN python -m pip install .

CMD ["toy/scrape.sh"]
