import io
import json
import os
import random
import time
import pandas as pd
import requests
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Mirage Employee Portal", page_icon="🔐", layout="wide"
)

# --- GLOBAL SYSTEM FILES & SECRETS ---
SHARED_FILE = "shared_payroll.xlsx"
STATUS_FILE = "portal_status.txt"
SESSIONS_FILE = "active_sessions.json"
ADMIN_PASSWORD = st.secrets.get(
    "ADMIN_PASSWORD", "Mirage_Payroll_Secured_2026!#$xK9"
)

# بيانات API إرسال الواتساب (Twilio)
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = st.secrets.get(
    "TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"
)

# --- ACTIVE SESSIONS & ONLINE STATUS HELPERS ---
def get_active_sessions():
    if not os.path.exists(SESSIONS_FILE):
        return {}
    try:
        with open(SESSIONS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def update_user_status(national_id: str, is_online: bool):
    if not national_id:
        return
    sessions = get_active_sessions()
    now = time.time()

    if is_online:
        sessions[str(national_id)] = now
    else:
        sessions.pop(str(national_id), None)

    # تنظيف الجلسات المنتهية (أي موظف خامل لأكثر من 5 دقائق يُعتبر أوفلاين)
    active_sessions = {
        k: v for k, v in sessions.items() if (now - v) < 300
    }

    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(active_sessions, f)
    except Exception:
        pass


def is_user_online(national_id: str) -> bool:
    sessions = get_active_sessions()
    last_seen = sessions.get(str(national_id))
    if last_seen and (time.time() - last_seen < 300):  # مهلة 5 دقائق
        return True
    return False


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
    p = clean_str(phone_str)
    if p.startswith("0"):
        p = "2" + p
    if not p.startswith("+") and not p.startswith("20"):
        p = "20" + p
    return p


def send_whatsapp_otp(phone_number: str, otp_code: str) -> bool:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return True

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    formatted_phone = f"whatsapp:+{phone_number.replace('+', '')}"

    payload = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": formatted_phone,
        "Body": f"🔐 كود التحقق الخاص بك لدخول بوابة رواتب ميراج هو: {otp_code}\nلا تشارك هذا الكود مع أي شخص.",
    }

    try:
        response = requests.post(
            url, data=payload, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        )
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


def save_excel_safely(df):
    if "الرقم القومي" in df.columns:
        df["الرقم القومي"] = df["الرقم القومي"].apply(clean_str)
    if "رقم الهاتف" in df.columns:
        df["رقم الهاتف"] = df["رقم الهاتف"].apply(clean_phone)
    df.to_excel(SHARED_FILE, index=False)
    load_excel_df.clear()


# --- TRANSLATIONS ---
t = {
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


# ====================================================================
# ADMIN CONTROL PANEL (SIDEBAR)
# ====================================================================
st.sidebar.header(t["admin_header"])

if not st.session_state.admin_logged_in:
    with st.sidebar.form(key="admin_login_form"):
        admin_pass_input = st.text_input(
            t["admin_pass_label"], type="password"
        )
        submit_admin = st.form_submit_button(t["admin_pass_btn"])

        if submit_admin:
            if admin_pass_input == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.sidebar.success(t["admin_panel_unlocked"])
                st.rerun()
            else:
                st.sidebar.error(t["admin_access_denied"])
else:
    st.sidebar.success("🔑 مرحباً بالمدير المالي")
    has_file = os.path.exists(SHARED_FILE)

    if has_file:
        current_status = is_portal_open()
        master_toggle = st.sidebar.checkbox(
            t["portal_master_toggle"], value=current_status
        )
        if master_toggle != current_status:
            set_portal_status(master_toggle)
            st.rerun()
    else:
        st.sidebar.warning("⚠️ يرجى رفع ملف إكسيل لتفعيل دخول الموظفين.")

    # رفع ملف الإكسيل
    uploaded_file = st.sidebar.file_uploader(
        t["upload_label"],
        type=["xlsx", "xls"],
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file is not None:
        try:
            df_upload = pd.read_excel(uploaded_file, dtype=str)
            save_excel_safely(df_upload)
            set_portal_status(True)
            st.session_state.uploader_key += 1
            st.sidebar.success("✅ تم رفع الملف وتحديث قاعدة البيانات!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ خطأ في قراءة الملف: {e}")

    # عرض حالة الموظفين (أونلاين / أوفلاين)
    if os.path.exists(SHARED_FILE):
        st.sidebar.markdown("---")
        df_admin = load_excel_df(SHARED_FILE)
        if df_admin is not None:
            st.sidebar.markdown("### 👤 حالة الموظفين الحالية")

            for idx, row in df_admin.iterrows():
                emp_name = row.get("الاسم", f"موظف {idx+1}")
                emp_id = str(row.get("الرقم القومي", ""))

                # التحقق من حالة الاتصال
                if is_user_online(emp_id):
                    st.sidebar.markdown(f"🟢 **{emp_name}** `أونلاين`")
                else:
                    st.sidebar.markdown(f"🔴 **{emp_name}** `أوفلاين`")

            st.sidebar.markdown("---")
            st.sidebar.write(f"📊 إجمالي الموظفين بالشيت: `{len(df_admin)}`")

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_admin.to_excel(writer, index=False)
            excel_bytes = output.getvalue()

            st.sidebar.download_button(
                label=t["download_btn"],
                data=excel_bytes,
                file_name="mirage_payroll_database.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # زر حذف الملف وإغلاق البوابة
    st.sidebar.markdown("---")
    if st.sidebar.button(t["remove_btn"]):
        for f in [SHARED_FILE, STATUS_FILE, SESSIONS_FILE]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        load_excel_df.clear()
        st.sidebar.success("🗑️ تم حذف الملف وإغلاق البوابة.")
        st.rerun()

    if st.sidebar.button("🔒 قفل لوحة المسؤول"):
        st.session_state.admin_logged_in = False
        st.rerun()


# ====================================================================
# MAIN PAGE LAYOUT
# ====================================================================
st.title(t["title"])
st.markdown("---")

if not is_portal_open():
    st.error(t["portal_locked_msg"])
    st.stop()

# 1. الموظف دخل بالفعل
if st.session_state.get("logged_in_user"):
    # تحديث إشارة الاتصال للحفاظ على حالة أونلاين طالما الموظف يعمل على الصفحة
    update_user_status(st.session_state.logged_in_id, True)

    st.success(t["welcome_banner"].format(name=st.session_state.logged_in_user))
    st.markdown(f"### {t['dashboard_title']}")

    if st.session_state.get("employee_row_data"):
        row_data = st.session_state.employee_row_data
        cols = st.columns(3)
        idx = 0
        for key, val in row_data.items():
            if str(key).strip().lower() in ["password", "كلمة المرور"]:
                continue
            display_val = (
                val
                if pd.notna(val) and str(val).strip() not in ["", "nan", "None"]
                else "0"
            )

            with cols[idx % 3]:
                st.metric(label=str(key), value=str(display_val))
            idx += 1

    st.markdown("---")
    if st.button(t["logout_btn"]):
        # تحويل حالة الموظف لـ أوفلاين عند الخروج
        update_user_status(st.session_state.logged_in_id, False)

        st.session_state.logged_in_user = None
        st.session_state.logged_in_id = None
        st.session_state.employee_row_data = None
        st.session_state.otp_sent = False
        st.rerun()

# 2. خطوة أدخال كود OTP
elif st.session_state.otp_sent:
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        st.warning(
            f"💡 **[وضع التجربة الاختباري]**: كود التحقق الخاص بك هو: `{st.session_state.generated_otp}`"
        )

    st.subheader("📩 تم إرسال كود التحقق إلى حساب الواتساب الخاص بك")
    st.info(
        "يرجى مراجعة تطبيق الواتساب وإدخال الرمز المكون من 4 أرقام لتأكيد الهوية."
    )

    with st.form(key="otp_verify_form"):
        user_otp_input = st.text_input(t["input_otp"], max_chars=4)
        submit_otp = st.form_submit_button(t["verify_otp_btn"])

        if submit_otp:
            if user_otp_input.strip() == str(st.session_state.generated_otp):
                emp_data = st.session_state.temp_emp_data
                st.session_state.logged_in_user = emp_data.get("الاسم", "الموظف")
                st.session_state.logged_in_id = emp_data.get("الرقم القومي")
                st.session_state.employee_row_data = emp_data

                # تسجيل دخول الموظف كـ أونلاين
                update_user_status(st.session_state.logged_in_id, True)

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

# 3. واجهة الموظف الأساسية
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
                    st.error(
                        "❌ عمود 'رقم الهاتف' غير موجود في شيت الإكسيل المرفوع."
                    )
                else:
                    matched = df[
                        (df["الرقم القومي"] == clean_id)
                        & (df["رقم الهاتف"] == clean_ph)
                    ]

                    if not matched.empty:
                        generated_code = str(random.randint(1000, 9999))

                        if send_whatsapp_otp(clean_ph, generated_code):
                            st.session_state.generated_otp = generated_code
                            st.session_state.temp_emp_data = (
                                matched.iloc[0].to_dict()
                            )
                            st.session_state.otp_sent = True
                            st.rerun()
                        else:
                            st.error("❌ فشل إرسال رسالة الواتساب.")
                    else:
                        st.error(t["error_not_found"])
