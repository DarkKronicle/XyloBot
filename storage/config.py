from storage.json_reader import *


class ConfigData:
    questions = JSONReader("data/questions.json")
    join = JSONReader("data/join.json")
    lober = JSONReader("data/lober.json")

    def reload(self):
        self.questions.loadfile()
        self.join.loadfile()
        self.lober.loadfile()
