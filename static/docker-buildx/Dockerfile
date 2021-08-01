FROM golang:1.16 AS prepare
WORKDIR /opt
RUN echo "package main;\nimport \"fmt\";\nfunc main() {\n  fmt.Println(\"Hello, world!\")\n}\n" > main.go
RUN go build -o app main.go

FROM alpine
COPY --from=prepare /opt/app /bin/app
