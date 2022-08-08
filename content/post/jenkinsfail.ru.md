---
date: 2022-08-08
draft: true
title: Два распространённых заблуждения о Jenkinsfile
slug: jenkinsfail
tags:
 - jenkins
categories:
 - CI
menu: main
---
## Заблуждение о том, что `Jenkinsfile` пишется на Groovy

> Если оно выглядит как утка, плавает как утка и крякает как утка, то это, вероятно, и есть утка.

Несмотря на то, что код `Jenkinsfile` компилируется при помощи Groovy-компилятора, в дальнейшем он подвергается
дополнительной обработке и перестаёт вести себя как Groovy-код.

То есть он выглядит как Groovy, компилируется как Groovy, но не ведёт себя как Groovy.

И речь не о том, что он выполняется в песочнице и часть библиотек не доступна. Всё гораздо хуже: некоторые базовые
конструкции тихо меняют своё поведение.

### Отличие поведения циклов

Пример проблемного `Jenkinsfile` (можно так же выполнить в https://groovyide.com/playground):

```groovy
def messages = []
messages += "Begin"
for (; ;) {
    messages += "Inside classic loop"
    break
}
messages += "End"

// Show result with little hack to use same code in groovy and Jenkinsfile
def echo = "echo" in this ? echo : { it -> println(it) }
echo(messages.join('\n'))
```

Вывод в https://groovyide.com/playground:

```text
Begin
Inside classic loop
End
```

Вывод в Jenkins:

```text
[Pipeline] Start of Pipeline
[Pipeline] echo
Begin
End
[Pipeline] End of Pipeline
```

Нарушенная спецификация:

- https://groovy-lang.org/semantics.html#_classic_for_loop
- https://docs.oracle.com/javase/specs/jls/se8/html/jls-14.html#jls-14.14-110
- https://docs.oracle.com/javase/tutorial/java/nutsandbolts/for.html

### Странное поведение вызова методов

Пример проблемного `Jenkinsfile` (можно так же выполнить в https://groovyide.com/playground):

```groovy
def messages = []
messages += "Begin"
// List 1
if ([]) {
    messages += "List 1 is not empty (WTF)"
} else {
    messages += "List 1 is empty (OK)"
}
// List 2
if (["a"]) {
    messages += "List 2 is not empty (OK)"
} else {
    messages += "List 2 is empty (WTF)"
}
// List 3
if ([].isEmpty()) {
    messages += "List 3 is empty (OK)"
} else {
    messages += "List 3 is not empty (WTF)"
}
// List 4
if (["a"].isEmpty()) {
    messages += "List 4 is empty (WTF)"
} else {
    messages += "List 4 is not empty (OK)"
}
// List 5
if ([].empty) {
    messages += "List 5 is empty (OK)"
} else {
    messages += "List 5 is not empty (WTF)"
}
// List 6
if (["a"].empty) {
    messages += "List 6 is empty (WTF)"
} else {
    messages += "List 6 is not empty (OK)"
}
messages += "End"

// Show result with little hack to use same code in groovy and Jenkinsfile
def echo = "echo" in this ? echo : { it -> println(it) }
echo(messages.join('\n'))
```

Вывод в https://groovyide.com/playground:

```text
Begin
List 1 is empty (OK)
List 2 is not empty (OK)
List 3 is empty (OK)
List 4 is not empty (OK)
List 5 is empty (OK)
List 6 is not empty (OK)
End
```

Вывод в Jenkins 2.346.2:

```text
[Pipeline] Start of Pipeline
[Pipeline] echo
Begin
List 1 is empty (OK)
List 2 is not empty (OK)
List 3 is empty (OK)
List 4 is not empty (OK)
List 5 is not empty (WTF)
List 6 is empty (WTF)
End
[Pipeline] End of Pipeline
```

Нарушенная спецификация:

https://groovy-lang.org/objectorientation.html#_property_naming_conventions

### Пара слов о данных примерах

После данных примеров, особо хотел бы отметить:

- Это далеко не исчерпывающий список проблем. В реальности всё гораздо хуже, просто эти два примера очень легко
  воспроизвести.
- Код в случае подобных проблем меняет своё поведение тихо, а не выплёвывает ошибку. Это добавляет отдельной остроты в
  поиске проблем.
- Очень тяжело писать код, когда ни в какой строке нельзя быть уверенным.

## Заблуждение о том, что в Jenkinsfile есть декларативный Pipeline

Как это ни странно звучит, в Jenkinsfile всегда выполняется императивный Pipeline. Просто в нём может быть
верхнеуровневый блок на декларативном синтаксисе.

Например:

```groovy
// Scripted pipeline
def time = System.currentTimeMillis()
if (time % 2 == 0) {
    stage("Even") {
        echo "Hello World"
    }
} else {
    stage("Odd") {
        echo "Hello World"
    }
}

// Declarative syntax
pipeline {
    agent any

    stages {
        stage("Bye") {
            steps {
                echo "See you"
            }
        }
    }
}

// Scripted pipeline (again)
stage("End") {
    echo "Time: ${time}"
}
```

То есть, синтаксис для декларативного Pipeline есть, но сам `Jenkinsfile` остаётся императивным.

Это нивелирует один из основных плюсов, которые имеет декларативный синтаксис: можно понять что этот код делает (какие
будут выполнены этапы, какие объявлены параметры и т.п.) без фактического выполнения кода.

Как следствие, в Jenkins для получения списка Stage-ей и параметров сборки нужно выполнить Pipeline. Получить параметры
для выполнения Pipeline до его выполнения принципиально нельзя.

Для обхода данной проблемы Jenkins берёт параметры для выполнения Pipeline от предыдущего запуска данной Job-ы.
