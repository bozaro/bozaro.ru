---
date: 2016-04-16
title: Сборка UnrealEngine с поддержкой WebPlugin под Linux
slug: ue4-libcef
tags:
 - linux
 - ubuntu
 - ue4
categories:
 - Unreal
menu: main
---

Пост про проблему из-за которой болит чуть ниже спины: https://holtstrom.com/michael/blog/post/437/Shared-Library-Symbol-Conflicts.html

Пост про видимость std: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=50348

Пачт на видимость std: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=36022

Волшебный патч на libstdc++: https://gcc.gnu.org/bugzilla/attachment.cgi?id=17216&action=diff

Финальный патч: https://bitbucket.org/chromiumembedded/cef/pull-requests/61/make-all-libcefso-fuctions-except-of-cef_/diff

Беда с tcmalloc: https://bitbucket.org/chromiumembedded/cef/issues/1827/tcmalloc-should-be-disabled-in-linux-osx

<!--more-->