import json

class Config():
    file = ""
    data = ""

    def __init__(self, file: str):
        self.file = file
        self.loadfile()

    def loadfile(self):
        with open(file=self.file) as f:
            self.data = json.load(f)

    def savefile(self):
        with open(file=self.file, mode='w') as json_file:
            json.dump(self.data, json_file, indent=4, sort_keys=True)