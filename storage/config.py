from storage.json_reader import *


class ConfigData:
    questions = JSONReader("data/questions.json")
    join = JSONReader("data/join.json")
    idstorage = JSONReader("data/idstorage.json")
    rolestorage = JSONReader("data/roles.json")
    defaultsettings = JSONReader("data/guildsettings.json")
    lober = JSONReader("data/lober.json")

    def reload(self):
        self.questions.loadfile()
        self.join.loadfile()
        self.autoreactions.loadfile()
        self.idstorage.loadfile()
        self.rolestorage.loadfile()
        self.defaultsettings.loadfile()
        self.lober.loadfile()
