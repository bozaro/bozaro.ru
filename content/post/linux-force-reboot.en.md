---
date: 2011-05-23
title: Linux force reboot
slug: linux-force-reboot
tags:
 - linux
 - ubuntu
 - reboot
categories:
 - Linux
menu: main
---

Unfortunately, sometimes the Linux reboot command is not enough to reboot. Because of this, there is a desire to reboot a computer located several kilometers away, without performing the correct stop of daemons, etc., that is, to reset it remotely.
<!--more-->
This can be done with the command:

    echo 1 | sudo tee /proc/sys/kernel/sysrq
    echo b | sudo tee /proc/sysrq-trigger

A similar command to shutdown the computer:

    echo 1 | sudo tee /proc/sys/kernel/sysrq
    echo o | sudo tee /proc/sysrq-trigger
