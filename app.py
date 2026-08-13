import hashlib
import io
import os
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Mirage Employee Portal", page_icon="🔐", layout="wide"
)

# --- GLOBAL SYSTEM FILES ---
SHARED_FILE = "shared_payroll.xlsx"
STATUS_FILE = "portal_status.txt"
ADMIN_PASSWORD = "Mirage_Payroll_Secured_2026!#$xK9"

# --- INITIALIZE SESSION STATES ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "logged_in_id" not in st.session_state:
    st.session_state.logged_in_id = None
if "employee_row_data" not in st.session_state:
    st.session_state.employee_row_data = None
if "checked_id" not in st.session_state:
    st.session_state.checked_id = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


# --- SECURITY HELPERS ---
def hash_password(password: str) -> str:
    """Hashes password using SHA-256 for secure storage."""
    if not password:
        return ""
    # If password is already hashed (64 char hex), keep it as is
    clean_p = str(password).strip()
    if len(clean_p) == 64 and all(c in '0123456789abcdefABCDEF' for c in clean_p):
        return clean_p
    return hashlib.sha256(clean_p.encode()).hexdigest()


# --- CORE LOGIC: PORTAL STATUS GATEKEEPER ---
def is_portal_open():
    """Returns True ONLY if shared file exists and status says OPEN."""
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


# --- Language Translations Dictionary ---
translations = {
    "English": {
        "title": "🔐 Mirage Payroll & Employee Portal",
        "subtitle": "🆔 Please enter your National ID to proceed.",
        "admin_header": "🛠️ Admin Control Panel",
        "admin_pass_label": "🔑 Enter Admin Password:",
        "admin_pass_btn": "🔓 Unlock Admin Panel",
        "admin_access_denied": "❌ Incorrect Admin Password.",
        "admin_panel_unlocked": "✨ Admin Panel Unlocked Successfully!",
        "portal_master_toggle": "🔓 Enable Employee Portal Access",
        "portal_locked_msg": (
            "⚠️ PORTAL LOCKED: Employee login is currently disabled. The "
            "Administrator must unlock the portal to grant access."
        ),
        "upload_label": "📁 Upload Employees Excel File (.xlsx or .xls)",
        "download_btn": "📥 Download Updated Database (Secure)",
        "remove_btn": "🗑️ Remove Excel Sheet (Lock Portal & Wipe Data)",
        "refresh_btn": "🔄 Refresh Data",
        "refresh_success": "✅ Data refreshed successfully!",
        "upload_success": (
            "✅ Excel uploaded successfully! Existing employee passwords preserved automatically."
        ),
        "remove_success": "🗑️ Excel file removed. Portal locked and data wiped.",
        "input_label": "🆔 National ID (الرقم القومي):",
        "check_id_btn": "➡️ Next / Verify ID",
        "password_input_label": "🔒 Password (كلمة المرور):",
        "new_password_label": "✨ Create Your Password (أنشئ كلمة المرور الخاصة بك):",
        "confirm_password_label": "✔️ Confirm Password (تأكيد كلمة المرور):",
        "register_btn": "🚀 Create Password & Login (حفظ كلمة المرور والدخول)",
        "login_btn": "🔑 Login (تسجيل الدخول)",
        "logout_btn": "🚪 Logout",
        "back_btn": "⬅️ Back",
        "empty_input": "⚠️ Please fill in all required fields.",
        "pass_mismatch": "❌ Passwords do not match. Please try again.",
        "error_id": "⚠️ National ID not found. Please check and try again.",
        "error_login": "❌ Incorrect Password. Please check and try again.",
        "register_success": "🎉 Password created & saved automatically! Welcome.",
        "error_read": "❌ Error reading file: {error}",
        "dashboard_title": "📊 Monthly Salary & Entitlements Details",
        "welcome_banner": "👋 Welcome, {name}!",
        "id_display": "🆔 National ID:",
        "table_col_key": "📋 Field / Column",
        "table_col_val": "💎 Value",
        "admin_employees_header": "👥 Employee Management & Passwords",
        "reset_pass_btn": "🔄 Reset Password",
        "reset_success": "✅ Password successfully reset for {name}.",
    },
    "العربية": {
        "title": "🔐 تفاصيل الرواتب الشهرية لافراد شركة ميراج",
        "subtitle": "🆔 الرجاء إدخال الرقم القومي للمتابعة.",
        "admin_header": "🛠️ لوحة تحكم المسؤول (Admin)",
        "admin_pass_label": "🔑 أدخل كلمة مرور المسؤول:",
        "admin_pass_btn": "🔓 فتح لوحة المسؤول",
        "admin_access_denied": "❌ كلمة مرور المسؤول غير صحيحة.",
        "admin_panel_unlocked": "✨ تم فتح لوحة المسؤول بنجاح!",
        "portal_master_toggle": "🔓 تفعيل دخول الموظفين للبوابة",
        "portal_locked_msg": (
            "⚠️ البوابة مغلقة: تسجيل دخول الموظفين معطل حالياً. يجب على"
            " المسؤول تفعيل البوابة للسماح بالوصول."
        ),
        "upload_label": "📁 رفع ملف الـ Excel للموظفين (.xlsx أو .xls)",
        "download_btn": "📥 تحميل قاعدة البيانات (Excel الآمن)",
        "remove_btn": "🗑️ حذف ملف الـ Excel (إغلاق البوابة ومسح البيانات)",
        "refresh_btn": "🔄 تحديث البيانات",
        "refresh_success": "✅ تم تحديث البيانات بنجاح!",
        "upload_success": "✅ تم رفع الملف بنجاح! تم الدمج والحفاظ على باسوردات الموظفين المسجلة تلقائياً.",
        "remove_success": "🗑️ تم حذف الملف وإغلاق البوابة ومسح البيانات.",
        "input_label": "🆔 الرقم القومي (National ID):",
        "check_id_btn": "➡️ التالي / التحقق من الرقم",
        "password_input_label": "🔒 كلمة المرور (Password):",
        "new_password_label": "✨ أنشئ كلمة المرور الخاصة بك لأول مرة:",
        "confirm_password_label": "✔️ تأكيد كلمة المرور:",
        "register_btn": "🚀 حفظ كلمة المرور وتسجيل الدخول",
        "login_btn": "🔑 تسجيل الدخول",
        "logout_btn": "🚪 تسجيل الخروج",
        "back_btn": "⬅️ رجوع",
        "empty_input": "⚠️ الرجاء ملء جميع الحقول المطلوبة.",
        "pass_mismatch": "❌ كلمتا المرور غير متطابقتين. يرجى المحاولة مرة أخرى.",
        "error_id": "⚠️ الرقم القومي غير موجود. يرجى التحقق والمحاولة.",
        "error_login": "❌ كلمة المرور غير صحيحة. يرجى التحقق.",
        "register_success": "🎉 تم حفظ كلمة المرور تلقائياً في قاعدة البيانات! أهلاً بك.",
        "error_read": "❌ خطأ في قراءة الملف: {error}",
        "dashboard_title": "📊 تفاصيل الراتب الشهري والمستحقات المالية",
        "welcome_banner": "👋 أهلاً بك يا {name}!",
        "id_display": "🆔 الرقم القومي:",
        "table_col_key": "📋 الحقل / العمود",
        "table_col_val": "💎 القيمة",
        "admin_employees_header": "👥 إدارة الموظفين وكلمات المرور",
        "reset_pass_btn": "🔄 إعادة تعيين كلمة المرور",
        "reset_success": "✅ تم إعادة تعيين كلمة المرور للموظف {name} بنجاح.",
    },
}

# --- Language Switcher in Sidebar ---
selected_lang = st.sidebar.selectbox(
    "🌐 Choose Language / اللغة", ["العربية", "English"]
)
t = translations[selected_lang]


# --- HELPER DATA FUNCTIONS ---
def clean_str(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip().replace("\t", "").replace("\n", "")
    return s[:-2] if s.endswith(".0") else s


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes column names for Arabic spelling differences."""
    df.columns = df.columns.str.strip()
    rename_dict = {}
    for col in df.columns:
        if col in ["الرقم القومى", "الرقم_القومي", "الرقم_القومى"]:
            rename_dict[col] = "الرقم القومي"
        elif col in ["اسم الموظف", "الاسم_الكامل"]:
            rename_dict[col] = "الاسم"
        elif col in ["كلمة المرور", "باسورد", "كلمة_المرور", "pass"]:
            rename_dict[col] = "Password"
    if rename_dict:
        df = df.rename(columns=rename_dict)
    return df


def read_excel_file(file_path_or_buffer):
    try:
        df = pd.read_excel(file_path_or_buffer, dtype=str)
        return normalize_dataframe(df)
    except Exception as e:
        raise Exception(f"Could not read the Excel file: {e}")


def load_excel_df():
    if not os.path.exists(SHARED_FILE):
        return None
    try:
        df = read_excel_file(SHARED_FILE)

        if "Password" not in df.columns:
            df["Password"] = ""
        else:
            df["Password"] = df["Password"].apply(clean_str)

        if "الرقم القومي" in df.columns:
            df["الرقم القومي"] = df["الرقم القومي"].apply(clean_str)

        return df
    except Exception:
        for f in [SHARED_FILE, STATUS_FILE]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        return None


def save_excel_safely(df):
    """Saves updated dataframe back to shared file."""
    if "الرقم القومي" in df.columns:
        df["الرقم القومي"] = df["الرقم القومي"].apply(clean_str)
    if "Password" in df.columns:
        df["Password"] = df["Password"].apply(clean_str)

    df.to_excel(SHARED_FILE, index=False)
    st.cache_data.clear()


# --- ADMIN SECTION (Sidebar) ---
st.sidebar.markdown("---")
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
                st.success(t["admin_panel_unlocked"])
                st.rerun()
            else:
                st.sidebar.error(t["admin_access_denied"])
else:
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
        st.sidebar.warning("⚠️ Upload an Excel sheet to enable portal access.")

    uploaded_file = st.sidebar.file_uploader(
        t["upload_label"],
        type=["xlsx", "xls"],
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file is not None:
        try:
            df_upload = read_excel_file(uploaded_file)

            # 1. الاحتفاظ بالكلمات المرور الحالية المخزنة في النظام إن وجدت
            existing_passwords = {}
            if os.path.exists(SHARED_FILE):
                df_old = load_excel_df()
                if (
                    df_old is not None
                    and "الرقم القومي" in df_old.columns
                    and "Password" in df_old.columns
                ):
                    for _, row in df_old.iterrows():
                        nid = clean_str(row["الرقم القومي"])
                        pwd = clean_str(row["Password"])
                        if pwd and pwd.lower() not in ["nan", "none"]:
                            existing_passwords[nid] = pwd

            # 2. فحص وتطابق الشيت المرفوع مع الباسوردات السابقة
            pass_col = []
            has_uploaded_pass = "Password" in df_upload.columns

            for _, row in df_upload.iterrows():
                nid = clean_str(row.get("الرقم القومي", ""))
                uploaded_pwd = clean_str(row.get("Password", "")) if has_uploaded_pass else ""

                # أولوية 1: الباسوردات المكتوبة يدوياً في الشيت المرفوع (إن وجدت)
                if uploaded_pwd and uploaded_pwd.lower() not in ["nan", "none"]:
                    pass_col.append(hash_password(uploaded_pwd))
                # أولوية 2: الباسوردات التي سجلها الموظفون بأنفسهم في النظام سابقاً
                elif nid in existing_passwords:
                    pass_col.append(existing_passwords[nid])
                else:
                    pass_col.append("")

            df_upload["Password"] = pass_col

            save_excel_safely(df_upload)
            set_portal_status(True)

            st.session_state.uploader_key += 1
            st.sidebar.success(t["upload_success"])
            st.rerun()
        except Exception as e:
            st.sidebar.error(t["error_read"].format(error=e))

    if os.path.exists(SHARED_FILE):
        st.sidebar.markdown("---")
        st.sidebar.subheader(t["admin_employees_header"])
        df_admin = load_excel_df()
        if df_admin is not None:
            for idx, row in df_admin.iterrows():
                name = row.get("الاسم", f"Employee {idx}")
                nid = clean_str(row.get("الرقم القومي", ""))
                current_pwd = clean_str(row.get("Password", ""))
                has_pass = bool(current_pwd)
                status_text = (
                    "🔒 Registered" if has_pass else "⏳ Not Registered"
                )

                with st.sidebar.expander(f"👤 {name} ({status_text})"):
                    st.write(f"🆔 ID: `{nid}`")
                    if has_pass:
                        if st.button(
                            t["reset_pass_btn"], key=f"reset_{nid}_{idx}"
                        ):
                            df_admin.at[idx, "Password"] = ""
                            save_excel_safely(df_admin)
                            st.success(t["reset_success"].format(name=name))
                            st.rerun()
                    else:
                        st.info("ℹ️ لم يقم الموظف بإنشاء كلمة مرور بعد.")

            st.sidebar.markdown("---")
            df_export = df_admin.copy()

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False)
            excel_bytes = output.getvalue()

            st.sidebar.download_button(
                label=t["download_btn"],
                data=excel_bytes,
                file_name="mirage_payroll_database_with_passwords.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )

    st.sidebar.markdown("---")
    if st.sidebar.button(t["remove_btn"]):
        for f in [SHARED_FILE, STATUS_FILE]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        st.cache_data.clear()
        st.sidebar.success(t["remove_success"])
        st.rerun()

    if st.sidebar.button("🔒 Lock Admin Panel / قفل لوحة المسؤول"):
        st.session_state.admin_logged_in = False
        st.cache_data.clear()
        st.rerun()


# --- MAIN PAGE LAYOUT ---
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.title(t["title"])
with col_refresh:
    st.write("")
    if st.button(t["refresh_btn"]):
        st.cache_data.clear()
        if is_portal_open() and st.session_state.get("logged_in_id"):
            df_refresh = load_excel_df()
            if df_refresh is not None:
                matched_ref = df_refresh[
                    df_refresh["الرقم القومي"].apply(clean_str)
                    == clean_str(st.session_state.logged_in_id)
                ]
                if not matched_ref.empty:
                    st.session_state.employee_row_data = matched_ref.iloc[
                        0
                    ].to_dict()
        st.success(t["refresh_success"])
        st.rerun()

st.markdown("---")

if not is_portal_open():
    st.error(t["portal_locked_msg"])
    st.stop()


# ====================================================================
# EMPLOYEE PORTAL VIEW
# ====================================================================

if st.session_state.get("logged_in_user"):
    df_verify = load_excel_df()
    user_exists = False
    if df_verify is not None:
        v_match = df_verify[
            df_verify["الرقم القومي"].apply(clean_str)
            == clean_str(st.session_state.get("logged_in_id"))
        ]
        if not v_match.empty:
            user_exists = True
            st.session_state.employee_row_data = v_match.iloc[0].to_dict()

    if not user_exists:
        st.session_state.logged_in_user = None
        st.session_state.logged_in_id = None
        st.session_state.employee_row_data = None
        st.session_state.checked_id = None
        st.rerun()

    st.success(
        t["welcome_banner"].format(name=st.session_state.logged_in_user)
    )
    st.markdown(f"### 📋 {t['dashboard_title']}")
    st.info(
        f"**{t['id_display']}**"
        f" `{clean_str(st.session_state.get('logged_in_id'))}`"
    )

    if st.session_state.get("employee_row_data") is not None:
        row_data = st.session_state.employee_row_data
        table_data = []
        for col_name, val in row_data.items():
            if str(col_name).strip().lower() in ["password", "كلمة المرور"]:
                continue
            display_val = val
            if pd.isna(val) or str(val).strip() in ["", "nan", "None"]:
                display_val = 0
            table_data.append(
                {
                    t["table_col_key"]: str(col_name),
                    t["table_col_val"]: display_val,
                }
            )

        df_display = pd.DataFrame(table_data)

        st.markdown(
            """
        <style>
            [data-testid="stTable"] th, 
            [data-testid="stTable"] td {
                text-align: center !important;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.table(df_display)

    st.markdown("---")
    if st.button(t["logout_btn"]):
        st.session_state.logged_in_user = None
        st.session_state.logged_in_id = None
        st.session_state.employee_row_data = None
        st.session_state.checked_id = None
        st.rerun()

else:
    st.write(t["subtitle"])
    try:
        df = load_excel_df()
        if df is None:
            st.error(t["error_read"].format(error="Could not load data."))
        else:
            if st.session_state.get("checked_id") is None:
                national_id_input = st.text_input(
                    t["input_label"], key="national_id_field"
                )
                submit_id = st.button(t["check_id_btn"])

                if submit_id:
                    clean_input_id = clean_str(national_id_input)
                    if not clean_input_id:
                        st.warning(t["empty_input"])
                    else:
                        matched = df[
                            df["الرقم القومي"].apply(clean_str) == clean_input_id
                        ]
                        if not matched.empty:
                            st.session_state.checked_id = clean_input_id
                            st.rerun()
                        else:
                            st.error(t["error_id"])
            else:
                national_id_input = st.session_state.checked_id
                df_current = load_excel_df()
                matched = df_current[
                    df_current["الرقم القومي"].apply(clean_str)
                    == clean_str(national_id_input)
                ]

                if not matched.empty:
                    idx = matched.index[0]
                    current_pass = clean_str(matched.loc[idx, "Password"])
                    emp_name = matched.loc[idx, "الاسم"]

                    st.info(f"👤 **{emp_name}** (ID: `{national_id_input}`)")

                    if st.button(t["back_btn"]):
                        st.session_state.checked_id = None
                        st.rerun()

                    # خطوة إنشاء الباسورد تلقائياً للموظف في أول مرة
                    if not current_pass:
                        st.warning(
                            "✨ هذه زيارتك الأولى! يرجى إنشاء كلمة مرور خاصة بك لحماية حسابك."
                        )
                        new_pass = st.text_input(
                            t["new_password_label"],
                            type="password",
                            key="new_pass_field",
                        )
                        confirm_pass = st.text_input(
                            t["confirm_password_label"],
                            type="password",
                            key="new_pass_field_confirm",
                        )
                        submit_register = st.button(t["register_btn"])

                        if submit_register:
                            if not new_pass or not confirm_pass:
                                st.warning(t["empty_input"])
                            elif new_pass != confirm_pass:
                                st.error(t["pass_mismatch"])
                            else:
                                # تشفير الباسورد وحفظه مباشرة داخل الملف الرئيسي
                                hashed_new_pass = hash_password(new_pass)
                                df_current.at[idx, "Password"] = hashed_new_pass
                                save_excel_safely(df_current)

                                st.session_state.logged_in_user = emp_name
                                st.session_state.logged_in_id = national_id_input
                                st.session_state.employee_row_data = (
                                    df_current.loc[idx].to_dict()
                                )
                                st.session_state.checked_id = None
                                st.success(t["register_success"])
                                st.rerun()
                    else:
                        password_input = st.text_input(
                            t["password_input_label"],
                            type="password",
                            key="password_input_field",
                        )
                        submit_login = st.button(t["login_btn"])

                        if submit_login:
                            if not password_input:
                                st.warning(t["empty_input"])
                            elif hash_password(password_input) == current_pass:
                                st.session_state.logged_in_user = emp_name
                                st.session_state.logged_in_id = national_id_input
                                st.session_state.employee_row_data = (
                                    matched.loc[idx].to_dict()
                                )
                                st.session_state.checked_id = None
                                st.rerun()
                            else:
                                st.error(t["error_login"])

    except Exception as e:
        st.error(t["error_read"].format(error=e))
