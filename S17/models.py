"""
Модели базы данных для Room Service (вариант 17)
Группа: 23-2П9
Оценка: 3

Используемые технологии:
- peewee ORM
- SQLite3
"""

from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    IntegerField,
    BooleanField,
    ForeignKeyField,
    CompositeKey,
    Check
)

# Инициализация базы данных
db = SqliteDatabase('rooms.db')


class BaseModel(Model):
    """Базовый класс модели с подключением к БД"""
    
    class Meta:
        database = db


class Room(BaseModel):
    """
    Модель аудитории (кабинеты, лаборатории, мастерские)
    
    Поля:
    - id: уникальный идентификатор (первичный ключ, автоинкремент)
    - number: номер аудитории
    - floor: этаж (0-25)
    - building: корпус (1-5 символов)
    - capacity: вместимость (1-500)
    - room_type: тип аудитории (cabinet, lab, workshop)
    - is_active: статус активности (мягкое удаление)
    
    Уникальная комбинация: (number, building) - в одном корпусе 
    не может быть двух аудиторий с одинаковым номером
    """
    
    number = CharField(
        max_length=10,
        verbose_name='Номер аудитории'
    )
    
    floor = IntegerField(
        constraints=[Check('floor BETWEEN 0 AND 25')],
        verbose_name='Этаж'
    )
    
    building = CharField(
        max_length=5,
        verbose_name='Корпус'
    )
    
    capacity = IntegerField(
        constraints=[Check('capacity BETWEEN 1 AND 500')],
        verbose_name='Вместимость'
    )
    
    room_type = CharField(
        max_length=20,
        verbose_name='Тип аудитории'  # cabinet, lab, workshop
    )
    
    is_active = BooleanField(
        default=True,
        verbose_name='Активна ли запись'
    )
    
    class Meta:
        table_name = 'rooms'
        verbose_name = 'Аудитория'
        verbose_name_plural = 'Аудитории'
        
        # Уникальность: в одном корпусе не может быть двух одинаковых номеров
        indexes = (
            (('number', 'building'), True),
        )


class Equipment(BaseModel):
    """
    Модель оборудования для связи многие ко многим с Room
    
    Поля:
    - id: уникальный идентификатор (первичный ключ, автоинкремент)
    - name: название оборудования (уникальное)
    - type: тип оборудования (projector, board, pc, etc.)
    """
    
    name = CharField(
        max_length=50,
        unique=True,
        verbose_name='Название оборудования'
    )
    
    type = CharField(
        max_length=30,
        verbose_name='Тип оборудования'
    )
    
    class Meta:
        table_name = 'equipment'
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'


class RoomEquipment(BaseModel):
    """
    Транзитивная таблица для связи многие ко многим между Room и Equipment
    
    Поля:
    - room: внешний ключ на Room (не может быть NULL)
    - equipment: внешний ключ на Equipment (не может быть NULL)
    - count: количество единиц оборудования в аудитории (>= 1)
    
    Связи:
    - Room (1) —— (M) RoomEquipment
    - Equipment (1) —— (M) RoomEquipment
    """
    
    room = ForeignKeyField(
        Room,
        backref='equipment_list',
        on_delete='CASCADE',
        verbose_name='Аудитория'
    )
    
    equipment = ForeignKeyField(
        Equipment,
        backref='rooms_list',
        on_delete='CASCADE',
        verbose_name='Оборудование'
    )
    
    count = IntegerField(
        constraints=[Check('count >= 1')],
        default=1,
        verbose_name='Количество'
    )
    
    class Meta:
        table_name = 'room_equipment'
        verbose_name = 'Оборудование аудитории'
        verbose_name_plural = 'Оборудование аудиторий'
        
        # Составной первичный ключ для уникальности пары (room, equipment)
        primary_key = CompositeKey('room', 'equipment')


def init_db():
    """
    Функция инициализации базы данных.
    Создаёт все необходимые таблицы, если они не существуют.
    Должна вызываться при старте приложения.
    """
    try:
        db.connect()
        # Создаём таблицы в правильном порядке (сначала независимые, потом с FK)
        db.create_tables([Room, Equipment, RoomEquipment], safe=True)
        print("✅ База данных успешно инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
    finally:
        db.close()


def get_db_connection():
    """
    Возвращает подключение к базе данных для использования в FastAPI.
    Рекомендуется использовать как dependency.
    """
    db.connect()
    try:
        yield db
    finally:
        db.close()


# Точка входа для прямой инициализации
if __name__ == '__main__':
    init_db()
    print("📁 Файл базы данных: rooms.db")
    
    # Вывод информации о созданных таблицах
    db.connect()
    tables = db.get_tables()
    print(f"📋 Созданные таблицы: {', '.join(tables)}")
    db.close()
