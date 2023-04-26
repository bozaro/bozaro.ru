---
date: 2023-04-06
title: "Битва за удобный для IDE stack trace в Go (с Bazel и без)"
slug: bazel-golang-vs-stacktrace
tags:
  - golang
  - bazel
  - joom
  - stacktrace
categories:
  - Bazel
menu: main

---

<img alt="Картинка для привлечения внимания :)" class="right" style="max-width: 50%;" src="../../../../img/bazel-golang-vs-stacktrace/battle-for-stacktrace.jpg">

Разработка программного обеспечения связана не только с написанием кода, но и с его отладкой. И отладка должна быть по
возможности комфортной.

С некоторыми ошибками мы пишем в лог стек вызовов. Используемая нами IDE (Idea, GoLand) позволяет по скопированному
стеку вызовов получить комфортную навигацию по
файлам ([Analyze external stack traces](https://www.jetbrains.com/help/idea/analyzing-external-stacktraces.html)). К
сожалению, эта возможность хорошо работает только в том случае, если бинарый файл собран на том же хосте, на котором
запущена IDE.

Этот пост посвящён тому, как мы пытались подружить формат стека вызовов и IDE.
<!--more-->

## А какие вообще варианты отображения стека предоставляет go build?

В go build для влияния на формат вывода стека есть две ручки:

- флаг `-trimpath` – приводит отображение стека вызовов к одинаковому виду, вне зависимости от локального расположения
  файлов;
- переменная окружения `GOROOT_FINAL` – позволяет заменить префикс до системных библиотек в стеке при выключенном
  флаге `-trimpath`.

### Программа для сравнения отображения стека

Рассматривать отображение стека будем на примере небольшой программы.

Исходный код можно скачать по адресу: https://github.com/bozaro/go-stack-trace

Собственно, программа:
{{< code file="go-stack-trace/stacktrace/main.go" language="go" label="stacktrace/main.go" >}}

И небольшой go.mod:
{{< code file="go-stack-trace/go.mod" language="go" label="go.mod" >}}

## Старый добрый GOPATH

Для порядка начнём со старого доброго `GOPATH`.

Пример вывода:

```text
➜ GO111MODULE=off GOPATH=$(pwd) go get -d github.com/bozaro/go-stack-trace/stacktrace
➜ GO111MODULE=off GOPATH=$(pwd) go run github.com/bozaro/go-stack-trace/stacktrace 
Hello World
main.HelloWorld
	/home/bozaro/gopath/src/github.com/bozaro/go-stack-trace/stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	/home/bozaro/gopath/src/github.com/Masterminds/cookoo/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	/home/bozaro/gopath/src/github.com/Masterminds/cookoo/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	/home/bozaro/gopath/src/github.com/Masterminds/cookoo/router.go:131
main.main
	/home/bozaro/gopath/src/github.com/bozaro/go-stack-trace/stacktrace/main.go:27
runtime.main
	/usr/lib/go-1.20/src/runtime/proc.go:250
runtime.goexit
	/usr/lib/go-1.20/src/runtime/asm_amd64.s:1598
```

Здесь всё просто: мы видим полные пути до каждого файла.

При этом все пути расположены либо в `src` директории GoLang, либо в каталоге `GOPATH`.

К сожалению, такой стек будет указывать на существующие файлы только в том случае, когда исполняемый файл собран в
окружении с тем же расположением каталогов. В нашем случае, когда у части разработчиков MacOS, а сборка для боевого
окружения осуществляется под Linux, это требование невыполнимо.

К счастью, есть флаг `-trimpath`, который отрезает вариативную часть от стека вызовов:

```text
➜ GO111MODULE=off GOPATH=$(pwd) go run -trimpath github.com/bozaro/go-stack-trace/stacktrace
Hello World
main.HelloWorld
	github.com/bozaro/go-stack-trace/stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	github.com/Masterminds/cookoo/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	github.com/Masterminds/cookoo/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	github.com/Masterminds/cookoo/router.go:131
main.main
	github.com/bozaro/go-stack-trace/stacktrace/main.go:27
runtime.main
	runtime/proc.go:250
runtime.goexit
	runtime/asm_amd64.s:1598
```

Получился вполне переносимый вид стека вызовов.

## Go Modules

При использовании Go Modules поведение флага `-trimpath` разительно меняется.

Сравним вывод стека вызовов без него:

```text
➜ git clone https://github.com/bozaro/go-stack-trace.git .
➜ go run ./stacktrace 
Hello World
main.HelloWorld
	/home/bozaro/github/go-stack-trace/stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	/home/bozaro/go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	/home/bozaro/go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	/home/bozaro/go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:131
main.main
	/home/bozaro/github/go-stack-trace/stacktrace/main.go:27
runtime.main
	/usr/lib/go-1.20/src/runtime/proc.go:250
runtime.goexit
	/usr/lib/go-1.20/src/runtime/asm_amd64.s:1598
```

И аналогичный вывод с `-trimpath`:

```text
➜ go run -trimpath ./stacktrace
Hello World
main.HelloWorld
	github.com/bozaro/go-stack-trace/stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	github.com/Masterminds/cookoo@v1.3.0/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	github.com/Masterminds/cookoo@v1.3.0/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	github.com/Masterminds/cookoo@v1.3.0/router.go:131
main.main
	github.com/bozaro/go-stack-trace/stacktrace/main.go:27
runtime.main
	runtime/proc.go:250
runtime.goexit
	runtime/asm_amd64.s:1598
```

Без `-trimpath` мы по прежнему видим полные пути до каждого файла. При этом у нас явно прослеживаются три источника с
исходными файлами:

- рабочий каталог с репозиторием (в данном примере: `$HOME/github/go-stack-trace`);
- системные библиотеки GoLang из `$GOROOT/src` (в данном примере: `/usr/lib/go-1.20/src`);
- сторонние библиотеки из `$GOMODCACHE` (в данном примере: `$HOME/go/pkg/mod`);

Что интересно, в отличие от `GOPATH`, флаг `-trimpath` не отрезает префикс в именах файла, а по-другому его формирует:

1. файлы из текущего модуля в рабочем каталоге получают имена с именем модуля из `go.mod` в качестве префикса (в данном
   примере: `$HOME/github/go-stack-trace` → `github.com/bozaro/go-stack-trace`);
2. системные библиотеки GoLang из `$GOROOT/src` получают имена файлов без префикса;
3. сторонние библиотеки в качестве префикса получают имя модуля с версией (в данном
   примере: `/home/bozaro/go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0` → `github.com/Masterminds/cookoo@v1.3.0` –
   особенно обращаю внимание на то, что слово `Masterminds` в пути к файлу и имени модуля пишется по-разному).

## Какой stack trace удобен для IDE?

Внезапно оказывается, что, если открыть проект из репозитория в Idea/GoLand и попробовать проанализировать любой из
вышеприведённых стеков вызовов, то навигации по исходным файлам не будет:

- варианты стека вызовов для `GOPATH` не подходят, так как этот мини-проект использует Go Modules и у него другое
  размещение файлов;
- вариант для Go Modules без `-trimpath` не подойдёт, так как, вероятнее всего, ваш домашний каталог будет отличатся от
  /home/bozaro;
- вариант для Go Modules с `-trimpath` не подойдёт, так как в IDE он не
  поддержан (https://youtrack.jetbrains.com/issue/GO-13827), а из всех путей, которые видны в стеке, суффиксами
  существующих файлов окажутся только файлы из Go SDK.

Со стороны выглядит так, что IDE в нашем случае ищет исходные файлы по путям относительно каталога проекта и его
родителей.

В итоге удовлетворительный формат переносимого стека вызовов получил такой вид:

```text
main.HelloWorld
	stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:131
main.main
	stacktrace/main.go:27
runtime.main
	GOROOT/src/runtime/proc.go:250
runtime.goexit
	GOROOT/src/runtime/asm_amd64.s:1598
```

То есть:

- пути до файлов проекта отображаются относительно корня проекта;
- в качестве путей до сторонних зависимостей используется путь до модуля относительно `$GOMODCACHE`, но с
  префиксом `go/pkg/mod` (IDE найдет этот путь, когда проект лежит в домашнем каталоге, и переменные окружения `GOPATH`
  и `GOMODCACHE` имеют значение «по умолчанию»);
- в качестве путей до файлов из Go SDK просто берём слово `GOROOT`. Нам так и не удалось придумать путь, чтобы IDE
  находило подобные файлы без плясок.

При таком формате стека вызовов IDE распознаёт все файлы, кроме файлов от Go SDK. Вся конструкция ломается, если
разработчик локально переопределил переменные окружения `GOPATH` или `GOMODCACHE`, но сценариев, когда это действительно
нужно, мне не известно.

## Как получить стек вызовов в нужном формате?

Я вижу следующие пути, как можно получить стек вызовов в нужном формате:

- повлиять на сборку, чтобы в отладочной информации были нужные пути файлов;
- перед выводом преобразовывать стек вызовов в нужный формат;
- сделать внешнюю утилиту, которая преобразовывает стек вызовов в нужный формат.

### Повлиять на сборку

Мы не можем повлиять на сборку в случае с Go Build, чтобы сразу получить нужный формат стека вызовов.

### Преобразование стека перед выводом

В нашем случае мы повсеместно используем библиотеку `github.com/joomcode/errorx`, а в ней есть метод для преобразования
в нужный формат стека вызовов перед
выводом: https://pkg.go.dev/github.com/joomcode/errorx#InitializeStackTraceTransformer

Преобразование пути из вида без `-trimpath` при этом выглядит тривиально.

Но у этого метода есть ряд недостатков:

- если стек вызовов прошел мимо этого фильтра, то он останется в исходном формате;
- некоторые места, например pprof, гарантированно передаются в исходном формате.

### Внешняя утилита

Использование внешней утилиты сильно усложняет общий сценарий разбора стека вызовов.

В нашем случае в большинстве случаев стек брался из логов и там он был уже в удобоваримом виде, так что мы этот вариант
серьезно не рассматривали.

## Второй раунд после перехода на сборку через Bazel

В целом, преобразование стека перед выводом в лог нас устраивало вплоть до перехода на сборку через Bazel. Но сборка
через Bazel вывела проблему на новый уровень.

### Формат стека вызовов после сборки bazel

```text
➜ bazel run //stacktrace
...
INFO: Running command line: bazel-bin/stacktrace/stacktrace_/stacktrace
Hello World
main.HelloWorld
	stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	external/com_github_masterminds_cookoo/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	external/com_github_masterminds_cookoo/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	external/com_github_masterminds_cookoo/router.go:131
main.main
	stacktrace/main.go:27
runtime.main
	GOROOT/src/runtime/proc.go:250
runtime.goexit
	src/runtime/asm_amd64.s:1598
```

Мы не требуем от разработчиков использование сборки и запуска файлов через Bazel по ряду причин. Основные из них:

- мы генерируем `BUILD`-файлы своей утилитой и не хотим требовать перегенерацию файлов на каждый чих (она быстрая, но не
  мгновенная);
- синхронизация IDE и `BUILD`-файлов довольно медленная.

При этом в стеке вызовов от Bazel:

- сторонние библиотеки начинают ссылаться на `external`-каталог, который IDE не видит;
- нельзя тривиальным образом получить путь до модуля в `GOMODCACHE` – потеряна информация о версии модуля;
- генерируемые файлы могут получать совершенно неожиданный префикс вида `bazel-out/k8-fastbuild-ST-2df1151a1acb/....`

Все эти пути ссылаются на реальные файлы и вполне осмысленны в контексте Bazel, но без полноценной интеграции они только
пугают.

### Преобразование стека перед выводом

Первоначально пытались собрать набор правил, которые позволяют сформировать из имеющегося стека вызовов нечто
приемлемое.

Для этого через `x_defs`, а потом и `embed` передавали в программу отдельно генерированный файл, который содержал
соответствие `external`-имени желаемому префиксу в стеке вызовов.

Также сделали ряд преобразований для обработки путей генерируемых файлов.

Проблема стала менее острой, но результат всё равно был неудовлетворительным:

- в pprof оставался полный кошмар;
- часть путей преобразовывались неправильно;
- вся конструкция в целом была довольно сложной и хрупкой.

### Внешняя утилита

Идти по этому пути не хотелось: помимо всей сложности и хрупкости при преобразовании стека перед выводом, добавлялась
еще проблема подкладывания этой утилите информации, которую мы зашивали в исполняемый файл, а именно
соответствие `external`-имени желаемому префиксу в стеке вызовов.

То есть, по сути, это должен был быть деобфускатор стека вызовов, но сама эта обфускация нам только мешала :(

### Повлиять на сборку, чтобы были нужные пути файлов

В случае использования Bazel сборка идёт на более низком уровне, чем Go Build. Появилась надежда поправить сборку, чтобы
сразу иметь удобные пути до файлов.

У утилиты `$(go env GOTOOLDIR)/compile` также есть параметр `-trimpath`. Но этот параметр уже не булевый флаг, а
перечень для замены префиксов.

В результате, мы добавили в правила `go_library` и `go_repository` дополнительные атрибуты, чтобы можно было влиять на
стек вызовов:

- https://github.com/bazelbuild/rules_go/pull/3307
- https://github.com/bazelbuild/bazel-gazelle/pull/1379

После этих изменений можно переопределить путь файлов в стеке вызовов, например:

```text
diff --git a/deps.bzl b/deps.bzl
index ffe4981..d917282 100644
--- a/deps.bzl
+++ b/deps.bzl
@@ -5,6 +5,7 @@ def go_dependencies():
         name = "com_github_masterminds_cookoo",
         importpath = "github.com/Masterminds/cookoo",
         sum = "h1:zwplWkfGEd4NxiL0iZHh5Jh1o25SUJTKWLfv2FkXh6o=",
+        stackpath = "go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0",
         version = "v1.3.0",
     )
     go_repository(
@@ -12,4 +13,5 @@ def go_dependencies():
         importpath = "github.com/pkg/errors",
         sum = "h1:FEBLx1zS214owpjy7qsBeixbURkuhQAwrK5UwLGTwt4=",
         version = "v0.9.1",
+        stackpath = "go/pkg/mod/github.com/pkg/errors@v0.9.1",
     )
```

Пример вывода в ветке bazel:

```text
➜ git checkout bazel
➜ bazel run //stacktrace
INFO: Running command line: bazel-bin/stacktrace/stacktrace_/stacktrace
Hello World
main.HelloWorld
	stacktrace/main.go:31
github.com/Masterminds/cookoo.(*Router).doCommand
	go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:209
github.com/Masterminds/cookoo.(*Router).runRoute
	go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:164
github.com/Masterminds/cookoo.(*Router).HandleRequest
	go/pkg/mod/github.com/!masterminds/cookoo@v1.3.0/router.go:131
main.main
	stacktrace/main.go:27
runtime.main
	GOROOT/src/runtime/proc.go:250
runtime.goexit
	src/runtime/asm_amd64.s:1598
```

**ПРИМЕЧАНИЕ:** Патч на Gazelle почему-то сам не подхватывается. Если во время запуска примера произойдёт ошибка
вида `flag provided but not defined: -stack_path_prefix`, то для её исправления нужно пересобрать саму Gazelle. В данном
случае проще всего сбросить кэш Bazel: `bazel clean --expunge && bazel shutdown`.
