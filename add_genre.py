from app import app, db
from sqlalchemy import text

def add_genre_column():
    with app.app_context():
        # Додаємо колонку genre за допомогою raw SQL
        try:
            db.session.execute(text('ALTER TABLE book ADD COLUMN genre VARCHAR(100)'))
            db.session.commit()
            print("Колонку 'genre' успішно додано!")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Колонка 'genre' вже існує")
            else:
                print(f"Помилка: {e}")
        
        # Оновлюємо тестові книги з жанрами (використовуємо raw SQL)
        try:
            # Отримуємо всі книги через raw SQL
            books = db.session.execute(text('SELECT id, title FROM book')).fetchall()
            
            genres = ['Поезія', 'Проза', 'Класика', 'Сучасна література', 
                      'Драма', 'Фантастика', 'Дитяча література', 'Роман',
                      'Детектив', 'Наукова література']
            
            for i, book in enumerate(books):
                genre = genres[i % len(genres)]
                db.session.execute(
                    text('UPDATE book SET genre = :genre WHERE id = :id'),
                    {'genre': genre, 'id': book.id}
                )
            
            db.session.commit()
            print("Жанри додано до книг!")
        except Exception as e:
            print(f"Помилка при додаванні жанрів: {e}")

if __name__ == '__main__':
    add_genre_column()