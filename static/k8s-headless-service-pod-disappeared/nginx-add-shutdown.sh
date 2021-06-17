#!/bin/bash
kubectl --context minikube patch deployment nginx --output yaml --patch '
---
spec:
  template:
    spec:
      containers:
        - name: nginx
          command: [ "sh" ]
          # Добавляем паузу после завершения nginx
          args:
            - "-c"
            - "nginx -g \"daemon off;\" && sleep 60"
          # К сожалению, sh не пробрасывает SIGTERM в дочерний процесс
          lifecycle:
            preStop:
              exec:
                command: ["sh", "-c", "nginx -s stop"]
      # Увеличиваем время, которое отводится на остановку Pod-а перед
      # его безусловным завершением
      terminationGracePeriodSeconds: 180
'
