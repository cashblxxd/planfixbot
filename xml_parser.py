from lxml.html import Element, tostring
from xml.etree.ElementTree import fromstring
from xmljson import badgerfish as bf
from requests import post
from pprint import pprint
from json import dump
from database import get_email, get_passwd, get_pf_auth_token
from datetime import datetime


def get_response(xml_string):
    s = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + tostring(xml_string).decode("utf-8")
    print(s)
    resp = post("https://apiru.planfix.ru/xml", data=s, headers={'Accept': 'application/xml', 'Content-Type': 'application/xml'},
                auth=(get_pf_auth_token(), '')).text
    #print(resp)
    p = fromstring(resp)
    #print(p)
    jr = bf.data(p)
    #pprint(jr)
    return jr


def auth(email, passw):
    return get_response(bf.etree({
        "account": "k3",
        "login": email,
        "password": passw
    }, root=Element('request', method="auth.login")))["response"]["sid"]["$"]


def get_template_list(uid):
    res = []
    try:
        for j in range(1, 11):
            resp = get_response(bf.etree({
                "account": "k3",
                "sid": auth(get_email(), get_passwd()),
                "user": {
                    "id": "3301968"
                },
                "target": "template",
                "pageSize": {
                    "$": "100"
                },
                "pageCurrent": {
                    "$": str(j)
                }
            }, root=Element("request", method="task.getList")))
            for c in resp["response"]["tasks"]["task"]:
                t = {"id": c["id"]["$"], "title": c["title"]["$"],
                     "description": c["description"]["$"] if c["description"] else "",
                     "owner": "3332912", "client": "", "worker": ""}
                if c["client"]["id"]["$"] != 0:
                    t["client"] = str(c["client"]["id"]["$"]) + " " + c["client"]["name"]["$"]
                if c["workers"]:
                    s = []
                    if "users" in c["workers"]:
                        if type(c["workers"]["users"]["user"]) != type([]):
                            t["worker"] = str(c["workers"]["users"]["user"]["id"]["$"]) + " " + \
                                          c["workers"]["users"]["user"]["name"]["$"]
                        else:
                            for i in c["workers"]["users"]["user"]:
                                try:
                                    s.append(str(c["workers"]["users"]["user"][i]["id"]["$"]) + " " + str(
                                        c["workers"]["users"]["user"][i]["name"]["$"]))
                                except Exception as e:
                                    try:
                                        s.append(str(i["id"]["$"]) + " " + i["name"]["$"])
                                    except Exception as e:
                                        print(i)
                            t["worker"] = "\n".join(s)
                if "beginDateTime" in t:
                    t["beginDateTime"] = c["beginDateTime"]["$"]
                if "endTime" in t:
                    t["endTime"] = c["endTime"]["$"]
                res.append(t)
    except Exception as e:
        print(e)
    dump(res, open(f'templates_{uid}.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


def send_task(template):
    print("TEMPLATE")
    pprint(template)
    js = {
        "account": "k3",
        "sid": auth(get_email(), get_passwd()),
        "task": {}
    }
    if "id" in template and template["id"]:
        js["task"] = {
            "template": {
                "$": str(template["id"])
            },
            "title": {
                "$": template["title"]
            },
            "description": {
                "$": str(datetime.now()).split(".")[0] + "\n\n" + template["description"]
            },
            "owner": {
                "id": {
                    "$": "3382098"
                }
            },
            "client": {
                "id": {
                    "$": template["client"]
                }
            },
            "endDateIsSet": {
                "$": "1"
            },
            "endDate": {
                "$": template["endTime"].split(" ")[0]
            }
        }
    else:
        js["task"] = {
            "title": {
                "$": template["title"]
            },
            "description": {
                "$": template["description"]
            },
            "owner": {
                "id": {
                    "$": "3382098"
                }
            },
            "client": {
                "id": {
                    "$": template["client"]
                }
            },
            "endDateIsSet": {
                "$": "1"
            },
            "endDate": {
                "$": template["endTime"].split(" ")[0]
            }
        }
    if not template["beginDateTime"]:
        js["task"]["startDateIsSet"] = {
            "$": "0"
        }
    else:
        js["task"]["startDateIsSet"] = {
            "$": "1"
        }
        js["task"]["startDate"] = {
            "$": template["beginDateTime"].split(" ")[0]
        }
    if len(template["beginDateTime"].split(" ")) > 1 and template["beginDateTime"].split(" ")[1] != "00:00":
        js["task"]["startTimeIsSet"] = {"$": "1"}
        js["task"]["startTime"] = {"$": template["beginDateTime"].split(" ")[1]}
    if len(template["endTime"].split(" ")) > 1 and template["endTime"].split(" ")[1] != "00:00":
        js["task"]["endTimeIsSet"] = {"$": "1"}
        js["task"]["endTime"] = {"$": template["endTime"].split(" ")[1]}
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
    #pprint(js)
    resp = get_response(bf.etree(js, root=Element("request", method="task.add")))
    #pprint(resp)
    id = resp["response"]["task"]["general"]["$"]
    return f"https://k3.planfix.ru/task/{id}"


def get_contact_list(uid):
    res = []
    try:
        for j in range(1, 11):
            js = {
                "account": "k3",
                "sid": auth(get_email(), get_passwd()),
                "target": {
                    "$": "company"
                },
                "pageCurrent": {
                    "$": str(j)
                },
                "pageSize": {
                    "$": "100"
                }
            }
            resp = get_response(bf.etree(js, root=Element("request", method="contact.getList")))
            clients = resp["response"]["contacts"]["contact"]
            print(j)
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
                    t["description"] = client["description"]["$"] if client["description"] else ""
                    res.append(t)
            print(j)
    except Exception as e:
        print(e)
    dump(res, open(f'contacts_{uid}.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


def get_fillist(uid):
    js = {
        "account": "k3",
        "sid": auth(get_email(), get_passwd())
    }
    resp = get_response(bf.etree(js, root=Element("request", method="contact.getFilterList")))
    pprint(resp)


def get_user_list(uid):
    res = []
    try:
        for j in range(1, 11):
            js = {
                "account": "k3",
                "sid": auth(get_email(), get_passwd()),
                "pageSize": {
                    "$": "100"
                },
                "pageCurrent": {
                    "$": str(j)
                }
            }
            resp = get_response(bf.etree(js, root=Element("request", method="user.getList")))
            pprint(resp)
            res.append(resp)
    except Exception as e:
        print(e)
    dump(res, open(f'users_{uid}.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


def get_contact(uid):
    js = {
        "account": "k3",
        "sid": auth(get_email(), get_passwd()),
        "contact": {
            "id": {
                "$": "3332912"
            }
        }
    }
    resp = get_response(bf.etree(js, root=Element("request", method="contact.get")))
    #pprint(resp)
#get_contact_list("111111")
#get_fillist("111")
#get_user_list("1")
#get_contact("1")
