---
date: 2016-12-31
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

Данный скрипт собира	ет все PR и берет из них:

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

Качество коммитор в расчет так же не бралось. То есть исправление тривиальной опечатки и исправление
ошибки работы с памятью в данной статистике имеет одинаковый вес.

### TOP 10 контрибьюторов

Пользователь | Количество коммитов
--- | --- 
[![bozaro](https://avatars.githubusercontent.com/u/2458138?v=3&s=32) bozaro](https://github.com/bozaro) | 149 (5.73%)
[![EverNewJoy](https://avatars.githubusercontent.com/u/7001841?v=3&s=32) EverNewJoy](https://github.com/EverNewJoy) | 106 (4.08%)
[![slonopotamus](https://avatars.githubusercontent.com/u/92637?v=3&s=32) slonopotamus](https://github.com/slonopotamus) | 86 (3.31%)
[![yaakuro](https://avatars.githubusercontent.com/u/7720708?v=3&s=32) yaakuro](https://github.com/yaakuro) | 42 (1.62%)
[![derekvanvliet](https://avatars.githubusercontent.com/u/301217?v=3&s=32) derekvanvliet](https://github.com/derekvanvliet) | 39 (1.50%)
[![Pierdek](https://avatars.githubusercontent.com/u/7024201?v=3&s=32) Pierdek](https://github.com/Pierdek) | 33 (1.27%)
[![3dluvr](https://avatars.githubusercontent.com/u/3603819?v=3&s=32) 3dluvr](https://github.com/3dluvr) | 32 (1.23%)
[![abergmeier](https://avatars.githubusercontent.com/u/2580183?v=3&s=32) abergmeier](https://github.com/abergmeier) | 28 (1.08%)
[![SRombauts](https://avatars.githubusercontent.com/u/868490?v=3&s=32) SRombauts](https://github.com/SRombauts) | 27 (1.04%)
[![projectgheist](https://avatars.githubusercontent.com/u/3892568?v=3&s=32) projectgheist](https://github.com/projectgheist) | 23 (0.88%)
