from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import sqlite3

import logging
import re
import config
from models import Thread

from datetime import datetime, timezone
now = datetime.now(timezone.utc)

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

    def db_reply(reply_id: int, replier_id: int, replied_question_id: int, reply: str, replied_at: str):
        insert_reply_query = 'INSERT INTO replies (reply_id, replier_id, replied_question_id, reply, replied_at) ' \
                             'VALUES (?, ?, ?, ?, ?);'
        cursor.execute(insert_reply_query, (reply_id, replier_id, replied_question_id, reply, replied_at))
        db.commit()

    def update_thread(thread_id: int, replied_at: datetime.now()):
        query = 'UPDATE threads SET total_messages = total_messages + 1, thread_duration = ? WHERE thread_id = ?'
        thread = Thread.filter(thread_id=thread_id).first()
        if thread:
            thread.thread_duration = (replied_at - thread.first_replied_at).seconds
            thread.save()
            cursor.execute(query, (thread.thread_duration, thread_id))
            db.commit()


    @dp.message_handler(commands=['start'])
    async def start_command(message: types.Message):
        print(message.date)
        await message.answer("Привет! Я бот для сбора информации и расчета времени между первым и последним сообщением в треде.\n\n"
                             "Обрати внимание, что все вопросы и ответы в данном чате будут записаны в базу данных.")


    @dp.message_handler(lambda x: re.compile(config.REGEX).match(x.text) and x.reply_to_message is None)
    async def add_message(message: types.Message):
        question_id = message.message_id
        student_id = message.from_user.id
        issue = message.text
        asked_at = message.date.now()

        # await message.answer(f'Студент {student_id} отправил вопрос №{question_id} в {asked_at}')
        db_question(question_id=question_id, student_id=student_id, issue=issue, asked_at=str(asked_at),
                    is_replied=False)

        thread = Thread(first_replied_at=asked_at, first_message_id=question_id, first_reply_id=None,
                        last_message_id=question_id, total_messages=0, thread_duration=0)
        thread.update()
        await message.answer('Ваш вопрос успешно записан!')


    @dp.message_handler(lambda x: x.reply_to_message is not None)
    async def add_reply(message: types.Message):
        reply_id = message.message_id
        replier_id = message.from_user.id
        replied_question_id = message.reply_to_message.message_id
        reply = message.text
        replied_at = message.reply_to_message.date.now()

        # await message.answer(f'Ответ на вопрос №{replied_question_id} был отправлен в {replied_at}')
        db_reply(reply_id=reply_id, replier_id=replier_id, replied_question_id=replied_question_id, reply=reply,
                 replied_at=str(replied_at))

        update_question_query = 'UPDATE questions SET is_replied = ? WHERE question_id = ?'
        cursor.execute(update_question_query, (True, replied_question_id))
        db.commit()

        thread = Thread.filter(first_message_id=replied_question_id).first()
        if thread:
            thread.last_message_id = reply_id
            thread.total_messages += 1
            thread.thread_duration = (replied_at - thread.first_replied_at).seconds
            thread.save()
            await message.answer('Ваш ответ был добавлен к начатому треду!')
        else:
            thread = Thread(first_message_id=replied_question_id, first_reply_id=reply_id, last_message_id=reply_id,
                            total_messages=2, thread_duration=0)
            thread.save()
            await message.answer('Вы начали новый тред!')

        update_thread(thread.thread_id, replied_at)
        thread.save()

except sqlite3.Error as error:
    print(f'Connection error: {error}')

if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True)
