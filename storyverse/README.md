# StoryVerse AI Studio — Phase 5 (ComfyUI Image Adapter)

> مجلد **معزول** عن تطبيق Flutter في جذر المستودع. لا يغيّر `lib/` أو `pubspec.yaml`.

**Phase 5:** Adapter توليد صور عبر **ComfyUI HTTP** (`127.0.0.1:8188`) فوق Phase 4 (قصة/مشاهد).

- Checkpoint الافتراضي: **`DreamShaper_8_pruned.safetensors`** (مثبت مسبقاً في Phase 2)
- **لا** تنزيلات نماذج جديدة في الكود
- **لا** APIs مدفوعة
- طابور عامل واحد (job واحد ثقيل في كل مرة)
- إصدارات صور لكل مشهد؛ إعادة توليد مشهد واحد لا تمسح المشروع

---

## مزامنة مع Windows (`D:\StoryVerse\app`)

```text
D:\StoryVerse\
  venv\
  apps\comfyui\              # محرك ComfyUI (شغّله على 8188 للاختبار الحي)
  models\checkpoints\
    DreamShaper_8_pruned.safetensors   # موجود — لا تنزّل بديله من التطبيق
  app\                       # ← انسخ محتوى storyverse/ إلى هنا
  data\
  projects\
```

### نسخ من المستودع (PowerShell)

```powershell
$src = "C:\path\to\flutter_project\storyverse"
$dst = "D:\StoryVerse\app"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
robocopy $src $dst /E /XD .venv venv data .git __pycache__ /NFL /NDL /NJH /NJS

$env:STORYVERSE_ROOT = "D:\StoryVerse"
setx STORYVERSE_ROOT "D:\StoryVerse"
```

### تثبيت وتشغيل API

```powershell
cd D:\StoryVerse
.\venv\Scripts\Activate.ps1
cd app
pip install -r requirements.txt
$env:STORYVERSE_ROOT = "D:\StoryVerse"
# اختياري — الافتراضي صحيح:
# $env:STORYVERSE_COMFYUI_BASE_URL = "http://127.0.0.1:8188"
# $env:STORYVERSE_COMFYUI_CHECKPOINT = "DreamShaper_8_pruned.safetensors"
python -m app.main
```

افتح: http://127.0.0.1:8765/docs

---

## ماذا يوجد هنا؟

| المسار | الوظيفة |
|--------|---------|
| `app/image/comfyui.py` | عميل HTTP لـ ComfyUI (`/prompt`, `/history`, `/view`) |
| `app/image/workflow.py` | رسم SD1.5 txt2img → DreamShaper |
| `app/image/adapter.py` | نسخ المخرجات إلى `projects/{id}/assets/scenes/{scene}/vNNN.png` |
| `app/queue.py` | `fake` + **`image_generate`** (عامل واحد) |
| `scripts/mock_comfyui.py` | خادم وهمي لـ CI بدون GPU |
| `scripts/smoke_test.py` | دخان: قصة + صور عبر الـ mock |

---

## نقاط API الرئيسية (Phase 5)

| Method | Path | وصف |
|--------|------|-----|
| POST | `/api/v1/scenes/{id}/generate-image` | طابور توليد صورة لمشهد واحد |
| POST | `/api/v1/projects/{pid}/scenes/{sid}/generate-image` | نفس الأمر مع تحقق المشروع |
| GET | `/api/v1/scenes/{id}/images` | كل إصدارات صور المشهد |
| POST | `/api/v1/characters/{id}/ref-stub` | مجلد مراجع خفيف (بدون توليد) |
| PATCH | `/api/v1/characters/{id}` | تحديث وصف / `visual_prompt` |

ما زالت نقاط Phase 4 (`/story/generate`, تعديل مشاهد، …) تعمل كما هي.

### مثال توليد صورة لمشهد

```powershell
curl -X POST http://127.0.0.1:8765/api/v1/scenes/1/generate-image `
  -H "Content-Type: application/json" `
  -d "{\"seed\":42,\"steps\":20,\"character_ids\":[1]}"
```

الاستجابة: job من نوع `image_generate` بحالة `queued`. راقب:

```powershell
curl http://127.0.0.1:8765/api/v1/jobs/1
curl http://127.0.0.1:8765/api/v1/scenes/1/images
```

الملفات تُحفظ تحت:

```text
D:\StoryVerse\projects\{project_id}\assets\scenes\{scene_id}\v001.png
D:\StoryVerse\projects\{project_id}\assets\scenes\{scene_id}\v002.png  # بعد regenerate
```

إعادة التوليد **تضيف** إصداراً جديداً؛ لا تحذف `v001` ولا تمس مشاهد أخرى.

---

## اختبار الدخان (CI / بدون GPU) — Mock ComfyUI

```powershell
cd D:\StoryVerse\app   # أو storyverse/ في المستودع
$env:STORYVERSE_ROOT = "D:\StoryVerse"   # أو اتركه فارغاً لمجلد مؤقت
python scripts\smoke_test.py
```

المتوقع:

`PASS — story + image_generate (mock ComfyUI) + versioned regenerate (no GPU / no model download)`

الـ smoke يشغّل `scripts/mock_comfyui.py` محلياً على منفذ عشوائي ويضبط `STORYVERSE_COMFYUI_BASE_URL` تلقائياً.

تشغيل الـ mock يدوياً:

```powershell
python scripts\mock_comfyui.py --port 18188
```

---

## اختبار حي على Windows (يتطلب ComfyUI شغّال)

> هذا المسار **ليس** جزءاً من CI السحابي. يحتاج GPU المستخدم وComfyUI.

1. تأكد أن النموذج موجود فقط محلياً (لا تنزيل من التطبيق):

```powershell
Get-Item "D:\StoryVerse\apps\comfyui\models\checkpoints\DreamShaper_8_pruned.safetensors"
# أو المسار الذي يستخدمه ComfyUI لـ checkpoints إن كان مختلفاً
```

2. شغّل ComfyUI (واجهة على http://127.0.0.1:8188):

```powershell
cd D:\StoryVerse\apps\comfyui
# حسب طريقة تثبيتك — مثال:
.\venv\Scripts\Activate.ps1   # إن وُجد venv منفصل
python main.py --listen 127.0.0.1 --port 8188
```

3. في طرفية أخرى شغّل StoryVerse API ثم:

```powershell
cd D:\StoryVerse\app
.\venv\Scripts\Activate.ps1
$env:STORYVERSE_ROOT = "D:\StoryVerse"
$env:STORYVERSE_COMFYUI_BASE_URL = "http://127.0.0.1:8188"
python -m app.main
```

4. ولّد قصة ثم صورة لمشهدين من `/docs` أو:

```powershell
# بعد POST /story/generate احصل على scene ids ثم:
curl -X POST http://127.0.0.1:8765/api/v1/scenes/<SCENE_A>/generate-image -H "Content-Type: application/json" -d "{}"
curl -X POST http://127.0.0.1:8765/api/v1/scenes/<SCENE_B>/generate-image -H "Content-Type: application/json" -d "{}"
```

5. تحقق من الملفات تحت `D:\StoryVerse\projects\...\assets\scenes\...` وصفوف `assets` في SQLite.

**ملاحظة VRAM (6GB):** الطابور يضمن job صورة واحد في كل مرة؛ الدقة الافتراضية 512×512.

---

## متغيرات البيئة (Phase 5)

| متغير | افتراضي | المعنى |
|--------|---------|--------|
| `STORYVERSE_ROOT` | `storyverse/data/root` | جذر البيانات/المشاريع |
| `STORYVERSE_COMFYUI_BASE_URL` | `http://127.0.0.1:8188` | عنوان ComfyUI |
| `STORYVERSE_COMFYUI_CHECKPOINT` | `DreamShaper_8_pruned.safetensors` | اسم ملف محلي فقط |
| `STORYVERSE_COMFYUI_TIMEOUT_SEC` | `300` | مهلة انتظار المخرجات |
| `STORYVERSE_COMFYUI_WIDTH` / `_HEIGHT` | `512` | سقف عملي لـ 6GB |
| `STORYVERSE_ALLOW_*_LLM` | off | كما في Phase 4 |

---

## سياسات Phase 5

- **لا** تنزيل نماذج من التطبيق (ممنوع URL/مسار تحميل في `checkpoint`).
- استخدم **DreamShaper_8_pruned.safetensors** الموجود فقط.
- عامل طابور واحد — لا توازي GPU.
- إصدارات صور محفوظة؛ regenerate لمشهد واحد آمن.
- مراجع الشخصيات: stub خفيف (`visual_prompt` + مجلد `refs/`) — بدون IP-Adapter افتراضياً.
- Phase 6+ (فيديو) تحتاج موافقة صريحة منفصلة.

---

## عزل Flutter

`storyverse/` مستقل تماماً. تطبيق Flutter بلا تغيير متعمد في Phase 5.
