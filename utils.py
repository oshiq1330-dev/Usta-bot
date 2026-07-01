last_message = {}

def delete_safe(bot, chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass


def send_replace(bot, chat_id, text, **kwargs):

    old_id = last_message.get(chat_id)

    if old_id:
        delete_safe(bot, chat_id, old_id)

    msg = bot.send_message(chat_id, text, **kwargs)

    last_message[chat_id] = msg.message_id

    return msg
