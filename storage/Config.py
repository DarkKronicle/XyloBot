from storage.JSONReader import *


class ConfigData:
    questions = JSONReader("data/questions.json")
    join = JSONReader("data/join.json")
    autoreactions = JSONReader("data/autotext.json")
    idstorage = JSONReader("data/idstorage.json")
    rolestorage = JSONReader("data/roles.json")

    def reload(self):
        self.questions.loadfile()
        self.join.loadfile()
        self.autoreactions.loadfile()
        self.idstorage.loadfile()
        self.rolestorage.loadfile()
