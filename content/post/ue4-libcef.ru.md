---
date: 2016-05-27
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

Некоторое время назад добавили в проект на UnrealEngine виджет WebBrowser.

Достаточно быстро выяснилось, что этот виджет отсутствует под Linux. Из-за этого развалился кукинг,
в том числе и серверной части.

Путем наворачивания костылей удалось восстановить сборку проекта без WebBrowser-а под Linux, но так
же было решено сделать это чуть позже по-человечески. То есть научиться собирать WebBrowser
под Linux.

<!--more-->

Изначально задача научиться собирать WebBrowser под Linux не выглядела страшно, так как на тот
момент уже достаточно давно существовал
pull request: [#977 Basic CEF support for GNU/Linux](https://github.com/EpicGames/UnrealEngine/pull/977).

Нам казалось, что достаточно просто взять и актуализировать этот pull request.

### Проблемы с песочницей

После взятия изменений из pull request-а и сборки Unreal Engine выяснилось, что при поптыке создать виджет редактор падает.

Последнее, что он пишет:
```
[0527/191819:ERROR:browser_main_loop.cc(173)] Running without the SUID sandbox! See https://code.google.com/p/chromium/wiki/LinuxSUIDSandboxDevelopment for more information on developing with the sandbox on.
```

При этом в коде Unreal Engine песочница выключена.

Достаточно много времени было потрачено на попытки понять, что пошло не так. Но в последствии
выяснилось, что это сообщение никакого отношения к падению редактора не имеет и его можно
игнорировать.

Осознание этого пришло после того, как в очередной раз был пересмотрен pull request, в котором
явно сказано:

> libcef.so is compiled using tcmalloc that causes crash in the CefDoMessageLoopWork(). The
> reason is that some functions frees resources using the ansi free functions even though they
> are allocated with tcmalloc. If libcef.so is preloaded before libc.so everything works.
> Slateviewer loads libcef.so before libc.so so no issues there.
>
> To run the other stuff
> ```
LD_PRELOAD=../libcef.so ./UE4Editor ...
```
> can be used.

### Пересборка `libcef` без `tcmalloc`

Естественным действием после этого была попытка пересобрать `libcef` без `tcmalloc`.

Это делается достаточно просто. Вся пересборка сводится к набору команд:

```bash
#!/bin/bash
mkdir -p ~/.gyp
echo "{
  'variables': {
    'use_allocator': 'none',
  },
}" > ~/.gyp/include.gypi
wget https://bitbucket.org/chromiumembedded/cef/raw/master/tools/automate/automate-git.py
python automate-git.py --download-dir=/mnt/storage/cef/cef.2357 --branch=2357 --no-debug-build --force-build
```

К сожалению, поведение с пересобранной библиотекой не сильно поменялось: оно так же запускалось
с `LD_PRELOAD` и так же крашилось без `LD_PRELOAD`. Но в краш-дамп содержал уже совершенно другой
стек.

### Разбор полётов с `std::*`

В стеке привлек внимание следующий фрагмент:

```cpp
#0  0x00007f46d8ca1f27 in arena_run_tree_insert (rbtree=0x7f45f4006a60, node=0x7f45f4000048) at src/arena.c:69
#1  0x00007f46d8caad35 in arena_bin_runs_insert (run=<optimized out>, bin=0x7f45f4006a30) at src/arena.c:1330
#2  arena_bin_lower_run (bin=0x7f45f4006a30, run=<optimized out>, chunk=<optimized out>, arena=<optimized out>) at src/arena.c:1868
#3  je_arena_dalloc_bin_locked (arena=0x7f45f4000020, chunk=0x7f45f4000000, ptr=<optimized out>, mapelm=<optimized out>) at src/arena.c:1898
#4  0x00007f46d8caae4a in je_arena_dalloc_bin (mapelm=<optimized out>, pageind=<optimized out>, ptr=0x7f45f4007d50, chunk=0x7f45f4000000, arena=0x7f45f4000020) at src/arena.c:1917
#5  je_arena_dalloc_small (arena=0x7f45f4000020, chunk=<optimized out>, ptr=0x7f45f4007d50, pageind=<optimized out>) at src/arena.c:1933
#6  0x00007f46d894592a in FMemory::Free (Original=0x7f45f4007d50) at /home/bozaro/github/unreal/Engine/Source/Runtime/Core/Private/HAL/UnrealMemory.cpp:114
#7  0x00007f46ceed19b6 in operator delete (Ptr=0x7f45f4006a60) at /home/bozaro/github/unreal/Engine/Source/Editor/UnrealEd/Private/UnrealEd.cpp:192
#8  0x00007f46cf7f15d0 in std::_Rb_tree<std::string, std::string, std::_Identity<std::string>, std::less<std::string>, std::allocator<std::string> >::_M_erase(std::_Rb_tree_node<std::string>*) ()
   from /home/bozaro/github/unreal/Engine/Binaries/Linux/libUE4Editor-UnrealEd.so
#9  0x00007f46afb51cb2 in CefURLRequestContextGetterImpl::SetCookieSupportedSchemes(std::vector<std::string, std::allocator<std::string> > const&) ()
   from /home/bozaro/github/unreal/Engine/Binaries/Linux/libcef.so
#10 0x00007f46afb519dc in CefURLRequestContextGetterImpl::SetCookieStoragePath(base::FilePath const&, bool) () from /home/bozaro/github/unreal/Engine/Binaries/Linux/libcef.so
#11 0x00007f46afb509f8 in CefURLRequestContextGetterImpl::GetURLRequestContext() () from /home/bozaro/github/unreal/Engine/Binaries/Linux/libcef.so
#12 0x00007f46b1cc273e in content::ChromeAppCacheService::InitializeOnIOThread(base::FilePath const&, content::ResourceContext*, net::URLRequestContextGetter*, scoped_refptr<storage::SpecialStoragePolicy>) () from /home/bozaro/github/unreal/Engine/Binaries/Linux/libcef.so
```

Привлекло следующее: если обратить внимание на 9-ый элемент, то там мы увидим, что работает код
из `libcef.so`, но на 8-ом элементе внезапно выполняется код из `libUE4Editor-UnrealEd.so`.

Тут надо сделать ремарку: libcef, как и UnrealEngine активно использует C++, но интерфейс между
libcef реализован через C-функции. То, что libcef использует C++ реализацию std-библиотеки из
UnrealEngine выглядит достаточно странно.

То есть возникла проблема с конфликтом функций между библиотекой и исполняемым файлом. Эта проблема
хорошо описана в статье: https://holtstrom.com/michael/blog/post/437/Shared-Library-Symbol-Conflicts.html

Первая мысль была в том, что `libcef` собирается без флага `-fvisibility=hidden`, но это оказалось не так.

Внезапно оказалось, что функции `std::*` всегда публикуются в динамической
библиотеке: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=50348

Подправив локальный файл `/usr/include/bits/c++config` и пересобрав `libcef` выяснилось, что исправление
видимости `std::*` решает проблему. К сожалению, такой вариант фикса не выглядит как корректное решение.

В конечном итоге удалось поправить видимость `std::*` на этапе линковки.

### Итого

В результате родились pull requests-ы:

 * Исправление видимости `std::*` в libcef: https://bitbucket.org/chromiumembedded/cef/pull-requests/61
 * Поддержка WebBrowser под Linux для UnrealEngine: https://github.com/EpicGames/UnrealEngine/pull/2438

А так же найден тикет про tcmalloc: https://bitbucket.org/chromiumembedded/cef/issues/1827
