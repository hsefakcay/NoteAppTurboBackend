# Note App Turbo - Backend API

FastAPI backend with Firebase Authentication and Firestore database for Note App Turbo.

## 🚀 Teknolojiler

- **Python 3.11+** - Modern Python
- **FastAPI** - Modern, hızlı web framework
- **Uvicorn** - ASGI server
- **Firebase Admin SDK** - Authentication ve Firestore
- **Pydantic** - Data validation
- **SlowAPI** - Rate limiting (opsiyonel)

## 📁 Proje Yapısı

```
note_app_backend/
├── app/
│   ├── api/v1/          # API endpoints
│   │   └── notes.py     # Notes CRUD operations
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings
│   │   └── security.py  # Firebase Auth
│   ├── db/              # Database
│   │   ├── session.py   # Firestore client
│   │   └── repositories.py  # Data access layer
│   ├── schemas/         # Pydantic models
│   │   └── note.py
│   ├── tests/           # Unit tests
│   └── main.py          # FastAPI app
├── scripts/
│   └── seed_firestore.py  # Seed data script
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── env.sample
```

## ⚙️ Kurulum

### 1. Ortam Değişkenlerini Ayarla

`.env` dosyası oluşturun:

```bash
cp env.sample .env
```

Gerekli değişkenleri düzenleyin:

```env
FIREBASE_PROJECT_ID=your-firebase-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 2. Virtual Environment Oluştur

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

## 🏃 Çalıştırma

### Yerel Geliştirme

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API Dokümantasyonu: http://127.0.0.1:8000/docs

### Docker ile

```bash
docker compose up --build
```

## 🧪 Test

```bash
pytest app/tests/
```

## 📝 API Endpoints

### Health Check
- `GET /health` - Server sağlık kontrolü

### Notes (Authentication Required)
- `GET /api/notes` - Notları listele (pagination, search, filter)
- `POST /api/notes` - Yeni not oluştur
- `PUT /api/notes/{note_id}` - Not güncelle
- `DELETE /api/notes/{note_id}` - Not sil

### Authentication

Tüm `/api/notes` endpoint'leri Firebase ID token gerektirir:

```
Authorization: Bearer <Firebase_ID_Token>
```

## 🔧 Örnek İstekler

### Not Listele

```bash
curl -X GET "http://127.0.0.1:8000/api/notes?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Yeni Not Oluştur

```bash
curl -X POST "http://127.0.0.1:8000/api/notes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Başlık", "content": "İçerik", "pinned": false}'
```

## 🗄️ Firestore Emulator (Yerel Geliştirme)

```bash
# Firebase CLI kur
npm i -g firebase-tools

# Emulator başlat
firebase emulators:start --only firestore --project demo-notes

# .env dosyasına ekle
FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
```

### Test Verisi Oluştur

```bash
python scripts/seed_firestore.py --user test-user-id --count 5
```

## 🐳 Docker

Production için:

```bash
docker build -t note-app-backend .
docker run -p 8000:8000 --env-file .env note-app-backend
```

## 📚 Daha Fazla Bilgi

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)

## 📄 Lisans

MIT License
