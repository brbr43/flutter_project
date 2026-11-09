# StoryVerse AI Studio — Phase 4 (Story / Script / Scenes)

> مجلد **معزول** عن تطبيق Flutter في جذر المستودع. لا يغيّر `lib/` أو `pubspec.yaml`.

**Phase 4:** فكرة → مسودة سيناريو → قائمة مشاهد قابلة للتحرير (JSON) + قوالب نوع أدبي.  
يبني على Phase 3 (SQLite + FastAPI + طابور عامل واحد).

**بدون** تنزيل نماذج، **بدون** استدعاء ComfyUI، **بدون** APIs مدفوعة افتراضياً.  
المولّد الافتراضي: **قوالب حتمية (template)** — لا ML.

---

## مزامنة مع Windows (`D:\StoryVerse\app`)

```text
D:\StoryVerse\
  venv\
  apps\comfyui\         # لا تلمسه
  models\               # لا تنزّل شيئاً جديداً في Phase 4
  app\                  # ← انسخ محتوى storyverse/ إلى هنا
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
# دائم:
setx STORYVERSE_ROOT "D:\StoryVerse"
```

أو:

```powershell
Copy-Item -Recurse -Force .\storyverse\* D:\StoryVerse\app\
```

### تثبيت وتشغيل

```powershell
cd D:\StoryVerse
.\venv\Scripts\Activate.ps1
cd app
pip install -r requirements.txt
$env:STORYVERSE_ROOT = "D:\StoryVerse"
python -m app.main
```

افتح: http://127.0.0.1:8765/docs

---

## ماذا يوجد هنا؟

| المسار | الوظيفة |
|--------|---------|
| `app/models.py` | جداول Phase 3 + حقول قصة/سيناريو/كاميرا/إضاءة/`content_tag` |
| `app/story/templates.py` | قوالب: documentary, hollywood, mystery, historical, drama, adventure |
| `app/story/generator.py` | مولّد حتمي → JSON قابل للتحرير |
| `app/story/llm.py` | بوابات LLM اختيارية (مغلقة افتراضياً — موثّقة فقط) |
| `scripts/smoke_test.py` | فكرة → مشاهد JSON + تعديل/إعادة ترتيب بدون ML |

---

## نقاط API الرئيسية (Phase 4)

| Method | Path | وصف |
|--------|------|-----|
| GET | `/api/v1/story/genres` | قائمة القوالب |
| GET | `/api/v1/story/llm-gates` | حالة بوابات LLM |
| POST | `/api/v1/story/generate` | فكرة → مشروع + سيناريو + مشاهد |
| GET | `/api/v1/projects/{id}/story` | JSON كامل قابل للتحرير |
| PUT | `/api/v1/projects/{id}/story` | تعديل عنوان/ملخص/beats |
| PATCH | `/api/v1/scenes/{id}` | تعديل يدوي لمشهد |
| PUT | `/api/v1/projects/{id}/scenes/reorder` | إعادة ترتيب `{ "scene_ids": [...] }` |

### مثال توليد

```powershell
curl -X POST http://127.0.0.1:8765/api/v1/story/generate `
  -H "Content-Type: application/json" `
  -d "{\"idea\":\"حارس منارة يفك شفرة أضواء سفينة مفقودة\",\"genre\":\"mystery\",\"true_story_mode\":false,\"language\":\"ar\"}"
```

الاستجابة تتضمن: `title`, `synopsis`, `beats`, `scenes[]` مع `camera` / `lighting` / `prompt` / `content_tag`.

### وضع القصة الحقيقية (true-story)

عند `"true_story_mode": true` تُوسم المشاهد بـ `fact` أو `dramatization` (لا تُخلط مع الخيال دون وسم).

---

## بوابات LLM (مغلقة افتراضياً)

| متغير البيئة | افتراضي | المعنى |
|--------------|---------|--------|
| `STORYVERSE_ALLOW_LOCAL_LLM` | `0` / off | إذن LLM محلي فقط — Phase 4 **لا** يحمّل نماذج |
| `STORYVERSE_ALLOW_CLOUD_LLM` | `0` / off | إذن سحابي |
| `STORYVERSE_CLOUD_LLM_API_KEY` | فارغ | مطلوب مع العلم السحابي |

حتى مع `STORYVERSE_ALLOW_CLOUD_LLM=1` ومفتاح موجود، Phase 4 **لا يستدعي** APIs مدفوعة تلقائياً؛ المولّد العامل يبقى القوالب. السحابي موثّق كمسار معلّق فقط.

**لا تنزيلات نماذج. لا ComfyUI.**

---

## اختبار الدخان (Smoke) — بدون ML

```powershell
cd D:\StoryVerse\app
$env:STORYVERSE_ROOT = "D:\StoryVerse"
.\venv\Scripts\Activate.ps1
python scripts\smoke_test.py
```

المتوقع:

`PASS — idea→editable JSON scenes + edit/reorder (template generator, no ML)`

---

## سياسات Phase 4

- لا تنزيل نماذج (SD / Wan / LTX / TTS / LLM).
- لا استدعاء ComfyUI.
- لا APIs مدفوعة افتراضياً؛ السحابي خلف علم + مفتاح وموثّق كمسار معلّق.
- Phase 5+ تحتاج موافقة صريحة منفصلة.

---

## عزل Flutter

`storyverse/` مستقل تماماً. تطبيق Flutter بلا تغيير متعمد في Phase 4.
