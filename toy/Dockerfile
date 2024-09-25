FROM python:3.12

WORKDIR /i8t
ADD . /i8t/

RUN python -m pip install -r requirements/ci.txt .

CMD ["toy/scrape.sh"]
