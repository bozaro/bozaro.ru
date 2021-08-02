---
date: 2021-08-01
title: Сборка Docker-образов для MacBook M1 под Linux
slug: docker-buildx-build
tags:
- docker
- ci
categories:
- Docker
menu: main
draft: true
---

Мы собираем зависимости для нашего тестового окружения в Docker-образ, что оказалось очень удобно. Но недавно у нас
появился разработчик с MacBook M1 и резко встал вопрос о возможности поддержки двух платформ.
<!--more-->

## Особенности поведения Docker на MacBook M1

Для начала пару слов о том, как повёл себя MacBook M1: в самом M1 предусмотрена неплохая поддержка программ, собранных
для Intel процессоров (Rosetta 2). То есть большинство программ, которые собраны для Intel процессоров запускаются на
нём без проблем.

В Docker подобное поведение так же реализовано, но несколько другим образом: Docker использует виртуальную машину для
запуска образов (как минимум по тому, что им нужно ядро Linux). Но в этой виртуальной машине есть поддержка исполнения
бинарных файлов для архитектуры `x86_64`.

В случае с MacBook M1 родной архитектурой для него будет являться `aarch64`:

```sh
$ docker run --rm alpine arch
aarch64
```

## Сборка образа для другой архитектуры

Docker-образы мы собираем под Linux.

К счастью под Linux можно собрать Docker-образ для другой архитектуры без особых проблем.

Для примера возьмём простой Dockerfile:

```Dockerfile
FROM alpine
RUN arch
```

Чтобы его собрать для M1 проще всего воспользоваться
BuildKit (https://docs.docker.com/develop/develop-images/build_enhancements/).

Для этого нужно выполнить команду вида:

```sh
DOCKER_BUILDKIT=1 docker build --progress=plain --platform=linux/arm64 .
...
#5 [2/2] RUN arch
#5 sha256:2bafefaa8ba4bf5ad20a6021513fbda85e9477b6e19bef84aa439c448f142237
#5 0.464 aarch64
#5 DONE 0.5s
...
```

Но скорее всего результат будет другим:

```sh
DOCKER_BUILDKIT=1 docker build --progress=plain --platform=linux/arm64 .
...
#5 [2/2] RUN arch
#5 sha256:f50bb518130ae7f87d8db06ecc362ef97445488cfcafcdc7ec0a66765a28b685
#5 0.336 standard_init_linux.go:228: exec user process caused: exec format error
#5 ERROR: executor failed running [/bin/sh -c arch]: exit code: 1
------
 > [2/2] RUN arch:
------
executor failed running [/bin/sh -c arch]: exit code: 1
```

Для того чтобы собрать образы под другую платформу, нужно поставить эмулятор для этой платформы.

### Установка эмулятора (быстрый метод)

Для установки эмулятора можно воспользоваться проектом https://github.com/multiarch/qemu-user-static:

```sh
docker run --rm --privileged multiarch/qemu-user-static:register --reset
```

Этот Docker-образ скопирует в систему `qemu-user-static` и зарегистрирует его для исполнения бинарных файлов
соответствующей платформы.

После этого, кстати, можно будет запускать статически слинкованные исполняемые файлы от другой платформы
(подобные файлы по умолчанию создаёт компилятор Go).

К сожалению, эффект от этой команды будет действовать до первой перезагрузки.

### Установка эмулятора (ручной метод)

Если мы по каким-то причинам не хотим воспользоваться первым методом, то можно сделать всё это вручную.

#### Установка qemu-user-static

Нужно установить `qemu-user-static` для вашего дистрибутива, например:

```sh
sudo apt-get install -y qemu-user-static
```

Если в вашем дистрибутиве используется `qemu-user-static` очень старой версии, то можно скачать пакет руками от
дистрибутива более свежей версии. У `qemu-user-static` нет внешних зависимостей и, к примеру пакет от Ubuntu 21.04 (qemu
version 5.2) хорошо встаёт на Ubuntu 18.04 (qemu version 2.11).

#### Зарегистрировать qemu-user-static в binfmt

Теоретически установки `qemu-user-static` должно быть достаточно. Но на некоторых дистрибутивах она не прописывается
в `binfmt` (https://www.kernel.org/doc/html/latest/admin-guide/binfmt-misc.html).

Проверить работоспособность можно командой:

```sh
echo -e "FROM aarch64/debian:stretch-slim\nRUN echo 'it works'" | docker build -
```

Я исправлял эту ситуацию по инструкции с сайта https://github.com/computermouth/qemu-static-conf#how-do-i-install:

```sh
git clone https://github.com/computermouth/qemu-static-conf.git
sudo mkdir -p /etc/binfmt.d
sudo cp qemu-static-conf/*.conf /etc/binfmt.d/
sudo systemctl restart systemd-binfmt.service
```

## Сборка образов по-отдельности

После того как мы научились собирать образ для другой платформы, надо научиться собирать образ для двух платформ
одновременно.

Это можно сделать несколькими способами.

Для начала рассмотрим сборку образа для нескольких платформ вручную.

```sh
local IMAGE=docker.example.com/example
local TAG=latest

# Собираем образ example_amd64 для amd64
DOCKER_BUILDKIT=1 docker build --progress=plain --platform=linux/amd64 --tag ${IMAGE}-amd64:${TAG} .

# Собираем образ example_arm64 для arm64
DOCKER_BUILDKIT=1 docker build --progress=plain --platform=linux/arm64 --tag ${IMAGE}-arm64:${TAG} .

# Заливаем образы в Docker registry
docker push ${IMAGE}-amd64:${TAG}
docker push ${IMAGE}-arm64:${TAG}

# Создаём manifest list, содержащий образы под несколько платформ.
docker manifest create ${IMAGE}:${TAG} ${IMAGE}-amd64:${TAG} ${IMAGE}-arm64:${TAG}

# Заливаем manifest list в Docker registry
docker manifest push ${IMAGE}:${TAG}
```

Проверить, что образ собрался успешно, можно командой вида:

```sh
local IMAGE=docker.example.com/example
local TAG=latest

docker run --rm --platform linux/arm64 ${IMAGE}:${TAG} arch
# aarch64

docker run --rm --platform linux/amd64 ${IMAGE}:${TAG} arch
# x86_64
```

## Сборка при помощи docker buildx

С недавнего времени в Docker появилась возможность собрать образ под несколько платформ одной
командой: https://docs.docker.com/buildx/working-with-buildx/

```sh
local IMAGE=docker.example.com/example
local TAG=latest

docker buildx create --name cibuilder --driver docker-container --use
docker buildx inspect --bootstrap
docker buildx build --push --progress=plain --platform linux/amd64 --platform linux/arm64 --tag ${IMAGE}:${TAG} .
```

Что здесь происходит:

1. `docker buildx create` создаёт в `DOCKER_CONFIG` (по-умолчанию `~/.docker`) описание сборщика. Флаг `--use` помечает
   этот сборщик используемым по-умолчанию (без этого его имя надо было бы протаскивать в последующие команды). Кроме
   конфигурационных файлов текущего пользователя эта команда не меняет и не использует ничего.
2. `buildx inspect --bootstrap` выводит информации о сборщике. Если он не запущен, то запускает его. Сам сборщик
   представляет собой Docker-контейнер.
3. `docker buildx build` собственно собирает образ.

### Особенности поведения на CI

При сборке на CI возникают следующие проблемы:

- `docker buildx create` при создании контейнера по-умолчанию прописывает в конфигурацию образ с DockerHub;
- `docker buildx inspect --bootstrap` создаёт контейнер со сборщиком и подвержен гонкам;
- единожды созданный сборщик используется между несколькими сборками.

Для решения этих проблем мы перенесли запуск сборщика на этап старта сборочного агента.

Таким образом при запуске агента мы выполняем команды вида:

```sh
export DOCKER_CONFIG="$(mktemp -d)"
docker buildx create --name cibuilder --driver docker-container --driver-opt image=dockerhub-proxy.example.com/moby/buildkit:buildx-stable-1
docker buildx inspect cibuilder --bootstrap
rm -fR "$DOCKER_CONFIG"
export -n DOCKER_CONFIG
```

Это запускает сборщик образов на старте агента с нужными нам параметрами.

При старте задачи на сборку мы выполняем команды вида (`DOCKER_CONFIG` переопределяется на каждую сборку):

```sh
local IMAGE=docker.example.com/example
local TAG=latest

docker buildx create --name cibuilder --driver docker-container --use
docker buildx build --push --progress=plain --platform linux/amd64 --platform linux/arm64 --tag ${IMAGE}:${TAG} .
```

### Кэширование сборки образов

В качестве бонуса при использовании BuildKit мы получаем возможность использовать внешний кэш для Docker-образов:

```sh
local IMAGE=docker.example.com/example
local TAG=feature-42

docker buildx build \
  --cache-from type=registry,ref=${IMAGE}:latest_cachebuild \
  --cache-from type=registry,ref=${IMAGE}:${TAG}_cachebuild \
  --cache-to type=registry,ref=${IMAGE}:${TAG}_cachebuild,mode=max \
  --push \
  ...
```

Особенность такого кэширования: отличие от кэша на базе предыдущего Docker-образа, хорошо работает с Dockerfile в
которых используется несколько FROM директив.

Например:

{{< code file="docker-buildx/Dockerfile" language="Dockerfile" label="Dockerfile" >}}
