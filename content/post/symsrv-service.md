---
date: 2016-01-15
title: Использование symsrv.dll внутри сервиса
slug: symsrv-service
tags:
 - pdb
 - symsrv
categories:
 - Libraries
menu: main
---
По работе приходится активно латать Unreal Engine. При сборке нового редактора порождается много толстых .pdb-файлов, которые мы выкладываем на самопальным Symbol Server.

Сам Unreal Engine удалось научить подгружать данные .pdb в случае краша и отображать детальный стек вызовов.

Подгрузка .pdb категорически отказывалась работать на сборочном сервере. И вот вчера я наконец-то заборол эту проблему...
<!--more-->

### Симптомы

Первоначальной задачей была локализация ошибки.

Путем использования утилиты [PsExec.exe](https://technet.microsoft.com/ru-ru/sysinternals/psexec.aspx) удалось констатировать: symsrv.dll не работает при запуске от имени системного пользователя.

То есть на одной и той же машие, она корректно работает от имени локального пользователя и **не работает от имени системного пользователя**.

При этом никаких запросов на стороне nginx от нашего самопального Symbol Server-а не фиксируется. Вообще.

### Диагностика

Первым делом, был прикручен отладочный вывод от symsrv.dll к Unreal Engine ([#1942](https://github.com/EpicGames/UnrealEngine/pull/1942)). Для этого воспользовался флажком [SYMOPT_DEBUG](https://msdn.microsoft.com/en-us/library/windows/desktop/gg278179(v=vs.85).aspx).

После этого играть в игру "найди 10 отличий" стало проще: в отладке запуска от имени системного пользователя появилось загадочное сообщение вида:
```
SYMSRV: WinHttp interface using proxy server: none.
```

Это сообщение при запуске от имени локального пользователя отсутствует.

### Источник проблемы (WinInet vs WinHttp)

После некоторого гугления удалось найти две рассылки от 2006 года (прошло более 9 лет), которые прояснили причину проблемы:

 * https://groups.google.com/forum/#!topic/microsoft.public.windbg/n1Ilf­-n-­orc
 * https://groups.google.com/forum/#!topic/microsoft.public.windbg/k75DAzpVnOc

Для скачивания .PDB данных утилита symsrv.dll использует одну из двух библиотек:

 * WinInet.dll ­ в случае запуска под обычным пользователем (использует настройки прокси из IE);
 * WinHttp.dll ­ в случае запуска под системным пользователем (использует свои настройки прокси). Судя по­всему они её используют, чтобы не вылезало GUI ­сообщений.

Выбор библиотеки осуществляется автоматически. Критерий по которому он производится не известен.

При этом, если Proxy не настроен, то в случае использования WinHttp.dll, утилита symsrv.dll использует зашитый в неё прокси с адресом: symsrvbogusproxy.default­dns­search­suffix. Если этот прокси отсутствует, то качать файлы она может. Без прокси под системным пользователем она работать не способна.

В этой же рассылке от февраля 2006-­ого года предлагается исправить баг путем изменения аргументов функции WinHttpOpen внутри .dll.

Я смог поменять этот вызов (это отдельный квест, так как у меня библиотечка на 10 лет старше и под AMD64), но нужного результата не получил (сообщение из логов исчезло, но работать утилита не стала).

Я уже было отчаялся, но решил погуглить по слову **symsrvbogusproxy** и нешел еще две ссылки:

 * http://sww-it.ru/2015-04-24/1263
 * [https://msdn.microsoft.com/en-­us/library/ff539229(VS.85).aspx](https://msdn.microsoft.com/en­-us/library/ff539229(VS.85).aspx)

В ни выяснилось, что отключить использование прокси для symsrv.dll под системным пользователем можно ключами в реестре:
```
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Symbol Server]
"NoInternetProxy"=dword:00000001

[HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Microsoft\Symbol Server]
"NoInternetProxy"=dword:00000001
```

Но результат остался тем же, что и после правки .dll: сообщение из логов исчезло, но работать утилита не стала.

При этом никаких запросов на стороне nginx от нашего самопального Symbol Server-а по прежнему не фиксируется. Вообще.

### Поиски пропавшего запроса

После включения тайного флажка ```NoInternetProxy``` ситуация изменилось не сильно. Но стало понятно, что хотя бы от этой проблемы удалось избавиться.

Возникла шальная мысль убрать номер порта из URL Symbol Server-а. До этого URL имел вид: http://utils.example.foo:8123.

После замены на URL вида http://utils.example.foo запросы начали отображаться в Symbol Server, но ожидаемо с результатом 404.

Мы перебросили данные на 80-ый порт и выполнили проверку еще раз.

К нашему удивлению, в логах по-прежнему мы видели 404-ый код ошибки. Те же файлы вполне спокойно на той же машине скачивались через браузер.

В результате изучения конфигурационных файлов nginx удалось вспомнить, что когда мы настраивали свой самопальный Symbol Server, в целях экономии места .pdb-файлы начали сохранять в сжатом виде.

Так как возиться с CAB-сжатием под Linux не было никакого желания, мы стали сжимать их GZip-ом, а в конфиг nginx дописали:
```
server {
    gzip_static on;
    ...
}
```

В случае использования WinHttp, на сервер не отправляется HTTP-заголовок:
```
Accept-Encoding: gzip
```

И nginx вместо сжатого файла выдает ошибку 404.

Полечилось включением разжатия для особо одаренных клиентов на стороне nginx:
```
server {
    gzip_static always;
    gunzip on;
    ...
}
```

### Итого

В итоге symsrv.dll при запуске из-под системного пользователя:

 * Не понимает номер порта в URL;
 * Не отправляет заголовок ```Accept-Encoding: gzip```.
 * Пытается использовать прокси с именем **symsrvbogusproxy** (лечится правкой реестра).

При запуске из обычного пользователя этих проблем нет.
