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
if "uploader_key" not in st.session_state:
  st.session_state.uploader_key = 0


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
        "subtitle": "🆔 Please enter your National ID to view your details.",
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
        "download_btn": "📥 Download Database",
        "remove_btn": "🗑️ Remove Excel Sheet (Lock Portal & Wipe Data)",
        "refresh_btn": "🔄 Refresh Data",
        "refresh_success": "✅ Data refreshed successfully!",
        "upload_success": (
            "✅ Excel uploaded successfully! Database updated."
        ),
        "remove_success": "🗑️ Excel file removed. Portal locked and data wiped.",
        "input_label": "🆔 National ID (الرقم القومي):",
        "login_btn": "🔑 View Dashboard / عرض التفاصيل",
        "logout_btn": "🚪 Logout / خروج",
        "empty_input": "⚠️ Please enter your National ID.",
        "error_id": "⚠️ National ID not found. Please check and try again.",
        "error_read": "❌ Error reading file: {error}",
        "dashboard_title": "📊 Monthly Salary & Entitlements Details",
        "welcome_banner": "👋 Welcome, {name}!",
        "id_display": "🆔 National ID:",
        "table_col_key": "📋 Field / Column",
        "table_col_val": "💎 Value",
        "admin_employees_header": "👥 Uploaded Employees Data",
    },
    "العربية": {
        "title": "🔐 تفاصيل الرواتب الشهرية لافراد شركة ميراج",
        "subtitle": "🆔 الرجاء إدخال الرقم القومي للانتقال إلى تفاصيل مرتبك.",
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
        "download_btn": "📥 تحميل قاعدة البيانات الحالية (Excel)",
        "remove_btn": "🗑️ حذف ملف الـ Excel (إغلاق البوابة ومسح البيانات)",
        "refresh_btn": "🔄 تحديث البيانات",
        "refresh_success": "✅ تم تحديث البيانات بنجاح!",
        "upload_success": "✅ تم رفع الملف وتحديث قاعدة البيانات بنجاح!",
        "remove_success": "🗑️ تم حذف الملف وإغلاق البوابة ومسح البيانات.",
        "input_label": "🆔 الرقم القومي (National ID):",
        "login_btn": "🔑 عرض التفاصيل والداشبورد",
        "logout_btn": "🚪 تسجيل الخروج",
        "empty_input": "⚠️ الرجاء أدخل الرقم القومي الخاص بك.",
        "error_id": "⚠️ الرقم القومي غير موجود. يرجى التحقق والمحاولة.",
        "error_read": "❌ خطأ في قراءة الملف: {error}",
        "dashboard_title": "📊 تفاصيل الراتب الشهري والمستحقات المالية",
        "welcome_banner": "👋 أهلاً بك يا {name}!",
        "id_display": "🆔 الرقم القومي:",
        "table_col_key": "📋 الحقل / العمود",
        "table_col_val": "💎 القيمة",
        "admin_employees_header": "👥 قائمة الموظفين المسجلين بالملف",
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
  df.to_excel(SHARED_FILE, index=False)
  st.cache_data.clear()


# --- ADMIN SECTION (Sidebar) ---
st.sidebar.markdown("---")
st.sidebar.header(t["admin_header"])

if not st.session_state.admin_logged_in:
  with st.sidebar.form(key="admin_login_form"):
    admin_pass_input = st.text_input(t["admin_pass_label"], type="password")
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
      st.sidebar.write(f"📊 إجمالي الموظفين: `{len(df_admin)}`")

      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_admin.to_excel(writer, index=False)
      excel_bytes = output.getvalue()

      st.sidebar.download_button(
          label=t["download_btn"],
          data=excel_bytes,
          file_name="mirage_payroll_database.xlsx",
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
          st.session_state.employee_row_data = matched_ref.iloc[0].to_dict()
    st.success(t["refresh_success"])
    st.rerun()

st.markdown("---")

if not is_portal_open():
  st.error(t["portal_locked_msg"])
  st.stop()


# ====================================================================
# EMPLOYEE PORTAL VIEW (Direct access via National ID only)
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
    st.rerun()

  st.success(t["welcome_banner"].format(name=st.session_state.logged_in_user))
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
          {t["table_col_key"]: str(col_name), t["table_col_val"]: display_val}
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
    st.rerun()

else:
  st.write(t["subtitle"])
  try:
    df = load_excel_df()
    if df is None:
      st.error(t["error_read"].format(error="Could not load data."))
    else:
      with st.form(key="direct_login_form"):
        national_id_input = st.text_input(
            t["input_label"], key="national_id_field"
        )
        submit_login = st.form_submit_button(t["login_btn"])

        if submit_login:
          clean_input_id = clean_str(national_id_input)
          if not clean_input_id:
            st.warning(t["empty_input"])
          else:
            matched = df[df["الرقم القومي"].apply(clean_str) == clean_input_id]
            if not matched.empty:
              emp_name = matched.iloc[0].get("الاسم", "الموظف")
              st.session_state.logged_in_user = emp_name
              st.session_state.logged_in_id = clean_input_id
              st.session_state.employee_row_data = matched.iloc[0].to_dict()
              st.rerun()
            else:
              st.error(t["error_id"])

  except Exception as e:
    st.error(t["error_read"].format(error=e))
