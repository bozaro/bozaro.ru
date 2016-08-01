---
date: 2016-08-01
title: Маленький .exe-файл без зависимостей
slug: minimal-exe
tags:
 - asm
 - windows
 - programming
categories:
 - Programming
menu: main
---
Некоторое время назад для диагностики проблем с антивирусом мне понадобился `.exe` файл без каких-либо внешних зависимостей.

<!--more-->
В результате родилось следующее чудо:
```x86asm
    global _main

    section .text
_main:
    xor     eax, eax
    ret
```

Для компиляции используется команда:
```bat
nasm -fwin32 nodeps.asm && "%VS120COMNTOOLS%\..\..\VC\bin\link.exe" /subsystem:console /nodefaultlib /entry:main nodeps.obj
```

В результате получился аналог Unix-команды `true` размером ровно 1Kb: [nodeps.zip](/minimal-exe/nodeps.zip).
