---
date: 2023-02-22
title: "Зачем мигрировать с go build на Bazel?"
slug: bazel-why-migrate
tags:
- golang
- bazel
- joom
categories:
- Bazel
menu: main

---

<img alt="Картинка для привлечения внимания :)" class="right" style="max-width: 50%;" src="../../../../img/bazel-why-migrate/bazel-research.jpg">

Это первый пост из цикла, посвященного миграции с `go build` на Bazel.

К процессу миграции мы подошли на этапе, когда запуск тестов на CI занимал примерно от 15 минут до часа. При этом мы уже
успели реализовать некоторое распараллеливание и кэширование результатов тестов. Без этого тесты на одной машине должны
были бы идти примерно часов восемь.

После внедрения **Bazel запуск тестов на CI в основном укладывается в интервал от 1,5 до 25 минут (50 перцентиль в
районе 12 минут)**, что гораздо комфортнее исходной ситуации.
<!--more-->

**Оговоримся**, что сравнение этих цифр «в лоб» несколько некорректно: с одной стороны, за время пути кодовая база стала
еще больше, а с другой — поменялась топология CI. Но в целом представление о полученном эффекте они дают.

Далее опишем, за счет какого механизма достигнуто ускорение.

## Что не так с go build?

Всем известно, что в GoLang очень быстрая компиляция. И это действительно так, но есть ряд особенностей, которые крайне
негативно сказываются на общем времени сборки.

### Особенности тестов в GoLang

При запуске теста можно выделить следующие стадии:

- генерация кода (можно выполнить один раз на все тесты);
- компиляция;
- линковка;
- выполнение теста.

Особенностью GoLang является то, что на каждый пакет с тестами создаётся исполняемый файл. В результате, каждый тестовый
пакет требует время на линковку. Как результат, сборка исполняемых файлов может занимать намного больше времени, чем
сами тесты.

Гораздо менее очевидно, что пакеты могут компилироваться персонально для каждого теста. Так, при тестировании пакета foo
все пакеты, которые используются в foo_test и сами используют foo, компилируются с тестовой версией пакета foo
персонально для этого теста. Таких пакетов могут быть сотни на один тестовый пакет.

Немного исходного кода:

{{< code file="bazel-why-migrate/compile-per-test/go.mod" language="go" label="go.mod" >}}
{{< code file="bazel-why-migrate/compile-per-test/bar/bar.go" language="go" label="bar/bar.go" >}}
{{< code file="bazel-why-migrate/compile-per-test/foo/foo.go" language="go" label="foo/foo.go" >}}
{{< code file="bazel-why-migrate/compile-per-test/foo/foo_test.go" language="go" label="foo/foo_test.go" >}}
{{< code file="bazel-why-migrate/compile-per-test/foo/foo_test_test.go" language="go" label="foo/foo_test_test.go" >}}

В проекте два пакета: `foo` и `bar`.

Для типа `foo.Foo` объявлен метод `Bar()` в файле `foo_test.go` (пакет `foo`), который является тестовым. В пакете `bar`
есть явное обращение к методу `Bar()` структуры `foo.Bar`.

В итоге получается:

- в файле `foo_test_test.go` (пакет `foo_test`) можно использовать пакет `bar`, так как он собран с тестовыми файлами
  пакета `foo`.
- отдельно пакет `bar` даже не скомпилируется, так как метод `Bar` объявлен в тестовых файлах и доступен только при
  компиляции тестов этого класса.

```shell
go test github.com/bozaro/example/...
# github.com/bozaro/example/bar
bar/bar.go:7:11: f.Bar undefined (type foo.Foo has no field or method Bar)
ok  	github.com/bozaro/example/foo	0.004s
FAIL
```

### Кэш компиляции

Если изучить, от чего зависит результат компиляции отдельного пакета в GoLang, то мы увидим, как минимум:

- тэги сборки;
- значение `GCO_ENABLED`;
- значение `GOOS` и `GOARCH`;
- то, какой тестовый пакет мы в данный момент собираем.

То есть в рамках сборки проекта один и тот же пакет в худшем случае может пересобираться сотни раз.

В рамках `go build` кэш компиляции есть, но он не всегда работает (на некоторых пакетах у нас два последовательных
запуска никогда не получают cache hit) и даже при полном попадании в кэш запуск может занимать несколько секунд.

### У go build нет промежуточных результатов

С учетом вышеприведённых особенностей сборки это, возможно, к лучшему. Однако из‑за отсутствия промежуточных артефактов
повторное использование промежуточных шагов сборки становится крайне затруднительным.

Повторно использовать какие‑то артефакты можно, только если спуститься на уровень ниже `go build` и реализовать сборку
самостоятельно.

### Генерация кода и go:generate

Мы использовали генерированный код для:

- protobuf-а;
- маршалинг-а;
- mock-ов.

Генерируемого кода было достаточно много, но при этом мы не хранили генерированные файлы внутри репозитория, используя
отдельный скрипт для перегенерации всех файлов.

Для генерации использовали стандартный механизм go:generate с некоторым обвесом для распараллеливания и кэширования.

У генераторов в GoLang есть ряд проблем.

#### Команды, объявленные в go:generate, не имеют никакого описания

А именно:

- у них не определён порядок вызова между файлами;
- по самой команде ничего нельзя сказать по поводу её входных и выходных данных.

Из-за этого, если возникают зависимость на порядок генерации файлов между пакетами, то всё сразу становится очень плохо.

#### Генераторы могут зависеть от компиляции

Сами генераторы можно разделить на два вида:

- генераторы, которые **создают код на базе анализа AST-дерева исходного кода** – с ними всё хорошо. Они работают очень
  быстро, но обычно они могут оперировать только ограниченным объемом информации о коде (так, к примеру,
  работает https://github.com/tinylib/msgp);
- генераторы, которые **компилируют пакет (со всеми зависимостями)**, для получения информации об исходном коде через
  reflection (так, к примеру, работает golang.org/x/tools/cmd/stringer). Эти генераторы имеют доступ к более богатой
  информации о типах, но в этом случае, помимо накладных расходов на компиляцию, мы бонусом получаем зависимость между
  генераторами разных пакетов.

### Проверка кода с помощью go vet

Для статического анализа кода в GoLang существует готовый инструмент: https://pkg.go.dev/cmd/vet

К сожалению, непонятно, как его запускать инкрементально: его можно запустить для одного пакета, но выглядит так, что он
пытается этот пакет скомпилировать со всеми зависимостями. Из-за этого не удаётся получить выигрыш в скорости при
инкрементальном запуске.

Именно из-за времени выполнения go vet мы получали нижнюю границу времени прогона на CI в 15 минут.

## За счет чего Bazel должен быть быстрее?

Bazel является средством сборки проектов общего назначения без привязки к конкретному стеку. Он изначально создавался с
расчетом на работу с обширной кодовой базой.

Bazel предоставляет язык для описания и выполнения графа сборки.

Ускорение при этом получается за счет двух основных вещей:

- агрессивное кэширование;
- встроенные механизмы для выполнения задач на ферме.

Для того, чтобы кэширование в принципе было возможно, каждый узел графа сборки явно объявляет свои входные и выходные
данные.

Чтобы кэширование было корректным, каждый узел графа выполняется в отдельной песочнице. То есть, если узлу нужно что‑то,
что он не объявил как входные данные, то на этапе выполнения этих данных не будет. Справедливо и обратное: если шаг
сборки породил данные, которые не были объявлены как выходные, то остальные шаги не увидят этот паразитный вывод.

В терминах Bazel такое выполнение узлов сборки называют «герметичным».

Так как для каждого шага сборки все входные и выходные данные объявлены, у Bazel есть возможность исполнять эти шаги на
ферме.

Герметичность не является полной: системные утилиты и библиотеки не учитываются. Это может вызывать проблемы, к примеру,
после локального обновления C++ компилятора.

## Порядок сборки Bazel

При сборке Bazel-у передаётся список собираемых целей. Каждая цель объявлена в своём `BUILD`-файле.

Bazel идёт по зависимостям из BUILD-файлов и строит граф сборки.

Правила из BUILD-файлов выглядят примерно следующим образом:
{{< code file="bazel-why-migrate/BUILD.example" language="python" >}}

При этом следует отметить ряд важных моментов:

- **узлом графа** сборки является шаг, который получает файлы на вход и порождает файлы;
- **ребрами графа** является передача файла из одного шага в другой;
- **одно правило** в `BUILD`-файле может порождать несколько узлов графа или не порождать ни одного вовсе;
- у правила есть **неявный аргумент «конфигурация»**, и правила с разной конфигурацией обрабатываются отдельно.
  Например, если есть правило `go_library`, которое явно или транзитивно используется внутри правил `go_binary` с 
  разными тэгами, то оно будет обработано несколько раз и породит разные узлы графа.

Построение графа сборки у Bazel выделено в отдельный этап `Analyze`.

После построения графа он начинает исполняться. Причем те узлы, которые не нужны для формирования запрошенного вывода,
не участвуют в процессе сборки.

Этот подход имеет ряд интересных следствий:

- **на момент построения графа никаких реальных команд не выполняется**, как следствие в объявлении правила на Starlark
  нет конструкции «прочитать файл», хотя «записать файл» можно;
- **для выполнения операции должны быть готовы все входные данные**, из-за этого, например, проблематично построить
  конструкцию вида «не выполняй шаг заливки Docker-образа, если образ уже залит» без загрузки всего образа на сборочный
  узел из кэша.

# Итого

В итоге, мы решили посмотреть в сторону Bazel для того, чтобы:

- **уменьшить время ожидания сборки на CI** для разработчиков за счет общего кэша сборки и запуска тестов на сборочной
  ферме;
- **заменить все костыли**, которые мы успели нагородить, для ускорения сборки, на более зрелое решение.

При этом у нас не было никаких иллюзий на тему «простого переезда» . Мы ожидали проблем из-за разного подхода к сборке,
как минимум, с:

- генерацией кода;
- Go-тэгами;
- CGO-сервисами;
- go vet;
- запуском тестов на ферме (тестам требуется определённое окружение).

Особенно сильно напрягало, что у нас на тот момент не было людей, которые активно работали с Bazel-ом. Понимания того,
как это должно выглядеть в итоге, тоже не было, но об этом в следующем посте.