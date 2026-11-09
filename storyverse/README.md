# StoryVerse AI Studio — Phase 3 (App Core)

> مجلد **معزول** عن تطبيق Flutter في جذر المستودع. لا يغيّر `lib/` أو `pubspec.yaml`.

**Phase 3 فقط:** SQLite + FastAPI + طابور عامل واحد + تخطيط ملفات.  
**بدون** تنزيل نماذج، **بدون** استدعاء ComfyUI، **بدون** إعادة تثبيت torch.

---

## ماذا يوجد هنا؟

| المسار | الوظيفة |
|--------|---------|
| `app/` | تطبيق Python الداخلي (API + DB + queue) |
| `app/models.py` | جداول: `projects`, `scenes`, `characters`, `assets`, `jobs`, `settings` |
| `app/main.py` | دخول FastAPI |
| `app/queue.py` | عامل واحد in-process (لا توازي GPU ثقيل) |
| `app/paths.py` | مساعدات الملفات تحت `STORYVERSE_ROOT` |
| `requirements.txt` | تبعيات خفيفة فقط |
| `scripts/smoke_test.py` | دورة مشروع + مشهد + job وهمي بدون ML |

---

## مزامنة مع جهاز Windows (`D:\StoryVerse`)

على PC المستخدم (بعد Phase 2):

```text
D:\StoryVerse\
  venv\                 # موجود من Phase 2
  apps\comfyui\         # موجود — لا تلمسه في Phase 3
  models\               # موجود — لا تنزّل شيئاً جديداً
  app\                  # ← انسخ محتوى storyverse/ إلى هنا
  data\                 # يُنشأ تلقائياً (DB)
  projects\             # يُنشأ تلقائياً لكل مشروع
```

### نسخ / مزامنة من المستودع

من PowerShell (عدّل مسار الـ clone):

```powershell
# مثال: المستودع على C أو أي مكان، والهدف D:\StoryVerse\app
$src = "C:\path\to\flutter_project\storyverse"
$dst = "D:\StoryVerse\app"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
robocopy $src $dst /E /XD .venv venv data .git __pycache__ /NFL /NDL /NJH /NJS
```

أو git worktree / clone داخل `D:\StoryVerse` ثم:

```powershell
Copy-Item -Recurse -Force .\storyverse\* D:\StoryVerse\app\
```

عيّن الجذر:

```powershell
setx STORYVERSE_ROOT "D:\StoryVerse"
# في الجلسة الحالية أيضاً:
$env:STORYVERSE_ROOT = "D:\StoryVerse"
```

---

## تثبيت التبعيات الخفيفة (Windows)

استخدم **نفس venv Phase 2** (Python 3.12) — لا تعِد تثبيت torch:

```powershell
cd D:\StoryVerse
.\venv\Scripts\Activate.ps1
cd app
pip install -r requirements.txt
```

`requirements.txt` يحتوي: `fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite`, `pydantic`, `httpx` فقط.

---

## تشغيل الـ API

```powershell
cd D:\StoryVerse\app
$env:STORYVERSE_ROOT = "D:\StoryVerse"
python -m app.main
# أو:
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

افتح: http://127.0.0.1:8765/docs  
صحة: `GET /api/v1/health`

### نقاط مهمة

| Method | Path | وصف |
|--------|------|-----|
| POST | `/api/v1/projects` | إنشاء مشروع |
| GET | `/api/v1/projects` | قائمة المشاريع |
| POST | `/api/v1/projects/{id}/scenes` | إنشاء مشهد |
| GET | `/api/v1/projects/{id}/scenes` | قائمة المشاهد |
| POST | `/api/v1/projects/{id}/jobs` | إنشاء job (يُصفّ في الطابور) |
| GET | `/api/v1/jobs/{id}` | حالة job: `queued` → `running` → `done`/`failed` |

---

## اختبار الدخان (Smoke) — بدون ComfyUI/ML

**مستحسن (لا يحتاج خادم منفصل):**

```powershell
cd D:\StoryVerse\app
$env:STORYVERSE_ROOT = "D:\StoryVerse"
.\venv\Scripts\Activate.ps1   # إن لم يكن مفعّلاً
python scripts\smoke_test.py
```

المتوقع: `PASS — project + scene + fake job lifecycle ... without ML`

**ضد خادم شغّال:**

```powershell
# طرفية 1
python -m app.main

# طرفية 2
python scripts\smoke_test.py --base-url http://127.0.0.1:8765
```

---

## تخطيط الملفات

```text
%STORYVERSE_ROOT%\
  data\storyverse.db
  projects\{project_id}\
    scenes\
    characters\
    assets\
    exports\
    scratch\          # علامات الـ fake jobs هنا
```

---

## سياسات Phase 3

- لا تنزيل نماذج (SD / Wan / LTX / TTS / LLM).
- لا استدعاء ComfyUI من الـ worker في هذه المرحلة.
- لا توازي وظائف GPU ثقيلة — عامل واحد فقط.
- Phase 4+ تحتاج موافقة صريحة منفصلة.

---

## عزل Flutter

هذا المجلد `storyverse/` مستقل تماماً. تطبيق Flutter (`lib/`, `android/`, …) بلا تغيير متعمد في Phase 3.
