---
date: 2022-08-08
draft: true
title: Jenkinsfile это не Groovy
slug: jenkinsfail-groovy
tags:
 - jenkins
categories:
 - CI
menu: main
---

## `Jenkinsfile` это не Groovy

Сразу стоит отметить, что я не нашел в документации к Jenkins утверждения, что `Jenkinsfile` пишется на Groovy.

В [документации к Jenkins](https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#advanced-scripted-pipeline) написано:
> Scripted Pipeline is a domain-specific language [3] based on Groovy, most Groovy syntax can be used in Scripted
> Pipeline without modification.

Но количество отсылок к Groovy столь велико, что у многих людей создаются ложные ожидания.

Я решил написать этот пост, после многократного объяснения коллегам отличий скрипта `Jenkisnfile` от Groovy.

Так же важно отметить, что всё примеры проверялись на версии 2.361.1 (самый свежий LTS на момент написания статьи) и
возможно ситуация изменится.

## А что собственно не так?

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

Причем это касается не только самого `Jenkinsfile`, но и кода
в [Jenkins Shared Libraries](https://www.jenkins.io/doc/book/pipeline/shared-libraries/).

## Как им удалось этого добиться?

Причина изменения поведения
кода: [Continuation Passing Style (CPS)](https://en.wikipedia.org/wiki/Continuation-passing_style) преобразование.

Jenkins преобразовывает уже скомпилированный в байт-код скрипт к виду, когда может выполнять его по шагам сохраняя
внутренне состояние отдельно. На этапе этого преобразования некоторые конструкции меняют своё поведение.

## Как жить?

Лучше всего избегать сложной логики в `Jenkinsfile`, но это не всегда возможно.

К счастью, есть проект [JenkinsPipelineUnit](https://github.com/jenkinsci/JenkinsPipelineUnit#note-on-cps), который
позволяет из Unit-тестов на настоящем Groovy выполнять код после CPS-преобразования.

Этот проект позволяет писать тесты на код, выполняемый в скриптах Jenkins, но я так и не смог, найти красивое решение по
организации тестируемого кода в `Jenkinfile`.

Общий механизм написания тестируемого кода у меня получился примерно следующий:

- весь тестируемый код оформляется
  в [Jenkins Shared Libraries](https://www.jenkins.io/doc/book/pipeline/shared-libraries/)
- на тестируемый код пишутся тесты с
  помощью [JenkinsPipelineUnit](https://github.com/jenkinsci/JenkinsPipelineUnit#note-on-cps)
- для использования этого кода из того же репозитория использую
  метод [library](https://www.jenkins.io/doc/pipeline/steps/workflow-cps-global-lib/#library-load-a-shared-library-on-the-fly)

Об использовании Jenkins Shared Libraries в том же репозитории много написано на
StackOverflow: https://stackoverflow.com/questions/46213913/load-jenkins-pipeline-shared-library-from-same-repository

Суть проблемы в том, что через `@Library` нельзя сослаться на тот же коммит того же репозитория.

В результате приходится загружать библиотеку динамически кодом вида:

```groovy
def lib = library(identifier: "local@latest", retriever: legacySCM(scm)).com.mycorp.pipeline
lib.Utils.someStaticMethod()
```

Если собрать всё это вместе, то оно работает, но результат выглядит так себе:

- в `Jenkinsfile` можно обращаться к статическим методам, но нельзя сослаться на типы;
- код Jenkins Shared Libraries лежит вперемешку с основным кодом репозитория.
