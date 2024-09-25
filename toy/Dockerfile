ARG  FROM=python:3.12
FROM ${FROM}

WORKDIR /i8t
COPY requirements /i8t/requirements
RUN python -m pip install -r requirements/toy.txt

COPY . /i8t/
RUN python -m pip install .

CMD ["toy/scrape.sh"]
