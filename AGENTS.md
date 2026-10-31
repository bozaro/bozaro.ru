# AGENTS.md

Личный блог bozaro.ru на [Hugo](https://gohugo.io/) (тема `hugo-geo`).

## Сборка и запуск

- Hugo **не установлен** в системе — используется wrapper `./hugo.sh`, который сам скачивает
  pinned-версию (0.82.1, tarball лежит в git LFS в `.jenkins/distrib/`) в `.build/`.
- Локальная сборка сайта: `./build.sh` (прогон с draft'ами + финальный прогон + gzip статики),
  результат в `public/`.
- Локальный dev-сервер: `./start.sh` (http://localhost/, с draft'ами и watch).
- Не обновляй версию Hugo без необходимости — тема и шаблоны завязаны на старую версию
  (есть deprecation warnings, но они не ломают сборку).

## Структура

- `content/post/` — посты, front matter в YAML. Файлы вида `*.ru.md` / `*.en.md`
  (два языка: ru → https://bozaro.ru/, en → https://bozaro.me/, см. `config.yaml`).
  Основное поле — `slug`; permalink: `/:year/:month/:day/:slug/`.
- `layouts/shortcodes/` — кастомные шорткоды:
  - `{{< code file="..." language="..." label="..." >}}` — вставляет файл из `static/` как
    подсвеченный код (через `readFile`, путь относительно корня репозитория);
  - `{{< img src="..." alt="..." width="..." >}}` — картинка.
- `themes/hugo-geo` и `static/go-stack-trace` — **git submodules**; после клонирования нужен
  `git submodule update --init --recursive`.
- `.jenkins/distrib/hugo_*.tar.gz` — в **git LFS**.
- `public/`, `.build/`, `.idea/` — в git не попадают (см. `.gitignore`).

## CI

- Основная сборка — **Drone CI** (`.drone.yml`): собирает docker-образ из `.jenkins/Dockerfile`
  и пушит в `docker.bozaro.ru/ci/${DRONE_REPO}`, затем build (`git submodule update --init
  --recursive`, `git lfs pull`, `./build.sh`), затем на ветке `master` — publish через
  `rsync` на `deploy@ivy.bozaro.ru:bozaro.ru/` (SSH-ключ из секрета `web_deploy_key`).
- Drone **не инициализирует submodules и LFS сам** — команды явно прописаны в build-шаге,
  не убирай их.
- `Jenkinsfile` — легаси-сборка, оставлена как fallback; если меняешь `.jenkins/Dockerfile`,
  она продолжит работать (Jenkinsfile указывает на `.jenkins`).

## Git workflow

- Делай коммит после завершения каждой осмысленной задачи.
- Push в рабочую ветку разрешён; **push в `master` — только по явному указанию пользователя**.

## Проверка изменений

После правок шаблонов/контента прогони `./build.sh` — сборка должна завершиться без ошибок
(hugo печатает таблицу Pages/Static files). Ошибки шорткодов и шаблонов видны только на сборке.
