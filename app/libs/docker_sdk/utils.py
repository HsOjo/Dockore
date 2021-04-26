def dict_to_lower(obj):
    import re
    if isinstance(obj, dict):
        r = {}
        for k, v in obj.items():
            k = re.sub('[A-Z]+', lambda x: '_%s' % x.group().lower(), k).lstrip('_')
            r[k] = dict_to_lower(v)

        return r
    elif isinstance(obj, list):
        r = []
        for i in obj:
            r.append(dict_to_lower(i))

        return r
    else:
        return obj


def remove_empty_obj(obj):
    if isinstance(obj, list):
        r = []
        for i in obj:
            i = remove_empty_obj(i)
            if i or i is False:
                r.append(i)
        return r
    elif isinstance(obj, dict):
        r = {}
        for k, v in obj.items():
            v = remove_empty_obj(v)
            if v or v is False:
                r[k] = v
        return r
    else:
        return obj
