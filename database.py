# database.py

import psycopg2
import psycopg2.extras # для RealDictCursor
import datetime
from collections import Counter
import configparser
import os

# --- Константы ---
PRIORITIES = {0: "Нет", 1: "Низкий", 2: "Средний", 3: "Высокий"}
STATUSES = ["К выполнению", "В процессе", "Отложено", "Завершено"]
WELCOME_NOTE_TITLE = "Добро пожаловать в Denkwürfel!"

def read_db_config(filename='config.ini', section='postgresql'):
    if not os.path.exists(filename):
        raise Exception(f"Файл конфигурации {filename} не найден!")
        
    parser = configparser.ConfigParser()
    parser.read(filename)
    
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Секция {section} не найдена в файле {filename}.')
        
    return db

class DatabaseManager:
    def __init__(self):
        try:
            params = read_db_config()
            self.conn = psycopg2.connect(**params)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            self._create_tables()
            self._ensure_welcome_note_exists()
        except Exception as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            raise e

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                details TEXT,
                tags TEXT,
                due_date TEXT,
                status VARCHAR(20) DEFAULT 'К выполнению' NOT NULL,
                priority INTEGER DEFAULT 0 NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id SERIAL PRIMARY KEY,
                task_id INTEGER NOT NULL,
                reminder_datetime TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def _ensure_welcome_note_exists(self):
        """Проверяет наличие приветственной заметки и создает ее, если она отсутствует."""
        self.cursor.execute("SELECT id FROM notes WHERE title = %s", (WELCOME_NOTE_TITLE,))
        if self.cursor.fetchone() is None:
            welcome_content = """
# Добро пожаловать в Denkwürfel!

Это ваш персональный помощник для управления задачами и хранения идей. Приложение создано для того, чтобы помочь вам организовать свою жизнь и работу.

---

## 📝 Как работать с задачами

*   **Создание:** В разделе "Задачи" нажмите кнопку `+ Новая задача`, чтобы добавить дело в список.
*   **Редактирование:** Дважды кликните по задаче, чтобы открыть окно редактирования. Там можно изменить детали, теги, срок выполнения, статус, приоритет и добавить напоминания.
*   **Приоритет:** Приоритет задачи отображается цветной полосой слева. "Высокий" приоритет можно быстро установить через меню кнопки `+ Новая задача`.
*   **Фильтрация:** Используйте фильтры слева ("Высокий приоритет", "Завершенные"), теги или календарь, чтобы быстро найти нужные задачи.

## 📔 Как работать с заметками

*   Перейдите в раздел "Заметки" на левой панели.
*   Нажмите `+ Новая заметка` для создания новой.
*   Дважды кликните по существующей заметке в списке, чтобы открыть ее в редакторе.
*   Заметки поддерживают синтаксис **Markdown** для форматирования текста (заголовки, списки, выделение).

---

Желаем продуктивной работы!
"""
            self.add_note(title=WELCOME_NOTE_TITLE, content=welcome_content)

    def _clean_tags(self, tags_string: str) -> str:
        return ','.join(tag.strip() for tag in tags_string.split(',') if tag.strip())

    def add_task(self, title, details="", tags="", due_date=None, priority=0, status="К выполнению"):
        now = datetime.datetime.now().isoformat()
        if isinstance(due_date, datetime.date):
            due_date = due_date.isoformat()
        cleaned_tags = self._clean_tags(tags)
        self.cursor.execute(
            'INSERT INTO tasks (title, details, tags, due_date, priority, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id',
            (title, details, cleaned_tags, due_date, priority, status, now)
        )
        new_id = self.cursor.fetchone()['id']
        self.conn.commit()
        return new_id

    def get_tasks(self, filter_by='all', value=None, sort_by='priority', start_date=None, end_date=None):
        query = "SELECT * FROM tasks"
        params = []
        conditions = []

        if filter_by == 'active':
            conditions.append("status != 'Завершено'")
        elif filter_by == 'completed':
            conditions.append("status = 'Завершено'")
        elif filter_by == 'important':
            conditions.append("priority = 3 AND status != 'Завершено'")
        
        if value is not None:
            if filter_by == 'tag':
                conditions.append("(tags = %s OR tags LIKE %s OR tags LIKE %s OR tags LIKE %s)")
                params.extend([value, f'{value},%', f'%,{value},%', f'%,{value}'])
                conditions.append("status != 'Завершено'")
            elif filter_by == 'date':
                conditions.append("due_date = %s")
                params.append(value)
        
        if start_date and end_date:
            conditions.append("due_date BETWEEN %s AND %s")
            params.extend([start_date, end_date])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        sort_clauses = {
            'priority': " ORDER BY priority DESC, due_date ASC NULLS LAST, created_at DESC",
            'due_date': " ORDER BY due_date ASC NULLS LAST, priority DESC, created_at DESC",
            'creation_date': " ORDER BY created_at DESC",
            'alphabetical': " ORDER BY title ASC"
        }
        query += sort_clauses.get(sort_by, sort_clauses['priority'])
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_task_by_id(self, task_id):
        self.cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,)); return self.cursor.fetchone()

    def update_task_status(self, task_id, status):
        self.cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id)); self.conn.commit()

    def update_task(self, task_id, data: dict):
        if 'tags' in data:
            data['tags'] = self._clean_tags(data['tags'])
        fields_to_update = [f"{key} = %s" for key in data]
        if not fields_to_update:
            return
        query = f"UPDATE tasks SET {', '.join(fields_to_update)} WHERE id = %s"
        params = list(data.values()) + [task_id]
        self.cursor.execute(query, params)
        self.conn.commit()
    
    def search_tasks(self, query_str):
        search_pattern = f"%{query_str}%"
        query = "SELECT * FROM tasks WHERE (title LIKE %s OR details LIKE %s OR tags LIKE %s) AND status != 'Завершено' ORDER BY priority DESC, due_date ASC NULLS LAST, created_at DESC"
        self.cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        return self.cursor.fetchall()
    
    def get_tags_with_counts(self):
        self.cursor.execute("SELECT tags FROM tasks WHERE status != 'Завершено' AND tags IS NOT NULL AND tags != ''")
        all_tags = [tag.strip() for row in self.cursor.fetchall() for tag in row['tags'].split(',') if tag.strip()]
        return Counter(all_tags)

    def add_reminder(self, task_id, reminder_datetime):
        self.cursor.execute("INSERT INTO reminders (task_id, reminder_datetime) VALUES (%s, %s)", (task_id, reminder_datetime))
        self.conn.commit()
    def get_reminders_for_task(self, task_id):
        self.cursor.execute("SELECT * FROM reminders WHERE task_id = %s ORDER BY reminder_datetime ASC", (task_id,))
        return self.cursor.fetchall()
    def delete_reminder(self, reminder_id):
        self.cursor.execute("DELETE FROM reminders WHERE id = %s", (reminder_id,))
        self.conn.commit()
    def replace_all_reminders_for_task(self, task_id, datetimes_list):
        self.cursor.execute("DELETE FROM reminders WHERE task_id = %s", (task_id,))
        if datetimes_list:
            data_to_insert = [(task_id, dt) for dt in datetimes_list]
            self.cursor.executemany("INSERT INTO reminders (task_id, reminder_datetime) VALUES (%s, %s)", data_to_insert)
        self.conn.commit()
    def get_due_reminders(self, current_datetime_iso):
        query = "SELECT r.id as reminder_id, r.reminder_datetime, t.id as task_id, t.title FROM reminders r JOIN tasks t ON r.task_id = t.id WHERE r.reminder_datetime <= %s AND t.status != 'Завершено'"
        self.cursor.execute(query, (current_datetime_iso,))
        return self.cursor.fetchall()

    def get_all_notes(self):
        self.cursor.execute("SELECT id, title, updated_at FROM notes ORDER BY updated_at DESC")
        return self.cursor.fetchall()
    def get_note_by_id(self, note_id):
        self.cursor.execute("SELECT * FROM notes WHERE id = %s", (note_id,))
        return self.cursor.fetchone()
    def add_note(self, title, content=""):
        now = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO notes (title, content, created_at, updated_at) VALUES (%s, %s, %s, %s) RETURNING id",
            (title, content, now, now)
        )
        new_id = self.cursor.fetchone()['id']
        self.conn.commit()
        return new_id
    def update_note(self, note_id, title, content):
        now = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "UPDATE notes SET title = %s, content = %s, updated_at = %s WHERE id = %s",
            (title, content, now, note_id)
        )
        self.conn.commit()
    def delete_note(self, note_id):
        self.cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()