import json

class json_utils:
    def __init__(self,fp: str = None,*,indent: int = 3):
        self.fp = fp
        self.indent = indent
    
    def content(self):
        with open(self.fp, 'r') as json_file:
            content = json.load(json_file)
            return content

    def save_to_file(self,content,indent: int = 3):
        with open(self.fp, 'w') as json_file:
            json.dump(content,json_file,indent=indent)