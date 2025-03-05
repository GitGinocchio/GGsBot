from cachetools import LRUCache
import json
import os

class _JsonDict(dict):
    def __init__(self, data : dict, file : 'JsonFile'):
        super().__init__(data)
        self.file = file

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.file.autosave: self.file.save()

    def __delitem__(self, key):
        super().__delitem__(key)
        if self.file.autosave: self.file.save()
    
    def pop(self, key):
        item = self[key]
        super().__delitem__(key)
        if self.file.autosave: self.file.save()
        return item
    
    def copy(self):
        return super().copy()

class _JsonList(list):
    def __init__(self, data : list, file : 'JsonFile'):
        super().__init__(data)
        self.file = file

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        if self.file.autosave: self.file.save()

    def __delitem__(self, index):
        super().__delitem__(index)
        if self.file.autosave: self.file.save()
    
    def append(self, value):
        super().append(value)
        if self.file.autosave: self.file.save()
    
    def remove(self, value):
        super().remove(value)
        if self.file.autosave: self.file.save()
        
class CustomDecoder(json.JSONDecoder):
    def __init__(self, file : 'JsonFile'):
        super().__init__()
        self.file = file

    def _remove_comments(self, s):
        longcomment = False
        lines = []
        for line in s.split('\n'):
            line = str(line.strip())
            doubleslash = line.find('//')
            slashastrsk = line.find('/*')
            astrskslash = line.find('*/')

            # Commenti singoli // 
            if line.count('\"',0,doubleslash) % 2 == 0 and doubleslash >= 0:
                line = line[:doubleslash]

            #Fine commento lungo */
            if longcomment:
                if astrskslash >= 0:
                    longcomment = False
                    line = line[astrskslash+2:]
                else: continue

            #Inizio commento lungo /*
            if line.count('\"',0,slashastrsk) % 2 == 0 and slashastrsk >= 0:
                if astrskslash < 0: longcomment = True
                line = line[:slashastrsk]

            if line != '': lines.append(line)
        return '\n'.join(lines)
            
    def decode(self, s):
        if self.file.commented:
            s = self._remove_comments(s)
        try:
            obj = dict(super().decode(s))
        except json.decoder.JSONDecodeError as e:
            print(e)
        else:
            for key,value in obj.items():
                if isinstance(value, dict):
                    obj[key] = _JsonDict(value,self.file)
                elif isinstance(value, list):
                    obj[key] = _JsonList(value,self.file)
                else:
                    obj[key] = value
            return obj

cache = LRUCache(maxsize=100)

class JsonFile(dict):
    def __init__(self, fp : str,*, indent : int = '\t', encoding : str = 'utf-8', autosave : bool = True, commented : bool = False, force_load : bool = False):
        """

        ---

        Subclass of dict for loading or creating JSON files.

        !! Warning !! 
        Not all dict methods supports autosave feature.

        ---
        
        :fp: the file path of the json file.
        :indent: the indentation of the file. default to '\\t'
        :encoding: the encoding of the file. default to 'utf-8'.
        :autosave: If True, the file is automatically saved after each change.
        :commented: Specify if there are comments in the json file
        :force_load: Force to load the file.
        """
        if not fp.endswith('.json') or not fp.endswith('.jsonc'): raise ValueError('fp must be a json file and end with ".json" or ".jsonc" (JSON with comments)')
        self.commented = True if fp.endswith('.jsonc') else commented
        self.encoding = encoding
        self.autosave = autosave
        self.indent = indent
        self.fp = os.path.realpath(os.path.normpath(fp))

        if self.fp not in cache or force_load:
            if os.path.exists(self.fp):
                #print(f"File '{self.fp}' not saved in cache, loading it...")
                with open(self.fp,encoding=encoding) as jsf:
                    fileobj = json.load(jsf,cls=CustomDecoder,file=self)
                    cache[self.fp] = _JsonDict(fileobj, self)
                    super().__init__(cache[self.fp])
                    #print(F"Updated cached JsonFiles list: {[key for key, _ in cache.items()]}")
            else:
                cache[self.fp] = _JsonDict({},self)
                super().__init__(cache[self.fp])
        else:
            #print(f"File '{self.fp}' already saved in cache")
            super().__init__(cache[self.fp])

    def __getitem__(self, key) -> _JsonDict | dict:
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if isinstance(value,dict):
            data = _JsonDict(value, self)
        elif isinstance(value,list):
            data = _JsonList(value, self)
        else: 
            data = value

        self.update({key : data})
        
        if self.autosave: self.save()

    def __delitem__(self, key):
        if key in dict(self.items()):
            self.pop(key)
            if self.autosave: self.save()
        else:
            raise KeyError(f"Key '{key}' not found in '{self.fp}'.")
    
    def __iter__(self):
        return dict.__iter__(self)

    def copy(self):
        return JsonFile(self.fp,indent=self.indent,encoding=self.encoding,autosave=self.autosave)

    def save(self, fp : str = None):
        cache[self.fp] = self
        with open(self.fp if fp is None else fp,'w',encoding=self.encoding) as jsf: json.dump(self,jsf,indent=self.indent)