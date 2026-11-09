# StoryVerse AI Studio — Phase 6 (Short Clip Video Engine)

> مجلد **معزول** عن تطبيق Flutter في جذر المستودع. لا يغيّر `lib/` أو `pubspec.yaml`.

**Phase 6:** محرك مقاطع قصيرة فوق Phase 5 (صور ComfyUI) + Phase 4 (قصة/مشاهد).

| الحقيقة | التفصيل |
|---------|---------|
| المسار الافتراضي | **FFmpeg Ken Burns** (still→MP4) — **fallback وليس فيديو بالذكاء الاصطناعي** |
| Wan 1.3B / LTX | Adapters جاهزة كسطح API — **مغلقة** حتى موافقة صريحة + نماذج محلية |
| تنزيلات نماذج فيديو | **لا تلقائياً أبداً** — علم `STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD` للموافقة اليدوية فقط |
| طابور | عامل واحد: `fake` / `image_generate` / **`video_generate`** |
| أصول | إصدارات لكل مشهد: `…/scenes/{id}/clips/vNNN.mp4` |

---

## مزامنة مع Windows (`D:\StoryVerse\app`)

```text
D:\StoryVerse\
  venv\
  apps\comfyui\              # محرك ComfyUI (صور Phase 5؛ I2V لاحقاً)
  models\checkpoints\
    DreamShaper_8_pruned.safetensors
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
# تأكد أن ffmpeg على PATH (مطلوب للـ fallback)
ffmpeg -version
python -m app.main
```

افتح: http://127.0.0.1:8765/docs

---

## ماذا يوجد هنا؟

| المسار | الوظيفة |
|--------|---------|
| `app/image/` | Phase 5 — ComfyUI صور + mock |
| `app/video/adapter.py` | حفظ مقاطع بإصدارات + اختيار المحرك |
| `app/video/ffmpeg_fallback.py` | Ken Burns / still→MP4 (**ليس AI**) |
| `app/video/comfyui_i2v.py` | Stub Wan/LTX — يرفض بدون أعلام + ملفات محلية |
| `app/video/gates.py` | بوابات الموافقة / لا تنزيل تلقائي |
| `app/queue.py` | `fake` + `image_generate` + **`video_generate`** |
| `scripts/smoke_test.py` | دخان: قصة + صور mock + مقاطع FFmpeg |

---

## نقاط API (Phase 6)

| Method | Path | وصف |
|--------|------|-----|
| POST | `/api/v1/scenes/{id}/generate-clip` | طابور مقطع قصير لمشهد |
| POST | `/api/v1/projects/{pid}/scenes/{sid}/generate-clip` | نفس الأمر مع تحقق المشروع |
| GET | `/api/v1/scenes/{id}/clips` | كل إصدارات مقاطع المشهد |
| GET | `/api/v1/video/gates` | حالة محرك الفيديو والأعلام |
| POST | `/api/v1/scenes/{id}/generate-image` | كما في Phase 5 |
| GET | `/api/v1/health` | يتضمن `video_engine` / `ai_video_active` |

### مثال مقطع (fallback)

```powershell
# بعد توليد صورة للمشهد:
curl -X POST http://127.0.0.1:8765/api/v1/scenes/1/generate-clip `
  -H "Content-Type: application/json" `
  -d "{\"duration_sec\":3,\"fps\":12,\"width\":512,\"height\":512}"
```

الملفات:

```text
D:\StoryVerse\projects\{project_id}\assets\scenes\{scene_id}\clips\v001.mp4
D:\StoryVerse\projects\{project_id}\assets\scenes\{scene_id}\clips\v002.mp4
```

`meta.ai_video=false` و `meta.fallback=true` و `meta.engine=ffmpeg_kenburns`.

---

## اختبار الدخان (CI / بدون GPU / بدون تنزيل نماذج)

```powershell
cd D:\StoryVerse\app   # أو storyverse/ في المستودع
python scripts\smoke_test.py
```

المتوقع:

`PASS — story + image_generate (mock ComfyUI) + video_generate (ffmpeg Ken Burns fallback, NOT AI) + versioned regenerate (no GPU / no model download)`

يتطلب **ffmpeg** على PATH. لا ينزّل Wan/LTX.

---

## نماذج AI I2V — موافقة صريحة مطلوبة (لا تدّعي أنها تعمل بعد)

> **صادق:** Phase 6 **لا** تدّعي أن فيديو Wan/LTX يعمل. المسار العامل هو FFmpeg fallback.

### الأعلام

| متغير | افتراضي | المعنى |
|--------|---------|--------|
| `STORYVERSE_VIDEO_ENGINE` | `ffmpeg_kenburns` | `ffmpeg_kenburns` / `mock` / `comfyui_wan` / `comfyui_ltx` |
| `STORYVERSE_ALLOW_AI_VIDEO` | off | إذن استخدام مسار AI (بدون تنزيل) |
| `STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD` | off | موافقة المستخدم على **تثبيت يدوي لاحق** فقط — التطبيق **لا** ينزّل |

حتى مع `ALLOW_AI_VIDEO=1` وملف محلي موجود، بناء Phase 6 يرفض التشغيل الفعلي لـ I2V (stub) حتى تُربط رسوم ComfyUI وتُختبر على العتاد.

### ملاحظات VRAM — RTX 4050 Laptop **6GB**

| نموذج مرشّح | ملاحظة واقعية |
|-------------|----------------|
| **Wan2.1 1.3B** (fp8 / GGUF + tiled VAE عبر ComfyUI) | فوق/حدّي على 6GB بدون تكميم؛ توقّع بطء دقائق لمقطع قصير منخفض الدقة |
| **LTX-Video 2B distilled / fp8 / GGUF** | بديل أخف للمسودات؛ قلّل الدقة والإطارات |
| Wan 14B / LTX 13B | **غير مناسب** كافتراضي على 6GB |

قيود Phase 6 الصارمة (عند تفعيل AI لاحقاً): مدة قصيرة (`STORYVERSE_VIDEO_MAX_DURATION_SEC` ≤ 8)، دقة منخفضة (512)، إطارات قليلة، طابور متسلسل (لا توازي GPU).

### كيف توافق لاحقاً (يدوياً — ليس من التطبيق)

1. اقرأ هذا القسم وقيود 6GB.
2. ثبّت الأوزان **بنفسك** تحت `D:\StoryVerse\models\…` أو مجلدات ComfyUI.
3. عيّن `STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD=1` لتوثيق الموافقة على التثبيت اليدوي.
4. عيّن `STORYVERSE_ALLOW_AI_VIDEO=1` و`STORYVERSE_VIDEO_ENGINE=comfyui_wan` أو `comfyui_ltx` فقط بعد وجود الملفات.
5. انتظر تحديثاً يربط workflow ComfyUI I2V ويُثبت على جهازك — حتى ذلك الحين **لا** تُعلن أن AI video يعمل.

---

## متغيرات البيئة

| متغير | افتراضي | المعنى |
|--------|---------|--------|
| `STORYVERSE_ROOT` | `storyverse/data/root` | جذر البيانات/المشاريع |
| `STORYVERSE_COMFYUI_BASE_URL` | `http://127.0.0.1:8188` | ComfyUI (صور) |
| `STORYVERSE_COMFYUI_CHECKPOINT` | `DreamShaper_8_pruned.safetensors` | محلي فقط |
| `STORYVERSE_VIDEO_ENGINE` | `ffmpeg_kenburns` | محرك المقاطع |
| `STORYVERSE_VIDEO_DURATION_SEC` | `3` | مدة المقطع الافتراضية |
| `STORYVERSE_VIDEO_FPS` | `12` | إطارات/ث |
| `STORYVERSE_ALLOW_AI_VIDEO` | off | بوابة AI |
| `STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD` | off | موافقة تثبيت يدوي فقط |

---

## سياسات Phase 6

- **لا** تنزيل نماذج فيديو من التطبيق.
- المسار الافتراضي **fallback** — لا تخلطه مع AI I2V في الواجهة أو التقارير.
- عامل طابور واحد لكل من الصور والمقاطع.
- إصدارات مقاطع محفوظة؛ regenerate لمشهد واحد آمن.
- Phase 7+ تحتاج موافقة صريحة منفصلة.

---

## عزل Flutter

`storyverse/` مستقل تماماً. تطبيق Flutter بلا تغيير متعمد في Phase 6.
