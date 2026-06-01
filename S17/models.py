"""
Room Service (Сервис аудиторий)
Модели для работы с базой данных

Стуктура:
- Room: аудитория (кабинет, лаборатория, мастерская)
  - number: номер аудитории
  - floor: этаж
  - building: корпус
  - capacity: вместимость
  - is_active: флаг мягкого удаления

Уникальное ограничение: (number, building) - в одном корпусе не может быть
двух аудиторий с одинаковым номером.
"""

from peewee import SqliteDatabase, Model, CharField, IntegerField, BooleanField

# Подключение к базе данных SQLite
db = SqliteDatabase('rooms.db')


class Room(Model):
    """
    Модель аудитории
    """
    number = CharField(
        max_length=20,
        verbose_name='Номер аудитории'
    )
    floor = IntegerField(
        verbose_name='Этаж',
        constraints=[SQL('CHECK (floor >= 0 AND floor <= 20)')]
    )
    building = CharField(
        max_length=50,
        verbose_name='Корпус'
    )
    capacity = IntegerField(
        verbose_name='Вместимость',
        constraints=[SQL('CHECK (capacity >= 1 AND capacity <= 500)')]
    )
    is_active = BooleanField(
        default=True,
        verbose_name='Активна'
    )

    class Meta:
        database = db
        table_name = 'rooms'


def init_db():
    """
    Инициализация базы данных:
    1. Подключение к БД
    2. Создание таблиц
    3. Создание составного уникального индекса
    """
    db.connect()
    
    # Создание таблицы (если не существует)
    db.create_tables([Room], safe=True)
    
    # Составной уникальный индекс на (number, building)
    # Обеспечивает уникальность комбинации номера и корпуса
    db.execute_sql("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_rooms_number_building 
        ON rooms (number, building);
    """)


def get_db():
    """Возвращает экземпляр базы данных"""
    return db


# Точка входа для инициализации БД
if __name__ == '__main__':
    init_db()
    print("База данных 'rooms.db' успешно инициализирована.")
    print("Создана таблица 'rooms' с уникальным ограничением (number, building).")
