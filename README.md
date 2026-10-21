# مكتبة الدكتور محمد بن فارس الجميل

الموقع: https://mjalameellibrary.com

## المحتوى
- `public/` الموقع الجاهز للنشر: الصفحات، والملفات، ونصوص البحث.
- `functions/` و`lib/` واجهة صغيرة لعدّاد القراءة والتحميل والتعليقات (Cloudflare Pages Functions + D1).
- `source/` مصدر الموقع: قالب البناء والبيانات (العناوين، الفهارس، الملخصات).

## إعداد Cloudflare Pages
1. Workers & Pages ← Create ← Pages ← Connect to Git ← هذا المستودع.
2. Build command: اتركه فارغاً. Build output directory: `public`.
3. بعد أول نشر: Storage & Databases ← D1 ← Create database باسم `aljameel-library`.
4. في مشروع Pages: Settings ← Bindings ← Add ← D1 database، الاسم `DB`، واختر قاعدة البيانات.
5. Settings ← Variables and Secrets ← Add ← نوع Secret، الاسم `ADMIN_PASSWORD`، والقيمة كلمة مرور قوية.
6. أعد النشر (Deployments ← Retry deployment).

إدارة التعليقات: `/admin/`

## التعديل والنشر
- كل تعديل يُبنى بالأمر `npm run build` (يتطلب Python 3 وملفات العمل في `../library`)، فيُعاد توليد `public/` و`lib/slugs.js`.
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
