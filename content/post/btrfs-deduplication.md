---
date: 2016-04-16
title: Настройка оффлайн дедупликации для Btrfs
slug: btrfs-deduplication
tags:
 - btrfs
 - ubuntu
categories:
 - Ubuntu
menu: main
---

К сожалению, дедупликация сама собой в Btrfs не происходит.

Для неё нужен пинок снаружи.

Для этого можно воспользоваться утилитой dupremove (https://github.com/markfasheh/duperemove):
```
#!/bin/sh
/usr/local/bin/duperemove -dr /var /usr /home
```
<!--more-->