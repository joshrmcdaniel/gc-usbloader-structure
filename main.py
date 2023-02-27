import os


from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from sys import platform


import pandas as pd
import requests


from dotenv import load_dotenv
from loguru import logger
# from lxml import etree


BASE_URL = "https://art.gametdb.com/wii/"
IMAGE_URL = f"{BASE_URL}{{img_type}}/{{region}}/{{game_id}}.png"
IMAGE_TYPES = ('disk', 'cover', 'cover3D', 'coverfull')


IMAGE_TYPE_PATH = {
    'disk': 'Disc',
    'cover': '2D',
    'cover3D': '3D',
    'coverfull': 'Full'
}

REGION_MAP = {
    'USA/NTSC-U': 'US',
    'EUR/PAL': 'EU',
    'JAP/NTSC-J': 'JA'
}


def main():
    df = pd.read_csv(GAME_CSV, delimiter='\t')
    results = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        for _, row in filter(lambda x: os.path.exists(x[1].path), df.iterrows()):
            results.append(executor.submit(run, row))
    
        for future in as_completed(results):
            print(f'Completed {future.result()}')


def run(ser: pd.Series) -> str:
    move_file(ser.title, ser.gameid, ser.path)
    get_images(ser.gameid, ser.region)
    return ser.title


def move_file(game: str, game_id: str, path: str):
    if not os.path.exists(path):
        logger.info('{} path (game: {}) does not exists, not moving', path, game)
        return
    game = _remove_ilgl_chars(game)
    dir_path = os.path.join(DEST_PATH, f'{game} [{game_id}]')
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    game_path = os.path.join(dir_path, 'game.iso')
    try:
        os.rename(path, game_path)
    except FileExistsError:
        logger.info('{} exists already, skipping')


def get_images(game_id: str, game_region: str):
    if game_region == 'UNK':
        logger.info('Game ID {} has unknown region, skipping', game_id)
        return
    region = REGION_MAP[game_region]
    for img_type in IMAGE_TYPES:
        url = IMAGE_URL.format(img_type=img_type, region=region, game_id=game_id)
        img_path = os.path.join(BASE_IMAGE_PATH, IMAGE_TYPE_PATH[img_type])
        if os.path.exists(img_path):
            logger.info('Image path exists for game ID {}, skipping', game_id)
        r = requests.get(url)
        if r.status_code != 200:
            logger.info('No {} image for game ID {}', img_type, game_id)
            logger.debug('URL requested: {} Status code: {}', url, r.status_code)
            continue
        if not os.path.exists(img_path):
            os.mkdir(img_path)
        with open(os.path.join(img_path, f'{game_id}.png'), 'wb') as f:
            f.write(r.content)
        

def _remove_ilgl_chars(s: str) -> str:
    repl = ' - '
    if platform == 'linux':
        illegal_chars = '/'
    elif platform == 'win32':
        illegal_chars = '<>:"/\\|?*'
    elif platform == 'darwin':
        illegal_chars =':/\x00'
    for c in illegal_chars:
        s = s.replace(c, repl)
    
    return s


def _get_game_table():
    if os.path.exists('tdb.csv'):
        return pd.read_csv('tdb.csv')
    #  TODO: implement xml -> csv or json
    raise NotImplementedError('dynamic game finding not implemented, please specify a tsv created in gcbm')
    if os.path.exists('tdb.xml'):
        tdb = etree.parse('tdb.xml')
    tdb = _get_wii_tbd()
    from code import interact
    interact(banner='', local=locals())


def _get_wii_tbd():
    raise NotImplementedError('dynamic game finding not implemented, please specify a tsv created in gcbm')

    import lxml
    url = 'https://www.gametdb.com/wiitdb.zip'
    #  websites auth is user-agent, lol
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46'
    }
    r = requests.get(url, headers=headers, allow_redirects=True)
    if r.status_code != 200:
        logger.critical('Error occured during wiitdb.zip download')
        logger.info('Status code: {}', r.status_code)
        from code import interact
        interact(banner='', local=locals())
        raise RuntimeError('Error occured during wiitdb.zip download')
    from zipfile import ZipFile
    with ZipFile(BytesIO(r.content)) as tdb_zip:
        with tdb_zip.open('wiitdb.xml') as tdb:
            with open('tdb.xml', 'wb') as f:
                f.write(tdb.read())
            tdb.seek(0)
            tdb_xml = etree.parse(tdb)

    return tdb_xml


if __name__ == '__main__':
    _get_game_table()
    load_dotenv()
    ISO_PATH = os.environ.get('ISO_PATH')
    DEST_PATH = os.environ.get('DEST_PATH')
    if not os.path.exists(DEST_PATH):
        raise RuntimeError('Destination path does not exist')

    BASE_IMAGE_PATH = os.environ.get('IMAGE_PATH')
    if BASE_IMAGE_PATH is None:
        raise RuntimeError('Image destination path not specified')

    GAME_CSV = os.environ.get('GAME_CSV')
    if not GAME_CSV:
        if not ISO_PATH:
            raise RuntimeError('No game path specified and no ISO path specified')
        GAME_CSV = _get_game_table()
    
    main()
