import os
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase
from playhouse.sqlite_ext import JSONField

# Инициализация базы данных
db = SqliteExtDatabase('rooms.db', pragmas={
    'journal_mode': 'wal',
    'cache_size': -1024 * 64,
})


def init_db():
    """Инициализация базы данных и создание таблиц"""
    db.connect()
    
    # Создание таблиц
    db.create_tables([Building, Room, Equipment, RoomEquipment], safe=True)
    
    # Для SQLite нужно создавать CHECK-ограничения через PRAGMA или raw SQL
    # Добавляем проверки для полей floor и capacity
    cursor = db.cursor()
    
    # Проверка для поля floor (от -2 до 25)
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name='rooms'
    """)
    result = cursor.fetchone()
    if result and 'CHECK' not in result[0]:
        # Пересоздаём таблицу с CHECK-ограничениями
        cursor.execute("""
            CREATE TABLE rooms_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number VARCHAR(20) NOT NULL,
                floor INTEGER NOT NULL CHECK (floor >= -2 AND floor <= 25),
                capacity INTEGER NOT NULL CHECK (capacity >= 1 AND capacity <= 500),
                building_id INTEGER NOT NULL,
                has_computers BOOLEAN NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (building_id) REFERENCES buildings (id) ON DELETE CASCADE,
                UNIQUE(number, building_id)
            )
        """)
        cursor.execute("""
            INSERT INTO rooms_new (id, number, floor, capacity, building_id, has_computers, is_active)
            SELECT id, number, floor, capacity, building_id, has_computers, is_active FROM rooms
        """)
        cursor.execute("DROP TABLE rooms")
        cursor.execute("ALTER TABLE rooms_new RENAME TO rooms")
    
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
        # Для SQLite CHECK-ограничения задаются через raw SQL в init_db()
        # так как Peewee не поддерживает их декларативно для SQLite
    
    def save(self, *args, **kwargs):
        """Валидация данных перед сохранением"""
        # Проверка диапазона floor
        if self.floor is not None and not (-2 <= self.floor <= 25):
            raise ValueError(f"floor должно быть в диапазоне от -2 до 25, получено: {self.floor}")
        
        # Проверка диапазона capacity
        if self.capacity is not None and not (1 <= self.capacity <= 500):
            raise ValueError(f"capacity должно быть в диапазоне от 1 до 500, получено: {self.capacity}")
        
        super().save(*args, **kwargs)


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
