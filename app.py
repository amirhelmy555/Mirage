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

# كلمة سر لوحة المحاسب (يمكنك تغييرها من هنا)
ACCOUNTANT_PASSWORD = "AdminPassword123"

st.title("💼 بوابة استعلام رواتب الفنيين")
st.write("مرحباً بك. يرجى اختيار الصفة من القائمة الجانبية.")

# القائمة الجانبية لتحديد المتبوع (فني / محاسب)
menu = st.sidebar.selectbox("القائمة", ["🔍 استعلام الفني", "🔒 لوحة المحاسب"])

# ==========================================
# 1️⃣ لوحة المحاسب (مُحمية بكلمة سر)
# ==========================================
if menu == "🔒 لوحة المحاسب":
    st.header("🔒 لوحة تحكم المحاسب")
    
    # التحقق من كلمة السر
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
                
                # التأكد من وجود الأعمدة المطلوبة
                required_cols = ['كود_الفني', 'الاسم', 'الأساسي', 'الحوافز', 'الخصومات', 'الصافي']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"⚠️ الملف المرفوع يفتقد الأوردة التالية: {', '.join(missing_cols)}")
                else:
                    # حفظ البيانات في ملف CSV محلياً ليقرأه الفنيون
                    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                    st.success("✅ تم حفظ وتحديث بيانات الرواتب بنجاح! يمكن للفنيين الاستعلام الآن.")
                    
                    st.subheader("📊 معاينة شيت الرواتب الحالي:")
                    st.dataframe(df)
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
                
    elif password != "":
        st.error("⚠️ كلمة السر غير صحيحة!")

# ==========================================
# 2️⃣ بوابة استعلام الفني
# ==========================================
elif menu == "🔍 استعلام الفني":
    st.header("🔍 استعلام مفردات الراتب")
    
    # التأكد من وجود ملف بيانات الرواتب المرفوع من المحاسب
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        
        tech_code = st.text_input("أدخل كود الفني الخاص بك (مثال: TECH-101):")
        
        if st.button("عرض مفردات الراتب"):
            if tech_code.strip():
                # البحث عن الفني بواسطة الكود
                user_data = df[df['كود_الفني'].astype(str).str.strip() == tech_code.strip()]
                
                if not user_data.empty:
                    row = user_data.iloc[0]
                    
                    st.markdown("---")
                    st.success(f"مرحباً **{row['الاسم']}** 👋")
                    
                    # عرض التفاصيل في كروت سريعة
                    col1, col2, col3 = st.columns(3)
                    col1.metric("الراتب الأساسي", f"{row['الأساسي']:,.2f} ج.م")
                    col2.metric("الحوافز / الإضافي", f"{row['الحوافز']:,.2f} ج.م")
                    col3.metric("الخصومات", f"{row['الخصومات']:,.2f} ج.م")
                    
                    st.markdown("---")
                    st.subheader(f"💵 صافي الراتب المستحق: {row['الصافي']:,.2f} ج.م")
                    
                    # طباعة إشعار الراتب
                    st.markdown("#### 📄 إشعار الراتب التفصيلي:")
                    details = f"""
                    - **الكود:** {row['كود_الفني']}
                    - **الاسم:** {row['الاسم']}
                    - **الراتب الأساسي:** {row['الأساسي']} ج.م
                    - **الحوافز والإضافي:** {row['الحوافز']} ج.م
                    - **إجمالي الخصومات:** {row['الخصومات']} ج.م
                    - **صافي المرتب:** {row['الصافي']} ج.م
                    """
                    st.info(details)
                else:
                    st.error("⚠️ كود الفني غير موجود في شيت هذا الشهر. يرجى مراجعة المحاسب.")
            else:
                st.warning("يرجى كتابة الكود أولاً.")
    else:
        st.info("ℹ️ لم يتم رفع شيت الرواتب لهذا الشهر بعد. يرجى مراجعة المحاسب.")
