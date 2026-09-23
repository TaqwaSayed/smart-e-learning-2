# Smart E-Learning 2

منصة تعليمية ذكية (Django) فيها:
- مساعد سقراطي بالـ Gemini (`google-genai`).
- كويز adaptive بيرتب الأسئلة حسب نقط ضعف كل طالب (فكرة زي Najwa Limited).
- نظام نقاط + مستويات + شارات (gamification).
- تذكير بالأذكار/التحفيز كل 25 دقيقة (بومودورو) قبل/أثناء/بعد المذاكرة.
- واجهة RTL بالكامل بالتدرج اللوني الفاخر (أخضر زيتوني غامق → أسود).

## التشغيل محليًا

1. ثبّتي PostgreSQL وشغّليه، وسجّلي قاعدة بيانات:
   ```
   createdb smart_e_learning_2
   ```
2. انسخي `.env.example` باسم `.env` واملي فيه بياناتك الحقيقية (خصوصًا `GEMINI_API_KEY`).
3. ثبّتي المكتبات:
   ```
   pip install -r requirements.txt
   ```
4. شغّلي الـ migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
5. اعملي حساب أدمن:
   ```
   python manage.py createsuperuser
   ```
6. سجّلي صور الأذكار الستة (موجودة بالفعل في media/mindfulness/):
   ```
   python manage.py seed_mindfulness
   ```
7. شغّلي السيرفر:
   ```
   python manage.py runserver
   ```

## قبل الـ Presentation — لازم تعمليه بنفسك

أنا اختبرت المشروع بالكامل (migrations + auth + enrollment + الكويز الـ adaptive +
النقاط + gamification) فعليًا على PostgreSQL حقيقي، بمحاكاة أكتر من طالب —
شوفي `smoke_test.py` (شغليه بـ `python manage.py shell < smoke_test.py`).

**اللي معرفتش أختبره من عندي:** المكالمة الفعلية لـ Gemini API. البيئة اللي بشتغل
فيها ممنوع عليها تتصل بأي API بره GitHub/PyPI (قيود شبكة)، فمقدرش أتأكد إن مفتاحك
شغال فعليًا مع Google. **قبل العرض بيوم على الأقل**، افتحي صفحة `/chat/`، ابعتي
رسالة، وتأكدي إنك بتاخدي رد حقيقي من Gemini. لو حصل أي خطأ:
- تأكدي إن `GEMINI_API_KEY` في `.env` صحيح ومفعّل من https://aistudio.google.com/apikey
- الكود فيه fallback: لو الاتصال فشل وقت العرض، هيرجع رد احتياطي بدل ما يكسر الصفحة،
  لكن الأفضل تتأكدي إن الاتصال شغال فعلاً قبلها.

## هيكل الـ ERD

الجداول والعلاقات مبنية بالظبط على صفحة الـ Relationships اللي بعتيها (22 علاقة)،
تفاصيل أي قرار مش 100% واضح من الرسمة متسجل كـ docstring جوه الـ model نفسه.

## ⚠️ If Arabic text shows as question marks (`????`)

This means your PostgreSQL database was created with the wrong encoding
(common default on Windows installs). Fix it by recreating the database
with UTF8 explicitly:

```
dropdb smart_e_learning_2
createdb --encoding=UTF8 --locale=en_US.UTF-8 --template=template0 smart_e_learning_2
python manage.py migrate
```

If `createdb` complains about the locale not existing, use:
```
createdb --encoding=UTF8 --template=template0 smart_e_learning_2
```
Then re-run `python manage.py migrate` and re-create your test data.
