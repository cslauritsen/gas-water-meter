FROM golang as builder

RUN go install github.com/bemasher/rtlamr@latest

FROM python:3
COPY --from=builder /go/bin/rtlamr /app/rtlamr

WORKDIR /app
COPY python/requirements.txt .
RUN pip3 install -r requirements.txt
ENV RTLTCP_SERVER "localhost:1234"
COPY python/ .
CMD [ "bash", "-o", "pipefail", "-c", "/app/rtlamr -server=${RTLTCP_SERVER} | python3 /app/publish.py" ]