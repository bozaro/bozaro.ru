---
date: 2010-04-12
title: Сверхбыстрое сжатие — lzo
slug: lzo
tags:
 - lzo
 - compression
categories:
 - Libraries
menu: main
---

Данная программа для потокового сжатия была мной обнаружена, когда надо было обеспечить регулярную (раз в сутки) передачу порядка 40Гбайт данных с одного сервера на другой по сети 100Мбит. Время копирования, в этом случае составляло чуть меньше часа. Пришла мысль передавать файл в сжатом виде, и после поиска в интернете я набрел на LZO (http://www.oberhumer.com/opensource/lzo/).

Основная прелесть данного архиватора в том, что он, в отличие, скажем, от GZip, жмет данные много быстрее, чем они читаются с диска. И при этом практически не нагружает процессор.

Это позволяет использовать его, например, для передачи по сети резервной копий базы данных — исходный файл огромный и упираешься в пропускную способность сети, а сжимать чем-то другим слишком долго.
<!--more-->