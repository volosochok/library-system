from app import app, db, LibraryInfo

def init_library_info():
    with app.app_context():
        if LibraryInfo.query.count() == 0:
            info = LibraryInfo(
                working_hours="Понеділок - П'ятниця: 9:00 - 20:00\nСубота: 10:00 - 18:00\nНеділя: Вихідний",
                contacts="вул. Книжкова, 15, Львів\n+380 (32) 123-45-67\nlibrary@example.com",
                history="Наша бібліотека заснована у 1950 році. За цей час ми стали центром знань та культури.",
                address="м. Львів, вул. Книжкова, 15"
            )
            db.session.add(info)
            db.session.commit()
            print("Інформацію про бібліотеку додано!")

if __name__ == '__main__':
    init_library_info()