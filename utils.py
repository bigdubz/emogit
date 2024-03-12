import os
from discord.ext import commands


def delete_music(dictionary: dict):
    for file in os.listdir(path='.'):
        split_tup = os.path.splitext(str(file))
        if split_tup[1] == ".webm" or split_tup == ".webm.part" or split_tup == ".part" or split_tup == ".mp4.part":
            os.remove(file)

    dictionary.clear()
