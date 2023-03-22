from peewee import *


db = SqliteDatabase('db_yandex.db')


class BaseModel(Model):
    class Meta:
        database = db


class Question(BaseModel):
    question_id = IntegerField(
        primary_key=True,
        null=False,
        help_text='Id вопроса студента'
    )
    student_id = IntegerField(
        help_text='Id студента'
    )
    issue = CharField(
        help_text='Текст вопроса студента'
    )
    asked_at = DateTimeField(
        null=False,
        help_text='Время отправки вопроса студента'
    )
    is_replied = BooleanField(
        default=False,
        help_text='Есть ли реплай на вопрос студента'
    )

    class Meta:
        db_table = 'questions'


class Reply(BaseModel):
    reply_id = IntegerField(
        primary_key=True,
        null=False,
        help_text='Id реплая'
    )
    replier_id = IntegerField(
        help_text='Id отправителя реплая'
    )
    replied_question_id = ForeignKeyField(
        Question,
        on_delete='CASCADE',
        related_name='reply',
        help_text='Id вопроса, на который дается ответ'
    )
    reply = CharField(
        help_text='Текст реплая'
    )
    replied_at = DateTimeField(
        null=False,
        help_text='Время отправки ответа на вопрос студента'
    )
    is_replied = BooleanField(
        default=False,
        help_text='Есть ли реплай на реплай'
    )

    class Meta:
        db_table = 'replies'


class Thread(BaseModel):
    thread_id = IntegerField(
        primary_key=True,
        help_text='Id треда'
    )
    first_message_id = ForeignKeyField(
        Question,
        related_name='thread_start',
        help_text='Первая запись в треде (вопрос студента)'
    )
    first_reply_id = ForeignKeyField(
        Reply,
        related_name='thread_first_reply',
        help_text='Первый реплай в треде'
    )
    last_message_id = ForeignKeyField(
        Reply,
        related_name='thread_end',
        help_text='Последнее сообщение в треде'
    )
    num_messages = IntegerField(
        help_text='Количество сообщений в треде'
    )

    class Meta:
        db_table = 'threads'


Question.create_table()
Reply.create_table()
Thread.create_table()

