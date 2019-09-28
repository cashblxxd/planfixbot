from json import load
from pprint import pprint


def get_template(template_id, uid):
    with open("templates_" + uid + ".json") as f:
        for i in load(f):
            if template_id == str(i["id"]):
                return i


def get_client(client_id, uid):
    with open("clients_" + uid + ".json") as f:
        for i in load(f):
            if client_id == str(i["id"]):
                return i


def get_next(template):
    pprint(template)
    if not template["title"]:
        return "title"
    if not template["description"]:
        return "description"
    if not template["beginDateTime"]:
        return "beginDateTime"
    if not template["endTime"]:
        return "endTime"
    if not template["client"]:
        return "client"
    return "done"

