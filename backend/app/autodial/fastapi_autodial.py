# -*- coding: utf-8 -*-
"""
Программа для осуществлении воспроизведения звукоых файлов клиентам телефонной сети
Файл маршрутов для FastAPI приложения
"""
# ##############################################################################
#  Copyright (c) 2021.
#  Projects from AndreyM                                   #
#  The best encoder in the world!                                              #
#  email: muraigtor@gmail.com                                                         #
# ##############################################################################
import os
import json
import time
import uuid
import zipfile
import io

import asyncio
from pydantic import BaseModel, Field
from pathlib import Path as Paths
from typing import List, Optional
import aiofiles

from fastapi import Form
from fastapi import UploadFile, File
from fastapi import Request
from fastapi import APIRouter
from fastapi import Response
from fastapi.params import Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocketDisconnect
from fastapi import WebSocket
from fastapi.responses import RedirectResponse, FileResponse

from app.autodial.autodial_apps import check_applications
from app.autodial.autodial_apps import create_and_maintain_channel
from app.autodial.synthesize_files import get_vaqriables_from_pages
from app.config.custom_logging import CustomizeLogger
from app.config.config import Settings
from app.autodial.autodial_fork import future_task

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

env = Paths(__file__).parent.parent.parent.joinpath('.env')

add_path = os.path.abspath(os.path.dirname(__file__)).rsplit('/', 1)[0]
os.chdir(add_path)
templates = Jinja2Templates(directory="templates")

#######################################################################
# Переменные #
PATHS = "./tmp/"
DIR_SOUND = Settings(_env_file=env, _env_file_encoding='utf-8').DIRSOUND
TMP_SOUND = './tmp/'
FILENAME = "/home/andrei/PycharmProjects/web_realtime_streaming/other/some_other_file.tsv"

#######################################################################
auto_router = APIRouter()


#######################################################################
# Формирование классов для переменных получаемых из request: Request #
def form_body(cls):
    """
    Класс для отправки данных с  Форм на страницах

    @param cls:
    @return:
    """
    cls.__signature__ = cls.__signature__.replace(
        parameters=[
            arg.replace(default=Form(...))
            for arg in cls.__signature__.parameters.values()
        ]
    )
    return cls


@form_body
class VariaBle(BaseModel):
    Input_text: str  # Привет!
    forms: str
    files: str


@form_body
class AutoDial(BaseModel):
    Input_text_File: str
    Input_textAdial: str
    formdial1: str
    formdial2: str
    formdial3: str


@form_body
class TypeDial(BaseModel):
    typeautodial: Optional[str] = Field()
    # typeautodial: str
    # typedi: str = Field(...,)
    # token_type: Optional[str] = "bearer"


class NewJobForm(BaseModel):
    name: str = Field(..., )
    body: str = Field(..., )
    tags: List[str] = Field(..., )
    mail: str = Field(..., )
    position: str = Field(..., )
    location: str = Field(..., )
    work_type: str = Field(..., )


#######################################################################
# Фейковые классы  для формирования ответов сервера
# на данный момент - не задействовано #
# Define your models here like
class model200(BaseModel):
    message: str = "Ok!"


class model404(BaseModel):
    message: str = "oppa..."


class model500(BaseModel):
    message: str = "mlya...."


#######################################################################
''' Для просмотра созданных каналов в Stasis приложении '''
'''@auto_router.get("/auto/phones")
async def form_post(request: Request):
    """

    :param request:
    :return:
    """
    result = "Type a number"
    return templates.TemplateResponse('phone.html', context={'request': request, 'result': result})
'''

####### Страница для просмотра типа автообзвона и остальными функциями приложения #######
''' Для создания Stasis приложения GET запрос'''


@auto_router.get("/auto/form")
async def form_get_post(request: Request, phone: Optional[str] = Query(None, max_length=50)):
    """

    :param request:
    :param phone:
    :return:
    """
    req_answer = await check_applications(env)
    req_ans = req_answer[1].replace('[{', '{').replace('}]', '}').split('},{')
    logger.debug(f"161:::form_get_post::req_answer:req_ans: {req_ans}")
    rq = []
    try:
        if len(req_ans) >= 1 and req_ans[0] != '[]':
            for r in req_ans:
                r = '{' + str(r) + '}'
                r = r.replace('{{', '{').replace('}}', '}').replace("'", '"')
                logger.info(f"for r in req_ans: {json.loads(r)}")
                _rq = dict(json.loads(str(r))).items()
                __rq = ';'.join([str(r) for r in _rq if not r[1] == []])
                # logger.info(f"for r in req_ans::rq: {__rq}")
                rq.append(__rq)
        else:
            rq = ['{"name":"None"}', '{"channel_ids":"None"}']
            logger.debug(f"ELSE::form_post_post::rq: {rq}")
    except Exception as e:
        rq = ['{"name":"None"}', '{"channel_ids":"None"}']
        logger.exception(f"form_post_post::Exception: {e}")
    finally:
        await asyncio.sleep(0.1)
        logger.info(f"Current date: {'Ok!'}")

    # return templates.TemplateResponse('form.html', context={'request': request, 'result': rq})
    response = templates.TemplateResponse('autodials.html', context={'request': request, 'result': rq})
    # response = RedirectResponse(url='/auto/form', status_code=302, headers=None, background=None)
    return response


''' Для создания вызова в Приложение автообзвона Post запрос '''


@auto_router.post("/auto/phones", response_model=TypeDial)
async def form_post(phone: int = Form(...), form: TypeDial = Depends(), ):
    """
    Форма для создания вызова по номеру телефона: phone и типа обзвона: typeautodial
    :param phone:
    :param form:
    :return:
    """

    # global result
    if form.typeautodial:
        typeautodial = form.typeautodial
        logger.info(f"if:::form_post::typeautodial: {typeautodial}")
    else:
        typeautodial = None
        logger.info(f"else:::form_post::typeautodial: {typeautodial}")

    # if phone == 4002 or phone == 4003 or phone == 4004 or 100 or 120:
    _time = str(time.time())
    _uniq = str(uuid.uuid4())
    ch_id = _time + '-' + _uniq
    result = await create_and_maintain_channel(env, typeautodial, phone, ch_id)
    if 'Not' not in str(result):
        logger.info(f"212:::read_phones::result: {result.id, result.connected.number}")
    else:
        logger.debug(f"214:::read_phones::result: {result}")

    response = RedirectResponse(url='/auto/form', status_code=302, headers=None, background=None)
    return response


''' Для остановки задачи автообзвона Post запрос '''


@auto_router.post("/auto/stop/")
async def form_get_post_stop(autodial: Optional[str] = Form(None)):
    """

    :param request:
    :param phone:
    :return:
    """

    await asyncio.sleep(0.3)
    logger.debug(f"323::form_get_post_stop: {autodial}")
    typeauto = autodial

    def get_task_from_all_trasks(all_tasks, autodial):
        def applay(t):
            if t.get_name() == autodial:
                t.cancel()
                try:
                    logger.debug(f"Задача автообзвона {autodial} остановлена: {t.cancelled()}")
                except Exception as e:
                    logger.debug(f"Исключение при остановки задачи автообзвона:autodial: {e}")

                try:
                    t.result()
                except Exception as e:
                    logger.debug(f"Исключение при остановки задачи автообзвона:autodial: {e}")

                try:
                    t.exception()
                except Exception as e:
                    logger.debug(f"Исключение при остановки задачи автообзвона:autodial: {e}")
                return t

        logger.debug(f"Остановка задачи автообзвона:autodial: {autodial}")
        return map(applay, all_tasks)

    tasks = get_task_from_all_trasks(asyncio.all_tasks(), autodial)
    for tt in list(tasks):
        logger.debug(f"Остановка задачи автообзвона: {tt}") if tt else False

    """ Отрисовываем перечень текущих запущеннызх задач(автообзовнов) """
    req_answer = await check_applications(env)
    req_ans = req_answer[1].replace('[{', '{').replace('}]', '}').split('},{')
    # logger.info(f"form_get_post::req_answer:type(req_ans): {type(req_ans)}")
    rq = []
    try:
        if len(req_ans) >= 1 and req_ans[0] != '[]':
            for r in req_ans:
                r = '{' + str(r) + '}'
                r = r.replace('{{', '{').replace('}}', '}').replace("'", '"')
                logger.info(f"for r in req_ans: {json.loads(r)}")
                _rq = dict(json.loads(str(r))).items()
                __rq = ';'.join([str(r) for r in _rq if not r[1] == []])
                # logger.info(f"for r in req_ans::rq: {__rq}")
                rq.append(__rq)
        else:
            rq = ['{"name":"None"}', '{"channel_ids":"None"}']
            logger.debug(f"ELSE::form_post_post::rq: {rq}")
    except Exception as e:
        rq = ['{"name":"None"}', '{"channel_ids":"None"}']
        logger.exception(f"form_post_post::Exception: {e}")
    finally:
        await asyncio.sleep(0.1)
        logger.info(f"Current date: {'Ok!'}")

    response = RedirectResponse(url='/auto/form', status_code=302, headers=None, background=None)
    return response


''' Для создания типа автообзвона Post запрос '''  # 200: {"response": model200},


@auto_router.post("/auto/form", responses={404: {"response": model404}, 500: {"response": model500}})
async def form_post_post(request: Request, typeauto: str = Form(...)):
    """
    сделал запуск форком. теперь нужно отследить процесс для управления
    # TODO: сделал запуск форком. теперь нужно отследить процесс для управления
    :param request:
    :param typeauto:
    :return:
    """

    timeout = 1

    # Получить текущий loop
    loop = asyncio.get_running_loop()

    # Создание корутины
    # coro = asyncio.sleep(1, result=3)
    date = future_task(typeauto=typeauto, loop=loop, timeout=timeout)

    # Отправить корутину в заданный цикл
    future = asyncio.run_coroutine_threadsafe(date, loop)
    logger.debug(f"FUTURE::form_post_post::date.cr_code: {date.cr_code}")
    logger.debug(f"FUTURE::form_post_post::future: {future}")

    await asyncio.sleep(1)
    # logger.debug(f"Остановка задачи автообзвона::asyncio.iscoroutine(fut):{asyncio.iscoroutinefunction(fut)}")
    # logger.debug(f"Остановка задачи автообзвона::fut:\n{[str(t) for t in fut]}\n")

    """ Отрисовываем перечень текущих запущеннызх задач(автообзовнов) """
    req_answer = await check_applications(env)
    req_ans = req_answer[1].replace('[{', '{').replace('}]', '}').split('},{')
    '''if str(req_ans[0]) == '[]':
        logger.debug(f"IF::form_post_post::str(req_ans): |{req_ans}|")
    else:
        logger.debug(f"ELSE::form_post_post::str(req_ans): |{req_ans}|")'''

    rq = []
    try:
        if not str(req_ans[0]) == '[]':
            for r in req_ans:
                r = '{' + str(r) + '}'
                r = r.replace('{{', '{').replace('}}', '}')
                # logger.info(f"for r in req_ans: {json.loads(r)}")
                _rq = dict(json.loads(str(r))).items()
                __rq = ';'.join([str(r) for r in _rq if not r[1] == []])
                logger.info(f"for r in req_ans::rq: {__rq}")
                rq.append(__rq)
        else:
            rq = ['{"name":"None"}', '{"channel_ids":"None"}']
            logger.debug(f"ELSE::form_post_post::rq: {rq}")
    except Exception as e:
        rq = ['{"name":"None"}', '{"channel_ids":"None"}']
        logger.exception(f"form_post_post::Exception: {e}")
    finally:
        await asyncio.sleep(0.1)
        logger.info(f"Произведена попытка получить данные, количество запущщеных автообзвонов: {len(rq)}")

    # return templates.TemplateResponse('form.html', context={'request': request, 'result': rq})
    response = templates.TemplateResponse('autodials.html', context={'request': request, 'result': rq})
    # response = RedirectResponse(url='/auto/form', status_code=302, headers=None, background=None)
    return response


###############################################################################
''' Функция создания автообзвона созданием задачи на данный момент - не задействовано '''


async def _form_post_post(request, typeauto):
    timeout = 1

    # Получить текущий loop
    loop = asyncio.get_running_loop()

    # Создание корутины
    # coro = asyncio.sleep(1, result=3)
    date = future_task(typeauto=typeauto, loop=loop, timeout=timeout)

    # Отправить корутину в заданный цикл
    future = asyncio.run_coroutine_threadsafe(date, loop)
    logger.debug(f"FUTURE::form_post_post::date.cr_code: {date.cr_code}")
    logger.debug(f"FUTURE::form_post_post::future: {future}")

    await asyncio.sleep(1)


######################## Files ###########################
# Using Request instance
@auto_router.get("/auto/url-list-from-request")
def get_all_urls_from_request(request: Request):
    url_list = [
        {"path": route.path, "name": route.name} for route in request.app.routes
    ]
    return url_list


#################### Upload file from Page ########################
@auto_router.post("/auto/uploadfiles/")  # files: bytes = File(...),
async def create_files(request: Request, uploaded_file: UploadFile = File(...)):
    file_location = f"{DIR_SOUND}/{uploaded_file.filename}"
    logger.info(f"Путь до файла: {file_location}")
    '''async with aiofiles.open("files/1.jpg", "wb") as f:
        await f.write(bytes([(file) for file in files]))'''
    async with aiofiles.open(file_location, "wb+") as f:
        await f.write(uploaded_file.file.read())
    # fileinfo = {"info": f"Файл '{uploaded_file.filename}' сохранен как '{file_location}'"}
    # result = ''
    response = RedirectResponse(url='/auto/form', status_code=302, headers=None, background=None)
    return response


#################### Create Audiofile from Text ########################
async def list_dir(dirs_=None, query_items=None):
    """
    Создание списка файлов по маске wav
    Возвращает список файлов в папке dirs_

    @rtype: object
    @param dirs_:
    @param query_items:
    @return:
    """
    olddir = os.getcwd()
    chdir = Paths(__file__).parent.parent.joinpath('tmp')
    """ Если нет папки - создаем ее """
    p = Paths(chdir.joinpath('tmp.file'))
    p.parent.mkdir(parents=True, exist_ok=True)
    # logger.info(f"Check dir: {chdir}")
    os.chdir(chdir)
    logger.info(f"listdir: {os.listdir()}")
    """ Если папка не указана - выбираем текущу папку """
    if not dirs_ == None:
        dirs = dirs_
    else:
        dirs = '.'
    try:
        folders = os.listdir(dirs + "/")
    except FileNotFoundError as e:
        logger.exception(f"FileNotFoundError: {e}")
        folders = []
        os.chdir(olddir)
        return 'File not Found'
    results = {}
    results["folders"] = [val for val in folders if os.path.isdir(dirs + "/" + val)]
    results["files"] = [val for val in folders if os.path.isfile(dirs + "/" + val) and 'wav' in val]
    results["path_vars"] = '.' if query_items is None else query_items["q"]
    os.chdir(olddir)

    return results


async def create_file_autodial(dirs_=None, query_items=None):
    """
    Создание списка файлов по маске txt
    Возвращает список файлов в папке dirs_

    @rtype: object
    @param dirs_:
    @param query_items:
    @return:
    """
    olddir = os.getcwd()
    chdir = Paths(__file__).parent.parent.joinpath('tmp')
    """ Если нет папки - создаем ее """
    p = Paths(chdir.joinpath('tmp.file'))
    p.parent.mkdir(parents=True, exist_ok=True)
    # logger.info(f"Check dir: {chdir}")
    os.chdir(chdir)
    # logger.info(f"listdir: {os.listdir()}")
    """ Если папка не указана - выбираем текущу папку """
    if not dirs_ == None:
        dirs = dirs_
    else:
        dirs = '.'
    folders = os.listdir(dirs + "/")
    results = {}
    results["folders"] = [val for val in folders if os.path.isdir(dirs + "/" + val)]
    results["files"] = [val for val in folders if os.path.isfile(dirs + "/" + val) and 'txt' in val]
    results["path_vars"] = '.' if query_items is None else query_items["q"]
    os.chdir(olddir)

    return results


@auto_router.get("/auto/shows")
async def get_folders(request: Request):
    results = await list_dir()

    return results


async def download(file_path):
    """
    Download file for given path.
    """
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        # return FileResponse(path=file_path)
    return None


@auto_router.get("/auto/shows/")
async def get_items(q: List[str] = Query(None)):
    '''
    Pass path to function.
    Returns folders and files.
    '''

    query_items = {"q": q}
    if query_items["q"]:
        dirs = PATHS + "/".join(query_items["q"])
    else:
        dirs = PATHS

    if os.path.isfile(dirs):
        return await download(dirs)
    results = await list_dir(dirs, query_items)

    return results


#################### Download file from Page ######################
async def zipfiles(filenames):
    zip_filename = "archive.zip"

    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)

        # Add file, at correct path
        zf.write(fpath, fname)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
        'Content-Disposition': f'attachment;filename={zip_filename}'
    })

    return resp


@auto_router.get("/auto/image_from_id/txt")
async def image_from_id(request: Request):
    # Get image from the database
    img = await create_file_autodial()
    logger.info(f"img: {img}")
    img = [f"./tmp/{img['files'][0]}"]

    return await zipfiles(img)


@auto_router.get("/auto/image_from_id/audio")
async def image_from_id(request: Request):
    # Get image from the database
    a_file = await list_dir()
    a_file = a_file['files']
    logger.info(f"a_file: {a_file}")
    logger.info(f"type(a_file): {type(a_file)}")
    audio = []
    # ['3_300_3000_persons.wav', '2_300_3000_persons.wav', '1_300_3000_persons.wav']
    for f in a_file:
        audio.append(f"./tmp/{f}")
        # logger.info(f"./tmp/{f}")
    logger.info(f"audio: {audio}")

    # return None
    return await zipfiles(audio)


#################### Create Audiofile from Text ########################
@auto_router.get('/auto/textarea')
async def home(request: Request):
    list_ = await list_dir()
    autodial = await create_file_autodial()
    logger.info(f"autodial: {autodial}")
    data = {'request': request, 'filenames': '/tmp/', 'list_dir': list_, 'autodial': autodial, }
    return templates.TemplateResponse('translates.html', data)


@auto_router.post("/auto/textarea", response_model=VariaBle)
async def create_files(request: Request, form: VariaBle = Depends(VariaBle)):
    # Внимание!  Уведомляем Вас об имеющейся задолженности за холодное водоснабжение и водоотведение по лицевому счету
    # перед МУП «Водоканал» города Иркутска в сумме
    # Убедительно просим оплатить задолженность в полном объеме.\
    # Более подробную информацию Вы можете получить по телефону 21-46-46
    """
    Получить данные из textarea со страницы
    добавить к ним тег <speak> и создать строку данных типа: "ssml": "<speak>ТУТ ТЕКСТ</speak>
    отправить данные на YandexSpeechKIT
    получить звуковой файл, сохранить его
    нарисовать интерфейс для дать возможность его проиграть,
    что бы убедиться что записалось именно то, что нужно было для реализации задачи

    @rtype: object
    @param request:
    @param form:
    @return:
    """
    args = await get_vaqriables_from_pages(form)
    '''try:
        files = form.files
    except Exception as e:
        files = 'test.raw'
        logger.exception(f"Exception: {e}")
    args = {}
    args = await token_variables(args)
    formats = form.forms
    args['formats'] = formats
    files += f".{formats}"
    file_location = f"{TMP_SOUND}/{files}"
    args['output'] = file_location
    args['output'] = args['output'].replace('//', '/')
    text = form.Input_text
    args['text'] = text
    # logger.info(f"files: {files}")
    # logger.info(f"formats: {formats}")
    # logger.info(f"text: {text}")
    await create_audio_files(args)'''

    text = args['text']
    formats = args['formats']
    filenames = '/tmp/'
    list_ = await list_dir()

    if args['output']:
        filenames = args['output']
        logger.info(f"filenames: {filenames}")
    else:
        logger.info(f"filenames: {filenames}")
    data = {
        'request': request,
        'translated': text,
        't_lang': formats,
        'filenames': filenames,
        'list_dir': list_,
    }

    return templates.TemplateResponse("translates.html", context=data, )


@auto_router.post("/auto/textarea1", response_model=VariaBle)
async def create_autodial(request: Request, form: AutoDial = Depends(AutoDial)):
    """
    Создание файла автообзвона в папке tmp

    @rtype: object
    @param request:
    @param form:
    @return:
    """
    file_autodial = {}
    #
    # file_autodial['Имя файла'] = form.Input_text_File
    file_autodial['Тип обзвона'] = form.Input_textAdial
    file_autodial['Первый файл'] = f"{form.formdial1}"
    file_autodial['Второй файл'] = f"{form.formdial2}"
    file_autodial['Третий файл'] = f"{form.formdial3}"
    adial = form.Input_text_File
    file_location = f"{TMP_SOUND}/{adial}"
    logger.info(f"Путь до файла: {file_location}")
    file_autodial = json.dumps(file_autodial, indent=2, ensure_ascii=False)
    async with aiofiles.open(file_location, "w+", encoding='utf-8') as f:
        await f.write(file_autodial)

    return RedirectResponse(url='/auto/textarea', status_code=302, headers=None, background=None)


######### Favicon ###############
@auto_router.route('/favicon.ico')
async def favicon(request: Request):
    chdir = Paths(__file__).parent.parent
    logger.info(f"Check dir: {chdir}")
    os.chdir(chdir)
    return FileResponse('static/favicon.ico', status_code=200, headers=None, media_type='image/vnd.microsoft.icon')


########## chat ##########################
messages = []  # List of chat messages

# Class for connecting the client with the webSocket
''' Класс для создания подключения к сокету и создания broadcast-сервера '''


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()  # instance of the Connection Manager


# websocket for publish the comming message to all client connected in
@auto_router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)  # connecting the client with the websocket
    try:
        while True:
            data = await websocket.receive_json()  # Data recieve when the client send a message
            messages.append(data)  # Add the coming message to the list of messages

            """ here we call a ConnectionManager method named "broadcast()" that publish the list of messages to
            all clients """
            await manager.broadcast(messages)
    except WebSocketDisconnect:
        manager.disconnect(websocket)  # deconnecting if an exeption handled
        # await manager.broadcast(messages)
