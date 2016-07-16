---
date: 2016-07-16
title: Небольшая статистика по Pull Request-ам в UnrealEngine
slug: ue4-pr
tags:
 - ue4
categories:
 - Unreal
menu: main
---

Достаточно длительное время я работал с UnrealEngine.

Основным моим занятием было решение проблем связанных непосредственно с движком, которых там, как и
в любом крупном продукте хватает.

Для работы мы использовали изрядно подлатанную локальную сборку UnrealEngine. При этом по возможности
отправляли изменения в исходный репозиторий к EpicGames в качестве Pull Requests-ов.

Недавно я решил ~~почесать своё чсв~~ удовлетворить свое любопытство и собрать
статистику по контрибьюторам.

<!--more-->

### Методика сбора данных

Для сбора статистики был написан небольшой [скрипт на Python](/examples/ue4-pr.py). Любой, кто имеет
доступ к репозиторию UnrealEngine, может запустить его самостоятельно.

Для статистики были взяты первые 2600 коммитов (на момент написания статьи всего их было 2604).

Данный скрипт собирает все PR и берет из них:

 * id - номер;
 * created_by - дата создания;
 * user - пользователь github;
 * avatar - аватарка пользователя;
 * commits - кол-во коммитов в PR;
 * title - текстовый заголовок PR.

Результирующий статус PR-а не берется, так как из-за того, что исходный репозиторий живет в Perforce,
выяснить, был ли данный PR принят или нет средствами GitHub-а нельзя.

Количество коммитов было взято для поиска "мусорных" PR, которые сделаны не в ту ветку. Обычно такие PR
содержат тысячи коммитов и какой-либо малосодержательный заголовок. Они оперативно закрываются и
живут обычно пару часов.

Качество коммитов в расчет так же не бралось. То есть исправление тривиальной опечатки и исправление
ошибки работы с памятью в данной статистике имеет одинаковый вес.

### TOP 10 контрибьюторов

Кол-во мусорных Pull Request-ов (>= 100 коммитов) составило 331 штуку (12.73%).

Без учета мусорных коммитов TOP 10 контрибьюторов по первым 2600 Pull Request-ам выглядит следующим образом:

Пользователь | Количество коммитов
--- | ---:
[{{< img src="https://avatars.githubusercontent.com/u/2458138?v=3&s=32" width="32px" height="32px" >}} bozaro](https://github.com/bozaro) | 149 (6.57%)
[{{< img src="https://avatars.githubusercontent.com/u/7001841?v=3&s=32" width="32px" height="32px" >}} EverNewJoy](https://github.com/EverNewJoy) | 105 (4.63%)
[{{< img src="https://avatars.githubusercontent.com/u/92637?v=3&s=32" width="32px" height="32px" >}} slonopotamus](https://github.com/slonopotamus) | 86 (3.79%)
[{{< img src="https://avatars.githubusercontent.com/u/7720708?v=3&s=32" width="32px" height="32px" >}} yaakuro](https://github.com/yaakuro) | 42 (1.85%)
[{{< img src="https://avatars.githubusercontent.com/u/301217?v=3&s=32" width="32px" height="32px" >}} derekvanvliet](https://github.com/derekvanvliet) | 39 (1.72%)
[{{< img src="https://avatars.githubusercontent.com/u/7024201?v=3&s=32" width="32px" height="32px" >}} Pierdek](https://github.com/Pierdek) | 31 (1.37%)
[{{< img src="https://avatars.githubusercontent.com/u/3603819?v=3&s=32" width="32px" height="32px" >}} 3dluvr](https://github.com/3dluvr) | 30 (1.32%)
[{{< img src="https://avatars.githubusercontent.com/u/2580183?v=3&s=32" width="32px" height="32px" >}} abergmeier](https://github.com/abergmeier) | 28 (1.23%)
[{{< img src="https://avatars.githubusercontent.com/u/868490?v=3&s=32" width="32px" height="32px" >}} SRombauts](https://github.com/SRombauts) | 27 (1.19%)
[{{< img src="https://avatars.githubusercontent.com/u/3892568?v=3&s=32" width="32px" height="32px" >}} projectgheist](https://github.com/projectgheist) | 23 (1.01%)
