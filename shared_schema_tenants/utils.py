
def import_class(class_path_str):
    last_dot_pos = class_path_str.rfind(".")
    class_name = class_path_str[last_dot_pos + 1:len(class_path_str)]
    class_module = __import__(
        class_path_str[0:last_dot_pos],
        globals(), locals(),
        [class_name]
    )
    return getattr(class_module, class_name)
