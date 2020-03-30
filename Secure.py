import base64
import hashlib
import json
import os
from pathlib import Path

from Crypto import Random
from Crypto.Cipher import AES

import bot_util as bt


class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = key  # hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


def load():
    """Loads the token from the file

    Returns:
        str: The string of the token
    """
    cipher = AESCipher(calculate_hash())
    with open('token.key', 'rb') as f:
        data = f.read()

    decrypted = cipher.decrypt(data)
    decrypted = decrypted.replace('\t', '\n')
    dictionary = json.loads(decrypted)
    token = dictionary.get('token')
    bt.INFO(f'Got bot token: {token}')
    return token


def calculate_hash():
    """Calculates the hash based from the text in a file

    Returns:
        str: The filename of where the token is stored
    """
    file = 'hashed.txt'
    file_dir = os.getcwd()
    while not os.path.isfile(str(file_dir) + '\\' + file):
        file_dir = Path(file_dir).parent

    file = str(file_dir) + '\\' + file

    with open(file, 'r') as f:
        content = f.readlines()

    hash1 = ""

    for line in content:
        string = hashlib.sha256(line.encode())
        hash1 += string.hexdigest()

    hashed = hashlib.sha256(hash1.encode())
    hashed = hashed.digest()
    return hashed


def load_data(file):
    """Loads a json file into a dictionary
    
    Args:
        file (str): The file to be loaded
    
    Returns:
        dict: The dictionary of the json file
    """
    if '.json' not in file:
        file += '.json'
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        return data
    except Exception:
        bt.ERROR(f'Unable to find file: {file}')
        return None


def save_data(data):
    """Saves the given data into a json file called data
    
    Args:
        data (dict): The data to be saved
    """
    with open('data.json', 'w') as f:
        json.dump(data, f)
