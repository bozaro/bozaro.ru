---
date: 2016-04-19
title: MSI packaging on Linux
slug: wix-wine-wixsharp-en
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

One of my pet projects (https://github.com/bozaro/octobuild) used .msi
packages for Windows installation. And not to keep Windows builder, I
sat down and figured out how to assemble under Windows.
<!--more-->
### MSI packaging tools
To build the .msi-package I use Wix (http://wixtoolset.org/).

To not bother with writing XML-files for Wix, I use WixSharp
(https://wixsharp.codeplex.com/).

WixSharp is self-sufficient. No additional installation is required to
build installation packages. WixSharp archive also contains Wix.

Build .msi package is very Windows-specific. As a result, I decided to
use Wine in Linux container. Ubuntu 16.04 using as a guest operating system.

### Installing: Wine
Installing Wine in Linux-container was not trivial. Main problem that Wine
actively uses 32-bit libraries.

To solve this problem you need to add support for 32-bit architecture:
```bash
sudo dpkg --add-architecture i386
```

You can then install Wine:
```bash
sudo apt install software-properties-common
sudo add-apt-repository ppa:ubuntu-wine/ppa
sudo apt update
sudo apt install wine1.8 winetricks
```

### Installing: Microsoft .NET on Wine
To begin, you need to install the Microsoft .NET on Wine.

#### Using 32-bits environment
Microsoft .NET 4.0 can be installed on Wine only in 32bits environment.

This will get you a 32-bit Wine environment:
```bash
# Using 32bits environment
export WINEARCH=win32
# Place Wine data to separate directory
export WINEPREFIX=$HOME/.wine-i686/
```

#### Add GUI support to Linux container
GUI is needed for Microsoft .NET installation.

Simplest way to get GUI on remote Linux host: connect by SSH with X-server
forwarding.

This can be done by command like:
```bash
ssh -X remote-host
```

Unfortunately, the default container that does not give effect, since there
is not installed `xauth`.

To fix you need to install the `xauth` container:
```bash
sudo apt install xauth
```

#### Installing .NET
Actually .NET can be installed with the command:
```bash
winetricks dotnet40
```

At the same time, it will ask to manually download a number of files from Microsoft, but it has not caused problems.

### Solve the error: The specified user does not have a valid profile
```
System.IO.FileLoadException: The specified user does not have a valid profile.  Unable to load 'WixSharp, Version=1.0.34.0, Culture=neutral, PublicKeyToken=3775edd25acc43c2'.
File name: 'WixSharp, Version=1.0.34.0, Culture=neutral, PublicKeyToken=3775edd25acc43c2'
```

This error I came up due to the use ManagedAction.

Solved by adding the magic key to the registry:
```bash
wine reg add "HKLM\\Software\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\S-1-5-21-0-0-0-1000"
```

### Solve the error: Unhandled exception 0xe0434352
```
System.IO.IOException: The parameter is incorrect.

   at System.IO.__Error.WinIOError(Int32 errorCode, String maybeFullPath)
   at System.IO.__Error.WinIOError()
   at System.Console.set_OutputEncoding(Encoding value)
   at csscript.CSExecutionClient.Main(String[] rawArgs)
wine: Unhandled exception 0xe0434352 in thread 9 at address 0x7b83ac1c (thread 0009), starting debugger...
err:winediag:nulldrv_CreateWindow Application tried to create a window, but no driver could be loaded.
err:winediag:nulldrv_CreateWindow Make sure that your X server is running and that $DISPLAY is set correctly.
```

This error bothered longer than the others.

The main problem is that it only appeared in the build with Jenkins.
When I connect via SSH is not reproduced. I suspect that the reason for
this problem is the lack of a terminal in the build with Jenkins.

The solution was simple: it was enough to update the file `csrcs.exe`, incoming
in WixSharp set.

Since `cscs.exe` and `WixSharp` created by same author, I asked him to update
the `cscs.exe` (https://wixsharp.codeplex.com/workitem/110).

As a result, this problem no longer relevant with WixSharp v1.0.35.0 or later.

### Solve the error: light.exe : error LGHT0216
```
light.exe : error LGHT0216 : An unexpected Win32 exception with error code 0x65B occurred: Function failed during execution
```

This error is due to the fact that Wine still not fully compatible with
Windows. In this particular case, Wix can not verify the generated package.

To work around this error, you can simply disable packet inspection
correctness, passing the parameter `-sval` to `light.exe`.

In the case of WixSharp it looks like this:
```c#
Project project = new Project("Test");
project.LightOptions = "-sval";
```
