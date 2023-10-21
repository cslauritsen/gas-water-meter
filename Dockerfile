FROM golang as builder

RUN go install github.com/bemasher/rtlamr@latest

FROM python:3
COPY --from=builder /go/bin/rtlamr /usr/local/bin/rtlamr

WORKDIR /app
COPY python/* .
RUN pip3 install -r requirements.txt
ENV RTLTCP_SERVER "localhost:1234"
CMD [  "sh", "-c", "/usr/local/bin/rtlamr -server=${RTLTCP_SERVER} | python3 /app/publish.py" ]