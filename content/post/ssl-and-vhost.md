---
date: 2009-12-06
title: SSL и VHost
slug: ssl-and-vhost
tags:
 - ssl
categories:
 - Web
menu: main
---

Тема старая, но почему-то раньше у меня руки до неё не доходили.

Суть проблемы в следующем: если создается SSL-сервер с самоподписанным сертификатом, то у него в CN может быть указан только один хост. В результате, если обращаться к HTTPS-серверу по другому доменному имени, получаем предупреждение не только о том, что сертификат самопальный, но и о том, что сертификат выдан другому сайту. А это как-то некузяво.
<!--more-->
Для генерации сертификата для нескольких доменных имен можно пойти следующим путем:

 1. Создаем приватный ключ, которым будем подписывать сертификат:

    ```
    openssl genrsa -out server.key 1024
    ```
 1. Подготавливаем файл с параметрами сертификата (я назвал его server.cfg):

    ```
    [req]
    # Задаем имя секции с базовыми параметрами сертификата
    distinguished_name = req_distinguished_name
    # Параметры перечислены, так что спрашивать их нет смысла
    prompt = no
    # Имя секции с расширениями для запроса сертификата
    req_extensions = req_v3
    # Имя секции с расширениями для подписи сертификата
    x509_extensions = req_v3

    [req_v3]
    # Все альтернативные имена перечислены в секции alt_name
    subjectAltName=@alt_name

    [alt_name]
    # Альтернативные имена
    DNS.1 = www.example1.ru
    DNS.2 = www.example2.ru
    DNS.3 = www.example1.com

    [req_distinguished_name]
    # Имя сайта, на который выдан сертификат
    CN=www.example1.ru
    # Штат
    ST=Moscow-State
    # Отдел
    OU=Software Development
    # Организация
    O=Example, LLC
    # Город
    L=Moscow City
    # Страна
    C=RU
    ```
 1. Генерируем запрос сертификата:

    ```
    openssl req -new -utf8 -key server.key -config server.cfg -out server.csr
    ```
 1. Подписываем сертификат:

    ```
    openssl x509 -req -days 365 -in server.csr -extfile server.cfg -extensions req_v3 -signkey server.key -out server.crt
    ```
    При этом важно задать параметр extfile и extensions, без них в сертификате альтернативные имена эффекта не возымеют.
 1. Посмотреть сертификат можно командой:

    ```
    openssl x509 -text -in server.crt
    В случае успеха в нем должны присутствовать строки вида:
    X509v3 extensions:
      X509v3 Subject Alternative Name:
        DNS:www.example1.ru, DNS:www.example2.ru, DNS:www.example1.com
    ```

Ссылки по теме:

 * http://openssl.org/docs/apps/req.html
 * http://wiki.cacert.org/VhostTaskForce