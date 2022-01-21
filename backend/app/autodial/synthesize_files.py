# -*- coding: utf-8 -*-
# ##############################################################################
#  Copyright (c) 2021.                                                         #
#  Projects from AndreyM                                                       #
#  The best encoder in the world!                                              #
#  email: muraig@ya.ru                                                         #
# ##############################################################################

import datetime
import requests
import asyncio  # [1]
import aiohttp
import sox

from pathlib import Path as Paths
from app.config.custom_logging import CustomizeLogger

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

TMP_SOUND = './tmp/'

async def create_token(_token):
    async with aiohttp.ClientSession() as session:
        prm = {'yandexPassportOauthToken': _token}
        async with session.post('https://iam.api.cloud.yandex.net/iam/v1/tokens', params=prm) as resp:  # [1]
            response = await resp.json()  # [2]
            # print(f'response: {response}')
            iam_token = response.get('iamToken')
            expires_iam_token = response.get('expiresAt')

            return iam_token, expires_iam_token


class SyntezeYndex:
    def __init__(self, folder_id, iam_token, text):
        self.url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        self.headers = {'Authorization': 'Bearer ' + iam_token, }
        self.data = {
            'text': text,
            'lang': 'ru-RU',
            'folderId': folder_id,
            'format': 'lpcm',
            'sampleRateHertz': 48000,
            'voice': 'filipp',
            # 'voice': 'alena',
        }
        self.folder_id = folder_id

    def synthesize_raw(self, data_=None):
        self.data['text'] = data_['text']
        with requests.post(self.url, headers=self.headers, data=self.data, stream=True) as resp:
            if resp.status_code != 200:
                raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))
            for chunk in resp.iter_content(chunk_size=None):
                yield chunk

    def synthesize_ogg(self, params_=None, data_=None):
        """
        curl -X POST \
        -H "Authorization: Bearer ${IAM_TOKEN}" \
        --data-urlencode "ssml='<speak>\n', 'Привет, чувак!!! Назови-ка мне свои имя и фамилию?\n', '</speak>\n'" \
        -d "lang=ru-RU&folderId=${FOLDER_ID}"
        "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize" > speech.ogg
        """
        if params_ == None:
            self.params = None
        else:
            self.params = params_
        if data_ == None:
            self.data = {
                'lang': 'ru-RU',
                'folderId': self.folder_id,
                'voice': 'filipp',
                'format': 'lpcm',
                'sampleRateHertz': 48000,
                # 'voice': 'alena',
            }
        else:
            self.data = data_
            self.data['folderId'] = self.folder_id
        print(f"headers: {self.headers}, params_: {self.params}, data_: {self.data}")

        with requests.post(self.url, headers=self.headers, data=self.data, params=self.params, stream=True) as resp:
            if resp.status_code != 200:
                raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))
            for chunk in resp.iter_content(chunk_size=None):
                yield chunk


async def token_variables(args):
    """ Создание токена авторизации в сервисе YandexSpeechKIT

    @rtype: object
    @param args:
    @return: args
    """
    oauth_token = "AQAAAABTwxInAATuwULUZhLjRUjLnEpMlle43dw"
    # token = asyncio.run(create_token(oauth_token))
    token = await create_token(oauth_token)
    print(f"Токен успешно сгенерирован и действует до {token[1]}")
    print(f"\nТокен: {token[0]}\nГоден до: {token[1].replace('T', ' ')}")
    today = datetime.datetime.today()
    print(f"Сейчас:   {today.strftime('%Y-%m-%d %H:%M:%S.%fZ')}")  # 2021-04-13 17:55:32.269303
    args['folder_id'] = 'b1ghvinsgfdldjmo8c69'
    # args['output'] = '5_speech.ogg'
    # args['text'] = 'Привет, чувак! Назови-ка мне свои имя и фамилию?'
    args['token'] = token[0]

    return args


async def convert_to_wav(output: str):
    # async def sox_transformer(file_path_):
    """Преобразуем файл в  8000kGz, иначе asterisk не примет"""
    files, format_ = output.rsplit('/')[::-1][0].rsplit('.')
    logger.info(f"files, format_: {files, format_}")
    logger.info(f"output {output}")
    file_new = output.rsplit('.', maxsplit=1)[0]

    if format_ == 'ogg':
        file_new += '.wav'
    elif format_ == 'wav':
        file_new += '.wav'
    elif format_ == 'raw':
        file_new += '.wav'
    logger.info(f"output, file_new: {output, file_new}")
    # subprocess.call(['sox', '/input/file.mp3', '-e', 'mu-law', '-r', '16k', '/output/file.wav', 'remix', '1,2'])
    # sox -r 48000 -b 16 -e signed-integer -c 1 3_300_3000_fizliza.raw 3_300_3000_fizliza.wav
    # sox ожидает ввода.raw с 8 -bit или более высоким кодированием. Поэтому, если вы запустите
    # sox -r 44100 -e signed -b 8 -c 2 in.raw out.wav
    '''data1 = await async_subprocess_command(
        soxExecutable, '-r', 48000, '-b', 16, '-e', 'signed-integer', '-c', 1, output, file_new)
    # sox -r 48000 -b 16 -e signed-integer -c 1 1_300_3000_fizliza.raw 1_300_3000_fizliza.wav
    logger.info(f"data1: {data1}")'''
    ''', data1b, data1b'''
    #os.rename(output, file_new), 'remix', '1,2'
    fm = sox.Transformer()
    fm.set_input_format(file_type='raw', rate=48000, bits=16, channels=1, encoding='signed-integer')
    fm.set_output_format(file_type='wav', rate=8000, bits=16, channels=1, encoding='signed-integer')
    try:
        fm.build(output, file_new)
    except Exception as e:
        logger.exception(f"Exception: {e}")

    return output

    '''#data1, data1b = await async_subprocess_command(soxExecutable, "--i", output)
    #data2, data2b = await async_subprocess_command(soxExecutable,  output,"-n", "stat")
    #logger.info(f"data1: {data1, data1b}")
    #logger.info(f"data2: {data2, data2b}")
    
    await sox_transformer(output)'''


async def create_audio_files(args):
    """ Получаем арументы из функции create_files(request: Request, form: VariaBle = Depends(VariaBle)) """
    text = args['text']
    formats = args['formats']
    if formats == 'raw':
        data_ = dict(text=text, lang='ru-RU', format='lpcm', sampleRateHertz=48000, voice='filipp')
        params = None
    else:
        params = {"ssml": f"<speak>{args['text']}</speak>"}
        data_ = None
    try:
        """ Пробуем создать обьект - звуковой файл """
        spech = SyntezeYndex(args['folder_id'], args['token'], args['text'])
        logger.info(f"params: {params}, data_: {data_}")
        with open(args['output'], "wb") as f:
            if formats == 'raw':
                for audio_content in spech.synthesize_raw(data_):
                    f.write(audio_content)
            elif formats == 'ogg':
                for audio_content in spech.synthesize_ogg(params, data_):
                    f.write(audio_content)
        """ Создали файл, теперь его конвертируем в формат wav """
        if formats == 'raw':
            logger.info(f"if formats == 'raw': {formats}")
            await convert_to_wav(args['output'])
        elif formats == 'ogg':
            await convert_to_wav(args['output'])
            logger.info(f"if formats == 'ogg': {formats}")
    except Exception as e:
        logger.exception(f"Exception: {e}")
    #finally:


async def get_vaqriables_from_pages(form):
    """ Создание аудио файлов из текста """
    '''
    try:
        files = form.files
    except Exception as e:
        files = 'test.raw'
        logger.exception(f"Exception: {e}")
    args = {}
    args = await token_variables(args)
    formats = form.format
    files += f".{formats}"
    file_location = f"{TMP_SOUND}/{files}"
    args['output'] = file_location
    args['output'] = args['output'].replace('//', '/')
    text = form.Input_text
    args['text'] = text
    logger.info(f"files: {files}")
    logger.info(f"formats: {formats}")
    logger.info(f"text: {text}")
    if formats == 'raw':
        data_ = dict(text=text, lang='ru-RU', format='lpcm', sampleRateHertz=48000, voice='filipp')
        params = None
        params = {"ssml": f"<speak>{args['text']}</speak>"}
    else:
        params = {"ssml": f"<speak>{args['text']}</speak>"}
        data_ = None
    try:
        spech = SyntezeYndex(args['folder_id'], args['token'], args['text'])
        logger.info(f"params: {params}, data_: {data_}")
        with open(args['output'], "wb") as f:
            if formats == 'raw':
                for audio_content in spech.synthesize_raw(data_):
                    f.write(audio_content)
            elif formats == 'ogg':
                for audio_content in spech.synthesize_ogg(params, data_):
                    f.write(audio_content)
    except Exception as e:
        logger.exception(f"Exception: {e}")
    finally:
        if formats == 'raw':
            logger.info(f"if formats == 'raw': {formats}")
            await convert_to_wav(args['output'])
        elif formats == 'ogg':
            await convert_to_wav(args['output'])
            logger.info(f"if formats == 'ogg': {formats}")
    return text, formats
    '''

    try:
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
    await create_audio_files(args)

    return args

"""
Перенес логику в отдельный файл
"""
