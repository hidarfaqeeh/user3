# 🚀 دليل النشر الشامل - Telegram Userbot Deployment Guide

## 📋 المتطلبات الأساسية

قبل النشر على أي منصة، تحتاج للبيانات التالية:

### 🔑 البيانات المطلوبة:
1. **API ID & Hash** من https://my.telegram.org/apps
2. **Bot Token** من @BotFather
3. **String Session** (استخدم `generate_session.py`)
4. **Admin User ID** (استخدم @userinfobot)
5. **معرفات القنوات** (اختياري - يمكن تعيينها لاحقاً)

---

## 🌐 1. Heroku

### الخطوات:
1. أنشئ حساب على [Heroku](https://heroku.com)
2. ثبت [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

```bash
# تسجيل الدخول
heroku login

# إنشاء تطبيق جديد
heroku create your-bot-name

# إضافة المتغيرات البيئية
heroku config:set TELEGRAM_API_ID=your_api_id
heroku config:set TELEGRAM_API_HASH=your_api_hash
heroku config:set TELEGRAM_STRING_SESSION=your_string_session
heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token
heroku config:set TELEGRAM_ADMIN_USER_ID=your_admin_id

# نشر الكود
git add .
git commit -m "Deploy telegram userbot"
git push heroku main

# تشغيل البوت
heroku ps:scale worker=1
```

### الميزات:
- ✅ مجاني (550 ساعة شهرياً)
- ✅ إعداد سهل
- ❌ يتوقف بعد 30 دقيقة من عدم النشاط

---

## 🚂 2. Railway

### الخطوات:
1. أنشئ حساب على [Railway](https://railway.app)
2. اربط مستودع GitHub

```bash
# تثبيت Railway CLI
npm install -g @railway/cli

# تسجيل الدخول
railway login

# إنشاء مشروع جديد
railway new

# إضافة المتغيرات البيئية
railway variables set TELEGRAM_API_ID=your_api_id
railway variables set TELEGRAM_API_HASH=your_api_hash
railway variables set TELEGRAM_STRING_SESSION=your_string_session
railway variables set TELEGRAM_BOT_TOKEN=your_bot_token
railway variables set TELEGRAM_ADMIN_USER_ID=your_admin_id

# نشر البوت
railway up
```

### الميزات:
- ✅ مجاني ($5 شهرياً)
- ✅ نشر تلقائي من GitHub
- ✅ لا يتوقف

---

## 🎨 3. Render

### الخطوات:
1. أنشئ حساب على [Render](https://render.com)
2. اربط مستودع GitHub
3. أنشئ "Web Service" جديد
4. استخدم الإعدادات التالية:

```yaml
Build Command: pip install -r requirements.txt
Start Command: python run_bot.py
```

### إضافة المتغيرات:
في لوحة تحكم Render > Environment:
```
TELEGRAM_API_ID = your_api_id
TELEGRAM_API_HASH = your_api_hash
TELEGRAM_STRING_SESSION = your_string_session
TELEGRAM_BOT_TOKEN = your_bot_token
TELEGRAM_ADMIN_USER_ID = your_admin_id
```

### الميزات:
- ✅ مجاني (750 ساعة شهرياً)
- ✅ SSL تلقائي
- ❌ يتوقف بعد 15 دقيقة من عدم النشاط

---

## ⚡ 4. Northflank

### الخطوات:
1. أنشئ حساب على [Northflank](https://northflank.com)
2. استورد المشروع من GitHub
3. استخدم `northflank.json` للإعداد التلقائي

### أو يدوياً:
```bash
# تثبيت Northflank CLI
npm install -g @northflank/cli

# تسجيل الدخول
northflank login

# إنشاء مشروع
northflank create project telegram-userbot

# نشر الخدمة
northflank deploy service \
  --name telegram-userbot \
  --project telegram-userbot \
  --image python:3.11-slim \
  --cmd "python run_bot.py"
```

### الميزات:
- ✅ مجاني (محدود)
- ✅ أداء عالي
- ✅ Docker native

---

## 🖥️ 5. VPS (السرفر المحلي)

### أ. باستخدام Docker:

```bash
# تحميل المشروع
git clone <your-repo-url>
cd telegram-userbot

# إنشاء ملف .env
cp .env.example .env
# املأ المتغيرات المطلوبة

# بناء وتشغيل البوت
docker-compose up -d

# مراقبة السجلات
docker-compose logs -f
```

### ب. التثبيت المباشر:

```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Python
sudo apt install python3 python3-pip git -y

# تحميل المشروع
git clone <your-repo-url>
cd telegram-userbot

# تثبيت المكتبات
pip3 install -r requirements.txt

# إعداد المتغيرات
cp .env.example .env
nano .env  # املأ البيانات

# تشغيل البوت
python3 run_bot.py
```

### ج. كخدمة نظام (systemd):

```bash
# إنشاء ملف الخدمة
sudo nano /etc/systemd/system/telegram-userbot.service
```

```ini
[Unit]
Description=Telegram Userbot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-userbot
Environment=PATH=/home/ubuntu/telegram-userbot/venv/bin
ExecStart=/home/ubuntu/telegram-userbot/venv/bin/python run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# تفعيل الخدمة
sudo systemctl daemon-reload
sudo systemctl enable telegram-userbot
sudo systemctl start telegram-userbot

# مراقبة الحالة
sudo systemctl status telegram-userbot
```

---

## 🔧 إعداد المتغيرات البيئية

### المتغيرات المطلوبة:
```env
TELEGRAM_API_ID=123456789
TELEGRAM_API_HASH=abcd1234efgh5678
TELEGRAM_STRING_SESSION=1BVtsOKoBu5...
TELEGRAM_BOT_TOKEN=1234567890:ABC...
TELEGRAM_ADMIN_USER_ID=123456789
```

### المتغيرات الاختيارية:
```env
SOURCE_CHAT_ID=-1001234567890
TARGET_CHAT_ID=-1001987654321
FORWARD_MODE=copy
MESSAGE_DELAY=1
LOG_LEVEL=INFO
ENVIRONMENT=production
```

---

## 🔍 استكشاف الأخطاء

### مشاكل شائعة:

#### 1. خطأ String Session:
```
AuthKeyError: Invalid authorization key
```
**الحل:** أعد إنشاء String Session باستخدام `generate_session.py`

#### 2. خطأ Bot Token:
```
BotAuthInvalidError
```
**الحل:** تحقق من صحة Bot Token من @BotFather

#### 3. خطأ في الصلاحيات:
```
ChatAdminRequiredError
```
**الحل:** تأكد من أن الحساب عضو في القناة المصدر

#### 4. مشكلة في المنصة:
- **Heroku**: تحقق من `heroku logs --tail`
- **Railway**: راجع لوحة التحكم > Logs
- **Render**: راجع لوحة التحكم > Logs
- **VPS**: استخدم `journalctl -u telegram-userbot -f`

---

## 📊 مقارنة المنصات

| المنصة | مجاني | مدة التشغيل | سهولة الإعداد | الأداء |
|--------|--------|------------|---------------|---------|
| Heroku | ✅ | متقطع | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Railway | ✅ | مستمر | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Render | ✅ | متقطع | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Northflank | ✅ | مستمر | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| VPS | ❌ | مستمر | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 التوصيات

### للمبتدئين:
- **Railway** أو **Render** للسهولة

### للاستخدام المكثف:
- **VPS** للتحكم الكامل والأداء العالي

### للتجربة:
- **Heroku** للبداية السريعة

---

## 🔐 نصائح الأمان

1. **لا تشارك** String Session أو Bot Token
2. **استخدم** متغيرات البيئة دائماً
3. **فعل** 2FA على جميع الحسابات
4. **راقب** سجلات البوت بانتظام
5. **حدث** المكتبات دورياً

---

🎉 **البوت جاهز للنشر على أي منصة تختارها!**