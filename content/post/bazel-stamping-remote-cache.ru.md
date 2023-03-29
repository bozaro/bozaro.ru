---
date: 2023-03-09
title: "Bazel, stamping, remote cache"
slug: bazel-stamping-remote-cache
tags:
  - golang
  - bazel
  - joom
  - stamping
categories:
  - Bazel
menu: main

---

<img alt="Картинка для привлечения внимания :)" class="right" style="max-width: 50%;" src="../../../../img/bazel-stamping-remote-cache/factory.jpg">

В Bazel есть любопытная фича, позволяющая добавить данные, которые не инвалидируют кэш сборки.

Например, это бывает полезно, чтобы добавить в исполняемый файл информацию о том, когда он был собран и из какой
ревизии. Если для времени и номера ревизии использовать stamping, то, когда собранный файл уже есть в кэше, он
пересобираться не будет.
<!--more-->

То есть мы получаем следующее:

- любое значимое изменение соберет файл заново;
- внутри файла будет информация, достаточная для того, чтобы заниматься его отладкой (из указанной ревизии можно собрать
  эквивалентный файл);
- при этом не будет происходить лишней пересборки на каждый коммит из-за не влияющих на него изменений, так как номер
  ревизии не учитывается при поиске в кэше.

В GoLang, к примеру, начиная с версии 1.18, можно получить идентификатор ревизии, от которой был собран файл,
через [debug.ReadBuildInfo](https://pkg.go.dev/runtime/debug#ReadBuildInfo).

## Как использовать stamping?

### Объявление переменных для stamping-а

Для объявления переменных stamping-а нужно завести исполняемый файл, который запишет в стандартный вывод пары
ключ-значение через пробел по одной паре на строку.

Этот файл будет выполняться в корне рабочего пространства.

Например:

```shell
#!/bin/sh
echo "GIT_COMMIT $(git rev-parse HEAD)"
echo "STABLE_GIT_URL $(git remote get-url origin)"
```

Пользовательские переменные с префиксом `STABLE_` будут участвовать в ключе кэширования.

Участвующие в ключе кэширования переменные попадут в файл `bazel-out/stable-status.txt`, а не участвующие попадут в
файл `bazel-out/volatile-status.txt`.

Для того, чтобы Bazel знал, где находится файл, собирающий пользовательские переменные, файл нужно ему передать через
ключ `--workspace_status_command=` (https://bazel.build/reference/command-line-reference#flag--workspace_status_command).

Любопытно, но при написании этого поста, я обнаружил, что скрипт размещенный в корне рабочего пространства, не работает.

У многих правил stamping работает только при сборке с флагом `--stamp`.

### Пример использования stamping и GoLang

[Полный пример доступен на Github](https://github.com/bozaro/bazel-stamping/tree/golang).

#### Минимальное рабочее пространство Bazel для GoLang

Для того, чтобы можно было работать с GoLang в Bazel, создадим три файла.

Пустой файл `BUILD`.

Файл `WORKSPACE` (этот фрагмент взят [здесь](https://github.com/bazelbuild/rules_go/releases/tag/v0.38.1)):
{{< code file="bazel-stamping-remote-cache/golang/WORKSPACE" language="python" >}}

Файл `go.mod` для того, чтобы можно было сравнить поведение с go build:
{{< code file="bazel-stamping-remote-cache/golang/go.mod" language="go" >}}

#### Скрипт для задания переменных

Создадим простой скрипт, который положит в переменную `GIT_COMMIT` текущую ревизию кода `example/stamping.sh`:
{{< code file="bazel-stamping-remote-cache/golang/example/stamping.sh" language="shell" >}}

И, чтобы не передавать имя этого файла при каждом запуске bazel, добавим его в `.bazelrc`:
{{< code file="bazel-stamping-remote-cache/golang/.bazelrc" language="shell" >}}

#### Тестовая программа

Добавил программу для вывода полученных на этапе сборки значений `example/main.go`:
{{< code file="bazel-stamping-remote-cache/golang/example/main.go" language="go" >}}

Эта программа делает следующее:

- выводит содержимое `debug.ReadBuildInfo` как есть;
- выводит значение `vcs.revision` и `vcs.time`, которые передаются средствами `go build`, если он используется;
- выводит значение переменных `gitCommit` и `buildTimestamp`, которые в коде нигде не задаются.

Если эту программу запустить через `go build . && ./example` или, начиная с Go 1.20, через `go run -buildvcs=true .`, то
мы увидим примерно следующее:

```
Stamping example
=== Begin build info ===
go	go1.20.1
path	github.com/bozaro/bazel-stamping/example
mod	github.com/bozaro/bazel-stamping	(devel)
build	-buildmode=exe
build	-compiler=gc
build	CGO_ENABLED=1
build	CGO_CFLAGS=
build	CGO_CPPFLAGS=
build	CGO_CXXFLAGS=
build	CGO_LDFLAGS=
build	GOARCH=amd64
build	GOOS=linux
build	GOAMD64=v1
build	vcs=git
build	vcs.revision=daa3fb74938a476db8bf4b295b01317226780a75
build	vcs.time=2023-02-10T17:03:08Z
build	vcs.modified=true

=== End build info ===
Found go build revision: daa3fb74938a476db8bf4b295b01317226780a75
Found go build timestamp: 2023-02-10T17:03:08Z
```

То есть, в `debug.ReadBuildInfo()` появилась информация из текущей рабочей копии Git. `gitCommit` и `buildTimestamp`
ожидаемо пусты.

#### Сборка тестовой программы

Добавим правило сборки `.go`-файла в `example/BUILD`:
{{< code file="bazel-stamping-remote-cache/golang/example/BUILD" language="python" >}}

В этом правиле примечателен только параметр `x_defs`:

- в переменную `gitCommit` задаётся значение из stamping-переменной `GIT_COMMIT`;
- в переменную `buildTimestamp` задаётся значение из stamping-переменной `BUILD_TIMESTAMP`.

В данном примере `x_defs` объявлен непосредственно на `go_binary`, но его так же можно использовать в `go_library`
и `go_test`.

Данные для `debug.ReadBuildInfo()` Bazel сам не заполняет, но, если очень хочется, то их можно задать
через `runtime.modinfo`.

Правда, есть ряд особенностей:

- версия Go живёт за пределами `modinfo`;
- в самом значении `runtime.modinfo` по 16 байт с краёв отводятся на различные служебные значения, позволяющие зачитать
  эти данные снаружи через `buildinfo.Read` (https://pkg.go.dev/debug/buildinfo#Read).

В результате при запуске этой программы мы получим:

```shell
bazel run --stamp //example

Stamping example
=== Begin build info ===
go	go1.20.1 X:nocoverageredesign
build	vcs.revision=f529d5877d4963ef5964363615b48cf066b8f1ef
build	vcs.time=2023-01-01T00:00:00Z

=== End build info ===
Found go build revision: f529d5877d4963ef5964363615b48cf066b8f1ef
Found go build timestamp: 2023-01-01T00:00:00Z
Found x_defs revision: f529d5877d4963ef5964363615b48cf066b8f1ef
Found x_defs build timestamp: 2023-02-27T06:26:16Z
```

При этом, что важно – если сделать коммит, который не затрагивает данную программу, то пересборки исполняемого файла не
произойдёт.

### Пример использования stamping и рукописного правила

[Полный пример доступен на Github](https://github.com/bozaro/bazel-stamping/tree/custom).

#### Небольшое рабочее пространство

Для примера создадим пустой файл `WORKSPACE` (в этом случае у нас нет внешних зависимостей).

Добавим генерацию переменных в файл `example/stamping.sh`:
{{< code file="bazel-stamping-remote-cache/custom/example/stamping.sh" language="shell" >}}

И добавим правило сборки, которое будет реализовано чуть ниже в файл `BUILD`:
{{< code file="bazel-stamping-remote-cache/custom/BUILD" language="python" >}}

Это правило будет подставлять значения stamping-переменных в шаблон `hello_template.txt`:
{{< code file="bazel-stamping-remote-cache/custom/hello_template.txt" language="text" >}}

#### Реализация правила stamping

Собственно, вся работа будет выполняться довольно простым скриптом на Python `example/stamping.py`:
{{< code file="bazel-stamping-remote-cache/custom/example/stamping.py" language="python" >}}

Этот скрипт:

- получает через аргументы командной строки файл шаблона, файлы со stamping-переменными и имя выходного файла;
- зачитывает stamping-переменные в dict;
- заменяет в шаблоне переменные через регулярное выражение;
- записывает результат в файл.

Никаких python-библиотек за пределами стандартного Python SDK он не использует.

#### Описание правила stamping

Для реализации правила stamping понадобится объявить дополнительные цели в `example/BUILD`:
{{< code file="bazel-stamping-remote-cache/custom/example/BUILD" language="python" >}}

Они понадобятся внутри реализации правила на Starlark для того, чтобы:

- `//example:stamping` – вызвать ранее созданный скрипт `stamping.py`;
- `//example:stamp_detect` – получить значение стандартного
  bazel-флага `--stamp` (https://bazel.build/reference/command-line-reference#flag--stamp).

Само правило на Starlark `example/stamping.bzl`:
{{< code file="bazel-stamping-remote-cache/custom/example/stamping.bzl" language="python" >}}

На что хотелось бы обратить внимание:

- все stamping-переменные разворачиваются уже на этапе выполнения правила;
- файлы `volatile-status.txt` и `stable-status.txt`, явно фигурируют как выходные данные правила;
- для обработки флага `--stamp`, нужно сделать дополнительные приседания с `config_setting`.

#### Проверка правила

Для проверки можно выполнить команды:

```shell
$ bazel build //:hello && cat bazel-bin/hello.txt

This file was generated from {STABLE_GIT_COMMIT} revision at {BUILD_TIME}.

$ bazel build --stamp //:hello && cat bazel-bin/hello.txt

This file was generated from 7b4e16010330195c58158e59d830ed9cfc789637 revision at 2023-02-27T10:03:58+00:00.
```

## Stamping-переменные по-умолчанию

По-умолчанию stamping всегда предоставляет ряд переменных:

- `BUILD_EMBED_LABEL` (stable) – значение флага `--embed_label=...`;
- `BUILD_HOST` (stable) – имя хоста, на котором инициировали сборку;
- `BUILD_USER` (stable) – имя пользователя, который инициировал сборку;
- `BUILD_TIMESTAMP` (volatile) – unix time времени начала сборки.

При этом, важно заметить, что на ферме внутри скрипта часто имеет смысл переопределить поля `BUILD_HOST` и `BUILD_USER`,
иначе смена хоста и пользователя будет провоцировать пересборку шагов, которые использую stamping.

## Stamping ломается при использовании внешнего кэша

Важная проблема stamping – он ломается при использовании внешнего кэша.

У Bazel есть несколько кэшей:

- кэш графа целей в памяти Bazel-демона;
- локальный кэш операций (`$(bazel info output_base)/action_cache`);
- внешний кэш операций (`--disk_cache`, `--remote_cache`, сборочная ферма и т.п.).

При этом у локального и внешнего кэша **разный** ключ кэширования.

В случае с внешним кэшем в ключе кэширования участвуют все входные данные, которые используются для выполнения
соответствующего действия, в том числе переменные окружения, командная строка, входные файлы (де-факто ключ
кэширования – это хэш от `protobuf`-описания шага сборки). Файл `bazel-out/volatile-status.txt` так же является входным
файлом и его содержимое начинает влиять на ключ кэширования.

В результате при использовании внешнего кэша и stamping-а, мы всегда получаем новый ключ кэширования: каждое действие
сборки, которое использует stamping, всегда идёт мимо кэша.

Крайне неприятно то, что при локальных экспериментах можно получать попадание в локальный кэш и создаётся впечатление,
что всё работает так, как нужно. А при сборке на ферме поведение резко меняется на постоянную пересборку.

### Как проверить, работает ли stamping и remote cache?

Убедиться в наличии или отсутствии проблемы со stamping и remote cache можно достаточно простым способом:

- Собрать файл с включенным `--disk_cache` и `--stamp`.

  После этого все данные для сборки должны попасть в дисковый кэш.

  Например:
  ```shell
  bazel run --stamp --disk_cache=/tmp/bazel-disk-cache //example
  ```
- Собрать файл с включенным `--disk_cache` без `--stamp`.

  Это действие должно инвалидировать локальных кэш Bazel.

  Например:
  ```shell
  bazel run --disk_cache=/tmp/bazel-disk-cache //example
  ```

- Еще раз собрать файл с включенным `--disk_cache` и `--stamp`.
  Это действие должно вместо сборки взять ранее собранный файл из дискового кэша.

  Например:
  ```shell
  bazel run --stamp --disk_cache=/tmp/bazel-disk-cache //example
  ```

Если после первого и третьего шага будет одинаковый результат – то проблемы с remote cache нет. К сожалению, на данный
момент (сейчас актуальная версия Bazel 6.0.0) это не так, и третий шаг гарантированно пересобирает исполняемый файл.

### Как подружить stamping и remote cache?

На эту тему в Bazel есть несколько репортов:

- https://github.com/bazelbuild/bazel/issues/10075
- https://github.com/bazelbuild/bazel/issues/16231

Но, к сожалению, корректное решение требует внесения правок во всю цепочку сборки:

- надо расширить [remote execution protocol](https://github.com/bazelbuild/remote-apis), добавив туда возможность
  передавать данные, которые не должны влиять на ключ кэша действия (сейчас ключ кэша – хэш от самого описания задачи
  для удалённой сборки);
- надо добавить поддержку нового протокола в Bazel;
- надо добавить поддержку нового протокола на ферме.

В частности, как я понимаю, из-за большого количества действующих лиц, эта проблема не решается на протяжении уже двух
лет.

#### Можно вынести stamping во внешний сервис

В качестве обходного варианта можно вынести логику шага, использующего stamping, во внешний сервис.

В таком случае действие должно получить примерно следующий вид:

- на вход получаем `volatile-status.txt` и входные файлы, которые необходимы и достаточны для следующего шага;
- считаем хэш от входных файлов для следующего шага и получаем какой-то идентификатор (назовём его `hash_id`);
- отправляем во внешний сервис `volatile-status.txt` и `hash_id`, а этот сервис возвращает `volatile-status.txt`,
  который был отправлен в первый раз для этого `hash_id`, назовём его `first-volatile-status.txt`;
- выполняем следующий шаг с `first-volatile-status.txt` вместо `volatile-status.txt`.

У этого механизма есть очевидная проблема: он требует модификации всех правил, которые используют stamping. Если
какое-то из них забыть поправить или ошибиться в реализации, то корректность работы будет нарушена.

#### Можно подштопать Bazel

Еще один из вариантов обхода этой проблемы: подштопать bazel, чтобы он при подсчете кэша не учитывал volatile-данные для
stamping-а.

К сожалению, в таком случае выполнять эти действия на ферме будет нельзя, но ничто не мешает их выполнять локально.

Заплатку с исправлением Bazel можно взять здесь:

- https://github.com/bazelbuild/bazel/pull/16240

Этот подход то же не без недостатка: у bazel-клиента должны быть права заливать данные в кэш сборки.

Тем не менее в нашем случае этот подход работает без особых нареканий.
