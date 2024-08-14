import os
from discord.ext import commands


file_types = [".webm", "webm.part", ".part", ".mp4.part", ".m4a"]

def delete_music(dictionary: dict):
    for file in os.listdir(path='.'):
        file_type = os.path.splitext(str(file))[1]
        if file_type in file_types:
            os.remove(file)

    dictionary.clear()
