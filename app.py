import telebot
import random
import requests
import json
# import sqlite3
import psycopg2
import urllib.parse
import telebot
from telebot import types
import os
from flask import Flask, request
# from flask import Flask, request

random_word = 'kjnl'
groups = []
games_for_admin = []
days_list = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
master_schedule_buttons = ['Название', 'Система', 'Описание', 'Длительность', 'Место проведения', 'День',
                           'Время', 'Подготовка', 'Стоимость участия', 'Количество игроков', 'Дополнительно',
                           'Заставка для игры', 'Удалить игру', 'Вернуться в главное меню']
master_short_schedule_buttons = ['Название', 'Описание', 'Заставка для игры', 'Удалить игру',
                                 'Вернуться в главное меню']
titles_for_players = ['Мастер', 'Название', 'По какой системе будет проводиться игра', 'Описание',
                      'На сколько сессий рассчитана игра', 'Где будет проходить игра', 'Когда будет проходить игра',
                      'Во сколько будет проходить игра', 'Подготовка к игре', 'Стоимость участия',
                      'Количество участников', 'Записалось участников', 'Участники', 'Дополнительно']
titles_for_masters = ['Мастер', 'Название', 'По какой системе будет проводиться игра', 'Описание',
                      'На сколько сессий рассчитана игра', 'Где будет проходить игра', 'Когда будет проходить игра',
                      'Во сколько будет проходить игра', 'Подготовка к игре', 'Стоимость участия',
                      'Количество участников', 'Записалось участников', 'Дополнительно']

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

DATABASE_URL = os.getenv("DATABASE_URL")

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://worker-production-4757.up.railway.app{WEBHOOK_PATH}"


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200


# player_functions
def add_player(name, data):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'INSERT INTO players (player, game, master) VALUES (%s, %s, %s)',
        (name, data, data))
    conn.commit()
    cursor.close()
    conn.close()


def delete_in_schedule(player, game, text):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        text, (game,))
    players = cursor.fetchall()
    cursor.close()
    conn.close()

    if len(players) != 0:
        players_dict = {}
        for names in players:
            id_game = names[0]
            names = names[1].split()
            players_dict[id_game] = names

        for key in players_dict:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT schedule.signed_players FROM schedule WHERE id ={int(key)}')
            result = cursor.fetchall()
            signed_players = int(result[0][0])
            cursor.close()
            conn.close()

            count, new_text = 0, ''
            data = players_dict[key]
            data_copy = data.copy()
            for elem in data:
                if '@' + player + ',' == elem:
                    data_copy.remove(elem)
                    count += 1
                elif '@' + player == elem:
                    data_copy.remove(elem)
                    count += 1
            if len(data_copy) == 0:
                new_text += '-'
                players_dict[key] = new_text
            else:
                for data in data_copy:
                    name = ''
                    for symbol in data:
                        if symbol != ',' and symbol != ' ':
                            name += symbol
                    new_text += name + ',' + ' '
                if new_text[-1] == ' ':
                    new_text = new_text[:-1]
                if new_text[-1] == ',':
                    new_text = new_text[:-1]

            if signed_players - count == 0:
                signed_players = '-'
            else:
                signed_players = signed_players - count

            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE schedule SET players=%s, signed_players=%s WHERE id=%s ',
                (new_text, signed_players, int(key)))
            conn.commit()
            cursor.close()
            conn.close()


def delete_player(username):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM players WHERE player=%s ', (username,))
    conn.commit()
    cursor.close()
    conn.close()
    delete_in_schedule(username, '-', 'SELECT schedule.id, schedule.players FROM schedule WHERE '
                                      'players !=%s')


def main_menu_player(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
    markup.add(types.KeyboardButton('Записаться на игру'),
               types.KeyboardButton('Отписаться от игры'),
               types.KeyboardButton('Посмотреть мои записи на игры'),
               types.KeyboardButton('Удалиться из бота'))
    return markup


def copy_game_for_player(name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM schedule WHERE title=%s', (name, ))
    masters_id = cursor.fetchall()
    cursor.close()
    conn.close()

    master_id = [elem[-1] for elem in masters_id][0]

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT master, title, system, description, address, day, time, before_game, count_players, duration, '
        f'cost, additionally, photo, signed_players, players, master_id, master_name, master_last_name  FROM schedule '
        f'WHERE id = {int(master_id)}')
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'INSERT INTO schedule (master, title, system, description, address, day, time, '
        f'before_game, count_players, duration, cost, additionally, photo, signed_players, players, master_id, '
        f'master_name, master_last_name) VALUES {result[0]}')
    conn.commit()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'DELETE FROM schedule WHERE id = {int(master_id)}')
    conn.commit()
    cursor.close()
    conn.close()


def get_data_for_player(name, argument):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    if argument == 'show_games_one_master':
        cursor.execute(
            'SELECT schedule.title FROM schedule WHERE master=%s', (name,))
        answer = cursor.fetchall()
        cursor.close()
        conn.close()
        result = [elem[0] for elem in answer]
        return result

    elif argument == 'show_games':
        cursor.execute(
            'SELECT schedule.title, schedule.master_name, schedule.master_last_name FROM schedule '
            'WHERE master=%s', (name, ))
        games = cursor.fetchall()
        cursor.close()
        conn.close()

        new_result = []
        for game in games:
            name_game = game[0]
            master = f'{game[1]} {game[2]}'
            text = f'🔥 "{name_game}" 🔥, мастер - {master}'
            new_result.append(text)
        return new_result

    elif argument == 'show_masters':
        cursor.execute(
            'SELECT schedule.master FROM schedule')
        masters = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(masters) == 0:
            result = 'Мастера ещё не выложили своё расписание😔\nПосмотри немного позже 👀'
        else:
            result = [master[0] for master in masters]
            result = list(set(result))
        return result

    elif argument == 'show_concrete_game':
        cursor.execute(
            f'SELECT schedule.photo FROM schedule WHERE title=%s', (name,))
        photo = cursor.fetchall()[0][0]
        cursor.close()
        conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT schedule.master, schedule.title, schedule.system, schedule.description, schedule.duration, '
            f'schedule.address, schedule.day, schedule.time, schedule.before_game, schedule.cost, '
            f'schedule.count_players, schedule.signed_players, schedule.additionally FROM schedule WHERE title=%s',
            (name,))
        last_game = cursor.fetchall()[0]
        cursor.close()
        conn.close()

        answer = {}
        for i in range(len(last_game)):
            if last_game[i] != '-':
                answer[titles_for_masters[i]] = last_game[i]
        len_answer = len(answer)
        count = 0

        text = ''
        for word in answer:
            count += 1
            if word == 'Мастер':
                text += f'*{word}*\n@{answer.get(word)}\n—\n'
            else:
                if count == len_answer:
                    text += f'*{word}*\n{answer.get(word)}'
                if count != len_answer:
                    text += f'*{word}*\n{answer.get(word)}\n—\n'

        result = []
        if photo != '-':
            result.append(photo)
            result.append(text)
            return result
        else:
            return text
    elif argument == 'show_last_game_for_player':
        cursor.execute(
            'SELECT schedule.id FROM schedule')
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        masters_id = [elem[0] for elem in result]
        masters_id.sort()
        master_id = masters_id[-1]

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT schedule.photo FROM schedule WHERE id=%s', (int(master_id),))
        photo = cursor.fetchall()[0][0]
        cursor.close()
        conn.close()

        answer = []
        if photo != '-':
            answer.append(photo)
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT schedule.master, schedule.title, schedule.system, schedule.description, schedule.duration, '
                f'schedule.address, schedule.day, schedule.time, schedule.before_game, schedule.cost, '
                f'schedule.count_players, schedule.signed_players, schedule.players, schedule.additionally '
                f'FROM schedule WHERE id=%s',
                (int(master_id),))
            result = cursor.fetchall()[0]
            cursor.close()
            conn.close()

            finally_answer = {}
            for i in range(len(result)):
                if result[i] != '-':
                    finally_answer[titles_for_players[i]] = result[i]
            answer.append(finally_answer)
            return answer

        else:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT schedule.master, schedule.title, schedule.system, schedule.description, schedule.duration, '
                f'schedule.address, schedule.day, schedule.time, schedule.before_game, schedule.cost, '
                f'schedule.count_players, schedule.signed_players, schedule.players, schedule.additionally '
                f'FROM schedule WHERE id=%s',
                (int(master_id),))
            result = cursor.fetchall()[0]
            cursor.close()
            conn.close()

            finally_answer = {}
            for i in range(len(result)):
                if result[i] != '-':
                    finally_answer[titles_for_players[i]] = result[i]
            return finally_answer

    elif argument == 'show_games_one_player':
        cursor.execute(
            'SELECT players.game FROM players WHERE player=%s', (name,))
        answer = cursor.fetchall()
        result = [elem[0] for elem in answer]
        cursor.close()
        conn.close()

        if len(result) == 0:
            return 'Вы пока не записались ни на одну игру :)'
        else:
            return result


def unsubscribe(player):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.id FROM schedule')
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    masters_id = [elem[0] for elem in result]
    masters_id.sort()
    master_id = masters_id[-1]

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT schedule.title FROM schedule WHERE id=%s', (int(master_id),))
    game = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM players WHERE game=%s ', (game,))
    conn.commit()
    cursor.close()
    conn.close()

    delete_in_schedule(player, game, 'SELECT schedule.id, schedule.players FROM schedule WHERE title =%s')


def checking_players_for_replay(text, username):
    list_names = []
    name = ''
    for i in range(len(text)):
        if text[i] != ',' and text[i] != ' ':
            name += text[i]
        if i == len(text) - 1:
            list_names.append(name)
        elif text[i] == ',':
            list_names.append(name)
            name = ''

    username = '@' + username
    if username in list_names:
        return 'Вы уже записаны на эту игру :)'


def notify_master(player, game):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    data = {}
    cursor.execute(
        'SELECT schedule.master_id FROM schedule WHERE title=%s', (game,))
    master = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()

    data['master'] = master
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.master_name FROM schedule WHERE title=%s', (game,))
    master_name = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()

    text = f'Привет, {master_name}!\nНа вашу игру << {game} >> записался новый участник: @{player} :)'
    data['text'] = text
    return data


def check_free_places(username, game):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.signed_players FROM schedule WHERE title=%s', (game,))
    signed_players = cursor.fetchall()
    cursor.close()
    conn.close()

    signed_players = signed_players[0][0]
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.count_players FROM schedule WHERE title=%s', (game,))
    count_players = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.master FROM schedule WHERE title=%s', (game,))
    master = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()

    if signed_players == '-':
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE schedule SET signed_players=%s WHERE title=%s', (1, game,))
        conn.commit()
        cursor.close()
        conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE schedule SET players=%s WHERE title=%s',
            ('@' + username, game,))
        conn.commit()
        cursor.close()
        conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE players SET game=%s WHERE game=%s AND player=%s', (game, 'default', username))
        conn.commit()
        cursor.close()
        conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE players SET master=%s WHERE game=%s AND player=%s', (master, game, username))
        conn.commit()
        cursor.close()
        conn.close()
        return 'Вы записались на игру'
    else:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT schedule.players FROM schedule WHERE title=%s', (game,))
        players = cursor.fetchall()[0][0]
        cursor.close()
        conn.close()

        if checking_players_for_replay(players, username) == 'Вы уже записаны на эту игру :)':
            return 'Вы уже записаны на эту игру :)'

        elif count_players == '-':
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE schedule SET signed_players=%s WHERE title=%s',
                (int(signed_players) + 1, game,))
            conn.commit()
            cursor.close()
            conn.close()

            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE schedule SET players=%s WHERE title=%s',
                (players + ', ' + '@' + username, game,))
            conn.commit()
            cursor.close()
            conn.close()

            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE players SET game=%s WHERE game=%s AND player=%s', (game, 'default', username))
            conn.commit()
            cursor.close()
            conn.close()

            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE players SET master=%s WHERE game=%s AND player=%s', (master, game, username))
            conn.commit()
            cursor.close()
            conn.close()
            return 'Вы записались на игру'
        elif len(count_players) == 1 or len(count_players) == 2:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            if int(count_players) == int(signed_players):
                cursor.close()
                conn.close()
                return 0
            elif int(signed_players) < int(count_players):
                cursor.execute(
                    'UPDATE schedule SET signed_players=%s WHERE title=%s',
                    (int(signed_players) + 1, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE schedule SET players=%s WHERE title=%s',
                    (players + ', ' + '@' + username, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET game=%s WHERE game=%s AND player=%s', (game, 'default', username))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET master=%s WHERE game=%s AND player=%s', (master, game, username))
                conn.commit()
                cursor.close()
                conn.close()
                return 'Вы записались на игру'
        elif len(count_players) == 3:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            if int(signed_players) < int(count_players[-1]):
                cursor.execute(
                    'UPDATE schedule SET signed_players=%s WHERE title=%s',
                    (int(signed_players) + 1, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE schedule SET players=%s WHERE title=%s',
                    (players + ', ' + '@' + username, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET game=%s WHERE game=%s AND player=%s', (game, 'default', username))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET master=%s WHERE game=%s AND player=%s', (master, game, username))
                conn.commit()
                cursor.close()
                conn.close()
                return 'Вы записались на игру'
            else:
                cursor.close()
                conn.close()
                return 0
        elif len(count_players) == 4:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            if int(signed_players) < int(count_players[2:]):
                cursor.execute(
                    'UPDATE schedule SET signed_players=%s WHERE title=%s',
                    (int(signed_players) + 1, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE schedule SET players=%s WHERE title=%s',
                    (players + ', ' + '@' + username, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET game=%s WHERE game=%s AND player=%s', (game, 'default', username))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET master=%s WHERE game=%s AND player=%s', (master, game, username))
                conn.commit()
                cursor.close()
                conn.close()
                return 'Вы записались на игру'
            else:
                cursor.close()
                conn.close()
                return 0
        elif len(count_players) == 5:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            if int(signed_players) < int(count_players[3:]):
                cursor.execute(
                    'UPDATE schedule SET signed_players=%s WHERE title=%s',
                    (int(signed_players) + 1, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE schedule SET players=%s WHERE title=%s',
                    (players + ', ' + '@' + username, game,))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET game=%s WHERE game=%s AND player=%s', (game, 'default', username))
                conn.commit()
                cursor.close()
                conn.close()

                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE players SET master=%s WHERE game=%s AND player=%s', (master, game, username))
                conn.commit()
                cursor.close()
                conn.close()
                return 'Вы записались на игру'
            else:
                cursor.close()
                conn.close()
                return 0


def check_games_player(player):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players WHERE player=%s', (player, ))
    games = cursor.fetchall()
    cursor.close()
    conn.close()

    id_games = []
    for game in games:
        schedule = [elem for elem in game if elem != '-']

        if len(schedule) == 2:
            id_games.append(schedule[-1])

    if len(id_games):
        for id_game in id_games:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM players WHERE id=%s ', (int(id_game),))
            conn.commit()
            cursor.close()
            conn.close()


def btn_back_to_main_menu_player(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Вернуться в главное меню'))
    return markup


def back_to_main_menu_player(message):
    result = main_menu_player(message)
    bot.send_message(message.chat.id, text='Выберите, что хотите сделать :)', reply_markup=result)


# master_functions
bot_info = bot.get_me()


def get_admins():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT administrators.name FROM administrators')
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    admins = [admin[0] for admin in result]
    return admins


def add_chats_to_database(link):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    name = bot.get_chat('@' + link[13:]).title
    id_chat = bot.get_chat('@' + link[13:]).id
    cursor.execute(
        f'INSERT INTO chats_with_games (link, name, id_chat) VALUES ("{link}", "{name}", "{id_chat}")')
    conn.commit()
    cursor.close()
    conn.close()


def get_chats(argument, chat):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    if argument == 'get_name':
        cursor.execute(
                'SELECT chats_with_games.name FROM chats_with_games')
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        chats = [link[0] for link in result]
        return chats
    elif argument == 'get_link':
        cursor.execute(
            'SELECT chats_with_games.link FROM chats_with_games WHERE name=%s', (chat, ))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        link = [link[0] for link in result]
        return link[0]
    elif argument == 'get_id':
        cursor.execute(
            'SELECT chats_with_games.id_chat FROM chats_with_games WHERE name=%s', (chat, ))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        id_chat = [link[0] for link in result]
        return id_chat[0]


def check_replay_links(data):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT chats_with_games.link FROM chats_with_games')
    links = cursor.fetchall()
    cursor.close()
    conn.close()

    links = [link[0] for link in links]
    if data in links:
        return True
    else:
        return False


def check_bot_group_membership(token, id_group):
    chat_member = bot.get_chat_member(chat_id=id_group, user_id=bot_info.id)
    if chat_member.status in ["member", "administrator", "creator"]:
        return True  # Бот состоит в группе
    else:
        return False  # Бот не состоит в группе


def check_count_players(data):
    new_dict = {}
    for i in range(len(data)):
        if data[i].isdigit():
            new_dict[i] = data[i]
    if len(new_dict) >= 5 or len(new_dict) == 0:
        return [0, data]
    else:
        if len(new_dict) == 1:
            count = [new_dict.get(key) for key in new_dict][0]
            return [1, count]
        elif len(new_dict) == 2:
            count = [key for key in new_dict]
            if int(count[0]) + 1 == int(count[1]):
                return [1, new_dict[count[0]] + new_dict[count[1]]]
            else:
                return [1, new_dict[count[0]] + '-' + new_dict[count[1]]]
        elif len(new_dict) == 3:
            count = [key for key in new_dict]
            if int(count[0]) + 1 == int(count[1]):
                return [0, data]
            else:
                first_digit = new_dict[count[0]]
                if int(count[1]) + 1 != int(count[2]):
                    return [0, data]
                elif int(count[1]) + 1 == int(count[2]):
                    second_digit = new_dict[count[1]] + new_dict[count[2]]
                    return [1, first_digit + '-' + second_digit]
        elif len(new_dict) == 4:
            count = [key for key in new_dict]
            if int(count[0]) + 1 != int(count[1]):
                return [0, data]
            elif int(count[0]) + 1 == int(count[1]):
                first_digit = new_dict[count[0]] + new_dict[count[1]]
                if int(count[2]) + 1 != int(count[3]):
                    return [0, data]
                elif int(count[2]) + 1 == int(count[3]):
                    second_digit = new_dict[count[2]] + new_dict[count[3]]
                    return [1, first_digit + '-' + second_digit]


def add_master(name, data, user_id, master_name, master_last_name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'INSERT INTO schedule (master, day, title, system, description, count_players, duration, time, '
        f'address, cost, before_game, photo, additionally, signed_players, players, master_id, master_name, '
        f'master_last_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (name, data, data, data, data, data, data, data, data, data, data, data, data, data, data,
         user_id, master_name, master_last_name))
    conn.commit()
    cursor.close()
    conn.close()


def delete_master(username):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM schedule WHERE master=%s ', (username,))
    conn.commit()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM players WHERE master=%s ', (username,))
    conn.commit()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM announcements WHERE master=%s ', (username,))
    conn.commit()
    cursor.close()
    conn.close()


def add_inf_masters(data, key, name):
    count = data.count('\n')
    if count != 0:
        data = data.replace('\n', ' ')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    all_data = {'title': 'UPDATE schedule SET title=%s WHERE id=%s',
                'system': 'UPDATE schedule SET system=%s WHERE id=%s',
                'description': 'UPDATE schedule SET description=%s WHERE id=%s',
                'count_players': 'UPDATE schedule SET count_players=%s WHERE id=%s',
                'duration': 'UPDATE schedule SET duration=%s WHERE id=%s',
                'time': 'UPDATE schedule SET time=%s WHERE id=%s',
                'day': 'UPDATE schedule SET day=%s WHERE id=%s',
                'address': 'UPDATE schedule SET address=%s WHERE id=%s',
                'cost': 'UPDATE schedule SET cost=%s WHERE id=%s',
                'before_game': 'UPDATE schedule SET before_game=%s WHERE id=%s',
                'photo': 'UPDATE schedule SET photo=%s WHERE id=%s',
                'additionally': 'UPDATE schedule SET additionally=%s WHERE id=%s',
                }
    cursor.execute(
        'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
    result = cursor.fetchall()
    masters_id = [elem[0] for elem in result]
    masters_id.sort()
    master_id = masters_id[-1]
    text = all_data.get(key)
    cursor.execute(text, (data, int(master_id)))
    conn.commit()
    cursor.close()
    conn.close()


def main_menu_master(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
    markup.add(types.KeyboardButton('Добавить игру'), types.KeyboardButton('Редактировать игру'),
               types.KeyboardButton('Список моих игр'), types.KeyboardButton('Удалиться из бота'))
    return markup


def main_menu_admin(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
    markup.add(types.KeyboardButton('Добавить группу для анонсов :)'),
               types.KeyboardButton('Список групп'),
               types.KeyboardButton('Список игр'),
               types.KeyboardButton('Вернуться в главное меню'))
    return markup


def back_to_main_menu_admin(message):
    result = main_menu_admin(message)
    bot.send_message(message.chat.id, text='Выберите, что хотите сделать :)', reply_markup=result)


def btn_back_to_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Вернуться в главное меню'))
    return markup


def back_to_main_menu(message):
    result = main_menu_master(message)
    bot.send_message(message.chat.id, text='Выберите, что хотите сделать :)', reply_markup=result)


def copy_game(data, name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM schedule WHERE master=%s', (name, ))
    masters_id = cursor.fetchall()
    cursor.close()
    conn.close()

    masters_id = [elem[0] for elem in masters_id]
    master_id = masters_id[data]

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT master, title, system, description, address, day, time, before_game, count_players, duration, '
        f'cost, additionally, photo, signed_players, players, master_id, master_name, master_last_name FROM schedule '
        f'WHERE id = {int(master_id)}')
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'INSERT INTO schedule (master, title, system, description, address, day, time, '
        f'before_game, count_players, duration, cost, additionally, photo, signed_players, players, master_id, '
        f'master_name, master_last_name) VALUES {result[0]}')
    conn.commit()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'DELETE FROM schedule WHERE id = {int(master_id)}')
    conn.commit()
    cursor.close()
    conn.close()


def delete_game(name, argument):
    if argument == 'master':
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        masters_id = [elem[0] for elem in result]
        masters_id.sort()
        master_id = int(masters_id[-1])

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT schedule.title FROM schedule WHERE id=%s', (int(master_id),))
        title = cursor.fetchall()[0][0]
        cursor.close()
        conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT players.game FROM players WHERE game=%s', (title, ))
        games = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(games) != 0:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM players WHERE game=%s ', (title,))
            conn.commit()
            cursor.close()
            conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM schedule WHERE id=%s ', (int(master_id),))
        conn.commit()
        cursor.close()
        conn.close()
    elif argument == 'admin':
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM schedule WHERE title=%s ', (name, ))
        conn.commit()
        cursor.close()
        conn.close()

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT players.game FROM players WHERE game=%s', (name,))
        games = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(games) != 0:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM players WHERE game=%s ', (name,))
            conn.commit()
            cursor.close()
            conn.close()


def check_buttons(name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    master_id = [elem[0] for elem in result]
    master_id.sort()
    edit = {}

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT schedule.title, schedule.system, schedule.description, schedule.duration,'
                   'schedule.address, schedule.day, schedule.time, schedule.before_game, schedule.cost, '
                   'schedule.count_players, schedule.additionally, schedule.photo '
                   'FROM schedule WHERE schedule.id=%s', (master_id[-1], ))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    new_data = data[0]
    for i in range(len(new_data)):
        if new_data[i] != '-':
            edit[i] = '✅ — '
    return edit


def check_buttons_short(name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    master_id = [elem[0] for elem in result]
    master_id.sort()
    edit = {}

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT schedule.title, schedule.description, schedule.photo FROM schedule '
                   'WHERE schedule.id=%s', (master_id[-1], ))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    new_data = data[0]
    for i in range(len(new_data)):
        if new_data[i] != '-':
            edit[i] = '✅ — '
    return edit


def master_schedule_elements(name):
    result = check_buttons(name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if len(result) == 0:
        markup.add(types.KeyboardButton(master_schedule_buttons[0]),
                   types.KeyboardButton(master_schedule_buttons[1]), types.KeyboardButton(master_schedule_buttons[2]),
                   types.KeyboardButton(master_schedule_buttons[3]), types.KeyboardButton(master_schedule_buttons[4]),
                   types.KeyboardButton(master_schedule_buttons[5]), types.KeyboardButton(master_schedule_buttons[6]),
                   types.KeyboardButton(master_schedule_buttons[7]), types.KeyboardButton(master_schedule_buttons[8]),
                   types.KeyboardButton(master_schedule_buttons[9]), types.KeyboardButton(master_schedule_buttons[10]),
                   types.KeyboardButton(master_schedule_buttons[11]), types.KeyboardButton(master_schedule_buttons[12]),
                   types.KeyboardButton(master_schedule_buttons[13]))

    else:
        new_buttons = master_schedule_buttons.copy()
        for elem in result:
            new_buttons[elem] = result.get(elem) + master_schedule_buttons[elem]
        markup.add(types.KeyboardButton(new_buttons[0]), types.KeyboardButton(new_buttons[1]),
                   types.KeyboardButton(new_buttons[2]), types.KeyboardButton(new_buttons[3]),
                   types.KeyboardButton(new_buttons[4]), types.KeyboardButton(new_buttons[5]),
                   types.KeyboardButton(new_buttons[6]), types.KeyboardButton(new_buttons[7]),
                   types.KeyboardButton(new_buttons[8]), types.KeyboardButton(new_buttons[9]),
                   types.KeyboardButton(new_buttons[10]), types.KeyboardButton(new_buttons[11]),
                   types.KeyboardButton('Посмотреть расписание этой игры 🎲'),
                   types.KeyboardButton('Анонсировать эту игру 🔥'), types.KeyboardButton(new_buttons[12]),
                   types.KeyboardButton(new_buttons[13]))
    return markup


def master_short_schedule_elements(name):
    result = check_buttons_short(name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if len(result) == 0:
        markup.add(types.KeyboardButton(master_short_schedule_buttons[0]),
                   types.KeyboardButton(master_short_schedule_buttons[1]),
                   types.KeyboardButton(master_short_schedule_buttons[2]),
                   types.KeyboardButton(master_short_schedule_buttons[3]),
                   types.KeyboardButton(master_short_schedule_buttons[4]))
    else:
        new_buttons = master_short_schedule_buttons.copy()
        for elem in result:
            new_buttons[elem] = result.get(elem) + master_short_schedule_buttons[elem]
        markup.add(types.KeyboardButton(new_buttons[0]), types.KeyboardButton(new_buttons[1]),
                   types.KeyboardButton(new_buttons[2]), types.KeyboardButton('Посмотреть расписание этой игры 🎲'),
                   types.KeyboardButton('Анонсировать эту игру 🔥'), types.KeyboardButton(new_buttons[3]),
                   types.KeyboardButton(new_buttons[4]))
    return markup


def get_data_for_master(name, argument):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    if argument == 'show_photo':
        cursor.execute(
            'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        masters_id = [elem[0] for elem in result]
        masters_id.sort()
        master_id = masters_id[-1]

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT schedule.photo FROM schedule WHERE id=%s', (int(master_id),))
        photo = cursor.fetchall()[0][0]
        cursor.close()
        conn.close()
        return photo

    elif argument == 'show_games_one_master':
        cursor.execute(
            'SELECT schedule.title FROM schedule WHERE master=%s', (name,))
        answer = cursor.fetchall()
        cursor.close()
        conn.close()
        result = [elem[0] for elem in answer]
        return result
    elif argument == 'show_all_games':
        cursor.execute(
            'SELECT schedule.title FROM schedule')
        answer = cursor.fetchall()
        cursor.close()
        conn.close()
        result = [elem[0] for elem in answer]
        return result
    elif argument == 'get_game':
        cursor.execute(
            'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        masters_id = [elem[0] for elem in result]
        masters_id.sort()
        master_id = masters_id[-1]

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT schedule.title FROM schedule WHERE id=%s', (int(master_id),))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        title = result[0][0]
        return title
    elif argument == 'show_masters':
        cursor.execute(
            'SELECT schedule.master FROM schedule')
        masters = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(masters) == 1:
            result = masters[0][0]
        elif len(masters) == 0:
            result = 'Мастера ещё не выложили своё расписание😔\nПосмотрите немного позже 👀'
        else:
            new_list = [master[0] for master in masters]
            result = list(set(new_list))
        return result


def check_replay_announcements(master, data):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT announcements.chat_name, announcements.text FROM announcements WHERE master=%s', (master, ))
    chats = cursor.fetchall()
    cursor.close()
    conn.close()
    if data in chats:
        return False
    else:
        return True


def announce_game(name, argument):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT schedule.id FROM schedule WHERE master=%s', (name,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    masters_id = [elem[0] for elem in result]
    masters_id.sort()
    master_id = masters_id[-1]

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT schedule.master, schedule.title, schedule.system, schedule.description, schedule.duration, '
        f'schedule.address, schedule.day, schedule.time, schedule.before_game, schedule.cost, '
        f'schedule.count_players, schedule.signed_players, schedule.additionally FROM schedule WHERE id=%s',
        (int(master_id),))
    last_game = cursor.fetchall()[0]
    cursor.close()
    conn.close()

    answer = {}
    for i in range(len(last_game)):
        if last_game[i] != '-':
            answer[titles_for_masters[i]] = last_game[i]
    len_answer = len(answer)
    count = 0

    text = ''
    for word in answer:
        new_word = answer.get(word)
        count += 1
        if word == 'Мастер':
            text += '*' + word + '*' + '\n' + '@' + new_word + '\n—\n'
        else:
            if count == len_answer:
                text += '*' + word + '*' + '\n' + new_word
            if count != len_answer:
                text += '*' + word + '*' + '\n' + new_word + '\n—\n'

    len_text = len(text)

    if argument == 'announce':
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            f'INSERT INTO announcements (text, master, chat_name, chat_link, chat_id) VALUES (%s, %s, %s, %s, %s)',
            (text, name, '-', '-', '-'))
        conn.commit()
        cursor.close()
        conn.close()

        name_bot = '@GamesNSbot'
        return (f'🔥🔥🔥\nВсем привет! А вот и анонс новой игры!\n🔥🔥🔥\n\n{text}\n\n🎲 Запись через бота '
                f'{name_bot} 🎲', len_text)

    elif argument == 'show':
        name_bot = '@GamesNSbot'
        return (f'🔥🔥🔥\nВсем привет! А вот и анонс новой игры!\n🔥🔥🔥\n\n{text}\n\n🎲 Запись через бота '
                f'{name_bot} 🎲', len_text)


def get_announce_game(name, chat, id_chat, argument):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT announcements.text FROM announcements WHERE chat_link=%s', ('-',))
    announcement = cursor.fetchall()
    cursor.close()
    conn.close()

    announcement = announcement[0][0]
    if check_replay_announcements(name, (chat, announcement)) or argument == 'replay':
        link = get_chats('get_link', chat)

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE announcements SET chat_name=%s, chat_id=%s, chat_link=%s WHERE chat_name=%s',
            (chat, id_chat, link, '-',))
        conn.commit()
        cursor.close()
        conn.close()

        name_bot = '@GamesNSbot'
        return (f'🔥🔥🔥\nВсем привет! А вот и анонс новой игры!\n🔥🔥🔥\n\n{announcement}\n\n🎲 '
                f'Запись через бота {name_bot} 🎲')
    else:
        return 'Вы уже выкладывали свой анонс в этой группе :)\nВыложить ещё раз?'


def delete_announce_game(name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(
        'DELETE FROM announcements WHERE chat_name=%s ', ('-',))
    conn.commit()
    cursor.close()
    conn.close()


def check_games_master(master):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM schedule WHERE master=%s', (master, ))
    games = cursor.fetchall()
    cursor.close()
    conn.close()

    id_games = []
    for game in games:
        schedule = [elem for elem in game if elem != '-']
        if len(schedule) == 5:
            id_games.append(schedule[-1])

    if len(id_games):
        for id_game in id_games:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM schedule WHERE id=%s ', (int(id_game),))
            conn.commit()
            cursor.close()
            conn.close()


class ConvertionException(Exception):
    pass


class MyCustomException(Exception):
    pass


@bot.message_handler(commands=['start', ])
def start(message: telebot.types.Message):
    if message.chat.type == 'private':
        username = message.from_user.username
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if message.text == '/help_me':
            help_me(message)
        elif message.text == '/roll_the_dice':
            roll_the_dice(message)
        else:
            admins = get_admins()
            if username in admins:
                delete_announce_game(username)
                markup.add(types.KeyboardButton('Я — мастер :)'),
                           types.KeyboardButton('Я — игрок :)'),
                           types.KeyboardButton('Я — администратор :)'))
                bot.send_message(message.chat.id, text="Привет, {0.first_name}! Решите, как хотите "
                                                       "использовать этот бот :)".format(message.from_user),
                                 reply_markup=markup)
                bot.register_next_step_handler(message, player_master_admin)
            else:
                delete_announce_game(username)
                markup.add(types.KeyboardButton('Я — мастер :)'),
                           types.KeyboardButton('Я — игрок :)'))
                bot.send_message(message.chat.id, text="Привет, {0.first_name}! Решите, как хотите "
                                                       "использовать этот бот :)".format(message.from_user),
                                 reply_markup=markup)
                bot.register_next_step_handler(message, player_master_admin)


@bot.message_handler(commands=['help_me', ])
def help_me(message: telebot.types.Message):
    if message.chat.type == 'private':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton('Вернуться в самое начало'))
        bot.send_message(message.chat.id, text='Привет, {0.first_name}!\nЯ помогу вам разобраться :)\nЭтот бот могут '
                                               'использовать мастера и игроки. В самом начале вам нужно выбрать, как '
                                               'именно вы собираетесь использовать этот бот:\n'
                                               'Если вы мастер, то следуйте указаниям на кнопках и '
                                               'составляйте своё расписание. Вы всегда можете изменить расписание '
                                               'своих игр, нажав на <Редактироовать игру>. Там же вы можете удалить '
                                               'игру.\n'
                                               'Вы можете посмотреть список своих игр и можете анонсировать свои игры '
                                               'в разные сообщества :)\n'
                                               'При записи к вам на игру вам придёт уведомление о том, какой участник '
                                               'записался к вам на игру :)\nЕсли вы игрок, то всё ещё проще: вы просто '
                                               'выбираете игру, на которую хотите записаться и записываетесь :) '
                                               'Потом также легко вы можете отписаться от любой игры :)\n'
                                               'Надеюсь, всё стало чуточку понятнее ☺️'.format(message.from_user),
                         reply_markup=markup)
        bot.register_next_step_handler(message, start)


@bot.message_handler(commands=['roll_the_dice', ])
def roll_the_dice(message: telebot.types.Message):
    if message.chat.type == 'private':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if message.text == '/start':
            start(message)
        elif message.text == '/help_me':
            help_me(message)
        else:
            markup.add(types.KeyboardButton('Бросить D20'), types.KeyboardButton('Бросить D12'),
                       types.KeyboardButton('Бросить D10'), types.KeyboardButton('Бросить D8'),
                       types.KeyboardButton('Бросить D6'), types.KeyboardButton('Бросить D4'))
            bot.send_message(message.chat.id, text='Выберите тип кубика :)'.format(message.from_user),
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw)


@bot.message_handler(content_types=['text', 'photo'])
def handle_edefaultor(message):
    bot.send_message(message.chat.id,
                     text='*СЛИШКОМ МНОГО БУКВ 😳😳😳*\nВозможно, вы ввели большой текст и телеграм'
                          ' автоматически разделил его на несколько частей, так как у телеграмма есть свои '
                          'ограничения по количеству символов в посте.\nЕсли вы заполняли расписание, то в расписание '
                          'попала лишь часть введённого вами текста :(\nВам нужно сократить текст, иначе '
                          'вы не сможете анонсировать ваши игры одним сообщением.\nОтредактируйте ваш текст :)'
                     .format(message.from_user), parse_mode='Markdown')


def player_master_admin(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        admins = get_admins()
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Я — мастер :)':
                        check_games_master(username)
                        main_menu = main_menu_master(message)
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, выберите, что хотите сделать :)'.
                                         format(message.from_user), reply_markup=main_menu, )
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text == 'Я — игрок :)':
                        check_games_player(username)
                        main_menu = main_menu_player(message)
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, выберите, что хотите сделать :)'.
                                         format(message.from_user), reply_markup=main_menu)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text == 'Я — администратор :)':
                        main_menu = main_menu_admin(message)
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, выберите, что хотите сделать :)'.
                                         format(message.from_user), reply_markup=main_menu)
                        bot.register_next_step_handler(message, admin_actions)
                    else:
                        raise ConvertionException('Выберите из нескольких вариантов на кнопках :)".\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')

            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                if username in admins:
                    markup.add(types.KeyboardButton('Я — мастер :)'), types.KeyboardButton('Я — игрок :)'),
                               types.KeyboardButton('Добавить группу для анонсов :)'))
                else:
                    markup.add(types.KeyboardButton('Я — мастер :)'), types.KeyboardButton('Я — игрок :)'))

                bot.send_message(message.chat.id, text='Нужно выбрать вариант, указанный на кнопках 😌\n—\nИли '
                                                       'выберите нужную команду в синей плашке меню :)'.
                                 format(message.from_user), reply_markup=markup)
                bot.register_next_step_handler(message, player_master_admin)

        except ConvertionException as e:
            delete_announce_game(username)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            if username in admins:
                markup.add(types.KeyboardButton('Я — мастер :)'), types.KeyboardButton('Я — игрок :)'),
                           types.KeyboardButton('Добавить группу для анонсов :)'))
                bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
                bot.register_next_step_handler(message, player_master_admin)
            else:
                markup.add(types.KeyboardButton('Я — мастер :)'), types.KeyboardButton('Я — игрок :)'))
                bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
                bot.register_next_step_handler(message, player_master_admin)


def throw(message: telebot.types.Message):
    if message.chat.type == 'private':
        text = 'Какое количество кубиков бросать? Напиши только число :)'
        user_name = message.from_user.first_name
        try:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Бросить D20':
                    bot.send_message(message.chat.id, text)
                    bot.register_next_step_handler(message, throw_d20)
                elif message.text == 'Бросить D12':
                    bot.send_message(message.chat.id, text)
                    bot.register_next_step_handler(message, throw_d12)
                elif message.text == 'Бросить D10':
                    bot.send_message(message.chat.id, text)
                    bot.register_next_step_handler(message, throw_d10)
                elif message.text == 'Бросить D8':
                    bot.send_message(message.chat.id, text)
                    bot.register_next_step_handler(message, throw_d8)
                elif message.text == 'Бросить D6':
                    bot.send_message(message.chat.id, text)
                    bot.register_next_step_handler(message, throw_d6)
                elif message.text == 'Бросить D4':
                    bot.send_message(message.chat.id, text)
                    bot.register_next_step_handler(message, throw_d4)
                else:
                    raise ConvertionException('Выберите тип кубика :)\n—\nИли выберите нужную команду в синей '
                                              'плашке меню :)')
        except ConvertionException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton('Бросить D20'), types.KeyboardButton('Бросить D12'),
                       types.KeyboardButton('Бросить D10'), types.KeyboardButton('Бросить D8'),
                       types.KeyboardButton('Бросить D6'), types.KeyboardButton('Бросить D4'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, throw)


def check(message: telebot.types.Message):
    pass


def throw_d20(message: telebot.types.Message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text.isdigit():
                        result = []
                        for i in range(int(message.text)):
                            new_digit = random.randrange(1, 20, 1)
                            result.append(new_digit)
                        markup.add(types.KeyboardButton('Бросить ещё раз?'))
                        bot.send_message(message.chat.id, f'{user_name}, результат вашего броска\n\n 🎲 {result} 🎲',
                                         reply_markup=markup)
                        bot.register_next_step_handler(message, roll_the_dice)
                    else:
                        raise ConvertionException('Вы не ввели число или ввели его некорректоно :(\nНапишите ниже, '
                                                  '*какое количество кубиков D20 бросить*.\nНапример, 3 :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели количество кубиков, которое нужно бросить 😔\n'
                                                       'Напишите ниже, *какое количество кубиков D20 бросить*.\n'
                                                       'Например, 3 :)'.format(message.from_user),
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, throw_d20)
        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', parse_mode='Markdown',
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw_d20)


def throw_d12(message: telebot.types.Message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text.isdigit():
                        result = []
                        for i in range(int(message.text)):
                            new_digit = random.randrange(1, 12, 1)
                            result.append(new_digit)
                        markup.add(types.KeyboardButton('Бросить ещё раз?'))
                        bot.send_message(message.chat.id, f'{user_name}, результат вашего броска\n\n 🎲 {result} 🎲',
                                         reply_markup=markup)
                        bot.register_next_step_handler(message, roll_the_dice)
                    else:
                        raise ConvertionException('Вы не ввели число :(\nНапишите ниже, *какое количество кубиков D12 '
                                                  'бросить*.\nНапример, 3 :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели количество кубиков, которое нужно бросить 😔\n'
                                                       'Напишите ниже, *какое количество кубиков D12 бросить*.\n'
                                                       'Например, 3 :)'.format(message.from_user),
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, throw_d12)
        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', parse_mode='Markdown',
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw_d12)


def throw_d10(message: telebot.types.Message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text.isdigit():
                        result = []
                        for i in range(int(message.text)):
                            new_digit = random.randrange(1, 10, 1)
                            result.append(new_digit)
                        markup.add(types.KeyboardButton('Бросить ещё раз?'))
                        bot.send_message(message.chat.id, f'{user_name}, результат вашего броска\n\n 🎲 {result} 🎲',
                                         reply_markup=markup)
                        bot.register_next_step_handler(message, roll_the_dice)
                    else:
                        raise ConvertionException('Вы не ввели число :(\nНапишите ниже, *какое количество кубиков D10 '
                                                  'бросить*.\nНапример, 3 :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели количество кубиков, которое нужно бросить 😔\n'
                                                       'Напишите ниже, *какое количество кубиков D10 бросить*.\n'
                                                       'Например, 3 :)'.format(message.from_user),
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, throw_d10)
        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', parse_mode='Markdown',
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw_d10)


def throw_d8(message: telebot.types.Message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text.isdigit():
                        result = []
                        for i in range(int(message.text)):
                            new_digit = random.randrange(1, 8, 1)
                            result.append(new_digit)
                        markup.add(types.KeyboardButton('Бросить ещё раз?'))
                        bot.send_message(message.chat.id, f'{user_name}, результат вашего броска\n\n 🎲 {result} 🎲',
                                         reply_markup=markup)
                        bot.register_next_step_handler(message, roll_the_dice)
                    else:
                        raise ConvertionException('Вы не ввели число :(\nНапишите ниже, *какое количество кубиков D8 '
                                                  'бросить*.\nНапример, 3 :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели количество кубиков, которое нужно бросить 😔\n'
                                                       'Напишите ниже, *какое количество кубиков D8 бросить*.\n'
                                                       'Например, 3 :)'.format(message.from_user),
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, throw_d8)
        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', parse_mode='Markdown',
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw_d8)


def throw_d6(message: telebot.types.Message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text.isdigit():
                        result = []
                        for i in range(int(message.text)):
                            new_digit = random.randrange(1, 6, 1)
                            result.append(new_digit)
                        markup.add(types.KeyboardButton('Бросить ещё раз?'))
                        bot.send_message(message.chat.id, f'{user_name}, результат вашего броска\n\n 🎲 {result} 🎲',
                                         reply_markup=markup)
                        bot.register_next_step_handler(message, roll_the_dice)
                    else:
                        raise ConvertionException('Вы не ввели число :(\nНапишите ниже, *какое количество кубиков D6 '
                                                  'бросить*.\nНапример, 3 :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели количество кубиков, которое нужно бросить 😔\n'
                                                       'Напишите ниже, *какое количество кубиков D6 бросить*.\n'
                                                       'Например, 3 :)'.format(message.from_user),
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, throw_d6)
        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', parse_mode='Markdown',
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw_d6)


def throw_d4(message: telebot.types.Message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text.isdigit():
                        result = []
                        for i in range(int(message.text)):
                            new_digit = random.randrange(1, 4, 1)
                            result.append(new_digit)
                        markup.add(types.KeyboardButton('Бросить ещё раз?'))
                        bot.send_message(message.chat.id, f'{user_name}, результат вашего броска\n\n 🎲 {result} 🎲',
                                         reply_markup=markup)
                        bot.register_next_step_handler(message, roll_the_dice)
                    else:
                        raise ConvertionException('Вы не ввели число :(\nНапишите ниже, *какое количество кубиков D4 '
                                                  'бросить*.\nНапример, 3 :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели количество кубиков, которое нужно бросить 😔\n'
                                                       'Напишите ниже, *какое количество кубиков D4 бросить*.\n'
                                                       'Например, 3 :)'.format(message.from_user),
                                 parse_mode='Markdown')
                bot.register_next_step_handler(message, throw_d4)
        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', parse_mode='Markdown',
                             reply_markup=markup)
            bot.register_next_step_handler(message, throw_d4)


def admin_actions(message: telebot.types.Message):
    if message.chat.type == 'private':
        username = message.from_user.username
        delete_announce_game(username)
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        user_last_name = message.from_user.last_name
        check_games_master(username)
        number_of_games = get_data_for_master(username, 'show_games_one_master')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        chats = get_chats('get_name', '')
        games = get_data_for_player(username, 'show_games')
        global games_for_admin
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    games_for_admin = []
                    start(message)
                elif message.text == '/help_me':
                    games_for_admin = []
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    games_for_admin = []
                    roll_the_dice(message)
                elif message.text == 'Вернуться в главное меню':
                    games_for_admin = []
                    back_to_main_menu_admin(message)
                    bot.register_next_step_handler(message, admin_actions)
                else:
                    if message.text in chats:
                        markup.add(types.KeyboardButton('Да, хочу удалить группу 😌'),
                                   types.KeyboardButton('Вернуться в главное меню'))
                        bot.send_message(message.chat.id, text='Удалить эту группу? После удаления мастера не смогут '
                                                               'анонсировать там свои игры :('
                                         .format(message.from_user), reply_markup=markup)
                        bot.register_next_step_handler(message, admin_actions)
                    elif message.text in games:
                        indexes = []
                        for i in range(len(message.text)):
                            if message.text[i] == '"':
                                indexes.append(i)
                        first = indexes[0] + 1
                        game = message.text[first:indexes[1]]
                        games_for_admin.append(game)
                        answer = get_data_for_player(game, 'show_concrete_game')
                        markup.add(types.KeyboardButton('Да, хочу удалить игру 😌'),
                                   types.KeyboardButton('Вернуться в главное меню'))
                        if type(answer) is list:
                            photo = answer[0]
                            text = answer[1]
                            bot.send_photo(message.chat.id, photo, text, parse_mode='Markdown')
                            bot.send_message(message.chat.id, text='Удалить игру?', reply_markup=markup)
                            bot.register_next_step_handler(message, admin_actions)
                        else:
                            bot.send_message(message.chat.id, answer, parse_mode='Markdown')
                            bot.send_message(message.chat.id, text='Удалить игру?', reply_markup=markup)
                            bot.register_next_step_handler(message, admin_actions)
                    elif message.text == 'Да, хочу удалить группу 😌':
                        pass
                    elif message.text == 'Да, хочу удалить игру 😌':
                        game = games_for_admin[-1]
                        games_for_admin = []
                        delete_game(game, 'admin')
                        bot.send_message(message.chat.id, text=f'{user_name}, вы удалили игру :)')
                        back_to_main_menu_admin(message)
                        bot.register_next_step_handler(message, admin_actions)
                    elif message.text == 'Добавить группу для анонсов :)':
                        bot.send_message(message.chat.id, text='Убедитесь, что группа, которую вы хотите добавить, '
                                                               'публичная и что этот бот в ней состоит.\nЕсли не '
                                                               'состоит, то попросите админов группы добавить бота :)'
                                                               '\nСкопируйте ссылку на группу и вставьте ниже :)'
                                         .format(message.from_user))
                        bot.register_next_step_handler(message, write_chats)
                    elif message.text == 'Список групп':
                        if len(chats) == 0:
                            main_menu = main_menu_admin(message)
                            bot.send_message(message.chat.id, text=f'{user_name}, здесь пока нет чатов с играми :(')
                            bot.send_message(message.chat.id, text='{0.first_name}, выберите, что хотите сделать :)'
                                             .format(message.from_user), reply_markup=main_menu, )
                            bot.register_next_step_handler(message, admin_actions)
                        else:
                            for chat in chats:
                                markup.add(chat)
                            markup.add('Вернуться в главное меню')
                            bot.send_message(message.chat.id,
                                             text=f'{user_name}, если вы хотите удалить группу из списка, то нажмите '
                                                  f'на эту группу :)', reply_markup=markup)
                            bot.register_next_step_handler(message, admin_actions)
                    elif message.text == 'Список игр':
                        if len(games) == 0:
                            bot.send_message(message.chat.id, text='Мастера ещё не выложили своё расписание😔\n'
                                                                   'Посмотрите немного позже 👀')
                            back_to_main_menu_admin(message)
                            bot.register_next_step_handler(message, admin_actions)
                        else:
                            for game in games:
                                markup.add(types.KeyboardButton(game))
                            markup.add(types.KeyboardButton('Вернуться в главное меню'))
                            bot.send_message(message.chat.id, text="{0.first_name}, выберите игру, которую хотите "
                                                                   "посмотреть :)".format(message.from_user),
                                             reply_markup=markup)
                            bot.register_next_step_handler(message, admin_actions)
                    else:
                        raise ConvertionException('Выберите один из вариантов, представленных ниже :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                result = main_menu_admin(message)
                bot.send_message(message.chat.id,
                                 text='{0.first_name}, выберите один из вариантов, представленных ниже :)\n—\nИли '
                                      'выберите нужную команду в синей плашке меню :)'.format(message.from_user),
                                 reply_markup=result)
                bot.register_next_step_handler(message, admin_actions)

        except ConvertionException as e:
            result = main_menu_admin(message)
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=result)
            bot.register_next_step_handler(message, admin_actions)


def write_chats(message):
    if message.chat.type == 'private':
        user_name = message.from_user.first_name
        btn_back = btn_back_to_main_menu(message)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                elif message.text == 'Вернуться в главное меню':
                    back_to_main_menu_admin(message)
                    bot.register_next_step_handler(message, admin_actions)
                else:
                    if message.text[0:13] == 'https://t.me/' or message.text[0:5] == 't.me/':
                        if message.text[0:5] == 't.me/':
                            link = 'https://' + message.text
                        else:
                            link = message.text
                        if not check_replay_links(link):
                            id_group = bot.get_chat('@' + link[13:]).id
                            if not check_bot_group_membership(TOKEN, id_group):
                                bot.send_message(message.chat.id, text="Бот ещё не состоит в этой группе и поэтому не "
                                                                       "сможет выкладывать там анонсы :(\nПопросите "
                                                                       "админов группы добавить бота в участники и "
                                                                       "попробуйте добавить группу снова :)".
                                                 format(message.from_user), reply_markup=btn_back)
                                bot.register_next_step_handler(message, write_chats)
                            elif check_bot_group_membership(TOKEN, id_group):
                                add_chats_to_database(link)
                                bot.send_message(message.chat.id, text="Группа добавлена! Теперь пользователи смогут "
                                                                       "анонсировать свои игры :)\nВернитесь в начало "
                                                                       "для дальнейшей работы с ботом :)".
                                                 format(message.from_user), reply_markup=btn_back)
                                bot.register_next_step_handler(message, write_chats)
                        elif check_replay_links(link):
                            bot.send_message(message.chat.id, text='Такая группа уже есть в списке :)\nВернитесь '
                                                                   'в начало для дальнейшей работы с ботом :)'.
                                             format(message.from_user), reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_chats)

                    else:
                        raise ConvertionException(f'Какая-то ошибка в вашей ссылке - <{message.text}>\n'
                                                  f'Ссылка должна выглядеть так "https: // t.me /<название>"\n'
                                                  f'Скопируйте и вставьте ссылку на телеграмм группу :)'
                                                  '\n—\nИли выберите нужную команду в синей плашке меню :)')
            else:
                bot.send_message(message.chat.id, text='Вы не ввели ссылку 😔\nСкопируйте и вставьте ссылку на '
                                                       'телеграмм группу :)\n—\nИли выберите нужную команду в синей '
                                                       'плашке меню :)'.
                                 format(message.from_user), reply_markup=btn_back)
                bot.register_next_step_handler(message, write_chats)

        except ConvertionException as e:
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}')
            bot.register_next_step_handler(message, write_chats)


def master_actions(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        delete_announce_game(username)
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        user_last_name = message.from_user.last_name
        check_games_master(username)
        number_of_games = get_data_for_master(username, 'show_games_one_master')
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu(message)
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text == 'Добавить игру':
                        add_master(username, '-', user_id, user_name, user_last_name)
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                        markup.add(types.KeyboardButton('Быстрое расписание :)'),
                                   types.KeyboardButton('Подробное расписание :)'),
                                   types.KeyboardButton('Вернуться в главное меню'))
                        bot.send_message(message.chat.id,
                                         text='Вы можете создать расписание самостоятельно и загрузить описание своей '
                                              'игры или создайте расписание при помощи бота :)'
                                         .format(message.from_user), reply_markup=markup, )
                        bot.register_next_step_handler(message, quick_or_detailed)
                    elif message.text == 'Редактировать игру':
                        if len(number_of_games) == 0:
                            btn_back = btn_back_to_main_menu(message)
                            bot.send_message(message.chat.id,
                                             text='У вас пока нет игр в расписании 🎲🎲🎲', reply_markup=btn_back)
                            bot.register_next_step_handler(message, show_master_schedule)
                        else:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                            for i in range(len(number_of_games)):
                                btn = types.KeyboardButton(number_of_games[i])
                                markup.add(btn)
                            markup.add(types.KeyboardButton('Вернуться в главное меню'))
                            bot.send_message(message.chat.id,
                                             text='Выберите игру, которую хотите редактировать :)', reply_markup=markup)
                            bot.register_next_step_handler(message, edit_master_schedule)
                    elif message.text == 'Список моих игр':
                        if len(number_of_games) == 0:
                            btn_back = btn_back_to_main_menu(message)
                            bot.send_message(message.chat.id,
                                             text='У вас пока нет игр в расписании 🎲🎲🎲', reply_markup=btn_back)
                            bot.register_next_step_handler(message, show_master_schedule)
                        else:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                            for i in range(len(number_of_games)):
                                btn = types.KeyboardButton(number_of_games[i])
                                markup.add(btn)
                            markup.add(types.KeyboardButton('Вернуться в главное меню'))
                            bot.send_message(message.chat.id,
                                             text='Выберите игру, которую хотите посмотреть :)', reply_markup=markup)
                            bot.register_next_step_handler(message, show_master_schedule)
                    elif message.text == 'Да, хочу удалиться, надоело всё уже 😐':
                        delete_master(username)
                        bot.send_message(message.chat.id, text='{0.first_name}, вы удалились из бота :)'
                                         .format(message.from_user))
                    elif message.text == 'Нет, я передумал! Я остаюсь 😉':
                        check_games_master(username)
                        result = main_menu_master(message)
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, выберите, что хотите сделать :)'
                                         .format(message.from_user), reply_markup=result, )
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text == 'Удалиться из бота':
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                        markup.add(types.KeyboardButton('Да, хочу удалиться, надоело всё уже 😐'),
                                   types.KeyboardButton('Нет, я передумал! Я остаюсь 😉'))
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, вы точно хотите удалиться из бота?\nТогда все ваши '
                                              'записи тоже удалятся :('.format(message.from_user), reply_markup=markup)
                        bot.register_next_step_handler(message, master_actions)
                    else:
                        raise ConvertionException('Выберите один из вариантов, представленных ниже :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                result = main_menu_master(message)
                bot.send_message(message.chat.id,
                                 text='{0.first_name}, выберите один из вариантов, представленных ниже :)\n—\nИли '
                                      'выберите нужную команду в синей плашке меню :)'.format(message.from_user),
                                 reply_markup=result)
                bot.register_next_step_handler(message, master_actions)

        except ConvertionException as e:
            result = main_menu_master(message)
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=result)
            bot.register_next_step_handler(message, master_actions)


def quick_or_detailed(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu(message)
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text == 'Быстрое расписание :)':
                        master_short_elements = master_short_schedule_elements(username)
                        bot.send_message(message.chat.id,
                                         text='Выберите нужный пункт и заполните его :)'.format(message.from_user),
                                         reply_markup=master_short_elements)
                        bot.register_next_step_handler(message, short_schedule)

                    elif message.text == 'Подробное расписание :)':
                        master_elements = master_schedule_elements(username)
                        bot.send_message(message.chat.id,
                                         text='Выберите нужный пункт и заполните его :)'.format(message.from_user),
                                         reply_markup=master_elements, )
                        bot.register_next_step_handler(message, master_schedule)
                    else:
                        raise ConvertionException('Выберите один из вариантов, представленных ниже :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add(types.KeyboardButton('Быстрое расписание :)'),
                           types.KeyboardButton('Подробное расписание :)'),
                           types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id,
                                 text='Выберите один из вариантов, представленных ниже на кнопках:)\n—\nИли выберите '
                                      'нужную команду в синей плашке меню :)'.format(message.from_user),
                                 reply_markup=markup, )
                bot.register_next_step_handler(message, quick_or_detailed)

        except ConvertionException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton('Быстрое расписание :)'),
                       types.KeyboardButton('Подробное расписание :)'),
                       types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, quick_or_detailed)


def short_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu(message)
                        bot.register_next_step_handler(message, master_actions)
                    else:
                        btn_back = btn_back_to_main_menu(message)
                        if message.text == 'Название' or message.text == '✅ — Название':
                            bot.send_message(message.chat.id, text='Как будет называться ваша игра? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_title_short)
                        elif message.text == 'Описание' or message.text == '✅ — Описание':
                            bot.send_message(message.chat.id, text='Пожалуйста, напишите краткое (или не краткое) '
                                                                   'описание своей игры :)', reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_description_short)
                        elif message.text == 'Заставка для игры' or message.text == '✅ — Заставка для игры':
                            bot.send_message(message.chat.id, text='Загрузите заставку для вашей игры :)\nЕсли вы '
                                                                   'хотите удалить заставку, то просто напишите в '
                                                                   'сообщении "-" '
                                                                   ':)', reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_photo_short)
                        elif message.text == 'Посмотреть расписание этой игры 🎲':
                            check_games_master(username)
                            result = main_menu_master(message)
                            number_of_games = get_data_for_master(username, 'show_games_one_master')
                            if len(number_of_games) == 0:
                                bot.send_message(message.chat.id,
                                                 text='У вас пока нет игр в расписании 🎲🎲🎲', reply_markup=result)
                                bot.register_next_step_handler(message, master_actions)
                            else:
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                   is_persistent=False)
                                picture = get_data_for_master(username, 'show_photo')
                                announcement = announce_game(username, 'show')
                                len_text = announcement[1]
                                text = announcement[0]
                                if picture != '-':
                                    if len_text <= 1024:
                                        bot.send_photo(message.chat.id, picture, text, parse_mode='Markdown')
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Анонсировать эту игру 🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id, text='{0.first_name}, расписание вашей игры '
                                                                               'составлено :)'.
                                                         format(message.from_user), reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте под '
                                                f'картинкой и не сможете выложить анонс вместе с заставкой :(\nДлина '
                                                f'вашего текста сейчас = {len_text}, а допустимое количество символов '
                                                f'= 1024 :(\nОтредактируйте ваше расписание: уменьшите количество '
                                                f'текста или уберите картинку 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                elif picture == '-':
                                    if len_text <= 4096:
                                        bot.send_message(message.chat.id, text, parse_mode='Markdown')
                                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                           is_persistent=False)
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Анонсировать эту игру 🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id, text='{0.first_name}, расписание вашей игры '
                                                                               'составлено :)'.
                                                         format(message.from_user), reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте :(\n'
                                                f'Длина вашего текста сейчас = {len_text}, а допустимое количество '
                                                f'символов = 4096 :(\nОтредактируйте ваше расписание: уменьшите '
                                                f'количество текста 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                        elif message.text == 'Анонсировать эту игру 🔥':
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                               is_persistent=False)
                            announcement = announce_game(username, 'announce')
                            chats = get_chats('get_name', '-')
                            picture = get_data_for_master(username, 'show_photo')
                            len_text = announcement[1]
                            text = announcement[0]
                            if len(chats) == 0:
                                result = main_menu_master(message)
                                bot.send_message(message.chat.id, text=f'{user_name}, здесь пока нет чатов с играми, '
                                                                       f'в которые можно анонсировать вашу игру :(')
                                bot.send_message(message.chat.id,
                                                 text='{0.first_name}, выберите, что хотите сделать :)'.format(
                                                     message.from_user),
                                                 reply_markup=result, )
                                bot.register_next_step_handler(message, master_actions)
                            else:
                                if picture != '-':
                                    if len_text <= 1024:
                                        bot.send_photo(message.chat.id, picture, text, parse_mode='Markdown')
                                        for chat in chats:
                                            markup.add(chat)
                                        markup.add(types.KeyboardButton('🔥🔥🔥 Выложить во все эти группы '
                                                                        '🔥🔥🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id,
                                                         text=f'{user_name}, ваш анонс готов!\nВыберите, в какую '
                                                              f'группу запостить объявление об игре :)',
                                                         reply_markup=markup)
                                        bot.register_next_step_handler(message, send_announcement)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте под '
                                                f'картинкой и не сможете выложить анонс вместе с заставкой :(\nДлина '
                                                f'вашего текста сейчас = {len_text}, а допустимое количество символов '
                                                f'= 1024 :(\nОтредактируйте ваше расписание: уменьшите количество '
                                                f'текста или уберите картинку 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                elif picture == '-':
                                    if len_text <= 4096:
                                        bot.send_message(message.chat.id, text, parse_mode='Markdown')
                                        for chat in chats:
                                            markup.add(chat)
                                        markup.add(types.KeyboardButton('🔥🔥🔥 Выложить во все эти группы '
                                                                        '🔥🔥🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id,
                                                         text=f'{user_name}, ваш анонс готов!\nВыберите, в какую группу'
                                                              f' запостить объявление об игре :)', reply_markup=markup)
                                        bot.register_next_step_handler(message, send_announcement)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте :(\n'
                                                f'Длина вашего текста сейчас = {len_text}, а допустимое количество '
                                                f'символов = 4096 :(\nОтредактируйте ваше расписание: уменьшите '
                                                f'количество текста 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                        elif message.text == 'Удалить игру':
                            check_games_master(username)
                            result = main_menu_master(message)
                            number_of_games = get_data_for_master(username, 'show_games_one_master')
                            if len(number_of_games) == 0:
                                bot.send_message(message.chat.id,
                                                 text='У вас пока нет игр в расписании 🎲🎲🎲', reply_markup=result)
                                bot.register_next_step_handler(message, master_actions)
                            else:
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                                markup.add(types.KeyboardButton('ДА'), types.KeyboardButton('НЕТ'))
                                result = get_data_for_master(username, 'get_game')
                                inf = f'Вы точно хотите удалить эту игру?\n🎲🎲🎲\n"{result}"'
                                bot.send_message(message.chat.id, text='{0.first_name}, '.format(message.from_user)
                                                                       + inf, reply_markup=markup)
                                bot.register_next_step_handler(message, delete_game_master)
                        else:
                            raise ConvertionException('Выберите один из вариантов, представленных на кнопках :)\n—\n'
                                                      'Или выберите нужную команду в синей плашке меню :)')
            else:
                result = master_short_schedule_elements(username)
                bot.send_message(message.chat.id, text='Выберите один из вариантов, представленных на кнопках :)\n—\n'
                                                       'Или выберите нужную команду в синей плашке меню :)',
                                 reply_markup=result)
                bot.register_next_step_handler(message, short_schedule)

        except ConvertionException as e:
            result = master_short_schedule_elements(username)
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=result)
            bot.register_next_step_handler(message, short_schedule)


def back_to_master_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        result = master_schedule_elements(username)
        bot.send_message(message.chat.id,
                         text='Выберите нужный пункт и заполните его :)'.
                         format(message.from_user), reply_markup=result, )
        bot.register_next_step_handler(message, master_schedule)


def back_to_master_short_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        result = master_short_schedule_elements(username)
        bot.send_message(message.chat.id,
                         text='Выберите нужный пункт и заполните его :)'.
                         format(message.from_user), reply_markup=result, )
        bot.register_next_step_handler(message, short_schedule)


def master_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu(message)
                        bot.register_next_step_handler(message, master_actions)
                    else:
                        btn_back = btn_back_to_main_menu(message)
                        if message.text == 'Название' or message.text == '✅ — Название':
                            bot.send_message(message.chat.id, text='Как будет называться ваша игра? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_title)
                        elif message.text == 'Система' or message.text == '✅ — Система':
                            bot.send_message(message.chat.id, text='По какой системе будет проходить игра? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_system)
                        elif message.text == 'Описание' or message.text == '✅ — Описание':
                            bot.send_message(message.chat.id, text='Пожалуйста, напишите краткое (или не краткое) '
                                                                   'описание своей игры :)', reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_description)
                        elif message.text == 'Длительность' or message.text == '✅ — Длительность':
                            bot.send_message(message.chat.id, text='На сколько сессий (примерно) вы планируете свою игру? '
                                                                   ':)', reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_duration)
                        elif message.text == 'Место проведения' or message.text == '✅ — Место проведения':
                            bot.send_message(message.chat.id, text='Напишите адрес, по которому будет проходить игра :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_address)
                        elif message.text == 'День' or message.text == '✅ — День':
                            bot.send_message(message.chat.id, text='В какой день вы планируете проводить игру? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_day)
                        elif message.text == 'Время' or message.text == '✅ — Время':
                            bot.send_message(message.chat.id, text='В какое время вы планируете проводить игру? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_time)
                        elif message.text == 'Подготовка' or message.text == '✅ — Подготовка':
                            bot.send_message(message.chat.id,
                                             text='Нужно ли как-то особенно готовиться к вашей игре? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_before_game)
                        elif message.text == 'Стоимость участия' or message.text == '✅ — Стоимость участия':
                            bot.send_message(message.chat.id,
                                             text='Напишите стоимость участия в вашей игре :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_cost)
                        elif message.text == 'Количество игроков' or message.text == '✅ — Количество игроков':
                            bot.send_message(message.chat.id, text='Напишите количество участников '
                                                                   'для вашей игры :)\nПросто напишите цифру, '
                                                                   'например: "4" или "3-5",если необходимо указать '
                                                                   'минимум и максимум участников',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_count_players)
                        elif message.text == 'Заставка для игры' or message.text == '✅ — Заставка для игры':
                            bot.send_message(message.chat.id, text='Загрузите заставку для вашей игры :)\nЕсли вы '
                                                                   'хотите удалить заставку, то просто напишите в '
                                                                   'сообщении "-" :)', reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_photo)
                        elif message.text == 'Дополнительно' or message.text == '✅ — Дополнительно':
                            bot.send_message(message.chat.id, text='Что бы вы ещё хотели добавить в расписание? :)',
                                             reply_markup=btn_back)
                            bot.register_next_step_handler(message, write_additionally)
                        elif message.text == 'Посмотреть расписание этой игры 🎲':
                            check_games_master(username)
                            result = main_menu_master(message)
                            number_of_games = get_data_for_master(username, 'show_games_one_master')
                            if len(number_of_games) == 0:
                                bot.send_message(message.chat.id,
                                                 text='У вас пока нет игр в расписании 🎲🎲🎲', reply_markup=result)
                                bot.register_next_step_handler(message, master_actions)
                            else:
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                   is_persistent=False)
                                picture = get_data_for_master(username, 'show_photo')
                                announcement = announce_game(username, 'show')
                                len_text = announcement[1]
                                text = announcement[0]
                                if picture != '-':
                                    if len_text <= 1024:
                                        bot.send_photo(message.chat.id, picture, text, parse_mode='Markdown')
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Анонсировать эту игру 🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id, text='{0.first_name}, расписание вашей игры '
                                                                               'составлено :)'
                                                         .format(message.from_user), reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте под '
                                                f'картинкой и не сможете выложить анонс вместе с заставкой :(\nДлина '
                                                f'вашего текста сейчас = {len_text}, а допустимое количество символов '
                                                f'= 1024 :(\nОтредактируйте ваше расписание: уменьшите количество '
                                                f'текста или уберите картинку 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                elif picture == '-':
                                    if len_text <= 4096:
                                        bot.send_message(message.chat.id, text, parse_mode='Markdown')
                                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                                           is_persistent=False)
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Анонсировать эту игру 🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id, text='{0.first_name}, расписание вашей игры '
                                                                               'составлено :)'
                                                         .format(message.from_user), reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте :(\n'
                                                f'Длина вашего текста сейчас = {len_text}, а допустимое количество '
                                                f'символов = 4096 :(\nОтредактируйте ваше расписание: уменьшите '
                                                f'количество текста 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)

                        elif message.text == 'Анонсировать эту игру 🔥':
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                               is_persistent=False)
                            announcement = announce_game(username, 'announce')
                            chats = get_chats('get_name', '-')
                            picture = get_data_for_master(username, 'show_photo')
                            len_text = announcement[1]
                            text = announcement[0]
                            if len(chats) == 0:
                                result = main_menu_master(message)
                                bot.send_message(message.chat.id, text=f'{user_name}, здесь пока нет чатов с играми, '
                                                                       f'в которые можно анонсировать вашу игру :(')
                                bot.send_message(message.chat.id,
                                                 text='{0.first_name}, выберите, что хотите сделать :)'.format(
                                                     message.from_user),
                                                 reply_markup=result, )
                                bot.register_next_step_handler(message, master_actions)
                            else:
                                if picture != '-':
                                    if len_text <= 1024:
                                        bot.send_photo(message.chat.id, picture, text, parse_mode='Markdown')
                                        for chat in chats:
                                            markup.add(chat)
                                        markup.add(types.KeyboardButton('🔥🔥🔥 Выложить во все эти группы '
                                                                        '🔥🔥🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id,
                                                         text=f'{user_name}, ваш анонс готов!\nВыберите, в какую '
                                                              f'группу запостить объявление об игре :)',
                                                         reply_markup=markup)
                                        bot.register_next_step_handler(message, send_announcement)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте под '
                                                f'картинкой и не сможете выложить анонс вместе с заставкой :(\nДлина '
                                                f'вашего текста сейчас = {len_text}, а допустимое количество символов '
                                                f'= 1024 :(\nОтредактируйте ваше расписание: уменьшите количество '
                                                f'текста или уберите картинку 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)
                                elif picture == '-':
                                    if len_text <= 4096:
                                        bot.send_message(message.chat.id, text, parse_mode='Markdown')
                                        for chat in chats:
                                            markup.add(chat)
                                        markup.add(types.KeyboardButton('🔥🔥🔥 Выложить во все эти группы '
                                                                        '🔥🔥🔥'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        bot.send_message(message.chat.id,
                                                         text=f'{user_name}, ваш анонс готов!\nВыберите, в какую '
                                                              f'группу запостить объявление об игре :)',
                                                         reply_markup=markup)
                                        bot.register_next_step_handler(message, send_announcement)
                                    else:
                                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                                   types.KeyboardButton('Вернуться в главное меню'))
                                        text = (f'{user_name}, Вы превысили допустимое количество символов в посте '
                                                f':(\nДлина вашего текста сейчас = {len_text}, а допустимое количество '
                                                f'символов = 4096 :(\nОтредактируйте ваше расписание: уменьшите '
                                                f'количество текста 😌')
                                        bot.send_message(message.chat.id, text, reply_markup=markup)
                                        bot.register_next_step_handler(message, master_additional_actions)

                        elif message.text == 'Удалить игру':
                            check_games_master(username)
                            result = main_menu_master(message)
                            number_of_games = get_data_for_master(username, 'show_games_one_master')
                            if len(number_of_games) == 0:
                                bot.send_message(message.chat.id,
                                                 text='У вас пока нет игр в расписании 🎲🎲🎲', reply_markup=result)
                                bot.register_next_step_handler(message, master_actions)
                            else:
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                                markup.add(types.KeyboardButton('ДА'), types.KeyboardButton('НЕТ'))
                                result = get_data_for_master(username, 'get_game')
                                inf = f'Вы точно хотите удалить эту игру?\n🎲🎲🎲\n"{result}"'
                                bot.send_message(message.chat.id, text='{0.first_name}, '.format(message.from_user)
                                                                       + inf, reply_markup=markup)
                                bot.register_next_step_handler(message, delete_game_master)

                        else:
                            raise ConvertionException('Выберите один из вариантов, представленных на кнопках :)\n—\n'
                                                      'Или выберите нужную команду в синей плашке меню :)')
            else:
                result = master_schedule_elements(username)
                bot.send_message(message.chat.id, text='Выберите один из вариантов, представленных на кнопках :)\n—\n'
                                                       'Или выберите нужную команду в синей плашке меню :)',
                                 reply_markup=result)
                bot.register_next_step_handler(message, master_schedule)

        except ConvertionException as e:
            result = master_schedule_elements(username)
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=result)
            bot.register_next_step_handler(message, master_schedule)


def write_title(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'title', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели название 😔\nВведите название ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_title)


def write_title_short(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'title', username)
                    back_to_master_short_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели название 😔\nВведите название ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_title_short)


def write_system(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'system', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели систему 😔\nВведите систему ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_system)


def write_description(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            elif message.text == 'Вернуться в главное меню':
                back_to_main_menu(message)
                bot.register_next_step_handler(message, master_actions)
            else:
                add_inf_masters(message.text, 'description', username)
                back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели описание 😔\nВведите описание ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_description)


def write_description_short(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            elif message.text == 'Вернуться в главное меню':
                back_to_main_menu(message)
                bot.register_next_step_handler(message, master_actions)
            else:
                add_inf_masters(message.text, 'description', username)
                back_to_master_short_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели описание 😔\nВведите описание ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_description)


def write_duration(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'duration', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели длительность игры 😔\nВведите длительность игры ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_duration)


def write_address(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'address', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели адрес 😔\nВведите адрес ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_address)


def write_day(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'day', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели день 😔\nВведите день ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_day)


def write_time(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'time', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели время 😔\nВведите время ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_time)


def write_before_game(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'before_game', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не написали, нужно ли готовиться к игре 😔\nВведите текст ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_before_game)


def write_cost(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'cost', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели стоимость 😔\nВведите стоимость ниже :)'
                                                   '\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_cost)


def write_count_players(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    result = check_count_players(message.text)
                    if result[0] == 0:
                        text = (f'В вашем ответе на вопрос про количество игроков что-то не так :(\n<{result[1]}>\n'
                                f'Пожалуйста, введите количество участников корректнее :)\n'
                                f'Например: "2" или "3-4".')
                        bot.send_message(message.chat.id, text.format(message.from_user), reply_markup=btn_back)
                        bot.register_next_step_handler(message, write_count_players)
                    if result[0] == 1:
                        add_inf_masters(result[1], 'count_players', username)
                        back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не ввели количество игроков 😔\nВведите количество игроков '
                                                   'ниже :)\n—\nИли выберите нужную команду в синей плашке меню :)'.
                             format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_count_players)


def write_photo(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        if message.text == '/start':
            start(message)
        elif message.text == '/help_me':
            help_me(message)
        elif message.text == '/roll_the_dice':
            roll_the_dice(message)
        elif message.text == 'Вернуться в главное меню':
            back_to_main_menu(message)
            bot.register_next_step_handler(message, master_actions)
        else:
            content_type = message.content_type
            if content_type != 'photo':
                if message.text == '-':
                    add_inf_masters(message.text, 'photo', username)
                    back_to_master_schedule(message)
                else:
                    btn_back = btn_back_to_main_menu(message)
                    bot.send_message(message.chat.id,
                                     text='Загрузите изображение, которое станет заставкой для вашей игры или напишите'
                                          ' "-" в сообщении, если хотите убрать заставку:)\n—\n'
                                          'Или выберите нужную команду в синей плашке меню :)'
                                     .format(message.from_user),reply_markup=btn_back)
                    bot.register_next_step_handler(message, write_photo)
            else:
                photo = message.photo[-1]  # Берем изображение с наибольшим разрешением
                add_inf_masters(photo.file_id, 'photo', username)
                back_to_master_schedule(message)


def write_photo_short(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        if message.text == '/start':
            start(message)
        elif message.text == '/help_me':
            help_me(message)
        elif message.text == '/roll_the_dice':
            roll_the_dice(message)
        elif message.text == 'Вернуться в главное меню':
            back_to_main_menu(message)
            bot.register_next_step_handler(message, master_actions)
        else:
            content_type = message.content_type
            if content_type != 'photo':
                if message.text == '-':
                    add_inf_masters(message.text, 'photo', username)
                    back_to_master_schedule(message)
                else:
                    btn_back = btn_back_to_main_menu(message)
                    bot.send_message(message.chat.id,
                                     text='Загрузите изображение, которое станет заставкой для вашей игры или напишите'
                                          ' "-" в сообщении, если хотите убрать заставку:)\n—\n'
                                          'Или выберите нужную команду в синей плашке меню :)'.
                                     format(message.from_user), reply_markup=btn_back)
                    bot.register_next_step_handler(message, write_photo)
            else:
                photo = message.photo[-1]  # Берем изображение с наибольшим разрешением
                add_inf_masters(photo.file_id, 'photo', username)
                back_to_master_short_schedule(message)


def write_additionally(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        btn_back = btn_back_to_main_menu(message)
        if type(message.text) is str:
            if message.text == '/start':
                start(message)
            elif message.text == '/help_me':
                help_me(message)
            elif message.text == '/roll_the_dice':
                roll_the_dice(message)
            else:
                if message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    add_inf_masters(message.text, 'additionally', username)
                    back_to_master_schedule(message)
        else:
            bot.send_message(message.chat.id, text='Вы не указали, нужно ли как-то дополнительно готовиться к игре 😔'
                                                   '\nВведите текст ниже :)\n—\nИли выберите нужную команду в синей '
                                                   'плашке меню :)'.format(message.from_user), reply_markup=btn_back)
            bot.register_next_step_handler(message, write_additionally)


def show_master_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        games = get_data_for_master(username, 'show_games_one_master')
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu(message)
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text in games:
                        position = games.index(message.text)
                        copy_game(position, username)
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                           is_persistent=False)
                        markup.add(types.KeyboardButton('Редактировать эту игру'),
                                   types.KeyboardButton('Анонсировать эту игру 🔥'),
                                   types.KeyboardButton('Вернуться в главное меню'))

                        announcement = announce_game(username, 'show')
                        picture = get_data_for_master(username, 'show_photo')
                        if len(picture) > 1:
                            bot.send_photo(message.chat.id, picture, announcement[0], parse_mode='Markdown',
                                           reply_markup=markup)
                            bot.register_next_step_handler(message, master_additional_actions)
                        elif len(picture) == 1:
                            bot.send_message(message.chat.id, announcement[0], parse_mode='Markdown',
                                             reply_markup=markup)
                            bot.register_next_step_handler(message, master_additional_actions)

                    else:
                        raise ConvertionException('Выберите игру, которую хотите посмотреть :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                answer = get_data_for_master(username, 'show_games_one_master')
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for i in range(len(answer)):
                    btn = types.KeyboardButton(answer[i])
                    markup.add(btn)
                markup.add(types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id, text='Выберите игру, которую хотите посмотреть :)\n—\nИли выберите '
                                                       'нужную команду в синей плашке меню :)', reply_markup=markup)
                bot.register_next_step_handler(message, show_master_schedule)

        except ConvertionException as e:
            answer = get_data_for_master(username, 'show_games_one_master')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in range(len(answer)):
                btn = types.KeyboardButton(answer[i])
                markup.add(btn)
            markup.add(types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, show_master_schedule)


def edit_master_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        games = get_data_for_master(username, 'show_games_one_master')
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                elif message.text == 'Вернуться в главное меню':
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    if message.text in games:
                        position = games.index(message.text)
                        copy_game(position, username)
                        announcement = announce_game(username, 'show')
                        picture = get_data_for_master(username, 'show_photo')
                        result = master_schedule_elements(username)
                        if picture != '-':
                            bot.send_photo(message.chat.id, picture, announcement[0], parse_mode='Markdown')
                            bot.send_message(message.chat.id,
                                             text='Выберите, что бы вы хотели изменить :)'.format(message.from_user),
                                             reply_markup=result, )
                            bot.register_next_step_handler(message, master_schedule)
                        elif picture == '-':
                            bot.send_message(message.chat.id, announcement[0], parse_mode='Markdown')
                            bot.send_message(message.chat.id,
                                             text='Выберите, что бы вы хотели изменить :)\nЕсли хотите удалить '
                                                  'какой-то пункт, то нажмите на него и введите "-" :)'
                                             .format(message.from_user), reply_markup=result, )
                            bot.register_next_step_handler(message, master_schedule)
                    else:
                        raise ConvertionException('Выберите игру, которую хотите редактировать :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                answer = get_data_for_master(username, 'show_games_one_master')
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for i in range(len(answer)):
                    btn = types.KeyboardButton(answer[i])
                    markup.add(btn)
                markup.add(types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id, text='Выберите игру, которую хотите редактировать :)\n—\nИли выберите'
                                                       ' нужную команду в синей плашке меню :)', reply_markup=markup)
                bot.register_next_step_handler(message, edit_master_schedule)
        except ConvertionException as e:
            answer = get_data_for_master(username, 'show_games_one_master')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in range(len(answer)):
                btn = types.KeyboardButton(answer[i])
                markup.add(btn)
            markup.add(types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, edit_master_schedule)


def master_additional_actions(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        check_games_master(username)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu(message)
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text == 'Редактировать эту игру':
                        result = master_schedule_elements(username)
                        bot.send_message(message.chat.id,
                                         text='Выберите, что бы вы хотели изменить :)\nЕсли хотите удалить какой-то '
                                              'пункт, то нажмите на него и введите "-" :)'.format(message.from_user),
                                         reply_markup=result, )
                        bot.register_next_step_handler(message, master_schedule)
                    elif message.text == 'Анонсировать эту игру 🔥':
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                           is_persistent=False)
                        announcement = announce_game(username, 'announce')
                        chats = get_chats('get_name', '')
                        if len(chats) == 0:
                            result = main_menu_master(message)
                            bot.send_message(message.chat.id, text=f'{user_name}, здесь пока нет чатов с играми, '
                                                                   f'в которые можно анонсировать вашу игру :(')
                            bot.send_message(message.chat.id,
                                             text='{0.first_name}, выберите, что хотите сделать :)'.format(
                                                 message.from_user),
                                             reply_markup=result, )
                            bot.register_next_step_handler(message, master_actions)
                        else:
                            picture = get_data_for_master(username, 'show_photo')
                            if picture != '-':
                                bot.send_photo(message.chat.id, picture, announcement[0], parse_mode='Markdown')
                                for chat in chats:
                                    markup.add(chat)
                                markup.add(types.KeyboardButton('🔥🔥🔥 Выложить во все эти группы 🔥🔥🔥'),
                                           types.KeyboardButton('Вернуться в главное меню'))
                                bot.send_message(message.chat.id,
                                                 text=f'{user_name}, ваш анонс готов!\nВыберите, в какую группу '
                                                      f'запостить объявление об игре :)', reply_markup=markup)
                                bot.register_next_step_handler(message, send_announcement)
                            elif picture == '-':
                                bot.send_message(message.chat.id, announcement[0], parse_mode='Markdown')
                                for chat in chats:
                                    markup.add(chat)
                                markup.add(types.KeyboardButton('🔥🔥🔥 Выложить во все эти группы 🔥🔥🔥'),
                                           types.KeyboardButton('Вернуться в главное меню'))
                                bot.send_message(message.chat.id,
                                                 text=f'{user_name}, ваш анонс готов!\nВыберите, в какую группу '
                                                      f'запостить объявление об игре :)', reply_markup=markup)
                                bot.register_next_step_handler(message, send_announcement)
                    else:
                        raise MyCustomException('Выберите один из вариантов, представленных ниже :)\n—\n'
                                                'Или выберите нужную команду в синей плашке меню :)')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
                markup.add(types.KeyboardButton('Редактировать эту игру'),
                           types.KeyboardButton('Анонсировать эту игру'),
                           types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id, text='Выберите один из вариантов, представленных ниже :)\n—\nИли '
                                                       'выберите нужную команду в синей плашке меню :)',
                                 reply_markup=markup)
                bot.register_next_step_handler(message, master_additional_actions)
        except MyCustomException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
            markup.add(types.KeyboardButton('Редактировать эту игру'),
                       types.KeyboardButton('Анонсировать эту игру'),
                       types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, master_additional_actions)


def send_announcement(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        check_games_master(username)
        user_name = message.from_user.first_name
        chats = get_chats('get_name', '')
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    delete_announce_game(username)
                    start(message)
                elif message.text == '/help_me':
                    delete_announce_game(username)
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    delete_announce_game(username)
                    roll_the_dice(message)
                elif message.text == 'Вернуться в главное меню':
                    delete_announce_game(username)
                    back_to_main_menu(message)
                    bot.register_next_step_handler(message, master_actions)
                else:
                    if message.text == 'Да! Выложить ещё раз :)':
                        picture = get_data_for_master(username, 'show_photo')
                        group = groups[-1]
                        id_group = get_chats('get_id', group)
                        result = get_announce_game(username, group, id_group, 'replay')
                        if picture != '-':
                            bot.send_photo(id_group, picture, result, parse_mode='Markdown')
                            back_main_menu = main_menu_master(message)
                            text = (f'🔥🔥🔥  Вы анонсировали свою игру в группе <{group}> 🔥🔥🔥 \n'
                                    f'Вернитесь в главное меню, чтобы продолжить работу с ботом или сделать анонс '
                                    f'снова :)')
                            bot.send_message(message.chat.id, text=text, reply_markup=back_main_menu)
                            bot.register_next_step_handler(message, master_actions)
                        elif picture == '-':
                            bot.send_message(id_group, result, parse_mode='Markdown')
                            back_main_menu = main_menu_master(message)
                            text = (f'🔥🔥🔥  Вы анонсировали свою игру в группе <{group}> 🔥🔥🔥 \n'
                                    f'Вернитесь в главное меню, чтобы продолжить работу с ботом или сделать анонс '
                                    f'снова :)')
                            bot.send_message(message.chat.id, text=text, reply_markup=back_main_menu)
                            bot.register_next_step_handler(message, master_actions)

                    elif message.text == 'Нет, больше не выкладывать :)':
                        btn_back = main_menu_master(message)
                        bot.send_message(message.chat.id,
                                         text='Выберите, что хотите сделать :)', reply_markup=btn_back)
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text in chats:
                        group = message.text
                        groups.append(group)
                        id_group = get_chats('get_id', group)
                        result = get_announce_game(username, group, id_group, '-')
                        if result == 'Вы уже выкладывали свой анонс в этой группе :)\nВыложить ещё раз?':
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                               is_persistent=False)
                            markup.add(types.KeyboardButton('Да! Выложить ещё раз :)'),
                                       types.KeyboardButton('Нет, больше не выкладывать :)'))
                            bot.send_message(message.chat.id, text=result, reply_markup=markup)
                            bot.register_next_step_handler(message, send_announcement)
                        else:
                            picture = get_data_for_master(username, 'show_photo')
                            if picture != '-':
                                bot.send_photo(id_group, picture, result, parse_mode='Markdown')
                                back_main_menu = main_menu_master(message)
                                text = (f'🔥🔥🔥 Вы анонсировали свою игру в группе <{group}> 🔥🔥🔥\n'
                                        f'Вернитесь в главное меню, чтобы продолжить работу с ботом или сделать анонс '
                                        f'снова :)')
                                bot.send_message(message.chat.id, text=text, reply_markup=back_main_menu)
                                bot.register_next_step_handler(message, master_actions)
                            elif picture == '-':
                                bot.send_message(id_group, result, parse_mode='Markdown')
                                back_main_menu = main_menu_master(message)
                                text = (f'🔥🔥🔥 Вы анонсировали свою игру в группе <{group}> 🔥🔥🔥\n'
                                        f'Вернитесь в главное меню, чтобы продолжить работу с ботом или сделать анонс '
                                        f'снова :)')
                                bot.send_message(message.chat.id, text=text, reply_markup=back_main_menu)
                                bot.register_next_step_handler(message, master_actions)
                    elif message.text == '🔥🔥🔥 Выложить во все эти группы 🔥🔥🔥':
                        for group in chats:
                            picture = get_data_for_master(username, 'show_photo')
                            id_group = get_chats('get_id', group)
                            result = get_announce_game(username, group, id_group, 'replay')
                            if picture != '-':
                                bot.send_photo(id_group, picture, result, parse_mode='Markdown')
                                text = f'🔥🔥🔥 Вы анонсировали свою игру в группе <{group}> 🔥🔥🔥'
                                bot.send_message(message.chat.id, text)
                                announce_game(username, 'announce')
                            elif picture == '-':
                                bot.send_message(id_group, result, parse_mode='Markdown')
                                text = f'🔥🔥🔥 Вы анонсировали свою игру в группе <{group}> 🔥🔥🔥'
                                bot.send_message(message.chat.id, text)
                                announce_game(username, 'announce')
                        back_main_menu = main_menu_master(message)
                        bot.send_message(message.chat.id, 'Вернитесь в главное меню, чтобы продолжить работу с ботом :)',
                                         reply_markup=back_main_menu)
                        bot.register_next_step_handler(message, master_actions)

                    else:
                        raise MyCustomException('Выберите, куда хотите анонсировать свою игру или добавьте новую группу'
                                                'для анонса :)\n—\n'
                                                'Или выберите нужную команду в синей плашке меню :)')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
                for chat in chats:
                    markup.add(chat)
                markup.add(types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id, text='Выберите, куда хотите анонсировать свою игру или добавьте '
                                                       'новую группу для анонса :)\n—\nИли выберите нужную команду в '
                                                       'синей плашке меню :)', reply_markup=markup)
                bot.register_next_step_handler(message, send_announcement)
        except MyCustomException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
            for chat in chats:
                markup.add(chat)
            markup.add(types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, send_announcement)


def delete_game_master(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        main_menu = main_menu_master(message)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'ДА':
                        delete_game(username, 'master')
                        bot.send_message(message.chat.id, text='Вы удалили игру!')
                        bot.send_message(message.chat.id, text='Выберите, что хотите сделать :)', reply_markup=main_menu)
                        bot.register_next_step_handler(message, master_actions)
                    elif message.text == 'НЕТ':
                        bot.send_message(message.chat.id, text='Выберите, что хотите сделать :)', reply_markup=main_menu)
                        bot.register_next_step_handler(message, master_actions)
                    else:
                        raise MyCustomException('Решите: вы хотите удалить игру или нет :)\n—\n'
                                                'Или выберите нужную команду в синей плашке меню :)')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add(types.KeyboardButton('ДА'), types.KeyboardButton('НЕТ'))
                bot.send_message(message.chat.id, text='Решите: вы хотите удалить игру или нет :)\n—\nИли выберите '
                                                       'нужную команду в синей плашке меню :)', reply_markup=markup)
                bot.register_next_step_handler(message, delete_game_master)

        except MyCustomException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton('ДА'), types.KeyboardButton('НЕТ'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, delete_game_master)


def player_actions(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        check_games_player(username)
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        main_menu = main_menu_player(message)
                        bot.send_message(message.chat.id, text='{0.first_name}, выберите, что хотите сделать :)'.
                                         format(message.from_user), reply_markup=main_menu)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text == 'Записаться на игру':
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                        games = get_data_for_player(username, 'show_games')
                        btn_menu_player = btn_back_to_main_menu_player(message)
                        if len(games) == 0:
                            bot.send_message(message.chat.id,
                                             text='Мастера ещё не выложили своё расписание😔\nПосмотрите немного '
                                                  'позже 👀', reply_markup=btn_menu_player)
                            bot.register_next_step_handler(message, player_actions)
                        else:
                            add_player(username, 'default')
                            for game in games:
                                markup.add(types.KeyboardButton(game))
                            markup.add(types.KeyboardButton('Вернуться в главное меню'))
                            bot.send_message(message.chat.id, text="{0.first_name}, выберите игру, на которую хотите"
                                                                   " записаться :)".format(message.from_user),
                                             reply_markup=markup)
                            bot.register_next_step_handler(message, player_schedule)

                    elif message.text == 'Отписаться от игры':
                        games = get_data_for_player(username, 'show_games_one_player')
                        if games == 'Вы пока не записались ни на одну игру :)':
                            main_menu = main_menu_player(message)
                            bot.send_message(message.chat.id, text=games, reply_markup=main_menu)
                            bot.register_next_step_handler(message, player_actions)
                        else:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                            for i in range(len(games)):
                                btn = types.KeyboardButton('🎲 ' + games[i] + ' 🎲')
                                markup.add(btn)
                            markup.add(types.KeyboardButton('Вернуться в главное меню'))
                            bot.send_message(message.chat.id,
                                             text='Выберите игру, от участия в которой хотите отписаться :)',
                                             reply_markup=markup)
                            bot.register_next_step_handler(message, delete_game_player)

                    elif message.text == 'Посмотреть мои записи на игры':
                        games = get_data_for_player(username, 'show_games_one_player')
                        if games == 'Вы пока не записались ни на одну игру :)':
                            main_menu = main_menu_player(message)
                            bot.send_message(message.chat.id, text=games, reply_markup=main_menu)
                            bot.register_next_step_handler(message, player_actions)
                        else:
                            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                            for i in range(len(games)):
                                btn = types.KeyboardButton('🎲 ' + games[i] + ' 🎲')
                                markup.add(btn)
                            markup.add(types.KeyboardButton('Вернуться в главное меню'))
                            bot.send_message(message.chat.id,
                                             text='Выберите игру, расписание которой вы хотите посмотреть :)',
                                             reply_markup=markup)
                            bot.register_next_step_handler(message, show_game_player)
                    elif message.text == 'Да, хочу удалиться, надоело всё уже 😐':
                        delete_player(username)
                        bot.send_message(message.chat.id, text='{0.first_name}, вы удалились из бота :)'
                                         .format(message.from_user))
                    elif message.text == 'Нет, я передумал! Я остаюсь 😉':
                        check_games_player(username)
                        main_menu = main_menu_player(message)
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, выберите, что хотите сделать :)'.
                                         format(message.from_user), reply_markup=main_menu)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text == 'Удалиться из бота':
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                        markup.add(types.KeyboardButton('Да, хочу удалиться, надоело всё уже 😐'),
                                   types.KeyboardButton('Нет, я передумал! Я остаюсь 😉'))
                        bot.send_message(message.chat.id,
                                         text='{0.first_name}, вы точно хотите удалиться из бота?\nТогда все ваши '
                                              'записи тоже удалятся :('.format(message.from_user), reply_markup=markup)
                        bot.register_next_step_handler(message, player_actions)
                    else:
                        raise ConvertionException('Выберите один из вариантов, представленных ниже :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                result = main_menu_player(message)
                bot.send_message(message.chat.id, text='Выберите один из вариантов, представленных ниже :)\n—\nИли '
                                                       'выберите нужную команду в синей плашке меню :)',
                                 reply_markup=result)
                bot.register_next_step_handler(message, player_actions)

        except ConvertionException as e:
            result = main_menu_player(message)
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=result)
            bot.register_next_step_handler(message, player_actions)


def player_schedule(message):
    if message.chat.type == 'private':
        username = message.from_user.username
        user_name = message.from_user.first_name
        games = get_data_for_player(username, 'show_games')
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                elif message.text == 'Вернуться в главное меню':
                    back_to_main_menu_player(message)
                    bot.register_next_step_handler(message, player_actions)
                else:
                    if message.text in games:
                        indexes = []
                        for i in range(len(message.text)):
                            if message.text[i] == '"':
                                indexes.append(i)
                        first = indexes[0] + 1
                        game = message.text[first:indexes[1]]
                        copy_game_for_player(game)
                        answer = get_data_for_player(game, 'show_concrete_game')
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                           is_persistent=False)
                        markup.add(types.KeyboardButton('Записаться на игру'),
                                   types.KeyboardButton('Вернуться в главное меню'))

                        if type(answer) is list:
                            photo = answer[0]
                            text = answer[1]
                            # new_text = ''
                            # for word in text:
                            #     if word == 'Мастер':
                            #         new_text += f'*{word}*\n@{text.get(word)}\n\n'
                            #     else:
                            #         new_text += f'*{word}*\n{text.get(word)}\n\n'

                            # bot.send_photo(message.chat.id, photo, text, reply_markup=markup)
                            bot.send_photo(message.chat.id, photo, text, parse_mode='Markdown', reply_markup=markup)
                            bot.register_next_step_handler(message, make_appointment)
                        else:
                            print(answer)
                            # text = ''
                            # for word in answer:
                            #     if word == 'Мастер':
                            #         text += f'*{word}*\n@{answer.get(word)}\n\n'
                            #     else:
                            #         text += f'*{word}*\n{answer.get(word)}\n\n'

                            bot.send_message(message.chat.id, answer, parse_mode='Markdown', reply_markup=markup)
                            bot.register_next_step_handler(message, make_appointment)

                    else:
                        raise ConvertionException('Выберите игру, на которую хотите попасть :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for game in games:
                    markup.add(types.KeyboardButton(game))
                markup.add(types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id, text='Выберите игру, на которую хотите попасть :)\n—\nИли выберите '
                                                       'нужную команду в синей плашке меню :)', reply_markup=markup)
                bot.register_next_step_handler(message, player_schedule)

        except ConvertionException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for game in games:
                markup.add(types.KeyboardButton(game))
            markup.add(types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, player_schedule)


def make_appointment(message):
    if message.chat.type == 'private':
        if message.text[0] == '🎲':
            message.text = message.text[2:-2]
        username = message.from_user.username
        user_name = message.from_user.first_name
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        back_to_main_menu_player(message)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text == 'Записаться на игру':
                        answer = get_data_for_player(username, 'show_last_game_for_player')
                        if type(answer) is list:
                            game = answer[1].get('Название')
                            result = check_free_places(username, game)

                            if result == 'Вы уже записаны на эту игру :)':
                                main_menu = main_menu_player(message)
                                bot.send_message(message.chat.id, text=result, reply_markup=main_menu)
                                bot.register_next_step_handler(message, player_actions)
                            elif result == 0:
                                main_menu = main_menu_player(message)
                                bot.send_message(message.chat.id,
                                                 text='К сожалению, на эту игру больше не осталось свободных мест :(',
                                                 reply_markup=main_menu)
                                bot.register_next_step_handler(message, player_actions)
                            elif result == 'Вы записались на игру':
                                notification = notify_master(username, game)
                                master, text = notification.get('master'), notification.get('text')
                                bot.send_message(master, text=text)
                                main_menu = main_menu_player(message)
                                bot.send_message(message.chat.id,
                                                 text='Вы записались на игру!',
                                                 reply_markup=main_menu)
                                bot.register_next_step_handler(message, player_actions)
                        else:
                            game = get_data_for_player(username, 'show_last_game_for_player')
                            game = game.get('Название')
                            result = check_free_places(username, game)
                            if result == 'Вы уже записаны на эту игру :)':
                                main_menu = main_menu_player(message)
                                bot.send_message(message.chat.id, text=result, reply_markup=main_menu)
                                bot.register_next_step_handler(message, player_actions)
                            elif result == 0:
                                main_menu = main_menu_player(message)
                                bot.send_message(message.chat.id,
                                                 text='К сожалению, на эту игру больше не осталось свободных мест :(',
                                                 reply_markup=main_menu)
                                bot.register_next_step_handler(message, player_actions)
                            elif result == 'Вы записались на игру':
                                notification = notify_master(username, game)
                                master, text = notification.get('master'), notification.get('text')
                                bot.send_message(master, text=text)
                                main_menu = main_menu_player(message)
                                bot.send_message(message.chat.id,
                                                 text='Вы записались на игру!',
                                                 reply_markup=main_menu)
                                bot.register_next_step_handler(message, player_actions)

                    else:
                        raise ConvertionException('Запишитесь на игру или вернитесь в главное меню :)\n—\n'
                                                  'Или выберите нужную команду в синей плашке меню :)')
            else:
                answer = get_data_for_player(username, 'show_last_game_for_player')
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
                markup.add(types.KeyboardButton('Записаться на игру'),
                           types.KeyboardButton('Вернуться в главное меню'))
                text = ''
                for word in answer:
                    if word == 'Мастер':
                        text += f'*{word}*\n@{answer.get(word)}\n\n'
                    else:
                        text += f'*{word}*\n{answer.get(word)}\n\n'

                bot.send_message(message.chat.id, text='Запишитесь на игру или вернитесь в главное меню :)\n—\nИли '
                                                       'выберите нужную команду в синей плашке меню :)')
                bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
                bot.register_next_step_handler(message, make_appointment)

        except ConvertionException as e:
            answer = get_data_for_player(username, 'show_last_game_for_player')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
            markup.add(types.KeyboardButton('Записаться на игру'),
                       types.KeyboardButton('Вернуться в главное меню'))
            text = ''
            for word in answer:
                if word == 'Мастер':
                    text += f'*{word}*\n@{answer.get(word)}\n\n'
                else:
                    text += f'*{word}*\n{answer.get(word)}\n\n'

            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}')
            bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(message, make_appointment)


def delete_game_player(message):
    if message.chat.type == 'private':
        if message.text[0] == '🎲':
            message.text = message.text[2:-2]
        username = message.from_user.username
        user_name = message.from_user.first_name
        games = get_data_for_player(username, 'show_games')
        games = games[0]

        indexes = []
        for i in range(len(games)):
            if games[i] == '"':
                indexes.append(i)

        beginning = indexes[0]
        end = indexes[1]
        game = games[beginning + 1:end]

        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Отписаться от этой игры':
                        unsubscribe(username)
                        main_menu = main_menu_player(message)
                        bot.send_message(message.chat.id, text='Вы отписались от участия в этой игре :)',
                                         reply_markup=main_menu)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text == 'Вернуться в главное меню':
                        back_to_main_menu_player(message)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text == game:
                        copy_game_for_player(message.text)
                        answer = get_data_for_player(username, 'show_last_game_for_player')
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                           is_persistent=False)
                        markup.add(types.KeyboardButton('Отписаться от этой игры'),
                                   types.KeyboardButton('Вернуться в главное меню'))

                        if len(answer) == 2:
                            photo = answer[0]
                            text = answer[1]
                            new_text = ''
                            for word in text:
                                if word == 'Мастер':
                                    new_text += f'*{word}*\n@{text.get(word)}\n\n'
                                else:
                                    new_text += f'*{word}*\n{text.get(word)}\n\n'
                            bot.send_photo(message.chat.id, photo, new_text, parse_mode='Markdown', reply_markup=markup)
                            bot.register_next_step_handler(message, delete_game_player)
                        else:
                            text = ''
                            for word in answer:
                                if word == 'Мастер':
                                    text += f'*{word}*\n@{answer.get(word)}\n\n'
                                else:
                                    text += f'*{word}*\n{answer.get(word)}\n\n'
                            bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
                            bot.register_next_step_handler(message, delete_game_player)

                    else:
                        raise ConvertionException('Отпишитесь от участия в игре или вернитесь в главное меню :)\n—\n'
                                                  '\nИли выберите нужную команду в синей плашке меню :)')

            else:
                answer = get_data_for_player(username, 'show_last_'
                                                       'game_for_player')
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
                markup.add(types.KeyboardButton('Отписаться от этой игры'),
                           types.KeyboardButton('Вернуться в главное меню'))
                text = ''
                for word in answer:
                    if word == 'Мастер':
                        text += f'*{word}*\n@{answer.get(word)}\n\n'
                    else:
                        text += f'*{word}*\n{answer.get(word)}\n\n'
                bot.send_message(message.chat.id, text='Отпишитесь от участия в игре или вернитесь в главное меню :)'
                                                       '\n—\n\nИли выберите нужную команду в синей плашке меню :)')
                bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
                bot.register_next_step_handler(message, delete_game_player)

        except ConvertionException as e:
            answer = get_data_for_player(username, 'show_last_game_for_player')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, is_persistent=False)
            markup.add(types.KeyboardButton('Отписаться от этой игры'),
                       types.KeyboardButton('Вернуться в главное меню'))
            text = ''
            for word in answer:
                if word == 'Мастер':
                    text += f'*{word}*\n@{answer.get(word)}\n\n'
                else:
                    text += f'*{word}*\n{answer.get(word)}\n\n'
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}')
            bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
            bot.register_next_step_handler(message, delete_game_player)


def show_game_player(message):
    if message.chat.type == 'private':
        if message.text[0] == '🎲':
            message.text = message.text[2:-2]
        username = message.from_user.username
        user_name = message.from_user.first_name
        games = get_data_for_player(username, 'show_games_one_player')
        try:
            if type(message.text) is str:
                if message.text == '/start':
                    start(message)
                elif message.text == '/help_me':
                    help_me(message)
                elif message.text == '/roll_the_dice':
                    roll_the_dice(message)
                else:
                    if message.text == 'Вернуться в главное меню':
                        main_menu = main_menu_player(message)
                        bot.send_message(message.chat.id, text='{0.first_name}, выберите, что хотите сделать :)'.
                                         format(message.from_user), reply_markup=main_menu)
                        bot.register_next_step_handler(message, player_actions)
                    elif message.text in games:
                        copy_game_for_player(message.text)
                        answer = get_data_for_player(username, 'show_last_game_for_player')
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True,
                                                           is_persistent=False)
                        markup.add(types.KeyboardButton('Отписаться от этой игры'),
                                   types.KeyboardButton('Вернуться в главное меню'))
                        if len(answer) == 2:
                            photo = answer[0]
                            text = answer[1]
                            new_text = ''
                            for word in text:
                                if word == 'Мастер':
                                    new_text += f'*{word}*\n@{text.get(word)}\n\n'
                                else:
                                    new_text += f'*{word}*\n{text.get(word)}\n\n'
                            bot.send_photo(message.chat.id, photo, new_text, parse_mode='Markdown', reply_markup=markup)
                            bot.register_next_step_handler(message, delete_game_player)
                        else:
                            text = ''
                            for word in answer:
                                if word == 'Мастер':
                                    text += f'*{word}*\n@{answer.get(word)}\n\n'
                                else:
                                    text += f'*{word}*\n{answer.get(word)}\n\n'
                            bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=markup)
                            bot.register_next_step_handler(message, delete_game_player)
                    else:
                        raise ConvertionException('Выберите игру, расписание которой хотели бы посмотреть или '
                                                  'вернитесь в главное меню :)\n—\nИли выберите нужную команду в '
                                                  'синей плашке меню :)')
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for i in range(len(games)):
                    btn = types.KeyboardButton('🎲 ' + games[i] + ' 🎲')
                    markup.add(btn)
                markup.add(types.KeyboardButton('Вернуться в главное меню'))
                bot.send_message(message.chat.id, text='Выберите игру, расписание которой хотели бы посмотреть или '
                                                       'вернитесь в главное меню :)\n—\nИли выберите нужную команду '
                                                       'в синей плашке меню :)', reply_markup=markup)
                bot.register_next_step_handler(message, show_game_player)

        except ConvertionException as e:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in range(len(games)):
                btn = types.KeyboardButton('🎲 ' + games[i] + ' 🎲')
                markup.add(btn)
            markup.add(types.KeyboardButton('Вернуться в главное меню'))
            bot.send_message(message.chat.id, f'{user_name}, что-то не так 🙃\n{e}', reply_markup=markup)
            bot.register_next_step_handler(message, show_game_player)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)