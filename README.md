
# BankAPI with fastAPI + sqlAlchemy


## Setup Instructions



### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/boychukmk/Bank.git
   cd Bank
   ```
2. Create .venv:
   ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ``` 

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add your db (example):
   ```
   echo -e "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name" > .env
   ```

5. Apply database migrations:
   ```sh
   alembic upgrade head
   ```

5. Start the FastAPI server:
   ```sh
    uvicorn app.main:app --reload
   ```

## 📘 API Документація
Після запуску доступна автоматична документація:

Swagger UI: http://localhost:8000/docs

Redoc: http://localhost:8000/redoc

## 📘 API endpoints
### 🔁 `/upload_csv/{table_name}`  
**POST** – Завантаження даних у вибрану таблицю з CSV

**Опис:**  
Дозволяє завантажити TSV-файл (табличка, розділена табуляцією) для однієї з таблиць:  
`users`, `credits`, `dictionary`, `plans`, `payments`.

**Параметри:**
- `table_name` — назва таблиці (у URL)
- `file` — файл типу CSV/TSV (налаштовано у проєкті для sep='\t')

**Приклад відповіді:**
```json
{
  "message": "Successfully uploaded 30 records to users.",
  "note": "Available tables: users, credits, dictionary, plans, payments"
}
```

---

### 📄 `/user_credits/{user_id}`  
**GET** – Інформація про кредити користувача

**Опис:**  
Повертає всі кредити користувача та додаткову інформацію:

- **Дата видачі**
- **Статус:** закритий чи відкритий
- Якщо **закритий**:
  - Дата повернення
  - Сума видачі
  - Нараховані відсотки
  - Загальна сума платежів
- Якщо **відкритий**:
  - Крайня дата повернення
  - Кількість днів прострочки
  - Сума тіла кредиту
  - Відсотки
  - Сума платежів по тілу та по відсотках

---

### 📄 `/plans_insert`  
**POST** – Завантаження планів на новий місяць

**Опис:**
- Приймає Excel-файл з полями: `period`, `category_name`, `sum`
- Перевіряє:
  - Формат першого числа місяця у полі `period`
  - Відсутність дублікатів (план з цим місяцем і категорією вже існує)
  - Відсутність пустих значень у полі `sum`

**Відповідь:**  
JSON із повідомленням про успішне збереження або список помилок.

---

### 📊 `/month_performance`  
**GET** – Перевірка виконання планів на певну дату

**Параметри:**  
- `date` (query param): дата перевірки (`YYYY-MM-DD`)

**Повертає:**
- Місяць плану
- Назва категорії
- Сума з плану
- Фактична сума:
  - Для "Видача" — сума виданих кредитів
  - Для "Збір" — сума платежів
- % виконання плану

---

### 📈 `/year_performance`  
**GET** – Зведення по місяцях за рік

**Параметри:**
- `year` (query param): рік (`YYYY`)

**Повертає:**
- Місяць та рік
- Кількість видач
- Сума з плану по видачам
- Фактична сума видач
- % виконання плану по видачам
- Кількість платежів
- Сума з плану по зборам
- Фактична сума платежів
- % виконання по зборам
- % від річного обсягу видач/зборів
