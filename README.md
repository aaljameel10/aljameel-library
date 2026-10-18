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
