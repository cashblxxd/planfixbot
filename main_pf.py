# coding=utf-8
import logging
from pprint import pprint
from uuid import uuid4
from json import load
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackQueryHandler
from telegram.utils.helpers import escape_markdown
from telegram.ext import InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegramcalendar
import datetime
import calendar
from json import load, dump, dumps
from time import sleep
from xml_parser import get_template_list, auth, send_task, get_contact_list
from stuff import get_template, get_next
from database import get_token


TOKEN = get_token()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


'''
context.user_data[update.callback_query.from_user.id][context.user_data[update.callback_query.from_user.id]["id"]]['state'] = 'done'
update.callback_query.edit_message_text('Рассылка успешно создана! Вы можете посмотреть её в /messages')
dump(context.user_data, open('dumpp.json', 'w+', encoding='utf-8'), ensure_ascii=False)
'''


def add_task(update, context, type):
    if type == "message":
        uid = str(update.message.chat_id)
    else:
        uid = str(update.callback_query.from_user.id)
    return send_task(context.user_data[uid]["template"])


def inlinequery(update, context):
    query = update.inline_query.query.lower()
    context.user_data = commit(update, context, "query")
    uid = str(update.inline_query.from_user.id)
    print(query, uid, context.user_data[uid])
    if len(''.join(query.split())) < 1:
        update.inline_query.answer([
            InlineQueryResultArticle(id=uuid4(), title="Search",
                                     input_message_content=InputTextMessageContent("Searching..."))
        ])
        return
    if context.user_data[uid]["state"] == "pending":
        update.inline_query.answer([
            InlineQueryResultArticle(id=uuid4(), title="Not in context",
                                     input_message_content=InputTextMessageContent("Sorry, I can't make a search yet."))
        ])
        return
    elif context.user_data[uid]["state"] == "client":
        #get_contact_list(uid)
        results = []
        with open("contacts_" + uid + ".json", "r") as f:
            for i in load(f):
                if query in i["name"].lower() or query in i["email"].lower() or query in i["description"].lower() or query in i["site"].lower():
                    desc = i["name"] + " " + i["description"] + " " + i["email"]
                    if not desc or desc == "  ":
                        desc = "No description.:("
                    # print(desc)
                    results.append(InlineQueryResultArticle(id=uuid4(), title=i["name"],
                                                            input_message_content=InputTextMessageContent(i["name"] + "::" + str(i["id"]))))
        # pprint(results)
        update.inline_query.answer(results)
    elif context.user_data[uid]["state"] == "template":
        #print(query)
        results = []
        with open("templates_" + uid + ".json", "r") as f:
            for i in load(f):
                #pprint(i)
                if query in i["owner"].lower() or query in i["title"].lower() or query in i["description"].lower() or query in i["client"].lower() or query in i["worker"].lower():
                    #print(i["title"])
                    desc = i["description"] + " " + i["worker"] + " " + i["client"]
                    if not desc or desc == "  ":
                        desc = "No description.:("
                    #print(desc)
                    results.append(InlineQueryResultArticle(id=uuid4(), title=i["title"],
                                                            input_message_content=InputTextMessageContent(i["title"] + "::" + str(i["id"]))))
        #pprint(results)
        update.inline_query.answer(results)
    else:
        # TODO: clients list
        update.inline_query.answer([
            InlineQueryResultArticle(id=uuid4(), title="Search agent",
                                     input_message_content=InputTextMessageContent("Searching agent. # TODO"))
        ])


def commit(update, context, type):
    user_data = {**load_db(), **context.user_data}
    if type == "message" or type == "command":
        uid = str(update.message.chat_id)
    elif type == "callback":
        uid = str(update.callback_query.from_user.id)
    elif type == "query":
        uid = str(update.inline_query.from_user.id)
    if uid not in user_data:
        user_data[uid] = {"state": "pending"}
    dump_db(user_data)
    return user_data


def load_db():
    with open('dumpp.json', 'r+', encoding='utf-8') as f:
        return load(f)


def dump_db(context):
    dump(context, open('dumpp.json', 'w+', encoding='utf-8'), ensure_ascii=False, indent=4)


def start(update, context):
    context.user_data = commit(update, context, "command")
    update.message.reply_text('Здравствуйте! Чем могу быть полезен?')


def help(update, context):
    context.user_data = commit(update, context, "command")
    update.message.reply_text('Здравствуйте! Я - бот компании \"K3\"! Чем могу быть полезен?')


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, error)


def new_task(update, context):
    context.user_data = commit(update, context, "command")
    uid = str(update.message.chat_id)
    get_template_list(uid)
    context.user_data[uid]["state"] = "template"
    update.message.reply_text("Включите инлайн и начните искать шаблон (@k3pfbot шаблон...) или отправьте -1, если не хотите сейчас добавлять шаблон (ввести поля вручную).")
    context.user_data = commit(update, context, "command")


def text_handler(update, context):
    context.user_data = commit(update, context, "message")
    uid = str(update.message.chat_id)
    if context.user_data[uid]["state"] == "template":
        if update.message.text == "-1":
            context.user_data[uid]["template"] = {
                "id": "",
                "title": "",
                "description": "",
                "owner": "",
                "client": "",
                "worker": "",
                "beginDateTime": "",
                "endTime": ""
            }
        else:
            template_id = update.message.text.rsplit("::", 1)[-1]
            context.user_data[uid]["template"] = get_template(template_id, uid)
            if "beginDateTime" not in context.user_data[uid]["template"]:
                context.user_data[uid]["template"]["beginDateTime"] = ""
            if "endTime" not in context.user_data[uid]["template"]:
                context.user_data[uid]["template"]["endTime"] = ""
    elif context.user_data[uid]["state"] == "title":
        context.user_data[uid]["template"]["title"] = update.message.text
    elif context.user_data[uid]["state"] == "description":
        context.user_data[uid]["template"]["description"] = update.message.text
    elif context.user_data[uid]["state"] == "client":
        if update.message.text == "-1":
            context.user_data[uid]["template"]["client"] = "0"
        else:
            context.user_data[uid]["template"]["client"] = update.message.text.rsplit("::", 1)[-1]
    n = get_next(context.user_data[uid]["template"])
    if n == "title":
        context.user_data[uid]["state"] = "title"
        update.message.reply_text("Введите название задачи")
    elif n == "description":
        context.user_data[uid]["state"] = "description"
        update.message.reply_text("Введите описание задачи")
    elif n == "beginDateTime":
        context.user_data[uid]["state"] = 'beginDateTime'
        update.message.reply_text("Выберите дату начала:", reply_markup=telegramcalendar.create_calendar())
    elif n == "endTime":
        context.user_data[uid]["state"] = 'endTime'
        update.message.reply_text("Выберите дату окончания:", reply_markup=telegramcalendar.create_calendar())
    elif n == "client":
        get_contact_list(uid)
        context.user_data[uid]["state"] = 'client'
        update.message.reply_text("Включите инлайн и начните искать контрагента (@k3pfbot имя контрагента...) или отправьте -1, если не хотите сейчас добавлять контрагента.")
    else:
        update.message.reply_text("Задача успешно создана!\n" + add_task(update, context, "message"))
        context.user_data[uid]["state"] = "pending"
        context.user_data[uid]["template"] = {
            "id": "",
            "title": "",
            "description": "",
            "owner": "",
            "client": "",
            "worker": "",
            "beginDateTime": "",
            "endTime": ""
        }
    context.user_data = commit(update, context, "message")


def button(update, context):
    context.user_data = commit(update, context, "callback")
    data = update.callback_query.data
    uid = str(update.callback_query.from_user.id)
    if data == "confirm_date":
        # TODO: clients list
        n = get_next(context.user_data[uid]["template"])
        if n == "endTime":
            context.user_data[uid]["state"] = 'endTime'
            update.callback_query.edit_message_text("Выберите дату окончания:", reply_markup=telegramcalendar.create_calendar())
        elif n == "client":
            get_contact_list(uid)
            context.user_data[uid]["state"] = 'client'
            update.callback_query.edit_message_text("Включите инлайн и начните искать контрагента (@k3pfbot имя контрагента...) или отправьте -1, если не хотите сейчас добавлять контрагента.")
        else:
            update.callback_query.edit_message_text("Задача успешно создана!\n" + add_task(update, context, "callback"))
            context.user_data[uid]["state"] = 'pending'
            context.user_data[uid]["template"] = {
                "id": "",
                "title": "",
                "description": "",
                "owner": "",
                "client": "",
                "worker": "",
                "beginDateTime": "",
                "endTime": ""
            }
    elif data == "change_date":
        r = "начала" if context.user_data[uid]["state"] == "beginDateTime" else "окончания"
        update.callback_query.edit_message_text(f"Выберите дату {r}:", reply_markup=telegramcalendar.create_calendar())
    else:
        selected, date = telegramcalendar.process_calendar_selection(update, context)
        if selected:
            if context.user_data[uid]["state"] == "beginDateTime":
                context.user_data[uid]["template"]["beginDateTime"] = str(date).split()[0]
            else:
                context.user_data[uid]["template"]["endTime"] = str(date).split()[0]
            update.callback_query.edit_message_text(text="Вы выбрали %s" % (date.strftime("%d/%m/%Y")),
                                                    reply_markup=InlineKeyboardMarkup(
                                                        [[InlineKeyboardButton("Подтвердить",
                                                                               callback_data="confirm_date")],
                                                         [InlineKeyboardButton("Выбрать другую",
                                                                               callback_data="change_date")]]
                                                    ))
    context.user_data = commit(update, context, "callback")


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("new_task", new_task))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(InlineQueryHandler(inlinequery))
    dp.add_handler(MessageHandler(Filters.text, text_handler))
    #dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
