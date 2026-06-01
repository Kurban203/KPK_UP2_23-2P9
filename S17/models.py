from peewee import *

db = SqliteDatabase('rooms.db')


class BaseModel(Model):
    class Meta:
        database = db


class Room(BaseModel):
    number = CharField(max_length=10)
    floor = IntegerField()
    building = CharField(max_length=50)
    capacity = IntegerField()
    is_active = BooleanField(default=True)

    class Meta:
        table_name = 'rooms'
        indexes = ((('number', 'building'), True),)


class Equipment(BaseModel):
    name = CharField(max_length=100, unique=True)

    class Meta:
        table_name = 'equipments'


class RoomEquipment(BaseModel):
    room = ForeignKeyField(Room)
    equipment = ForeignKeyField(Equipment)
    count = IntegerField(default=1)

    class Meta:
        table_name = 'room_equipment'
        primary_key = CompositeKey('room', 'equipment')


def init_db():
    db.connect()
    db.create_tables([Room, Equipment, RoomEquipment], safe=True)
    db.close()
    print("✅ База данных создана!")


def get_db_connection():
    db.connect()
    try:
        yield db
    finally:
        db.close()


if __name__ == '__main__':
    init_db()
