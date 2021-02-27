#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
from telegram.inline import inlinequery
import sqlite3
import conf
import os
import datetime
from subprocess import Popen
from termcolor import colored
import logging
from uuid import uuid4
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineQueryResultCachedVoice
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, InlineQueryHandler
PIPE_PATH = conf.PIPE_TEMP

if not os.path.exists(PIPE_PATH):
    os.mkfifo(PIPE_PATH)

Popen(['lxterminal', '--geometry=80x60' , '-e','tail -f %s' % PIPE_PATH])


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

VNAME , GVNAME , REC  = range(3)


class DatabaseManager(object):
    def __init__(self, db):
        self.conn = sqlite3.connect(db , check_same_thread=False)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def query(self, arg):
        self.cur.execute(arg)
        self.conn.commit()
        return self.cur

    def __del__(self):
        self.conn.close()

dbmgr = DatabaseManager(conf.DATABASE)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

def username (update, context):
    user = update.message.from_user
    uname = str()
    if user["username"] != None:
        uname += "username : " + user["username"] + " |"
    else :
        uname += "username : unknown |"

    if user["first_name"] != None:
        uname += " firstname : " + user["first_name"] + " |"
    else :
        uname += " firstname : unknown |"

    if user["last_name"] != None:
        uname += " lastname : " + user["last_name"]
    else :
        uname += " lastname : unknown "
    return uname

def show(content):
    open(PIPE_PATH, "w").write(colored(datetime.datetime.now(), "magenta") + "\n" + colored("-"*80, "cyan") + "\n" + str(content) + "\n" + colored("-"*80, "cyan"))

def log(userinfo , task):
    f = open("bot.log", "a")
    trig = colored(datetime.datetime.now(), "magenta") + "\n" + colored("-"*80, "cyan")+ "\n" + colored(userinfo , "yellow") + "\n" + colored(" >> " , "blue") + colored(str(task) , "green") + "\n" + colored("-"*80, "cyan")
    f.write(trig)
    open(PIPE_PATH, "w").write(trig)
    f.close()



def start(update, context):
    """Send a message when the command /start is issued."""
    log(username(update , context) , "STARTS")
    reply_keyboard = [['/add' , '/search' , '/cancel']]
    update.message.reply_text('Hi there ! (Demo version)' ,reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Sorry :(  this option is not available yet")


def getvoicename(update, context):
    update.message.reply_text("What name do you want people to find your voice with ?")
    return VNAME

global vname
def voicename(update , context):
    global vname
    user = update.message.from_user
    vname = str(update.message.text)
    update.message.reply_text("Now send your voice :)")
    return REC

def rec(update, context):
    global vname
    user = update.message.from_user
    voice_file = update.message.voice.get_file()
    #show(update.message.voice.file_id)
    # todo : if(flag) : download
    if (conf.DOWNLOAD_FLAG):
        voice_file.download(conf.VOICE_DIR + vname+'.ogg')
    #voices.append(vname+'.ogg')
    dbmgr.query('INSERT INTO "%s" VALUES ("%s" , "%s" , "%s")' %(conf.DATABASE_TABLE , vname ,update.message.voice.file_id , username(update,context) ))
    log(username(update , context) , " added voice named '%s' \n with file_id %s " %(vname ,update.message.voice.file_id ) )
    #c.execute("INSERT INTO '%s' VALUES ('%s' , '%s')" %(conf.DATABASE , vname ,update.message.voice.file_id ))
    #conn.commit()

    update.message.reply_text("DONE!")
    return ConversationHandler.END

def search(update, context):
    user = update.message.from_user
    update.message.reply_text("Sorry :(  Search option is not available yet ")


def cancel(update, context):
    update.message.reply_text('Maybe next time ;)') #,reply_markup=ReplyKeyboardRemove()
    return ConversationHandler.END




#-------------------------------Inline query
def inlinequery(update, context):
    global results
    """Handle the inline query."""
    #voices = list of voice names
    #voice lication conf.VOICE_DIR
    query = update.inline_query.query
    show(colored("Query" , "blue") + colored(" >>  ", "green" ) + colored(query , "yellow"))
    results = []
    for row in dbmgr.query('SELECT * FROM "%s" WHERE name LIKE "%s" '% (conf.DATABASE_TABLE, query + "%")):
        results.append(
            InlineQueryResultCachedVoice(id=uuid4(), type='voice', title=row[0], voice_file_id=row[1])
        )
    show(colored("Refresh results from DataBase", "red"))
    update.inline_query.answer(results)




def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1083087111:AAE3rcKrfhHXz0fJOx8YtXZm-ZDvvFJs4E0", use_context=True,
                      request_kwargs={'proxy_url': 'socks5h://192.168.1.100:9050'})

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("search", search))
    #dp.add_handler(CommandHandler("user", username))

    # on noncommand i.e message - echo the message on Telegram

    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', getvoicename)],
        states={
            GVNAME: [MessageHandler(Filters.text, getvoicename)],
            VNAME: [MessageHandler(Filters.text, voicename)],
            REC: [MessageHandler(Filters.voice,rec)],
        }
        ,fallbacks = [CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    #--------------------------------------------------InlineQuery
    dp.add_handler(InlineQueryHandler(inlinequery))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
