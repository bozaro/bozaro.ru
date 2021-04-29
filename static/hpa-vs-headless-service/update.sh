#!/bin/bash
kubectl --context minikube patch deployment nginx --patch "
---
spec:
  template:
    metadata:
      annotations:
        version: v$(date +'%s')
"
