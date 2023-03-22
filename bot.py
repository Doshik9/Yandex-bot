from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import sqlite3

import logging
import pytz
import re
import config
from models import Question, Reply, Thread

tz = pytz.timezone('Europe/Moscow')
logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=config.TOKEN_API)
dp = Dispatcher(bot,
                storage=storage)

try:
    with sqlite3.connect('db_yandex.db') as db:
        cursor = db.cursor()
        print('Connected')

    def db_question(question_id: int, student_id: int, issue: str, asked_at: str, is_replied: bool = False):
        insert_question_query = 'INSERT INTO questions (question_id, student_id, issue, asked_at, is_replied) ' \
                                'VALUES (?, ?, ?, ?, ?);'
        cursor.execute(insert_question_query, (question_id, student_id, issue, asked_at, is_replied))
        db.commit()

    def db_reply(reply_id: int, replier_id: int, replied_question_id: int, reply: str, replied_at: str,
                 is_replied: bool = False):
        insert_reply_query = 'INSERT INTO replies (reply_id, replier_id, replied_question_id, reply, replied_at, ' \
                             'is_replied) VALUES (?, ?, ?, ?, ?, ?);'
        cursor.execute(insert_reply_query, (reply_id, replier_id, replied_question_id, reply, replied_at, is_replied))
        db.commit()

    @dp.message_handler(commands=['start'])
    async def start_command(message: types.Message):
        print(message.date)
        await message.answer('Hello! I am a bot for calculating mean time of replies.')

    @dp.message_handler(commands=['help'])
    async def help_command(message: types.Message):
        print(message.date)
        await message.answer('All messages will be stored in a database.')

    @dp.message_handler(lambda x: re.compile(config.REGEX).match(x.text) and x.reply_to_message is None)
    async def add_message(message: types.Message):
        question_id = message.message_id
        student_id = message.from_user.id
        issue = message.text
        asked_at = message.date.replace(tzinfo=pytz.utc).astimezone(tz)

        # await message.answer(f'Looks like {student_id} sent a question №{question_id} at {asked_at}')
        db_question(question_id=question_id, student_id=student_id, issue=issue, asked_at=str(asked_at),
                    is_replied=False)

        start_thread = Thread(first_message_id=question_id, first_reply_id=0, last_message_id=question_id, num_messages=1)
        start_thread.update()
        await message.answer('Your question is saved successfully!')

    @dp.message_handler(lambda x: x.reply_to_message is not None)
    async def add_reply(message: types.Message):
        reply_id = message.message_id
        replier_id = message.from_user.id
        replied_question_id = message.reply_to_message.message_id
        reply = message.text
        replied_at = message.reply_to_message.date.replace(tzinfo=pytz.utc).astimezone(tz)

        # await message.answer(f'Question №{replied_question_id} was replied at {replied_at}')
        db_reply(reply_id=reply_id, replier_id=replier_id, replied_question_id=replied_question_id, reply=reply,
                 replied_at=str(replied_at), is_replied=False)

        start_thread = Thread(first_message_id=replied_question_id, first_reply_id=reply_id, last_message_id=reply_id,
                              num_messages=2)
        start_thread.save()
        await message.answer('Your reply is saved successfully!')

except sqlite3.Error as error:
    print(f'Connection error: {error}')

if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True)