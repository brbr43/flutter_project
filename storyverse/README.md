# StoryVerse AI Studio — سقالة المرحلة 2

> مجلد **جديد** مستقل عن تطبيق Flutter الموجود في جذر هذا المستودع. لا يحوّل تطبيق Flutter إلى StoryVerse.

## ماذا يوجد هنا؟

| المسار | الوظيفة |
|--------|---------|
| `scripts/windows/collect-env.ps1` | تقرير بيئة حي (بدون تثبيت / بدون نماذج) |
| `scripts/windows/bootstrap-venv.ps1` | venv + تبعيات خفيفة؛ PyTorch/ComfyUI اختياريان ومُبوَّبان |
| `scripts/windows/smoke-test-light.ps1` | اختبار دخان للتبعيات الخفيفة فقط |

## الوثائق الكاملة (مخزن المشروع)

على أجهزة Cursor Project، انظر:

- `docs/phase-2-environment-runbook.md`
- `docs/phase-2-live-checklist.md`
- `docs/phase-2-status.md`
- `docs/phase-1-engineering-report.md`

## تشغيل سريع على Windows 11

```powershell
cd storyverse
..\..\  # أو انسخ السكربتات إلى مجلد عمل D:\StoryVerse

# 1) جمع تقرير فقط
.\scripts\windows\collect-env.ps1 -OutputDir .\reports

# 2) venv خفيف (افتراضي — بدون torch)
.\scripts\windows\bootstrap-venv.ps1 -VenvPath .\venv

# 3) دخان خفيف
.\scripts\windows\smoke-test-light.ps1 -VenvPath .\venv

# اختياري بعد موافقة صريحة:
# .\scripts\windows\bootstrap-venv.ps1 -VenvPath .\venv -ApproveTorch
# .\scripts\windows\bootstrap-venv.ps1 -VenvPath .\venv -ApproveComfyClone -ComfyPath .\apps\comfyui
```

## سياسات صارمة

- **لا** تنزيل نماذج (SD / Wan / LTX / TTS / LLM) من هذه السكربتات.
- **لا** `-ApproveTorch` / `-ApproveComfyClone` بدون قرار المستخدم.
- ربط وكيل محلي: `agent worker start` على جهاز GPU (انظر دليل Phase 2).

## الحالة

Phase 2 هنا = **تجهيز** فقط. تهيئة GPU الحية ما زالت معلّقة حتى يتصل جهاز Windows أو يُشغَّل `collect-env.ps1` ويُعاد الناتج.
