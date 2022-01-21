# -*- coding: utf-8 -*-
# ##############################################################################
#  Copyright (c) 2021.
#  Projects from AndreyM                                   #
#  The best encoder in the world!                                              #
#  email: muraigtor@gmail.com                                                         #
# ##############################################################################
"""
Программа для осуществлении воспроизведения звукоых файлов клиентам телефонной сети
Файл для создания asyncio.task
"""
"""
Аргумент для run_until_completeуправления продолжительностью выполнения цикла событий.
И как только цикл событий прекращает работу, все сопрограммы фактически приостанавливаются,
а не только та, которую вы ждали. Но у вас есть разные варианты:

loop.run_until_complete(some_func())- что вы уже использовали;
запустите цикл обработки событий до завершения some_func сопрограммы.
Параллельно выполняет другие сопрограммы в течение этого времени,
но также прекращает их выполнение, как только цикл обработки событий завершается.

loop.run_forever()- запускать цикл обработки событий до тех пор,
пока не будет вызвана какая-либо сопрограмма или обратный вызов loop.stop().
Если ни один из них этого не сделает, цикл обработки событий не остановится,
даже если все сопрограммы завершатся. В вашем случае вы бы позвонили
loop.create_task(while_loop()), loop.create_task(some_func()) а затем и затем loop.run_forever().

loop.run_until_complete(asyncio.gather(while_loop(), some_func())) запустите цикл обработки событий,
пока обе указанные сопрограммы не закончат работу. Это (ожидание всех задач), по-видимому, является тем,
что вы ожидали loop.run_until_complete()сделать автоматически, даже если вы укажете только одну,
за исключением того, что это не работает так, она останавливается, как только указанная сопрограмма завершается.
asyncio.gather может использоваться для ожидания нескольких сопрограмм одновременно.
Для более точной настройки ожидания см asyncio.wait. Также .

Поскольку одна из ваших сопрограмм работает вечно, последние два параметра будут эквивалентны и приведут к ожидаемому результату.
"""

import os
import sys
import time

from pathlib import Path as Paths
from contextlib import suppress
import asyncio

from app.config.custom_logging import CustomizeLogger
from app.autodial.autodial_apps import ARIApp


try:
    config_path = Paths(__file__).parent.parent.joinpath('config').joinpath("logging_config.json")
    config_path.exists()
except FileNotFoundError as e:
    config_path = Paths(__file__).parent.joinpath('config').joinpath("logging_config.json")
    config_path.exists()
except Exception as e:
    print(f"File not found: {e}")
    config_path = ''
logger = CustomizeLogger.make_logger(config_path)


######### From futures task #########
async def create_connection_to_the_asterisk(typeauto=None):
    """
    Создание процесса подключения к Астериску для реализации в нем Stasis приложения
    :param typeauto:
    :return:
    """
    results = os.getpid()
    sys.stdout = open(str(os.getpid()) + ".out", "w+")
    await asyncio.sleep(0.1)
    print(f"Запускаем субпроцесс c PID'ом: {results}")
    try:
        env = Paths(__file__).parent.parent.parent.joinpath('.env')
        logger.info(f"env: {env}")
        logger.debug(f"DEBUG::create_connection_to_the_asterisk: {results}")
        # print(f"env: {env}") #; import sys ; sys.exit()
        # code = await ARIApp(env).connect(typeauto)
        code = await ARIApp(env, typeauto=typeauto).listen_forever(typeauto)
        print(f"IF::Config file: {code}")
        logger.debug(f"DEBUG::create_connection_to_the_asterisk: {code}")
    except Exception as e:
        logger.exception(f"Exception: {e}")
    #print(f"Запущена задача с PID'ом: {results}")

    return results


async def future_task(typeauto=None, loop=None, timeout=None):
    """
    Добавление в текущий loop задачи asyncio.create_task
    :param typeauto:
    :param loop:
    :param timeout:
    :return:
    """
    logger.debug(f"started main at {time.strftime('%X')}")
    try:
        future = asyncio.create_task(create_connection_to_the_asterisk(typeauto), name=typeauto)
        await asyncio.sleep(1)
    finally:
        logger.debug(f"finished main at {time.strftime('%X')}")

    return future

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        #date = asyncio.run(get_date(), debug=True)
        date = asyncio.run(future_task('urliz'), debug=True)
        #date = asyncio.threads.
        # выводим результат работы
        print(f"Current date: {date}")
