def ser_list(tlist, level=0):
    rval = "[\n"
    for item in tlist:
        rval += ser_struct(item) + ",\n"
    rval += "]"
    return rval


def ser_dict(tdict, level=0):
    rval = "{\n"
    size = len(tdict)
    count = 0
    for key, value in tdict.iteritems():
        count += 1
        rval += "    " * (level + 1) + "\"" + key + "\": " + ser_struct(value, level + 1)
        if count < size:
            rval += ","
        rval += "\n"
    rval += level * "    " + "}"
    return rval


def ser_struct(value, level=0):
    if isinstance(value, list):
        return ser_list(value, level)
    elif isinstance(value, dict):
        return ser_dict(value, level)
    elif isinstance(value, basestring):
        return '"{0}"'.format(value)
    else:
        return str(value)


def print_struct(value):
    print ser_struct(value)
