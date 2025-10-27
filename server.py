from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import os
import logging
from io import BytesIO
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

app = Flask(__name__)
CORS(app)  # دعم CORS للسماح بطلبات من الواجهة الأمامية
app.config['UPLOAD_FOLDER'] = 'Uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # حد حجم الملف: 5 ميجابايت
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تحميل التوكن من متغير بيئي
HF_TOKEN = os.getenv('HF_TOKEN')
if not HF_TOKEN:
    logger.error("لم يتم العثور على HF_TOKEN في متغيرات البيئة")
    raise ValueError("HF_TOKEN is required")
MODEL_REPO = "dima806/chest_xray_pneumonia_detection"

try:
    # تحميل النموذج والمعالج مع use_fast=True
    processor = AutoImageProcessor.from_pretrained(MODEL_REPO, token=HF_TOKEN, use_fast=True)
    model = AutoModelForImageClassification.from_pretrained(MODEL_REPO, token=HF_TOKEN)
    logger.info("تم تحميل النموذج والمعالج بنجاح")
except Exception as e:
    logger.error(f"فشل تحميل النموذج: {str(e)}")
    raise

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """التحقق من أن امتداد الملف مسموح"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# تعريف التفسيرات الطبية
EXPLANATIONS = {
    'NORMAL': {
        'ar': 'الصورة طبيعية: لا توجد علامات واضحة للالتهاب الرئوي في الأشعة. هذا يعني أن الرئتين تبدوان خاليتين من الالتهابات البكتيرية أو الفيروسية بناءً على تحليل النموذج. يُنصح بالحفاظ على نمط حياة صحي ومراجعة الطبيب إذا ظهرت أعراض مثل السعال أو الحمى.',
        'en': 'The image is normal: No clear signs of pneumonia detected in the X-ray. This indicates that the lungs appear free of bacterial or viral infections based on the model’s analysis. It is recommended to maintain a healthy lifestyle and consult a doctor if symptoms like cough or fever appear.'
    },
    'PNEUMONIA': {
        'ar': 'تم الكشف عن التهاب رئوي: تشير الأشعة إلى وجود علامات التهاب رئوي، مما قد يشمل التهابًا بكتيريًا أو فيروسيًا. يُنصح بمراجعة طبيب مختص فورًا لإجراء فحوصات إضافية وتحديد العلاج المناسب.',
        'en': 'Pneumonia detected: The X-ray shows signs of pneumonia, which may include bacterial or viral infection. It is strongly recommended to consult a doctor immediately for further tests and appropriate treatment.'
    }
}

@app.route('/analyze', methods=['POST'])
def analyze():
    logger.info("تلقي طلب تحليل صورة")
    
    # التحقق من وجود ملف في الطلب
    if 'file' not in request.files:
        logger.warning("لم يتم رفع أي ملف")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    
    # التحقق من اسم الملف
    if file.filename == '':
        logger.warning("لم يتم اختيار ملف")
        return jsonify({'error': 'No file selected'}), 400
    
    # التحقق من نوع الملف
    if not allowed_file(file.filename):
        logger.warning(f"نوع ملف غير مدعوم: {file.filename}")
        return jsonify({'error': 'Unsupported file type. Only PNG and JPEG are allowed'}), 400

    try:
        # معالجة الصورة مباشرة من الذاكرة
        image = Image.open(BytesIO(file.read())).convert('RGB')
        
        # معالجة الصورة باستخدام المعالج
        inputs = processor(images=image, return_tensors="pt")
        
        # تشغيل النموذج
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)  # حساب درجات الثقة
            predicted_class_idx = logits.argmax(-1).item()
            confidence = probabilities[0][predicted_class_idx].item() * 100  # تحويل إلى نسبة مئوية
            label = model.config.id2label[predicted_class_idx]
        
        # إعداد الاستجابة مع الشرح المفصل
        response = {
            'result': label,
            'confidence': round(confidence, 2),  # درجة الثقة بنسبة مئوية
            'explanation': EXPLANATIONS.get(label, {'ar': 'نتيجة غير معروفة', 'en': 'Unknown result'})
        }
        
        logger.info(f"تم تحليل الصورة بنجاح، النتيجة: {label}، درجة الثقة: {confidence:.2f}%")
        return jsonify(response)

    except Exception as e:
        logger.error(f"خطأ أثناء تحليل الصورة: {str(e)}")
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("تشغيل التطبيق على المنفذ 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)