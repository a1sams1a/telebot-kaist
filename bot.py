# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import psutil
import logging
import os
import random
import telegram
import datetime


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = ''
ADMIN_ID = []
MESSAGE = {}


def start(bot, update):
    bot.sendMessage(update.message.chat_id, text=MESSAGE['start'])

def help(bot, update):
    bot.sendMessage(update.message.chat_id, text=MESSAGE['help'])

def ping(bot, update):
    bot.sendMessage(update.message.chat_id, text='pong')

def nyang(bot, update):
    bot.sendMessage(update.message.chat_id, text='nyang! nyang!')

def rand(bot, update):
    msg = update.message.text.strip().split(' ')
    if len(msg) != 2 or not msg[1].isdigit():
        resp = "usage: /rand <int>"
    else:
        resp = "RANDOM: %s" % random.randint(0, int(msg[1]))

    bot.sendMessage(update.message.chat_id, text=resp)

def stat(bot, update, mode):
    def H(size):
        tail = ['', 'KB', 'MB', 'GB', 'TB']
        lev = 0
        while size >= 1024:
            size /= 1024.0
            lev += 1
        return '%s%s' % (round(size, 2), tail[lev])

    def T(time):
        return datetime.datetime.fromtimestamp(time).strftime("%Y-%m-%dT%H:%M:%S")

    chat_id = update.message.chat_id
    bot.sendChatAction(chat_id=chat_id, action=telegram.ChatAction.TYPING)

    if chat_id not in ADMIN_ID:
        resp = MESSAGE['forbid']
    elif mode == 'sys':
        boot = T(psutil.boot_time())
        user = map(lambda x: 'name=%s, term=%s, started=%s' % (x.name, x.terminal, T(x.started)),
                   psutil.users())
        resp = 'BOOT: %s\nUSER:\n%s' % (boot, '\n'.join(user))
    elif mode == 'cpu':
        cpu = psutil.cpu_times_percent(interval=1, percpu=False)
        resp = 'CPU: user=%s%%, system=%s%%, iowait=%s%%, idle=%s%%' % \
                (cpu.user, cpu.system, cpu.iowait, cpu.idle)
    elif mode == 'mem':
        mem = psutil.virtual_memory()
        resp = 'MEM: total=%s, avail=%s, percent=%s%%' % \
                (H(mem.total), H(mem.available), mem.percent)
    elif mode == 'web':
        pinfo = []
        for proc in psutil.process_iter():
            try:
                if proc.name() != 'apache2':
                    continue
            except psutil.NoSuchProcess:
                continue
            pinfo.append('pid=%s, ppid=%s, started=%s, status=%s' %
                         (proc.pid, proc.ppid(), T(proc.create_time()), proc.status()))

        resp = 'APACHE2:\n%s' % '\n'.join(pinfo)
    elif mode == 'disk':
        resp = 'DISK:\n'
        disk = map(lambda x: [x.mountpoint, psutil.disk_usage(x.mountpoint)],
                   psutil.disk_partitions())
        disk = map(lambda x: [x[0], H(x[1].total), x[1].percent], disk)
        disk = map(lambda x: 'mount=%s, total=%s, percent=%s%%' % \
                   (x[0], x[1], x[2]), disk)
        resp += '\n'.join(disk)
    elif mode == 'proc':
        pinfo = []
        for proc in psutil.process_iter():
            try:
                pinfo.append(proc.name())
            except psutil.NoSuchProcess:
                pass
        resp = 'PROC: %s' % ','.join(pinfo)
    elif mode == 'bak':
        resp = 'BACKUP: TBI'

    bot.sendMessage(chat_id, text=resp)

def unknown(bot, update):
    bot.sendMessage(update.message.chat_id, text=MESSAGE['unknown'])

def echo(bot, update):
    resp = 'echo: %s' % update.message.text
    bot.sendMessage(update.message.chat_id, text=resp)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def init():
    global TOKEN, ADMIN_ID, MESSAGE
    random.seed(os.urandom(128))

    file_list = ['bot.key', 'me.id']
    if any(not os.path.isfile(n) for n in file_list):
        raise Error

    with open('bot.key', 'r') as f:
        TOKEN = f.read().strip()

    with open('me.id', 'r') as f:
        ADMIN_ID = map(lambda x: int(x), f.read().strip().split(','))

    msg_list = ['start', 'help', 'unknown', 'forbid']

    for fn in msg_list:
        if not os.path.isfile('msg/'+fn):
            continue
        with open('msg/'+fn, 'r') as f:
            MESSAGE[fn] = f.read().strip()

def main():
    try:
        init()
    except:
        logger.error('INIT FAIL')
        return


    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("ping", ping))
    dp.add_handler(CommandHandler("nyang", nyang))
    dp.add_handler(CommandHandler("rand", rand))

    dp.add_handler(CommandHandler("sysstat", lambda x, y: stat(x, y, 'sys')))
    dp.add_handler(CommandHandler("cpustat", lambda x, y: stat(x, y, 'cpu')))
    dp.add_handler(CommandHandler("memstat", lambda x, y: stat(x, y, 'mem')))
    dp.add_handler(CommandHandler("webstat", lambda x, y: stat(x, y, 'web')))
    dp.add_handler(CommandHandler("diskstat", lambda x, y: stat(x, y, 'disk')))
    dp.add_handler(CommandHandler("procstat", lambda x, y: stat(x, y, 'proc')))
    dp.add_handler(CommandHandler("bakstat", lambda x, y: stat(x, y, 'bak')))
    dp.add_handler(MessageHandler([Filters.command], unknown))
    dp.add_handler(MessageHandler([Filters.text], echo))

    dp.add_error_handler(error)


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
