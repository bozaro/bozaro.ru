---
date: 2015-02-02
title: Plex внутри libvirt
tags:
 - plex
 - libvirt
 - ubuntu
categories:
 - Ubuntu
menu: main
---

Недавно озадачился установкой Plex-сервера внутри виртуальной машины (libvirt qemu внутри Ubuntu).

Долго не мог понять, почему телевизор видит Plex-сервер только очень небольшое время после его запуска.

Способ лечения проблемы оказался следующим:

    echo -n 0 > /sys/devices/virtual/net/br0/bridge/multicast_snooping
<!--more-->