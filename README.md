# يا سلام! لايف

نسخة غرف متزامنة من لعبة «يا سلام!». المضيف ينشئ غرفة، واللاعبون يدخلون من جوالاتهم بكود من أربعة أرقام. تستخدم FastAPI وWebSockets.

## تشغيل محلي

على Windows يمكنك الضغط مرتين على `start_live.bat`، أو استخدام الأوامر التالية:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

افتح `http://127.0.0.1:8000`. وللتجربة من جوالات على نفس الشبكة افتح عنوان IP الخاص باللابتوب على المنفذ 8000.

## النشر على Render

1. ارفع مجلد المشروع إلى مستودع GitHub.
2. في Render اختر **New > Web Service** واربط المستودع.
3. اترك Root Directory فارغًا إذا رفعت محتويات هذا المجلد في مستودع مستقل. إذا رفعت مستودع FASTER كاملًا، اجعله `ya_salam_live`.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. اختر الخطة المناسبة ثم Deploy.

يوجد `render.yaml` جاهز أيضًا للنشر بطريقة Blueprint.

## حدود النسخة الحالية

- الغرف محفوظة في ذاكرة السيرفر وتُحذف بعد ساعتين من عدم الاستخدام.
- إعادة تشغيل الخدمة تنهي الغرف المفتوحة.
- شغّل نسخة سيرفر واحدة فقط. للتوسع إلى عدة نسخ استخدم Redis لحفظ حالة الغرف وتوزيع الرسائل.
