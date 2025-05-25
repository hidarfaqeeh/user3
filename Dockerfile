# استخدام Python 3.11 كصورة أساسية محسنة
FROM python:3.11-slim

# تثبيت المكتبات النظامية المطلوبة
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt ./

# تحديث pip وتثبيت المكتبات
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع ملفات البوت
COPY . .

# إنشاء مستخدم غير جذر للأمان
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# تعيين متغيرات البيئة
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# تعيين البورت
EXPOSE 8080

# إعطاء صلاحيات تنفيذ للملفات
USER root
RUN chmod +x /app/*.py
USER app

# تشغيل النظام السريع مع دعم Webhook التلقائي
CMD ["python", "run_ultra_fast.py"]