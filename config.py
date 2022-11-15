import os

class Config():

    @staticmethod
    def write(key, value):
        lines = []
        write = False
        if os.path.exists("config.ini"):
            with open("config.ini", "r") as f:
                lines = f.readlines()
        data = "{key}:={value}\n".format(key=key, value=value)
        for idx, content in enumerate(lines):
            if key in content:
                lines[idx] = data
                write = True
        if write == False:
            lines.append(data)
        with open("config.ini", "w+") as f:   
            for line in lines:
                f.write(line)

    @staticmethod
    def extract(key):
        if not os.path.exists("config.ini"):
            raise Exception("[CONFIG] Unable to find config.ini")
        with open("config.ini", "r") as f:
            value = None
            lines = f.readlines()
            for idx, content in enumerate(lines):
                if key in content:
                    data = content.rstrip("\n").split(":=")
                    value = data[1]
            return value
            