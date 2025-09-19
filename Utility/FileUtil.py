import  json

def WriteJson(path, json_object):
    with open(path, 'w') as f:
        json.dump(json_object, f, indent=4)


def ReadJson(path):
    with open(path, 'r') as f:
        return json.load(f)
