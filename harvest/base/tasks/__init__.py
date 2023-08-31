class TaskChain(list):
    def __init__(self):
        super().__init__()


class Task:
    plugins = []

    def __init__(self):
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)
        pass
