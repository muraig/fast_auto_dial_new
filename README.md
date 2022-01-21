# auto_dial

## Как пользоваться

------------------------------------------------

Для взаимодействия с серврером FastPBX с него нужно примонтировать по NFS пару папок:

на клиенте:

Создать папки:

mkdir -p /var/lib/asterisk/sounds/{autodial,ru/autodialer}

chown -R asterisk: /var/lib/asterisk/sounds

отредактировать файл /etc/fstab

cat /etc/fstab 

192.168.x.249:/var/lib/asterisk/sounds/autodial  /var/lib/asterisk/sounds/autodial nfs rw,noauto,user 0 0
192.168.x.249:/var/lib/asterisk/sounds/ru/autodialer /var/lib/asterisk/sounds/ru/autodialer nfs rw,noauto,user 0 0

на сервере:

отредактировать файл /etc/exports

с указанием парметров вот так:

/var/lib/asterisk/sounds/autodial 192.168.x.0/24(rw,async,no_subtree_check,all_squash,anonuid=995,anongid=995)
/var/lib/asterisk/sounds/ru/autodialer 192.168.x.0/24(rw,async,no_subtree_check,all_squash,anonuid=995,anongid=995)

где anonuid=995 и 995 - id пользователя asterisk

Данные настройки необходимы для создания аудиофайлов:
1. номер контракта
2. сумма долга
3. так же из этих папок берутся файлы для формировнаия озвучки автообзвона.


Аудиофайлы создаются этим же проектом с помощью YandexSpeechKIT
Либо поднимается решение RhVoice, но которое http запросами оправляется цифры и строки и получаются в ответ аудиофайлы

Данный проект не требует запуска всех контейнеров, перечисленных в файле docker-compose.yaml,
так как рабочая часть, необходимая для создания звонков в Астериске выдрана из общего проекта

-----------------------------------------------------


-------------------------------------------------------------------------


## Backend Requirements

* [Docker](https://www.docker.com/).
* [Docker Compose](https://docs.docker.com/compose/install/).
* [Poetry](https://python-poetry.org/) for Python package and environment management.




