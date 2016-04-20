---
date: 2016-04-19
title: Сборка .msi-пакетов под Linux
slug: wix-wine-wixsharp
tags:
 - linux
 - ubuntu
 - wine
 - wixsharp
 - wix
 - msi
categories:
 - Development
menu: main
---

Одно из моих поделий (https://github.com/bozaro/octobuild) для установки
под Windows упаковывается в .msi-пакеты. И чтобы не держать для сборки
Windows, я заморочился и разобрался, как собираться из под Windows.
<!--more-->
### Инструментарий для сборки MSI-пакетов
Для сборки .msi-пакетов я использую Wix (http://wixtoolset.org/).

Чтобы не возиться с написанием XML-файлов для Wix, я использую WixSharp
(https://wixsharp.codeplex.com/).

WixSharp самодостаточен. Для сборки установочных пакетов ничего, кроме него
устанавливать не нужно. Архив с WixSharp в том числе содержит и Wix.

Сборка .msi-пакетов крайне платформозависимая вещь. В результате я решил
использовать Wine внутри Linux-контейнера. В качестве гостевой ОС использую
Ubuntu 16.04.

### Установка Wine
Установка Wine в Linux-контейнер оказалась не тривиальной. Основная проблема
в том, что Wine активно использует 32-х битные библиотеки.

Для решения этой проблемы нужно добавить поддержку 32-х битной архитектуры:
```bash
sudo dpkg --add-architecture i386
```

После этого можно собственно установить Wine:
```bash
sudo apt install software-properties-common
sudo add-apt-repository ppa:ubuntu-wine/ppa
sudo apt update
sudo apt install wine1.8 winetricks
```

### Установка .NET внутри Wine
Для начала, нужно установить .NET внутри Wine.

#### Используем в Wine 32-х битное окружений
.NET 4.0 в Wine поддерживается только в 32-х битном окружении.

Для его использования нужно задать переменные окружения:
```bash
# Используем 32-х битное окружение
export WINEARCH=win32
# Используем отдельный каталог для Wine
export WINEPREFIX=$HOME/.wine-i686/
```

#### Добавляем в контейнер поддержку GUI
Для утсановки .NET нужен GUI.

Самый простой способ получить доступ к GUI на удаленной машине: подключиться
к ней по SSH с поддержкой X-сервера.

Это делается командой вида:
```bash
ssh -X remote-host
```

К сожалению, в контейнере по-умолчанию это не дало эффекта, так как
там не установлен `xauth`.

Для исправления ситуации нужно установить в контейнер `xauth`:
```bash
sudo apt install xauth
```

#### Собственно установка .NET
Сама уставнока .NET выполняется командой:
```
winetricks dotnet40
```

При этом она попросит вручную скачать ряд файлов от Microsoft, но трудностей
это у меня не вызвало.

### Исправление ошибки: The specified user does not have a valid profile
```
System.IO.FileLoadException: The specified user does not have a valid profile.  Unable to load 'WixSharp, Version=1.0.34.0, Culture=neutral, PublicKeyToken=3775edd25acc43c2'.
File name: 'WixSharp, Version=1.0.34.0, Culture=neutral, PublicKeyToken=3775edd25acc43c2'
```

### Исправление ошибки: Unhandled exception 0xe0434352
```
System.IO.IOException: ������ ��ࠬ���.

   at System.IO.__Error.WinIOError(Int32 errorCode, String maybeFullPath)
   at System.IO.__Error.WinIOError()
   at System.Console.set_OutputEncoding(Encoding value)
   at csscript.CSExecutionClient.Main(String[] rawArgs)
wine: Unhandled exception 0xe0434352 in thread 9 at address 0x7b83ac1c (thread 0009), starting debugger...
err:winediag:nulldrv_CreateWindow Application tried to create a window, but no driver could be loaded.
err:winediag:nulldrv_CreateWindow Make sure that your X server is running and that $DISPLAY is set correctly.
```

#### Отключаем валидацию .msi-пакетов
