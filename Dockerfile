FROM python:3.9.1 as build
RUN python3 -m venv /usr/src/venv
ENV PATH="/usr/src/venv/bin:$PATH"
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

FROM python:3.9.1-slim as app
ENV PATH="/usr/src/venv/bin:$PATH"
RUN apt-get update \
  && apt-get install -qy git \
  && rm -rf /var/cache/apt
WORKDIR /usr/src/app
COPY --from=build /usr/src/venv /usr/src/venv
COPY . /usr/src/app