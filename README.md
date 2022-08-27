![ci](https://github.com/v-v-d/billing/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/v-v-d/billing/branch/main/graph/badge.svg?token=Q8NOGB813N)](https://codecov.io/gh/v-v-d/billing)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

# Cервис для проведения оплат и оформления чеков

![схема TO BE](architecture/to-be.png)

## Ресурсы
- Доска: https://github.com/users/v-v-d/projects/3

Репозитории:
- сервис Auth API: https://github.com/v-v-d/Auth_sprint_1
- сервис Movies API: https://github.com/v-v-d/Async_API_sprint_1
- сервис Movies ETL: https://github.com/v-v-d/ETL
- сервис Admin panel: https://github.com/v-v-d/Admin_panel_sprint_1
- сервис UGC: https://github.com/v-v-d/ugc_sprint_1
- сервис Notifications: https://github.com/v-v-d/notifications_sprint_1

## Основные сущности
REST-API, которое:
  - управляет покупкой фильмов
  - управляет оформлением возврата фильма
  - показывает админу список совешенных транзакций
  - показывает юзеру его транзакции
  - управляет связями по купленным юзерами фильмам

## Основные компоненты системы
- Cервер ASGI — сервер с запущенным приложением.
- Nginx — прокси-сервер, который является точкой входа для веб-приложения.
- PostgreSQL — хранилище данных, в котором лежит вся необходимая информация для сервса.
- SQLAlchemy — используется в качестве ORM.
- Elastic APM — инструмент для работы с метриками приложения (включая трассировку запросов)

## Используемые технологии
- FastAPI
- PostgreSQL
- Docker
- Pytest + pytest coverage
- SQLAlchemy
- Elastic APM

## Работа с проектом
### Запуск
1. Создать общую сеть для всех проектов практикума, чтобы была связь между всеми контейнерами курса
    ```shell
    docker network create yandex
    ```
2. Создать файл .env в корне проекта. Для локального запуска достаточно будет скопировать все переменные из .env.sample
3. В качестве source root необходимо указать путь до директории src
4. Собрать и запустить текущий проект
    ```shell
    make start
    ```
5. Дока API закрыта basic auth и доступна по адресу `http://0.0.0.0/api/docs/`. Креды задаются энвами SECURITY_BASIC_AUTH_USERNAME и SECURITY_BASIC_AUTH_PASSWD
6. Мониторинг API и воркеров доступен в elastic APM по адресу `http://0.0.0.0:5602/app/apm/services/notifications-app`. Чтобы APM был доступен надо поднять APM сервер из репозитория сервиса Auth API https://github.com/v-v-d/Auth_sprint_1
    ```shell
   docker-compose up es-apm apm-server kibana-apm
    ```

### Тестирование
Собрать тестовое окружение и запустить тесты
```shell
make tests
```

### Миграции
1. Сгенерировать файлы миграций
```shell
make migrate name=<Тут короткое текстовое описании миграции>
```
2. Применить миграцию
```shell
make upgrade
```
3. Откатить миграцию
```shell
make downgrade
```