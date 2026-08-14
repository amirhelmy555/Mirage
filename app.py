import io
import os
import random
import requests
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Mirage Employee Portal", page_icon="🔐", layout="wide"
)

# --- GLOBAL SYSTEM FILES & SECRETS ---
SHARED_FILE = "shared_payroll.xlsx"
STATUS_FILE = "portal_status.txt"
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "Mirage_Payroll_Secured_2026!#$xK9")

# بيانات API إرسال الواتساب (توضع في Streamlit Secrets أو متغيرات بيئة)
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = st.secrets.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")


# --- INITIALIZE SESSION STATES ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "logged_in_id" not in st.session_state:
    st.session_state.logged_in_id = None
if "employee_row_data" not in st.session_state:
    st.session_state.employee_row_data = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# أجزاء عملية التحقق بالـ OTP
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "temp_emp_data" not in st.session_state:
    st.session_state.temp_emp_data = None


# --- CORE LOGIC & HELPERS ---
def is_portal_open():
    if not os.path.exists(SHARED_FILE) or not os.path.exists(STATUS_FILE):
        return False
    try:
        with open(STATUS_FILE, "r") as f:
            return f.read().strip() == "OPEN"
    except Exception:
        return False


def set_portal_status(is_open: bool):
    with open(STATUS_FILE, "w") as f:
        f.write("OPEN" if is_open else "CLOSED")


def clean_str(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip().replace("\t", "").replace("\n", "").replace(" ", "")
    return s[:-2] if s.endswith(".0") else s


def clean_phone(phone_str):
    """تنظيف رقم الهاتف وتنسيقه بالصيغة الدولية لمصر"""
    p = clean_str(phone_str)
    if p.startswith("0"):
        p = "2" + p  # تحويل 010xxxx إلى 2010xxxx
    if not p.startswith("+") and not p.startswith("20"):
        p = "20" + p
    return p


def send_whatsapp_otp(phone_number: str, otp_code: str) -> bool:
    """دالة إرسال الـ OTP عبر Twilio WhatsApp API"""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        # في حالة التجربة المحلية أو عدم ضبط المفاتيح
        st.info(f"💡 [وضع التطوير]: رمز التحقق OTP الخاص بك هو: {otp_code}")
        return True

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    formatted_phone = f"whatsapp:+{phone_number.replace('+', '')}"
    
    payload = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": formatted_phone,
        "Body": f"🔐 كود التحقق الخاص بك لدخول بوابة رواتب ميراج هو: {otp_code}\nلا تشارك هذا الكود مع أي شخص."
    }
    
    try:
        response = requests.post(url, data=payload, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        return response.status_code in [200, 201]
    except Exception as e:
        st.error(f"خطأ أثناء إرسال رسالة الواتساب: {e}")
        return False


@st.cache_data(show_spinner=False)
def load_excel_df(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_excel(file_path, dtype=str)
        df.columns = df.columns.str.strip()
        
        # توحيد مسميات الأعمدة
        rename_dict = {}
        for col in df.columns:
            if col in ["الرقم القومى", "الرقم_القومي", "الرقم_القومى"]:
                rename_dict[col] = "الرقم القومي"
            elif col in ["اسم الموظف", "الاسم_الكامل"]:
                rename_dict[col] = "الاسم"
            elif col in ["رقم التليفون", "الموبايل", "الهاتف", "رقم الموبايل"]:
                rename_dict[col] = "رقم الهاتف"
        if rename_dict:
            df = df.rename(columns=rename_dict)

        if "الرقم القومي" in df.columns:
            df["الرقم القومي"] = df["الرقم القومي"].apply(clean_str)
        if "رقم الهاتف" in df.columns:
            df["رقم الهاتف"] = df["رقم الهاتف"].apply(clean_phone)
            
        return df
    except Exception:
        return None


# --- TRANSLATIONS ---
translations = {
    "العربية": {
        "title": "🔐 تفاصيل الرواتب الشهرية لافراد شركة ميراج",
        "subtitle": "🆔 أدخل الرقم القومي ورقم الموبايل المسجل لاستلام كود التحقق (OTP)",
        "admin_header": "🛠️ لوحة تحكم المسؤول (Admin)",
        "admin_pass_label": "🔑 أدخل كلمة مرور المسؤول:",
        "admin_pass_btn": "🔓 فتح لوحة المسؤول",
        "admin_access_denied": "❌ كلمة مرور المسؤول غير صحيحة.",
        "admin_panel_unlocked": "✨ تم فتح لوحة المسؤول بنجاح!",
        "portal_master_toggle": "🔓 تفعيل دخول الموظفين للبوابة",
        "portal_locked_msg": "⚠️ البوابة مغلقة حالياً من قبل المسؤول.",
        "upload_label": "📁 رفع ملف الـ Excel للموظفين (.xlsx أو .xls)",
        "download_btn": "📥 تحميل قاعدة البيانات الحالية",
        "remove_btn": "🗑️ حذف الملف ومسح البيانات",
        "refresh_btn": "🔄 تحديث البيانات",
        "input_id": "🆔 الرقم القومي:",
        "input_phone": "📱 رقم الموبايل المسجل بالشيت:",
        "send_otp_btn": "📩 إرسال كود التحقق (OTP) عبر الواتساب",
        "verify_otp_btn": "🔓 دخول وتأكيد الكود",
        "input_otp": "🔑 أدخل كود الـ OTP المكون من 4 أرقام:",
        "error_not_found": "❌ البيانات غير مطابقة. أعد التأكد من الرقم القومي ورقم الموبايل.",
        "welcome_banner": "👋 أهلاً بك يا {name}!",
        "dashboard_title": "📊 تفاصيل الراتب الشهري والمستحقات المالية",
        "logout_btn": "🚪 تسجيل الخروج",
    }
}

t = translations["العربية"]

# --- MAIN PAGE LAYOUT ---
st.title(t["title"])
st.markdown("---")

if not is_portal_open():
    st.error(t["portal_locked_msg"])
    st.stop()


# ====================================================================
# EMPLOYEE PORTAL VIEW (WITH OTP VERIFICATION)
# ====================================================================

# 1. الموظف قام بتسجيل الدخول بنجاح
if st.session_state.get("logged_in_user"):
    st.success(t["welcome_banner"].format(name=st.session_state.logged_in_user))
    st.markdown(f"### {t['dashboard_title']}")
    
    if st.session_state.get("employee_row_data"):
        row_data = st.session_state.employee_row_data
        
        # عرض البيانات على شكل كروت تفاعلية (Metrics)
        cols = st.columns(3)
        idx = 0
        for key, val in row_data.items():
            if str(key).strip().lower() in ["password", "كلمة المرور"]:
                continue
            display_val = val if pd.notna(val) and str(val).strip() not in ["", "nan", "None"] else "0"
            
            with cols[idx % 3]:
                st.metric(label=str(key), value=str(display_val))
            idx += 1

    st.markdown("---")
    if st.button(t["logout_btn"]):
        st.session_state.logged_in_user = None
        st.session_state.logged_in_id = None
        st.session_state.employee_row_data = None
        st.session_state.otp_sent = False
        st.rerun()

# 2. خطوة تأكيد كود الـ OTP
elif st.session_state.otp_sent:
    st.subheader("📩 تم إرسال كود التحقق إلى حساب الواتساب الخاص بك")
    st.info("يرجى مراجعة تطبيق الواتساب وإدخال الرمز المكون من 4 أرقام لتأكيد الهوية.")
    
    with st.form(key="otp_verify_form"):
        user_otp_input = st.text_input(t["input_otp"], max_chars=4)
        submit_otp = st.form_submit_button(t["verify_otp_btn"])

        if submit_otp:
            if user_otp_input.strip() == str(st.session_state.generated_otp):
                emp_data = st.session_state.temp_emp_data
                st.session_state.logged_in_user = emp_data.get("الاسم", "الموظف")
                st.session_state.logged_in_id = emp_data.get("الرقم القومي")
                st.session_state.employee_row_data = emp_data
                
                # إعادة ضبط حالة الـ OTP
                st.session_state.otp_sent = False
                st.session_state.generated_otp = None
                st.session_state.temp_emp_data = None
                st.rerun()
            else:
                st.error("❌ كود التحقق غير صحيح! يرجى المحاولة مرة أخرى.")

    if st.button("⬅️ إلغاء والعودة للخلف"):
        st.session_state.otp_sent = False
        st.session_state.generated_otp = None
        st.rerun()

# 3. شاشة إدخال الرقم القومي ورقم الموبايل الأوليّة
else:
    st.write(t["subtitle"])
    df = load_excel_df(SHARED_FILE)
    
    if df is None:
        st.error("❌ تعذر تحميل قاعدة البيانات. يرجى التواصل مع المسؤول.")
    else:
        with st.form(key="login_request_form"):
            national_id_input = st.text_input(t["input_id"])
            phone_input = st.text_input(t["input_phone"])
            submit_request = st.form_submit_button(t["send_otp_btn"])

            if submit_request:
                clean_id = clean_str(national_id_input)
                clean_ph = clean_phone(phone_input)

                if not clean_id or not clean_ph:
                    st.warning("⚠️ يرجى إدخال الرقم القومي ورقم الموبايل.")
                elif "رقم الهاتف" not in df.columns:
                    st.error("❌ عمود 'رقم الهاتف' غير موجود في شيت الإكسيل المرفوع.")
                else:
                    # المطابقة بشرطين: الرقم القومي + رقم الهاتف
                    matched = df[
                        (df["الرقم القومي"] == clean_id) & 
                        (df["رقم الهاتف"] == clean_ph)
                    ]

                    if not matched.empty:
                        # إنشاء OTP عشوائي من 4 أرقام
                        generated_code = str(random.randint(1000, 9999))
                        
                        # إرسال عبر الواتساب
                        if send_whatsapp_otp(clean_ph, generated_code):
                            st.session_state.generated_otp = generated_code
                            st.session_state.temp_emp_data = matched.iloc[0].to_dict()
                            st.session_state.otp_sent = True
                            st.rerun()
                        else:
                            st.error("❌ فشل إرسال رسالة الواتساب. تأكد من صحة الخدمة أو الرقم.")
                    else:
                        st.error(t["error_not_found"])
