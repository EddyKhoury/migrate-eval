FROM golang:1.25-bookworm

RUN useradd --create-home --uid 10001 runner

WORKDIR /work

USER runner

CMD ["go", "version"]