FROM python:3-alpine
USER root
RUN apk add \
      --no-cache --update --virtual .build-deps build-base libffi-dev openssl-dev \
    && pip install nexus3-cli \
    && apk del .build-deps \
    && rm -rf ~/.cache/pip
CMD ["/usr/local/bin/nexus3"]
