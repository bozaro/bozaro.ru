#!/bin/bash
echo "
tee dialer.go << EEOF
$(cat dialer.go)
EEOF

go run dialer.go nginx:80
" | kubectl --context=minikube run -i --rm "debug-$(date +'%s')" --image=golang:1.16 --restart=Never --
