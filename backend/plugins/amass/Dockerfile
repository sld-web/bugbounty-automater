FROM golang:1.25-alpine AS builder

RUN apk add --no-cache git

RUN go install -v github.com/owasp-amass/amass/v4/...@latest

FROM alpine:3.19

RUN apk add --no-cache ca-certificates

COPY --from=builder /go/bin/amass /usr/local/bin/amass

RUN amass -version

ENTRYPOINT ["amass"]
