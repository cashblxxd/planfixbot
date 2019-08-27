from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def week(selected=[]):
    d = {
        "mo_week": 'Mo',
        "tu_week": 'Tu',
        "we_week": 'We',
        "th_week": 'Th',
        "fr_week": 'Fr',
        "sa_week": 'Sa',
        "su_week": 'Su'
    }
    keyboard = []
    for i in d:
        if i in selected:
            keyboard.append([InlineKeyboardButton("{}✓".format(d[i]), callback_data=i)])
        else:
            keyboard.append([InlineKeyboardButton(d[i], callback_data=i)])
    keyboard.append([InlineKeyboardButton("Подтвердить", callback_data="confirm_week")])
    return InlineKeyboardMarkup(keyboard)


def days(selected=[]):
    keyboard = [[]]
    for j in range(1, 32):
        if j % 5:
            i = str(j)
            if i.strip("_day") in selected:
                keyboard[-1].append(InlineKeyboardButton("{}✓".format(i), callback_data=i + "_day"))
            else:
                keyboard[-1].append(InlineKeyboardButton(i, callback_data=i + "_day"))
        else:
            i = str(j)
            if i.strip("_day") in selected:
                keyboard.append([InlineKeyboardButton("{}✓".format(i), callback_data=i + "_day")])
            else:
                keyboard.append([InlineKeyboardButton(i, callback_data=i + "_day")])
    keyboard.append([InlineKeyboardButton("Подтвердить", callback_data="confirm_days")])
    return InlineKeyboardMarkup(keyboard)


def time_hours():
    keyboard = []
    for j in range(24):
        if j % 6:
            i = str(j)
            keyboard[-1].append(InlineKeyboardButton(i, callback_data=i + "_hr"))
        else:
            i = str(j)
            keyboard.append([InlineKeyboardButton(i, callback_data=i + "_hr")])
    keyboard.append([InlineKeyboardButton("Подтвердить", callback_data="confirm_days")])
    return InlineKeyboardMarkup(keyboard)
