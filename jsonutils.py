import os,json



class jsonfile:
    def __init__(self,fp : str = None,*,indent : int = 3,encoding : str = 'utf-8',autosave : bool = True):
        assert fp.endswith('.json'),'fp must be a json file and end with ".json"'
        self.fp = fp
        self.indent = indent
        self.encoding = encoding
        self.autosave = autosave
        if os.path.exists(self.fp):
            with open(self.fp, 'r', encoding=encoding) as jsf: self.content = json.load(jsf)
        else: 
            self.content = {}
            if self.autosave: self.save()

    def __str__(self):
        return str(self.content)

    def __len__(self):
        return len(self.content)

    def __contains__(self, __k):
        return __k in self.content

    def __getitem__(self, __k):
        if __k in self.content: return self.content[__k]
        else: raise KeyError(f"Key '{__k}' not found in JSON data.")

    def __setitem__(self, __k, __v):
        self.content[__k] = __v
        if self.autosave:self.save()

    def __delitem__(self, __k):
        if __k in self.content:
            del self.content[__k]
            if self.autosave:self.save()
        else:
            raise KeyError(f"Key '{__k}' not found in '{self.fp}'.")

    def __iter__(self):
        return iter(self.content)

    def __next__(self):
        raise StopIteration

    def keys(self):
        return self.content.keys()

    def set(self, keys : list[str], value):
        current = self.content
        for key in keys[:-1]:
            if isinstance(current, dict):
                current = current.setdefault(key, {})
            elif isinstance(current, list):
                try:
                    key = int(key)
                    current = current[key]
                except (ValueError, IndexError):
                    return
        if isinstance(current, dict):
            current[keys[-1]] = value
            if self.autosave:
                self.save()
        elif isinstance(current, list):
            try:
                key = int(keys[-1])
                current[key] = value
                if self.autosave:
                    self.save()
            except (ValueError, IndexError):
                pass

    def clear(self):
        self.content = {}
        if self.autosave: self.save()

    def loads(data : str | bytes):
        return json.loads(data)

    def dumps(data : dict):
        return json.dumps(data)

    def save(self,content : dict = None):
        with open(self.fp, 'w',encoding=self.encoding) as jsf: json.dump(content if content is not None else self.content,jsf,indent=self.indent,ensure_ascii=True)
