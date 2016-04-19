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

### Исправление ошибки: The specified user does not have a valid profile
```
System.IO.FileLoadException: The specified user does not have a valid profile.  Unable to load 'WixSharp, Version=1.0.34.0, Culture=neutral, PublicKeyToken=3775edd25acc43c2'.
File name: 'WixSharp, Version=1.0.34.0, Culture=neutral, PublicKeyToken=3775edd25acc43c2'
   at System.Reflection.RuntimeAssembly._nLoad(AssemblyName fileName, String codeBase, Evidence assemblySecurity, RuntimeAssembly locationHint, StackCrawlMark& stackMark, Boolean throwOnFileNotFound, Boolean forIntrospection, Boolean suppressSecurityChecks)
   at System.Reflection.RuntimeAssembly.nLoad(AssemblyName fileName, String codeBase, Evidence assemblySecurity, RuntimeAssembly locationHint, StackCrawlMark& stackMark, Boolean throwOnFileNotFound, Boolean forIntrospection, Boolean suppressSecurityChecks)
   at System.Reflection.RuntimeAssembly.InternalLoadAssemblyName(AssemblyName assemblyRef, Evidence assemblySecurity, StackCrawlMark& stackMark, Boolean forIntrospection, Boolean suppressSecurityChecks)
   at System.Reflection.RuntimeAssembly.InternalLoad(String assemblyString, Evidence assemblySecurity, StackCrawlMark& stackMark, Boolean forIntrospection)
   at System.Reflection.Assembly.Load(String assemblyString)
   at System.Runtime.Serialization.FormatterServices.LoadAssemblyFromString(String assemblyName)
   at System.Reflection.MemberInfoSerializationHolder..ctor(SerializationInfo info, StreamingContext context)
   at System.AppDomain.add_AssemblyResolve(ResolveEventHandler value)
   at WixSharp.Utils.ExecuteInTempDomain[T](Func`2 action)
   at WixSharp.Utils.OriginalAssemblyFile(String file)
   at WixSharp.Compiler.ResolveClientAsm(String asmName, String outDir)
   at WixSharp.Compiler.PackageManagedAsm(String asm, String nativeDll, String[] refAssemblies, String outDir, String configFilePath, Nullable`1 platform, Boolean embeddedUI, String batchFile)
   at WixSharp.Compiler.ProcessCustomActions(Project wProject, XElement product)
   at WixSharp.Compiler.GenerateWixProj(Project project)
   at WixSharp.Compiler.BuildWxs(Project project, String path, OutputType type)
   at WixSharp.Compiler.BuildWxs(Project project, OutputType type)
   at WixSharp.Compiler.Build(Project project, String path, OutputType type)
   at WixSharp.Compiler.Build(Project project, OutputType type)
   at WixSharp.Compiler.BuildMsi(Project project)
   at Script.Main(String[] args)

WRN: Assembly binding logging is turned OFF.
To enable assembly bind failure logging, set the registry value [HKLM\Software\Microsoft\Fusion!EnableLog] (DWORD) to 1.
Note: There is some performance penalty associated with assembly bind failure logging.
To turn this feature off, remove the registry value [HKLM\Software\Microsoft\Fusion!EnableLog].
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
Unhandled exception: 0xe0434352 in 32-bit code (0x7b83ac1c).
Register dump:
 CS:0023 SS:002b DS:002b ES:002b FS:0063 GS:006b
 EIP:7b83ac1c ESP:0032efe4 EBP:0032f068 EFLAGS:00000216(   - --  I   -A-P- )
 EAX:7b827a79 EBX:00000010 ECX:0032f010 EDX:0032f0cc
 ESI:00000000 EDI:0012d810
```
