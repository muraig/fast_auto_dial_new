# -*- coding: utf-8 -*-
"""
Программа для осуществлении воспроизведения звукоых файлов клиентам телефонной сети
"""
# ##############################################################################
#  Copyright (c) 2021.                                                         #
#  Projects from AndreyM                                                       #
#  The best encoder in the world!                                              #
#  email: muraig@ya.ru                                                         #
# ##############################################################################
import asyncio
import json
import signal

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

##########################################
from starlette.concurrency import run_until_first_complete
from starlette.routing import WebSocketRoute
from broadcaster import Broadcast
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path as Paths
############################################################
from app.config.custom_logging import CustomizeLogger
from app.autodial import fastapi_autodial as fastapi_auto_dial
from app.api.api_v1.routers.users import users_router
from app.api.api_v1.routers.auth import auth_router
from app.core import config
from app.db.session import SessionLocal
from app.core.auth import get_current_active_user
from app.core.celery_app import celery_app
from app import tasks
from app.core.config import settings

env = Paths(__file__).parent.parent.joinpath('.env')
# print(f"env: {env}") ; import sys ; sys.exit()
try:
    config_path = Paths(__file__).parent.joinpath('config').joinpath("logging_config.json")
    config_path.exists()
except FileNotFoundError as e:
    config_path = Paths(__file__).joinpath('config').joinpath("logging_config.json")
    config_path.exists()
except Exception as e:
    print(f"File not found: {e}")
    config_path = ''

'''logger = CustomizeLogger.customize_logging(
    'log_fastapi_full_stack.log', 'debug', '20 days', '1 months',
    '<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>'
    ' request id: {extra[request_id]} - <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>')
logger = CustomizeLogger.customize_logging(
    'log_fastapi_full_stack.log', 'debug', '20 days', '1 months',
    '<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>'
    ' request id: {extra[request_id]} - <cyan>{name}</cyan>:<light-blue>{function}</light-blue>:<red>{line}</red> - <level>{message}</level>'
    )'''
logger = CustomizeLogger.make_logger(config_path)
uvicorn_log_config = uvicorn.config.LOGGING_CONFIG


# print(f"IF::Config file: {uvicorn_log_config}")
# del uvicorn_log_config["loggers"]["*"]
# uvicorn_log_config["disable_existing_loggers"] = True
# print(f"IF::Config file: {uvicorn_log_config['disable_existing_loggers']}")
# uvicorn_log_config['loggers']['uvicorn']['level'] = 'DEBUG'
# uvicorn_log_config['loggers']['uvicorn.error']['level'] = 'DEBUG'
# uvicorn_log_config['loggers']['uvicorn.access']['level'] = 'DEBUG'
# print(f"IF::Config file: {uvicorn_log_config['loggers']}")

class Publish(BaseModel):
    """
    Class publish
    """
    channel: str = "lebowski"
    message: str


broadcast = Broadcast('memory://')


async def events_ws(websocket):
    """
    Мы определили две асинхронные функции для получения и публикации
    сообщений и передали их старлетке WebSocketRoute.
    Использовал Postgres как серверную часть для вещательной компании.
    async def events_ws(websocket):
    :rtype: object
    :param websocket:

    """
    await websocket.accept()
    await run_until_first_complete(
        (events_ws_receiver, {"websocket": websocket}),
        (events_ws_sender, {"websocket": websocket}),
    )


async def events_ws_receiver(websocket):
    """

    :param websocket:
    """
    async for message in websocket.iter_text():
        await broadcast.publish(channel="events", message=message)


async def events_ws_sender(websocket):
    """

    :param websocket:
    """
    async with broadcast.subscribe(channel="events") as subscriber:
        async for event in subscriber:
            await websocket.send_text(event.message)


routes = [
    WebSocketRoute("/events", events_ws, name="events_ws"),
]

app = FastAPI(
    title=settings.PROJECT_NAME, docs_url="/api/docs", openapi_url="/api",
    routes=routes, on_startup=[broadcast.connect], on_shutdown=[broadcast.disconnect],

)

'''
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response
'''


@app.get("/api/v1")
async def root():
    return {"message": "Hello World"}


@app.get("/api/v1/task")
async def example_task():
    celery_app.send_task("app.tasks.example_task", args=["Hello World"])

    return {"message": "success"}


# Routers
app.include_router(
    users_router,
    prefix="/api/v1",
    tags=["users"],
    dependencies=[Depends(get_current_active_user)],
)
app.include_router(auth_router, prefix="/api", tags=["auth"])
app.include_router(fastapi_auto_dial.auto_router)

"""
Теперь, когда мы определили маршрут веб-сокета с вещателем,
давайте просто добавим его FastAPI и заключим сделку.
"""
# app = FastAPI(routes=routes, on_startup=[broadcast.connect], on_shutdown=[broadcast.disconnect], )
#########################################################
# монтирование статической папки для обслуживания статических файлов
# add_path = Paths(__file__).parent.parent
# print(f"add_path: {add_path}")
# os.chdir(add_path)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.exception(f"{e}")

midlew = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS], \
         'http://192.168.1.97', 'http://127.0.0.1:8080', 'http://localhost:3000', 'http://192.168.1.97:3000'
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# logger.info(f"app.middleware(): {midlew}")


@app.post("/auto/push")
async def push_message(publish: Publish):
    """
    Я добавил маршрут веб-сокета в приложение FastAPI и публикую его в канале при каждом вызове API.
    """
    await broadcast.publish(publish.channel, json.dumps(publish.message))
    return Publish(channel=publish.channel, message=json.dumps(publish.message))


# sanity check route
@app.get('/auto/ping')
async def ping_pong(msg: str):
    """

    :param msg:
    :return:
    """
    # return {"ping": "pong"}
    # return jsonify('pong!')
    logger.info(f"ping: {msg}")
    return {msg: "pong!"}


async def monitor_tasks():
    while True:
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [t.print_stack(limit=5) for t in tasks]
        await asyncio.sleep(2)


# loop = asyncio.get_event_loop()  # Start main event loop.
# loop.create_task(monitor_tasks()) # To monitor stack trace
def handle_exception(loop, context):
    msg = context.get("exception", context["message"])
    # logging.error(f"Caught exception: {msg}")
    # logging.info("Shutting down...")
    logger.error(f"Caught exception: {msg}")
    logger.info("Shutting down...")
    asyncio.create_task(shutdown(loop))


async def shutdown(loop, signal=None):
    if signal:
        await logger.info(f"Received exit signal {signal.name}...")
    await logger.info("Closing database connections")
    await logger.info("Nacking outstanding messages")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]

    await logger.info("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    await logger.info(f"Flushing metrics")
    await logger.info(f"Shutting down aiologger")
    await logger.shutdown()
    loop.stop()


def main():
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_tasks())  # To monitor stack trace

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop, signal=s))
        )
    loop.set_exception_handler(handle_exception)

    queue = asyncio.Queue()
    try:
        # loop.create_task(publish(queue))
        # loop.create_task(consume(queue))
        loop.run_forever()
    finally:
        loop.close()
        # logging.info("Successfully shutdown the Mayhem service.")
        logger.info("Successfully shutdown the Mayhem service.")


if __name__ == "__main__":
    '''log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8888, log_config=log_config)'''
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8888, log_config=uvicorn_log_config)
