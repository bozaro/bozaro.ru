---
date: 2013-05-29
title: VNC сервер в Ubuntu 13.04
tags:
 - vnc
 - ubuntu
categories:
 - Ubuntu
menu: main
---

Оказывается, в Ubuntu можно включить человеческий доступ по VNC.

Для этого нужно добавить в /etc/lightdm/lightdm.conf строки:

    [VNCServer]
    enabled=true
    command=Xvnc -SecurityTypes None
    depth=16
    width=1280
    height=960

И перезапустить lightdm (sudo service lightdm restart).

После этого, при попытке подключиться к компьютеру по VNC мы увидим нормальное окно приветствия.

Unity, кстати, по VNC работать отказался.
<!--more-->