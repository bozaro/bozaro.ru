---
date: 2019-07-21
title: Логирование в Jenkins
slug: jenkins-logging
tags:
 - jenkins
categories:
 - CI
menu: main
---

В Jenkins очень забавно сделано логирование: через WEB UI можно добавить логирование нужных логгеров в кольцевой буффер.

Но для логирования в файл нужно немного поплясать с бубном.

<!--more-->
Если загуглить, что можно найти страницу https://wiki.jenkins.io/display/JENKINS/Logging, но пример с неё не очень
удачный: там нет логирования времени события.

После некоторого копания я пришел к следующему файлу `init.groovy.d/extralogging.groovy`:

```
import jenkins.model.Jenkins

import java.util.logging.FileHandler
import java.util.logging.LogManager
import java.util.logging.LogRecord
import java.util.logging.SimpleFormatter

// Log into a file
def RunLogger = LogManager.getLogManager().getLogger("org.kohsuke.github")
def logsDir = new File(Jenkins.instance.rootDir, "logs")
if (!logsDir.exists()) {
    logsDir.mkdirs()
}
FileHandler handler = new FileHandler(logsDir.absolutePath + "/org.kohsuke.github-%g.log", 100 * 1024 * 1024, 10, true)
handler.setFormatter(new SimpleFormatter() {
    private static final String format = '[%1$tF %1$tT] [%2$-7s] %3$s %n'

    @Override
    synchronized String format(LogRecord lr) {
        return String.format(format,
                new Date(lr.getMillis()),
                lr.getLevel().getLocalizedName(),
                formatMessage(lr)
        );
    }
})
RunLogger.addHandler(handler)
```
