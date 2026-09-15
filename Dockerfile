FROM golang as builder

RUN go install github.com/bemasher/rtlamr@latest

FROM python:3
COPY --from=builder /go/bin/rtlamr /app/rtlamr

WORKDIR /app
COPY python/requirements.txt .
RUN pip3 install -r requirements.txt
ENV RTLTCP_SERVER "host.docker.internal:1234"
ENV SAMPLE_RATE "2048000"
COPY python/ .
#CMD [ "bash", "-o", "pipefail", "-c", "/app/rtlamr -samplerate=${SAMPLE_RATE} -server=${RTLTCP_SERVER} | python3 /app/publishha.py" ]
CMD [ "bash", "-o", "pipefail", "-c", "/app/rtlamr | python3 /app/publishha.py" ]
