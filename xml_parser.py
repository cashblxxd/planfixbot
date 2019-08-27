from lxml.html import Element, tostring
from xml.etree.ElementTree import fromstring
from xmljson import badgerfish as bf
from requests import post
from pprint import pprint
from json import dump
from database import get_email, get_passwd, get_pf_auth_token


def get_response(xml_string):
    s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + tostring(xml_string).decode("utf-8")
    print(s)
    resp = post("https://apiru.planfix.ru/xml", data=s, headers={'Accept': 'application/xml', 'Content-Type': 'application/xml'},
                auth=(get_pf_auth_token(), '')).text
    print(resp)
    p = fromstring(resp)
    print(p)
    jr = bf.data(p)
    pprint(jr)
    return jr


def auth(email, passw):
    return get_response(bf.etree({
        "account": "k3",
        "login": email,
        "password": passw
    }, root=Element('request', method="auth.login")))["response"]["sid"]["$"]


def get_template_list(uid):
    resp = get_response(bf.etree({
        "account": "k3",
        "sid": auth(get_email(), get_passwd()),
        "user": {
            "id": "3301968"
        },
        "target": "template"
    }, root=Element("request", method="task.getList")))
    res = []
    for c in resp["response"]["tasks"]["task"]:
        t = {"id": c["id"]["$"], "title": c["title"]["$"],
             "description": c["description"]["$"] if c["description"] else "",
             "owner": str(c["owner"]["id"]["$"]) + " " + c["owner"]["name"]["$"], "client": "", "worker": ""}
        if c["client"]["id"]["$"] != 0:
            t["client"] = str(c["client"]["id"]["$"]) + " " + c["client"]["name"]["$"]
        if c["workers"]:
            s = []
            if type(c["workers"]["users"]["user"]) != type([]):
                t["worker"] = str(c["workers"]["users"]["user"]["id"]["$"]) + " " + c["workers"]["users"]["user"]["name"]["$"]
            else:
                for i in c["workers"]["users"]["user"]:
                    s.append(str(c["workers"]["users"]["user"][i]["id"]["$"]) + " " + str(c["workers"]["users"]["user"][i]["name"]["$"]))
                t["worker"] = "\n".join(s)
        t["beginDateTime"] = c["beginDateTime"]["$"]
        t["endTime"] = c["endTime"]["$"]
        res.append(t)
    pprint(res)
    dump(res, open(f'templates_{uid}.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


def send_task(template):
    js = {
        "account": "k3",
        "sid": auth(get_email(), get_passwd()),
        "task": {
            "title": {
                "$": template["title"]
            },
            "description": {
                "$": template["description"]
            },
            "beginDateTime": {
                "$": template["beginDateTime"]
            },
            "endTime": {
                "$": template["endTime"]
            }
        }
    }
    if template["owner"]:
        js["task"]["owner"] = {
                "id": {
                    "$": template["owner"].split(" ", 1)[0]
                }
            }
    if template["id"]:
        js["task"]["template"] = {
            "$": template["id"]
        }
    if template["client"]:
        js["task"]["client"] = {
            "id": {
                "$": template["client"].split(" ", 1)[0]
            }
        }
    if template["worker"]:
        a = []
        for i in template["worker"].split():
            if i.isdigit() and len(i) > 6:
                a.append(i)
        js["task"]["workers"] = {
            "users": [
                {
                    "id": {"$": i}
                } for i in a
            ]
        }
    resp = get_response(bf.etree(js, root=Element("request", method="task.add")))
    id = resp["response"]["task"]["id"]["$"]
    return f"https://k3.planfix.ru/?action=planfix&task={id}"
