#!/bin/bash
kubectl --context minikube patch deployment nginx --output yaml --patch '
---
spec:
  template:
    spec:
      containers:
        - name: nginx
          # Добавляем задержку перед оставнокой nginx
          lifecycle:
            preStop:
              exec:
                command: ["sh", "-c", "sleep 60 && nginx -s stop"]
      # Увеличиваем время, которое отводится на остановку Pod-а перед
      # его безусловным завершением
      terminationGracePeriodSeconds: 180
'
