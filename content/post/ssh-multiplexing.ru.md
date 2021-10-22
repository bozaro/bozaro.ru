---
date: 2015-06-28
title: SSH мультиплексирование
slug: ssh-multiplexing
tags:
 - ssh
categories:
 - Linux
menu: main
---

Некоторое время назад пришлось разобраться с мультиплексированием в SSH.

После этого повторные подключения по SSH выполняются мгновенно.
<!--more-->
Для его включения под Linux необходимо выполнить команды:
```
#!/bin/sh
echo "Host *
     ControlMaster auto
     ControlPath ~/.ssh/controlmasters/%r@%h:%p
     ControlPersist 10m
" > ~/.ssh/config
mkdir ~/.ssh/controlmasters
chmod 700 ~/.ssh/controlmasters
```
