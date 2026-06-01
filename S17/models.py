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
    
    # Создание таблиц
    db.create_tables([Building, Room, Equipment, RoomEquipment], safe=True)
    
    # Добавление CHECK-ограничений для SQLite
    cursor = db.cursor()
    
    # Проверяем и добавляем ограничение для floor
    cursor.execute("PRAGMA table_info(rooms)")
    columns = cursor.fetchall()
    has_floor_check = False
    has_capacity_check = False
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='rooms'")
    table_sql = cursor.fetchone()[0]
    
    if 'CHECK' not in table_sql:
        # Создаём временную таблицу с CHECK-ограничениями
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
        
        # Копируем данные
        cursor.execute("""
            INSERT INTO rooms_new (id, number, floor, capacity, building_id, has_computers, is_active)
            SELECT id, number, floor, capacity, building_id, has_computers, is_active FROM rooms
        """)
        
        # Заменяем таблицу
        cursor.execute("DROP TABLE rooms")
        cursor.execute("ALTER TABLE rooms_new RENAME TO rooms")
    
    db.close()


# Модель: Корпус
class Building(Model):
    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)
    address = CharField(max_length=255, null=False)
    floors_count = IntegerField(null=False)

    class Meta:
        database = db
        table_name = 'buildings'


# Модель: Аудитория (основная сущность)
class Room(Model):
    id = AutoField()
    number = CharField(max_length=20, null=False)
    floor = IntegerField(null=False)
    capacity = IntegerField(null=False)
    building_id = ForeignKeyField(Building, backref='rooms', on_delete='CASCADE', null=False)
    has_computers = BooleanField(default=False, null=False)
    is_active = BooleanField(default=True, null=False)

    class Meta:
        database = db
        table_name = 'rooms'
        indexes = (
            (('number', 'building_id'), True),
        )

    def save(self, *args, **kwargs):
        """Валидация данных перед сохранением"""
        if self.floor is not None and not (-2 <= self.floor <= 25):
            raise ValueError(f"floor должно быть от -2 до 25, получено: {self.floor}")
        
        if self.capacity is not None and not (1 <= self.capacity <= 500):
            raise ValueError(f"capacity должно быть от 1 до 500, получено: {self.capacity}")
        
        super().save(*args, **kwargs)


# Модель: Оборудование
class Equipment(Model):
    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)
    description = TextField(null=True)

    class Meta:
        database = db
        table_name = 'equipments'


# Модель: Связь аудиторий и оборудования (многие ко многим)
class RoomEquipment(Model):
    id = AutoField()
    room_id = ForeignKeyField(Room, backref='equipment_links', on_delete='CASCADE', null=False)
    equipment_id = ForeignKeyField(Equipment, backref='room_links', on_delete='CASCADE', null=False)
    quantity = IntegerField(default=1, null=False)

    class Meta:
        database = db
        table_name = 'room_equipment'
        indexes = (
            (('room_id', 'equipment_id'), True),
        )


def get_db():
    db.connect()
    try:
        yield db
    finally:
        db.close()
