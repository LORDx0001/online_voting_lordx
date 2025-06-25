# 🗳️ Online Voting System (LORDx)

Oddiy va xavfsiz onlayn ovoz berish tizimi. Django REST Framework asosida qurilgan bo‘lib, foydalanuvchilar ro‘yxatdan o‘tib, ovoz berish jarayonida ishtirok etishlari mumkin. Admin panel orqali foydalanuvchilar, ovozlar va natijalarni boshqarish imkoniyati mavjud.

## ⚙️ Texnologiyalar
- Python 3.x  
- Django  
- Django REST Framework  
- SQLite  
- Swagger (drf-yasg)

## 🚀 O‘rnatish

Online Voting System’ni ishga tushirish uchun quyidagi bosqichlarni bajaring:

### 1. Repoyni klonlash

```bash
git clone https://github.com/LORDx0001/online_voting_lordx.git
cd online_voting_lordx
```

### 2. Virtual muhit yaratish va faollashtirish

```bash
python -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows
```

### 3. Kutubxonalarni o‘rnatish

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Migratsiyalarni bajarish

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Superuser (admin) yaratish

```bash
python manage.py createsuperuser
```

### 6. Loyihani ishga tushurish

```bash
python manage.py runserver
```

Endi brauzeringizda `http://127.0.0.1:8000/` manziliga o‘ting.  
API hujjatlari esa [`http://127.0.0.1:8000/api/swagger/`](http://127.0.0.1:8000/api/swagger/) orqali mavjud.

## 🔌 API Hujjatlari

Swagger orqali barcha endpointlar hujjatlashtirilgan. Ushbu sahifa orqali siz:
- Endpointlar ro‘yxatini ko‘rishingiz  
- Parametrlar va javob formatlarini o‘rganishingiz  
- Bevosita so‘rov yuborishingiz mumkin

## 🧪 API Misollari

**Ro‘yxatdan o‘tish:**
```bash
curl -X POST http://localhost:8000/api/register/ \
     -H "Content-Type: application/json" \
     -d '{"phone_number": "verified_phone_number", "password": "parol"}'
```

## 🔐 Avtorizatsiya

Token asosida autentifikatsiya talab qilinadi. So‘rovlar quyidagicha yuboriladi:

```
Authorization: Bearer <token>
```

**Ovoz berish:**
```bash
curl -X POST http://localhost:8000/api/vote/ \
     -H "Authorization: Bearer <token>" \
     -d '{"candidate_id": 3}'
```

## 📂 Loyihaning Tuzilmasi

```
.
├── app/              # Asosiy ilova
├── config/           # Django konfiguratsiyasi
├── db.sqlite3        # Ma'lumotlar bazasi
├── requirements.txt  # Kutubxonalar ro‘yxati
├── manage.py
└── README.md
```

## 🤝 Hissa Qo‘shish

Takliflar va pull requestlar mamnuniyat bilan qabul qilinadi!
