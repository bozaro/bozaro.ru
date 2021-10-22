---
date: 2011-05-23
title: Жесткая перезагрузка Linux
slug: linux-force-reboot
tags:
 - linux
 - ubuntu
 - reboot
categories:
 - Linux
menu: main
---

К сожалению, иногда команды reboot в Linux не достаточно для перезагрузки. Из-за этого появляется желание перезагрузить комп, находящийся за несколько километров, без выполнения корректной остановки демонов и т.п., то есть удаленно его Reset-нуть.
<!--more-->
Выполнить это можно командой:

    echo 1 | sudo tee /proc/sys/kernel/sysrq
    echo b | sudo tee /proc/sysrq-trigger

Аналогичная конструкций для выключения компьютера:

    echo 1 | sudo tee /proc/sys/kernel/sysrq
    echo o | sudo tee /proc/sysrq-trigger
