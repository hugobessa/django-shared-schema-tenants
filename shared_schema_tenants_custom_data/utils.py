def compose_list(funcs):
    def inner(data, funcs=funcs):
        return inner(funcs[-1](data), funcs[:-1]) if funcs else data
    return inner
