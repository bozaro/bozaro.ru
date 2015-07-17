---
date: 2015-07-18
title: Багло негаданно найдется, там где его совсем не ждешь
slug: svnkit-guid
tags:
 - svnkit
 - bug
categories:
 - Development
menu: main
---

Иногда натыкаешься на программные ошибки, в местах где их меньше всего ожидаешь увидеть: в простом коде, который не менялся вот уже много лет и активно используется в разных частях программы.

Исправление таких "невозможных" ошибок обычно возможно только в случае особого стечения обстоятельств.

После обнаружения этой ошибки эмоции меня переполняли около суток.
<!--more-->

## Описание мигающего теста
А началось все с того, что у меня в проекте https://github.com/bozaro/git-as-svn мигал тест.

Этот тест относился к числу тех тестов, которые проверяли, что моя реализация Subversion-сервера совпадает по поведению с эталонной. В качестве эталонов использовались родной svnserve и SvnKit.

Данные тесты выполнялись по три раза:

 * с родным svnserve;
 * с SvnKit;
 * с Git as Svn.

При этом суть теста предельна проста:

 # создается тестовый репозиторий;
 # берется svn lock на файл (блокировка_1);
 # снимается с файла блокировка_1;
 # берется svn lock на файл (блокировка_2);
 # снимается с файла блокировка_1 - тут ожидается ошибка о попытке снять уже несуществующую блокировку.

Мигала реализация с SvnKit: иногда удавалось снять ранее снятую блокировку без ошибок.

## Ловля ошибки
Обычно мигание теста связано с состоянием гонки и ищется достаточно просто:

 * ставится breakpoint на место, где можно определить некорректное поведение;
 * тест запускается в цикле;
 * как только остановились на breakpoint-е, пытаемся выяснить, что пошло не так.

Я знал об этой ошибке, так как она регулярно появляла себя на Travis-е, но не исправил её, так как она локально у меня не воспроизводилась.

В этот день она первый раз проявила себя на локальной машине и я начал охоту за ней.

В результате выяснилось: внезапно, обе блокировки иногда имеют одинаковый идентификатор.

Я начал смотреть, как этот идентификатор формируется и узрел простой вызов метода ```SVNUUIDGenerator.generateUUID()```. То есть, получается, что два раза генерируется одинаковый GUID.

Далее я начал методом пристального взгляда изучать код генерации GUID-ов.

Суть проблемы оказалась следующая:

 * GUID получается из 2-х частей:
   * идентификатора запуска приложения (для нас - константа);
   * текущего времени, которое получается через ```SVNUUIDGenerator.getCurrentTime()```.
 * Метод ```SVNUUIDGenerator.getCurrentTime()``` должен всегда возвращать уникальное в рамках процесса значение не меньше текущего времени.
 * Для обеспечения уникальности значения было две переменных: 
   * ```ourLastGeneratedTime``` - время последнего вызова;
   * ```ourFudgeFactor``` - сдвиг значения.

Сам метод:
```
    private static long getCurrentTime() {
        long currentTime = System.currentTimeMillis();
        /* if clock reading changed since last UUID generated... */
        if (ourLastGeneratedTime != currentTime) {
            /*
             * The clock reading has changed since the last UUID was generated.
             * Reset the fudge factor. if we are generating them too fast, then
             * the fudge may need to be reset to something greater than zero.
             */
            if (ourLastGeneratedTime + ourFudgeFactor > currentTime) { // <== BUG HERE
                ourFudgeFactor = ourLastGeneratedTime + ourFudgeFactor - currentTime + 1;
            } else {
                ourFudgeFactor = 0;
            }
            ourLastGeneratedTime = currentTime;
        } else {
            /* We generated two really fast. Bump the fudge factor. */
            ++ourFudgeFactor;
        }
        return currentTime + ourFudgeFactor;
    }
```

Исправление при этом выглядит очень просто:
```
diff --git a/svnkit/src/main/java/org/tmatesoft/svn/core/internal/util/SVNUUIDGenerator.java b/svnkit/src/main/java/org/tmatesoft/svn/core/internal/util/SVNUUIDGenerator.java
index ac13a02..228ff74 100644
--- a/svnkit/src/main/java/org/tmatesoft/svn/core/internal/util/SVNUUIDGenerator.java
+++ b/svnkit/src/main/java/org/tmatesoft/svn/core/internal/util/SVNUUIDGenerator.java
@@ -48,7 +48,7 @@ public class SVNUUIDGenerator {
              * Reset the fudge factor. if we are generating them too fast, then
              * the fudge may need to be reset to something greater than zero.
              */
-            if (ourLastGeneratedTime + ourFudgeFactor > currentTime) {
+            if (ourLastGeneratedTime + ourFudgeFactor >= currentTime) {
                 ourFudgeFactor = ourLastGeneratedTime + ourFudgeFactor - currentTime + 1;
             } else {
                 ourFudgeFactor = 0;
```

## Последовательность событий, при которой воспроизводится проблема

Из-за ошибки знака, ошибка воспроизводилась примерно в следующей ситуации:
 
**Первая генерация:**

До вызова:
```
System.currentTimeMillis() == 42;
ourLastGeneratedTime = 0;
ourFudgeFactor = 0;
```
После вызова:
```
ourLastGeneratedTime = 42;
ourFudgeFactor = 0;
```
Результат: 42

**Вторая генерация**

До вызова:
```
System.currentTimeMillis() == 42;
ourLastGeneratedTime = 42;
ourFudgeFactor = 0;
```
После вызова:
```
ourLastGeneratedTime = 42;
ourFudgeFactor = 1;
```
Результат: 43

**Третья генерация**
До вызова:
```
System.currentTimeMillis() == 43;
ourLastGeneratedTime = 42;
ourFudgeFactor = 1;
```
После вызова:
```
ourLastGeneratedTime = 43;
ourFudgeFactor = 0;
```
Результат: 43, но это значение уже было!

## Итог

По результатам раскопок был заведен баг: https://issues.tmatesoft.com/issue/SVNKIT-608

Исправление попадает в SvnKit начиная с версии 1.8.11.