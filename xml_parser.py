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
            "startDateIsSet": {
                "$": "1"
            },
            "startDate": {
                "$": template["beginDateTime"].split(" ")[0]
            },
            "endDateIsSet": {
                "$": "1"
            },
            "endDate": {
                "$": template["endTime"].split(" ")[0]
            }
        }
    }
    if len(template["beginDateTime"].split(" ")) > 1 and template["beginDateTime"].split(" ")[1] != "00:00":
        js["task"]["startTimeIsSet"] = {"$": "1"}
        js["task"]["startTime"] = {"$": template["beginDateTime"].split(" ")[1]}
    if len(template["endTime"].split(" ")) > 1 and template["endTime"].split(" ")[1] != "00:00":
        js["task"]["endTimeIsSet"] = {"$": "1"}
        js["task"]["endTime"] = {"$": template["endTime"].split(" ")[1]}
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
    pprint(js)
    resp = get_response(bf.etree(js, root=Element("request", method="task.add")))
    id = resp["response"]["task"]["id"]["$"]
    return f"https://k3.planfix.ru/?action=planfix&task={id}"


def get_contact_list(uid):
    js = {
        "account": "k3",
        "sid": auth(get_email(), get_passwd()),
        "pageCurrent": {
            "$": "1"
        },
        "pageSize": {
            "$": "100"
        },
        "target": {
            "$": "company"
        }
    }
    resp = get_response(bf.etree(js, root=Element("request", method="contact.getList")))
    clients = resp["response"]["contacts"]["contact"]
    pprint(clients)
    res = []
    for client in clients:
        if client["canBeClient"]["$"]:
            t = {"id": client["id"]["$"], "name": client["name"]["$"],
                 "email": client["email"]["$"] if client["email"] else "",
                 "site": client["site"]["$"] if client["site"] else "", "phones": {}}
            if "phone" in client["phones"] and "number" in client["phones"]["phone"]:
                if "$" in client["phones"]["phone"]["number"]:
                    ttt = ""
                    if "typeName" in client["phones"]["phone"] and "$" in client["phones"]["phone"]["typeName"]:
                        ttt = client["phones"]["phone"]["typeName"]["$"]
                    t["phones"][client["phones"]["phone"]["number"]["$"]] = {
                        "type": ttt
                    }
            else:
                for phone in client["phones"]["phone"]:
                    if phone["number"]:
                        ttt = ""
                        if "typeName" in phone and "$" in phone["typeName"]:
                            ttt = phone["typeName"]["$"]
                        t["phones"][phone["number"]["$"]] = {
                            "type": ttt
                        }
            t["description"] = client["description"]["$"] if client["description"] else ""
            res.append(t)
    dump(res, open(f'contacts_{uid}.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


#get_contact_list("111111")

