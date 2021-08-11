FROM alpine:latest
RUN addgroup -S -g 1000 jenkins
RUN adduser -S -u 1000 -G jenkins jenkins
RUN apk add git git-lfs rsync openssh-client curl
