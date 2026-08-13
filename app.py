import streamlit as st
import pandas as pd
import os

# ضبط إعدادات الصفحة
st.set_page_config(
    page_title="نظام مفردات الرواتب",
    page_icon="💰",
    layout="centered"
)

# مسار حفظ الملف المرفوع محلياً
DATA_FILE = "current_salary_data.csv"

# كلمة سر لوحة المحاسب (يمكنك تعديلها هنا أو من Streamlit Secrets)
ACCOUNTANT_PASSWORD = st.secrets.get("ACCOUNTANT_PASSWORD", "AdminPassword123")

st.title("💼 بوابة استعلام رواتب الموظفين")
st.write("مرحباً بك. يرجى اختيار الصفة من القائمة الجانبية.")

# القائمة الجانبية لتحديد الصفة
menu = st.sidebar.selectbox("القائمة", ["🔍 استعلام الموظف / الفني", "🔒 لوحة المحاسب"])

# ==========================================
# 1️⃣ لوحة المحاسب (مُحمية بكلمة سر)
# ==========================================
if menu == "🔒 لوحة المحاسب":
    st.header("🔒 لوحة تحكم المحاسب")
    
    password = st.text_input("أدخل كلمة السر الخاصة بالمحاسب:", type="password")
    
    if password == ACCOUNTANT_PASSWORD:
        st.success("تم التحقق بنجاح! يمكنك رفع شيت الرواتب الآن.")
        
        uploaded_file = st.file_uploader(
            "يرجى رفع شيت الرواتب (ملف Excel أو CSV):", 
            type=["xlsx", "csv"]
        )
        
        if uploaded_file is not None:
            try:
                # قراءة الملف المرفوع
                if uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)
                
                # إزالة أي مسافات من أسماء الأعمدة
                df.columns = df.columns.str.strip()
                
                # الأعمدة المطلوبة
                required_cols = ['الرقم_القومي', 'الاسم', 'الأساسي', 'الحوافز', 'الخصومات', 'الصافي']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"⚠️ الملف المرفوع يفتقد الأعمدة التالية: {', '.join(missing_cols)}")
                    st.info("تأكد أن أسماء الأعمدة في الإكسيل تحتوي على: الرقم_القومي | الاسم | الأساسي | الحوافز | الخصومات | الصافي")
                else:
                    # تحويل الرقم القومي لنص وتعديل الصيغ
                    df['الرقم_القومي'] = df['الرقم_القومي'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    
                    # حفظ البيانات محلياً
                    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                    st.success("✅ تم حفظ وتحديث بيانات الرواتب بنجاح! يمكن للجميع الاستعلام بالرقم القومي الآن.")
                    
                    st.subheader("📊 معاينة شيت الرواتب الحالي:")
                    st.dataframe(df)
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
                
    elif password != "":
        st.error("⚠️ كلمة السر غير صحيحة!")

# ==========================================
# 2️⃣ بوابة استعلام الموظف / الفني
# ==========================================
elif menu == "🔍 استعلام الموظف / الفني":
    st.header("🔍 استعلام مفردات الراتب")
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype={'الرقم_القومي': str})
        
        # إدخال الرقم القومي
        national_id = st.text_input("أدخل الرقم القومي الخاص بك (14 رقم):", type="password")
        
        if st.button("عرض مفردات الراتب"):
            clean_id = national_id.strip()
            if clean_id:
                # تحويل العمود لمقارنة دقيقة
                df['الرقم_القومي'] = df['الرقم_القومي'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                # البحث بالرقم القومي
                user_data = df[df['الرقم_القومي'] == clean_id]
                
                if not user_data.empty:
                    row = user_data.iloc[0]
                    
                    st.markdown("---")
                    st.success(f"مرحباً **{row['الاسم']}** 👋")
                    
                    # عرض التفاصيل
                    col1, col2, col3 = st.columns(3)
                    col1.metric("الراتب الأساسي", f"{float(row['الأساسي']):,.2f} ج.م")
                    col2.metric("الحوافز / الإضافي", f"{float(row['الحوافز']):,.2f} ج.م")
                    col3.metric("الخصومات", f"{float(row['الخصومات']):,.2f} ج.م")
                    
                    st.markdown("---")
                    st.subheader(f"💵 صافي الراتب المستحق: {float(row['الصافي']):,.2f} ج.م")
                    
                    st.markdown("#### 📄 بيان مفردات الراتب:")
                    details = f"""
                    - **الاسم:** {row['الاسم']}
                    - **الراتب الأساسي:** {row['الأساسي']} ج.م
                    - **الحوافز والإضافي:** {row['الحوافز']} ج.م
                    - **إجمالي الخصومات:** {row['الخصومات']} ج.م
                    - **صافي المرتب:** {row['الصافي']} ج.م
                    """
                    st.info(details)
                else:
                    st.error("⚠️ الرقم القومي غير موجود في شيت هذا الشهر. يرجى مراجعة المحاسب.")
            else:
                st.warning("يرجى كتابة الرقم القومي أولاً.")
    else:
        st.info("ℹ️ لم يتم رفع شيت الرواتب لهذا الشهر بعد. يرجى مراجعة المحاسب.")
