// عناصر الصفحة
const imageInput = document.getElementById('imageInput');
const uploadedImage = document.getElementById('uploaded-image');
const analyzeBtn = document.getElementById('analyzeBtn');
const uploadStatus = document.getElementById('upload-status');
const resultsList = document.getElementById('resultsList');

// اللغة الافتراضية
let currentLang = 'ar';

// دالة تبديل اللغة
function setLanguage(lang) {
  currentLang = lang;
  // تحديث النصوص بناءً على اللغة
  document.querySelectorAll('.lang-text').forEach(element => {
    element.textContent = element.dataset[lang];
  });

  // تحديث حالة أزرار اللغة
  document.querySelectorAll('.lang-toggle button').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick') === `setLanguage('${lang}')`);
  });

  // تحديث اتجاه النص
  document.documentElement.setAttribute('lang', lang);
  document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
}

// عرض الصورة عند رفعها
imageInput.addEventListener('change', function() {
  const file = this.files[0];
  if (file) {
    // التحقق من نوع الملف
    if (!file.type.startsWith('image/')) {
      resultsList.innerHTML = '';
      const msg = document.createElement('p');
      msg.textContent = currentLang === 'ar' ? 'الرجاء رفع ملف صورة صالح' : 'Please upload a valid image file';
      msg.style.color = 'orange';
      resultsList.appendChild(msg);
      return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
      uploadedImage.src = e.target.result;
      uploadedImage.style.display = 'block';
      resultsList.innerHTML = ''; // مسح النتائج السابقة
      uploadStatus.style.display = 'none';
    };
    reader.readAsDataURL(file);
  }
});

// دالة تحليل الصورة
async function analyzeImage(event) {
  if (event) event.preventDefault();

  if (!imageInput.files[0]) {
    resultsList.innerHTML = '';
    const msg = document.createElement('p');
    msg.textContent = currentLang === 'ar' ? 'الرجاء رفع صورة أولاً' : 'Please upload an image first';
    msg.style.color = 'orange';
    resultsList.appendChild(msg);
    return;
  }

  // عرض حالة التحميل
  uploadStatus.style.display = 'block';
  resultsList.innerHTML = '';

  try {
    const formData = new FormData();
    formData.append('file', imageInput.files[0]);

    const response = await fetch('http://127.0.0.1:5000/analyze', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(currentLang === 'ar' ? 'فشل الاتصال بالخادم' : 'Failed to connect to server');
    }

    const data = await response.json();
    resultsList.innerHTML = ''; // مسح رسالة التحميل
    uploadStatus.style.display = 'none';

    if (data.error) {
      throw new Error(data.error);
    }

    // إنشاء عناصر العرض
    const resultContainer = document.createElement('div');
    resultContainer.className = 'result-container';

    const resultMsg = document.createElement('p');
    resultMsg.className = 'result-text';
    const timestamp = new Date().toLocaleString();

    if (data.result.toUpperCase() === 'NORMAL') {
      resultMsg.textContent = currentLang === 'ar' 
        ? `[${timestamp}] النتيجة: طبيعية ✅`
        : `[${timestamp}] Result: Normal ✅`;
      resultMsg.className += ' negative';
    } else if (data.result.toUpperCase() === 'PNEUMONIA') {
      resultMsg.textContent = currentLang === 'ar' 
        ? `[${timestamp}] النتيجة: التهاب رئوي ⚠️`
        : `[${timestamp}] Result: Pneumonia ⚠️`;
      resultMsg.className += ' positive';
    } else {
      resultMsg.textContent = currentLang === 'ar' 
        ? `[${timestamp}] النتيجة: ${data.result}`
        : `[${timestamp}] Result: ${data.result}`;
      resultMsg.style.color = 'black';
    }

    // إضافة درجة الثقة
    const confidenceMsg = document.createElement('p');
    confidenceMsg.className = 'confidence-text';
    confidenceMsg.textContent = currentLang === 'ar' 
      ? `درجة الثقة: ${data.confidence}%`
      : `Confidence: ${data.confidence}%`;

    // إضافة التفسير
    const explanationMsg = document.createElement('p');
    explanationMsg.className = 'explanation-text';
    explanationMsg.textContent = data.explanation[currentLang];

    // تجميع العناصر
    resultContainer.appendChild(resultMsg);
    resultContainer.appendChild(confidenceMsg);
    resultContainer.appendChild(explanationMsg);
    resultsList.appendChild(resultContainer);

  } catch (err) {
    uploadStatus.style.display = 'none';
    resultsList.innerHTML = '';
    const errorMsg = document.createElement('p');
    errorMsg.textContent = currentLang === 'ar' 
      ? `حدث خطأ أثناء تحليل الصورة: ${err.message}`
      : `An error occurred during image analysis: ${err.message}`;
    errorMsg.style.color = 'orange';
    resultsList.appendChild(errorMsg);
    console.error('خطأ في تحليل الصورة:', err);
  }
}

// ربط زر التحليل
analyzeBtn.addEventListener('click', analyzeImage);

// تهيئة اللغة الافتراضية
setLanguage('ar');