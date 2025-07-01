# دليل المهام المتعددة المتزامنة - Multi-Task Concurrent Steering Guide

## 🎯 المميزات الجديدة / New Features

### العربية
تم تطوير البوت ليدعم **مهام توجيه متعددة ومتزامنة** مع إمكانيات متقدمة:

#### 🚀 الميزات الأساسية:
- **تشغيل مهام متعددة في نفس الوقت** - كل مهمة تعمل بشكل مستقل
- **إعدادات منفصلة لكل مهمة** - فلاتر وإعدادات مخصصة
- **إدارة كاملة من لوحة التحكم** - إضافة، حذف، تشغيل، إيقاف
- **مراقبة الأداء لكل مهمة** - إحصائيات مفصلة ومعدلات النجاح
- **إدارة الموارد الذكية** - تحكم في معدلات الإرسال لكل مهمة

#### 🎛️ إمكانيات الإدارة:
- ✅ إضافة مهام جديدة بسهولة
- ⏸️ إيقاف/تشغيل مهام محددة
- 🔄 إعادة تشغيل المهام
- 📊 مراقبة الإحصائيات لكل مهمة
- ⚙️ إعدادات مستقلة لكل مهمة
- 🗑️ حذف المهام غير المرغوبة

### English
Enhanced the bot to support **multiple concurrent steering tasks** with advanced capabilities:

#### 🚀 Core Features:
- **Multiple simultaneous tasks** - Each task operates independently
- **Individual task settings** - Custom filters and configurations
- **Full control panel management** - Add, delete, start, stop tasks
- **Per-task performance monitoring** - Detailed statistics and success rates
- **Smart resource management** - Rate limiting per task

## 📋 كيفية الاستخدام / How to Use

### 1. تشغيل البوت / Starting the Bot

```bash
# تشغيل البوتين معاً مع دعم المهام المتعددة
python run_bot.py
# اختر الخيار 3 لتشغيل البوتين معاً
```

### 2. الوصول لإدارة المهام / Accessing Task Management

1. **افتح بوت التحكم** / Open the control bot
2. **اضغط على "🎯 إدارة المهام المتعددة"** / Click "🎯 Multi-Task Management"
3. **ستظهر لك القائمة الرئيسية للمهام** / Main task menu will appear

### 3. إضافة مهمة جديدة / Adding a New Task

#### من لوحة التحكم / From Control Panel:
1. اضغط **"➕ إضافة مهمة"**
2. أدخل **اسم المهمة** (مثل: "توجيه الأخبار")
3. أدخل **معرف القناة المصدر** (مثل: `-1001234567890`)
4. أدخل **معرف القناة الهدف** (مثل: `-1009876543210`)
5. المهمة ستبدأ تلقائياً!

#### التنسيقات المقبولة للقنوات / Accepted Channel Formats:
```
• معرف رقمي: -1001234567890
• اسم مستخدم: @channel_name  
• رابط: https://t.me/channel_name
```

### 4. إدارة المهام الموجودة / Managing Existing Tasks

#### عرض المهام / View Tasks:
- **📋 عرض المهام**: قائمة بجميع المهام وحالتها
- **📊 إحصائيات المهام**: بيانات مفصلة عن الأداء

#### التحكم في المهام / Task Control:
- **▶️ تشغيل مهمة**: تشغيل مهمة متوقفة
- **⏹️ إيقاف مهمة**: إيقاف مهمة نشطة
- **🔄 إعادة تشغيل**: إعادة تشغيل مهمة
- **🗑️ حذف مهمة**: حذف مهمة نهائياً

## 🔧 الإعدادات المتقدمة / Advanced Configuration

### إعدادات ملف JSON

المهام تُحفظ في ملف `steering_tasks.json`:

```json
[
  {
    "task_id": "task_1234567890_abc123",
    "name": "توجيه الأخبار",
    "source_chat": "-1001234567890",
    "target_chat": "-1009876543210",
    "enabled": true,
    "forward_delay": 1.0,
    "max_retries": 3,
    "forward_mode": "copy",
    "forward_text": true,
    "forward_photos": true,
    "forward_videos": true,
    "blacklist_enabled": false,
    "whitelist_enabled": false,
    "clean_links": true,
    "header_enabled": false,
    "footer_enabled": true,
    "footer_text": "قناة الأخبار الرسمية"
  }
]
```

### إعدادات مخصصة لكل مهمة / Per-Task Custom Settings

كل مهمة يمكن أن تحتوي على:

#### 🎛️ فلاتر المحتوى / Content Filters:
```json
{
  "forward_text": true,
  "forward_photos": true,
  "forward_videos": false,
  "forward_music": true,
  "forward_stickers": false
}
```

#### 🚫 قوائم الحظر والسماح / Blacklist & Whitelist:
```json
{
  "blacklist_enabled": true,
  "blacklist_words": "إعلان,ترويج,دعاية",
  "whitelist_enabled": false,
  "whitelist_words": "مهم,عاجل,خبر"
}
```

#### 📝 معالجة النصوص / Text Processing:
```json
{
  "header_enabled": true,
  "header_text": "🔴 عاجل:",
  "footer_enabled": true,
  "footer_text": "قناة الأخبار الرسمية",
  "clean_links": true,
  "clean_hashtags": false
}
```

#### 🔄 استبدال النصوص / Text Replacement:
```json
{
  "replacer_enabled": true,
  "replacements": "كلمة قديمة->كلمة جديدة,نص للحذف->"
}
```

## 📊 مراقبة الأداء / Performance Monitoring

### إحصائيات المهام / Task Statistics

لكل مهمة تحصل على:

```
📊 إحصائيات المهمة:
• الرسائل المعالجة: 150
• الرسائل الموجهة: 145  
• الرسائل الفاشلة: 5
• معدل النجاح: 96.7%
• آخر نشاط: 14:30:25
• مدة التشغيل: 2 ساعة و 15 دقيقة
```

### أوامر المراقبة / Monitoring Commands

من البوت الأساسي:

```
/ping - حالة جميع المهام
/tasks - تفاصيل كل مهمة
```

## 🚀 أمثلة عملية / Practical Examples

### مثال 1: توجيه الأخبار / News Forwarding
```json
{
  "name": "توجيه أخبار التقنية",
  "source_chat": "@tech_news_source",
  "target_chat": "@my_tech_channel",
  "forward_text": true,
  "forward_photos": true,
  "forward_videos": false,
  "blacklist_enabled": true,
  "blacklist_words": "إعلان,ترويج",
  "header_enabled": true,
  "header_text": "🔴 أخبار التقنية:"
}
```

### مثال 2: نسخ المحتوى الترفيهي / Entertainment Content
```json
{
  "name": "محتوى ترفيهي",
  "source_chat": "-1001234567890",
  "target_chat": "-1009876543210",
  "forward_photos": true,
  "forward_videos": true,
  "forward_stickers": true,
  "forward_text": false,
  "clean_links": true,
  "footer_enabled": true,
  "footer_text": "قناة الترفيه | @entertainment_channel"
}
```

### مثال 3: توجيه انتقائي / Selective Forwarding
```json
{
  "name": "المحتوى المهم فقط",
  "source_chat": "@main_channel",
  "target_chat": "@filtered_channel",
  "whitelist_enabled": true,
  "whitelist_words": "مهم,عاجل,حصري,خبر",
  "forward_mode": "copy",
  "clean_hashtags": true,
  "replacer_enabled": true,
  "replacements": "قناة أخرى->قناتنا الرسمية"
}
```

## 🛠️ استكشاف الأخطاء / Troubleshooting

### مشاكل شائعة / Common Issues

#### 1. المهمة لا تعمل / Task Not Working
```
✅ تحقق من:
• صحة معرفات القنوات
• صلاحيات البوت في القنوات
• تفعيل المهمة من لوحة التحكم
• اتصال البوت الأساسي
```

#### 2. رسائل مفقودة / Missing Messages
```
✅ تحقق من:
• فلاتر المحتوى (forward_text, forward_photos, etc.)
• قوائم الحظر والسماح
• إعدادات التنظيف (clean_links, clean_hashtags)
```

#### 3. بطء في التوجيه / Slow Forwarding
```
✅ اضبط:
• forward_delay (قلل القيمة)
• max_retries (قلل عدد المحاولات)
• عدد المهام المتزامنة (أوقف بعض المهام)
```

### سجلات التشخيص / Diagnostic Logs

```bash
# عرض السجلات
tail -f userbot.log

# البحث عن مهمة محددة
grep "task_1234567890" userbot.log

# مراقبة الأخطاء
grep "ERROR" userbot.log
```

## 🔒 الأمان والحدود / Security and Limits

### حدود الأداء / Performance Limits
- **الحد الأقصى للمهام المتزامنة**: 10-15 مهمة
- **تأخير التوجيه المنصوح**: 0.5-2 ثانية
- **عدد المحاولات**: 3 محاولات كحد أقصى

### أمان البيانات / Data Security
- جميع الإعدادات محفوظة محلياً
- لا يتم إرسال بيانات للخارج
- المهام معزولة عن بعضها البعض

## 🎉 الخلاصة / Conclusion

الآن البوت يدعم:
- ✅ **مهام متعددة متزامنة** مع إدارة كاملة
- ✅ **إعدادات منفصلة** لكل مهمة
- ✅ **مراقبة شاملة** للأداء والإحصائيات
- ✅ **إدارة سهلة** من لوحة التحكم التفاعلية
- ✅ **مرونة كاملة** في التخصيص

🚀 **ابدأ الآن واستمتع بقوة المهام المتعددة!**

---

## 📞 الدعم / Support

إذا واجهت أي مشاكل:
1. تحقق من السجلات (`userbot.log`)
2. راجع إعدادات المهام في `steering_tasks.json`
3. استخدم أوامر التشخيص (`/ping`, `/tasks`)
4. أعد تشغيل البوت إذا لزم الأمر