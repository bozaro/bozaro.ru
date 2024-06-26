---
date: 2024-03-11
title: "Bazel, stamping, remote cache (часть 2)"
slug: bazel-stamping-remote-cache-2
tags:
  - golang
  - bazel
  - joom
  - stamping
categories:
  - Bazel
menu: main
---

<img alt="Картинка для привлечения внимания :)" class="right" style="max-width: 50%;" src="../../../../img/bazel-stamping-remote-cache-2/to-the-future.jpg">
В Bazel есть две крайне полезные фичи:

- stamping &mdash; позволяет встроить в артефакт данные о том, от какого коммита можно собрать аналогичный артефакт;
- remote cache и remote build &mdasg; позволяет иметь общий кэш между сборщиками или даже собрать артефакты на ферме.

Ранее, к сожалению, эти фичи были взаимоисключающими, но с версии Bazel 7.0 можно использовать stamping с remote cache
при помощи scrubbing-а. Сегодня вышла версия Bazel 7.1, в которой появилась возможность использовать `stamping`
с `remote build`.
<!--more-->

Подробнее об этой проблеме я писал ранее в статье
[Bazel, stamping, remote cache]({{< ref "bazel-stamping-remote-cache.md" >}}).

# Что такое stamping?

Stamping позволяет добавить в артефакт информацию о том, от какой версии можно собрать аналогичный артефакт.

Не ту версию, для которой была запущена сборка, а ту, от которой можно получить аналог.

К примеру, есть два коммита, которые отличаются только README-файлом. Тогда собранный из этих коммитов исполняемый файл
может содержать один и тот же коммит в качестве информации о том, из какой ревизии можно его собрать, так как изменения
между этими ревизиями никак на него не влияют.

Это позволяет с одной стороны иметь информацию о том, от какой ревизии можно собрать эквивалентный артефакт, а с другой
стороны не пересобирать его на каждый коммит.

# Как работает stamping?

Внутри stamping реализован просто: файлы, передаваемые для встраивания версии в артефакт исключаются (в случае Bazel:
`bazel-out/volatile-status.txt`) из ключа кэширования.

Таким образом, пересборка артефакта происходит только в том случае, если поменялось хотя бы что-то из входных
параметров, кроме файла с данными для версии.

# В чем проблема с remote cache?

В Bazel есть несколько кэшей. Внутренний кэш Bazel и удалённый кэш имеют разные ключи кэширования. Bazel для disk
cache/remote cache/remote build используют один и тот же ключ кэш (disk cache это частный случай remote cache).

Проблема в том, что ключом кэширования action для сборки на ферме или remote cache является хэш от задачи для сборки. На
этот хэш влияют все входные данные и семантика файлов для stamping-а не распространяется. То есть файлы для stamping-а
влияют на хэш задачи для сборки.

Таким образом, мы получаем ситуацию, когда любая сборка всегда получает уникальный файл с данными информации для версии
и никогда не попадает в кэш.

Самое неприятное, что даже отметка правила со stamping-ом для локальной сборки через тэги не исправляет ситуацию – мы
будем получать одинаковый артефакт, только если попадём в кэш с предыдущей сборкой на том же сборщике.

# Что такое scrubbing?

В Bazel 7.0 появился scrubbing. Он позволяет влиять на ключ кэширования для remote cache.

К примеру:

- добавлять соль при хэшировании;
- подменять аргументы сборки;
- исключать входные файлы из ключа кэширования.

В случае stamping-а можно исключить из ключа кэширования файл `bazel-out/volatile-status.txt` и мы получим при
использовании remote cache то же поведение, что и при локальной сборке.

Помимо этого scrubbing позволяет решить проблему, когда нужно использовать какое-то производное от
`bazel-out/volatile-status.txt` для встраивания данных о версии.

# Пример использования scrubbing

Для использования scrubbing нужно создать файл с конфигурацией scrubbing-а, например:

```
rules {
  matcher {
    kind: "stamping"
    mnemonic: "Example"
  }
  transform {
    omitted_inputs: "^bazel-out/volatile-status\\.txt$"
  }
}
```

Список допустимых полей можно подсмотреть
здесь: https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/remote_scrubbing.proto

На сборочное действие применяется трансформация последнего правила, которое подходит под заявленные критерии.

Для того чтобы конфигурация scrubbing-а использовалась при сборке, её надо передать параметром
`--experimental_remote_scrubbing_config`.

# В чем проблема scrubbing и remote cache?

В Bazel 7.0 при попытке использовать параметр `--experimental_remote_scrubbing_config` с удалённой сборкой, мы получим
ошибку: `Cannot combine remote cache key scrubbing with remote execution`

К счастью, в Bazel 7.1 поведение изменилось (https://github.com/bazelbuild/bazel/pull/21384): вместо глобальной ошибки
выполнение действий, которые подвергаются scrubbing-у, происходит на локальном хосте.

Это позволяет использовать stamping и сборку на ферме, но надо очень аккуратно подбирать `matcher`-ы для правил:

- нужно, чтобы под них попадало всё, что использует stamping, так как иначе будет постоянный промах мимо кэша (вне
  зависимости от того, меняет ли данная трансформация значение ключа кэширования);
- нужно, чтобы под них не попадало лишнее, так как оно перестанет собираться на ферме и будет собираться локально (но
  при этом будет использоваться удаленный кэш).

# Подведем итог

С версии Bazel 7.1 наконец-то появилась возможность использовать stamping и удалённую сборку, хотя и не без проблем.

Я надеюсь, что через какое-то время интерфейс трансформации для scrubbing-а будет зафиксирован и его поддержка появится
в протоколе для удалённой сборки. Это должно будет снять ограничения на локальное выполнение и позволит выполнять на
ферме все задачи для сборки.
