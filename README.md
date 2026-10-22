# مكتبة الدكتور محمد بن فارس الجميل

الموقع: https://mjalameellibrary.com

## المحتوى
- `public/` الموقع الجاهز للنشر: الصفحات، وملفات PDF المنشورة، ونصوص البحث. **يُولَّد آلياً، لا يُعدَّل يدوياً.**
- `functions/` و`lib/` واجهة صغيرة لعدّاد القراءة والتحميل والتعليقات (Cloudflare Pages Functions + D1).
- `source/` قالب البناء `build.py`، والتصميم والنصوص البرمجية في `src/`، ومكتبات البناء في `package.json`.
- `library/` ملفات العمل:
  - `content/` بيانات المؤلفات: `base.json` (العنوان، النوع، السنة، المحور، الناشر)، `toc.json` (الفهارس وأرقام الصفحات)، `summaries.json` (النبذ والنتائج والمقتطفات)، `research.json` (بيانات نشر الأبحاث)، `cite.json` (حقول التوثيق)، `bio.json` (سيرة المؤلف).
  - `covers/` الأغلفة الأصلية (`<id>.webp`) وصورة المؤلف، و`media/` الفيديو والصور.
  - `ocr/<id>/` نص كل صفحة مستخرجاً آلياً، و`site-data/search/` فهارس البحث المبنية منه، و`rot/<id>` زاوية تدوير الملفات المائلة.
  - `tools/` أدوات استخراج النص وبناء الفهارس وضغط الملفات الثقيلة.
  - ملفات PDF الأصلية الكبيرة (`pdfs/` و`fixed/` و`web/`) لا تُرفع إلى GitHub لحجمها؛ النسخ المنشورة في `public/pdfs` والأصول في Google Drive العائلة. البناء يعمل بدونها.

## إعداد Cloudflare Pages
1. Workers & Pages ← Create ← Pages ← Connect to Git ← هذا المستودع.
2. Build command: اتركه فارغاً. Build output directory: `public`.
3. بعد أول نشر: Storage & Databases ← D1 ← Create database باسم `aljameel-library`.
4. في مشروع Pages: Settings ← Bindings ← Add ← D1 database، الاسم `DB`، واختر قاعدة البيانات.
5. Settings ← Variables and Secrets ← Add ← نوع Secret، الاسم `ADMIN_PASSWORD`، والقيمة كلمة مرور قوية.
6. أعد النشر (Deployments ← Retry deployment).

إدارة التعليقات: `/admin/`

## التعديل والنشر
- بعد أي تعديل في `library/content` أو `source/`: `npm run build` (يتطلب Node وPython 3)، فيُعاد توليد `public/` و`lib/slugs.js`، ثم `npm test`.
- أي دفع إلى الفرع `main` يُنشر تلقائياً على الموقع. للمعاينة قبل النشر يُدفع إلى الفرع `preview`، فيظهر على `https://preview.aljameel-library.pages.dev`.
- **التراجع عند حدوث مشكلة:** Cloudflare ← Workers & Pages ← aljameel-library ← Deployments ← اختر النشر السابق ← ⋯ ← **Rollback to this deployment**. يعود الموقع خلال ثوانٍ، ولا تتأثر قاعدة البيانات (العدادات والتعليقات).

## الاختبارات
- `npm test`: فحص الموقع المبني: كل كتاب له صفحة وملف PDF وفهرس بحث ومدخل في خريطة الموقع، وأرقام صفحات الفهرس داخل حدود الملف، والتحويلات القديمة سليمة، ولا توجد نصوص برمجية مضمّنة تخالف سياسة الأمان.
- `npm run test:api`: اختبار الواجهة على خادم محلي (`npm run dev`) بكلمة مرور تجريبية في `.dev.vars` (لا تُستخدم كلمة المرور الحقيقية أبداً):
  العدادات، ومنع التكرار، والتحقق من التعليقات وفخاخ البرامج الآلية، وحماية لوحة الإدارة وقفلها بعد المحاولات الخاطئة.
- `python3 tests/browser_check.py`: يفتح الصفحات الرئيسية في متصفح على مقاسي الجوال والحاسوب، ويبلّغ عن أخطاء البرمجة ومخالفات سياسة الأمان والتمرير الأفقي.

## الأمان
- كلمة مرور الإدارة سرّ في Cloudflare (`ADMIN_PASSWORD`) وليست في الكود.
- جلسة الإدارة ٧ أيام في ملف تعريف موقّع (HttpOnly, Secure, SameSite=Strict)، وتُقفل محاولات الدخول بعد ٥ أخطاء في الساعة لكل زائر.
- ترويسات الأمان في `public/_headers` (تُولَّد من `source/build.py`): Content-Security-Policy صارمة بلا نصوص مضمّنة، وHSTS، وغيرها.

## إضافة كتاب أو بحث جديد
1. اختر رقماً جديداً (مثل `25`) وضع الملف في `library/pdfs/25.pdf`.
2. إن كانت صفحاته مائلة، اكتب الزاوية في `library/rot/25` (مثل `90`)، وضع نسخة مستقيمة في `library/fixed/25.pdf` (`qpdf pdfs/25.pdf --rotate=+90 fixed/25.pdf`). وإن كان ملفاً ممسوحاً ثقيلاً جداً: `python3 library/tools/recompress.py 25`.
3. استخرج النص: `library/tools/ocr.sh 25` (يتطلب tesseract بالنموذج العربي `ara` وpoppler-utils وimagemagick)، ثم ابنِ الفهارس: `npm run index`.
4. أضف بياناته في `library/content/base.json` (معرّف URL ثابت في `slug`)، والفهرس في `toc.json` (العنوان، رقم الصفحة المطبوع، رقم صفحة الملف)، والنبذة في `summaries.json`، وبيانات النشر في `research.json` و`cite.json`، والغلاف في `library/covers/25.webp`.
5. `npm run build` ثم `npm test`، وادفع إلى الفرع `preview` للمعاينة، ثم إلى `main` للنشر.
