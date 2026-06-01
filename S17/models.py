import os
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

# Инициализация базы данных
db = SqliteExtDatabase('rooms.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64,
})


def init_db():
    """Инициализация базы данных и создание таблиц"""
    db.connect()
    db.create_tables([Building, Room, Equipment, RoomEquipment], safe=True)
    db.close()


# Модель: Корпус
class Building(Model):
    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)  # Название корпуса
    address = CharField(max_length=255, null=False)  # Адрес
    floors_count = IntegerField(null=False)  # Количество этажей

    class Meta:
        database = db
        table_name = 'buildings'


# Модель: Аудитория (основная сущность)
class Room(Model):
    id = AutoField()
    number = CharField(max_length=20, null=False)  # Номер аудитории
    floor = IntegerField(null=False)  # Этаж
    capacity = IntegerField(null=False)  # Вместимость
    building_id = ForeignKeyField(Building, backref='rooms', on_delete='CASCADE', null=False)
    has_computers = BooleanField(default=False, null=False)  # Наличие компьютеров
    is_active = BooleanField(default=True, null=False)  # Активность записи

    class Meta:
        database = db
        table_name = 'rooms'
        indexes = (
            (('number', 'building_id'), True),  # Уникальная комбинация
        )


# Модель: Оборудование
class Equipment(Model):
    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)  # Название оборудования
    description = TextField(null=True)  # Описание

    class Meta:
        database = db
        table_name = 'equipments'


# Модель: Связь аудиторий и оборудования (многие ко многим)
class RoomEquipment(Model):
    id = AutoField()
    room_id = ForeignKeyField(Room, backref='equipment_links', on_delete='CASCADE', null=False)
    equipment_id = ForeignKeyField(Equipment, backref='room_links', on_delete='CASCADE', null=False)
    quantity = IntegerField(default=1, null=False)  # Количество единиц оборудования

    class Meta:
        database = db
        table_name = 'room_equipment'
        indexes = (
            (('room_id', 'equipment_id'), True),  # Уникальная пара
        )


# Функция для получения сессии базы данных
def get_db():
    db.connect()
    try:
        yield db
    finally:
        db.close()
