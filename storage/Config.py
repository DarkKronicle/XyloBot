from storage.JSONReader import *


class ConfigData:
    questions = JSONReader("data/questions.json")
    join = JSONReader("data/join.json")
    autoreactions = JSONReader("data/autoreaction.json")
    idstorage = JSONReader("data/idstorage.json")
