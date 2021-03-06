import ast
import base64
import json
import re

import logger
import requests
from bs4 import BeautifulSoup
from pyDes import *
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from songModel import songModel

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_soup(self, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'lxml')
        return soup
    else:
        return None


def getPlayList(self, playlist_url):
    soup = self.get_soup(playlist_url)
    playlist_id = soup.select(".flip-layout")[0]["data-listid"]
    songs_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?listid={0}&_format=json&__call=playlist.getDetails'.format(playlist_id),
        verify=False)
    if respone.status_code == 200:
        songs_json = list(filter(lambda x: x.startswith("{"), respone.text.splitlines()))[0]
        songs_json = json.loads(songs_json)
    return self.make_json(songs_json)


def setDecipher(self):
    return des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)


def getAlbum(self, album_url):
    soup = self.get_soup(album_url)
    getAlbumID = soup.select(".play")[0]["onclick"]
    albumId = ast.literal_eval(re.search("\[(.*?)\]", getAlbumID).group())[1]
    songs_json = []
    print('https://www.saavn.com/api.php?_format=json&__call=content.getAlbumDetails&albumid={0}'.format(albumId))
    respone = requests.get(
        'https://www.saavn.com/api.php?_format=json&__call=content.getAlbumDetails&albumid={0}'.format(albumId),
        verify=False)
    if respone.status_code == 200:
        songs_json = list(filter(lambda x: x.startswith("{"), respone.text.splitlines()))[0]
        songs_json = json.loads(songs_json)
    return self.make_json(songs_json)


def make_json(self, json_data):
    des_cipher = self.setDecipher()
    lst = []
    for song in json_data['songs']:
        try:
            enc_url = base64.b64decode(song['encrypted_media_url'].strip())
            dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
            dec_url = dec_url.replace('_96.mp4', '_320.mp4')
        except Exception as e:
            dec_url = None
            logger.error('Download Error' + str(e))

        title = song['song']
        album = song['album']
        year = song['year']
        url = dec_url
        release_date = song['release_date']
        image = song['image']
        artist = song['primary_artists']
        genre = ', '.join([hashtags['title'].replace('#','') for hashtags in song['hashtags'] if hashtags['type'] == 'channel'])
        song = songModel( title, album, year, url, release_date, image, artist, genre)
        lst.append(song)

    return lst
