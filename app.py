import streamlit as st
from ultralytics import YOLO
from PIL import Image
import tempfile
import io
import base64
from datetime import datetime
from supabase import create_client, Client


# 1. إعداد الصفحة والاتصال بـ Supabase
st.set_page_config(
    page_title="نظام كشف الحفريات ومتابعتها",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()


def image_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def base64_to_image(base64_str: str):
    if not base64_str:
        return None
    try:
        img_data = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(img_data))
    except Exception:
        return None


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

try:
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass


# تحميل نموذج YOLO
@st.cache_resource
def load_model():
    return YOLO("best.pt")

model = load_model()



# 2. الصفحة الرئيسية

if st.session_state["current_page"] == "الرئيسية":

    st.markdown('<div class="main-title">نظام كشف الحفريات ومتابعتها</div>', unsafe_allow_html=True)
    st.write("")
    st.subheader("مرحباً بك، يرجى اختيار الخدمة المطلوبة:")
    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; height: 100%;">
            <h2 style="color: #1565C0;">تقديم بلاغ جديد</h2>
            <p style="color: #555; font-size: 15px;">رفع صور الحفريات وإرسالها للبلدية مع تحديد موقع الشارع والحي.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("تقديم بلاغ", key="btn_report", use_container_width=True):
            st.session_state["current_page"] = "تقديم بلاغ"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; height: 100%;">
            <h2 style="color: #1565C0;">متابعة بلاغ</h2>
            <p style="color: #555; font-size: 15px;">الاستعلام عن حالة بلاغ سابق باستخدام رقم البلاغ الخاص بك.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("متابعة بلاغ", key="btn_track", use_container_width=True):
            st.session_state["current_page"] = "متابعة بلاغ"
            st.rerun()

    with col3:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; height: 100%;">
            <h2 style="color: #1565C0;">دخول البلدية</h2>
            <p style="color: #555; font-size: 15px;">مخصص للموظفين لمتابعة البلاغات المقدمة وتحديث حالتها الميدانية.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("الدخول كـ موظف بلدي", key="btn_muni", use_container_width=True):
            st.session_state["current_page"] = "دخول البلدية"
            st.rerun()



# 2. صفحة تقديم بلاغ
elif st.session_state["current_page"] == "تقديم بلاغ":

    if st.button("العودة للقائمة الرئيسية", key="back_home1"):
        st.session_state["current_page"] = "الرئيسية"
        st.rerun()

    st.markdown('<div class="main-title">تقديم بلاغ عن حفرية</div>', unsafe_allow_html=True)
    st.write("")

    uploaded_file = st.file_uploader("رفع صورة الطريق", type=["jpg", "jpeg", "png"])

    st.write("")
    st.subheader("بيانات الموقع")

    col1, col2, col3 = st.columns(3)
    with col1:
        street = st.text_input("اسم الشارع")
    with col2:
        district = st.text_input("اسم الحي")
    with col3:
        city = st.text_input("المدينة")

    st.write("")
    analyze = st.button("تحليل الصورة وإرسال البلاغ", use_container_width=True)

    if analyze:
        if uploaded_file is None:
            st.warning("الرجاء رفع صورة للطريق أولاً.")
        elif street.strip() == "" or district.strip() == "" or city.strip() == "":
            st.warning("الرجاء إدخال بيانات الموقع بالكامل.")
        else:
            with st.spinner("جاري تحليل الصورة وحفظ البلاغ في قاعدة البيانات..."):
                # تحويل نمط الألوان إلى RGB لتجنب خطأ الشفافية PNG
                image = Image.open(uploaded_file).convert("RGB")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                image.save(temp_file.name)

                # تنفيذ نموذج YOLO
                results = model.predict(source=temp_file.name, conf=0.25, save=False)
                result = results[0]
                plotted = result.plot()
                detected_image = Image.fromarray(plotted)

                detections = len(result.boxes)
                confidence = 0.0
                if detections > 0:
                    confidence = float(result.boxes.conf.max()) * 100
                    status = "تم اكتشاف حفريات"
                else:
                    status = "لم يتم اكتشاف حفريات"

                orig_b64 = image_to_base64(image)
                det_b64 = image_to_base64(detected_image)

                new_report_data = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "city": city,
                    "district": district,
                    "street": street,
                    "detections": detections,
                    "confidence": f"{confidence:.1f}%",
                    "status": "قيد المعالجة",
                    "original_image": orig_b64,
                    "detected_image": det_b64
                }

                res = supabase.table("potholes_reports").insert(new_report_data).execute()
                inserted_id = res.data[0]["id"] if res.data else "جديد"

            st.success("اكتمل تحليل الصورة وتسجيل البلاغ بنجاح!")
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("الصورة الأصلية")
                st.image(image, use_container_width=True)
            with col2:
                st.subheader("الصورة بعد التحليل")
                st.image(detected_image, use_container_width=True)

            st.divider()

            st.subheader("نتائج التحليل")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(label="الحالة", value=status)
            with c2:
                st.metric(label="نسبة الثقة", value=f"{confidence:.2f}%")
            with c3:
                st.metric(label="عدد الحفريات", value=detections)

            st.divider()
            st.info(f"بيانات الموقع:\n- الشارع: {street}\n- الحي: {district}\n- المدينة: {city}")
            st.success(f"تم تسجيل البلاغ وإرساله للبلدية بنجاح. رقم البلاغ الخاص بك هو: {inserted_id}")


# 4. صفحة متابعة بلاغ
elif st.session_state["current_page"] == "متابعة بلاغ":

    if st.button("العودة للقائمة الرئيسية", key="back_home_track"):
        st.session_state["current_page"] = "الرئيسية"
        st.rerun()

    st.markdown('<div class="main-title">متابعة حالة بلاغ</div>', unsafe_allow_html=True)
    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("الاستعلام عن بلاغ")
        search_id = st.number_input("أدخل رقم البلاغ:", min_value=1, step=1, value=1)
        search_button = st.button("بحث عن البلاغ", use_container_width=True)

        if search_button:
            with st.spinner("جاري البحث في قاعدة البيانات..."):
                response = supabase.table("potholes_reports").select("*").eq("id", search_id).execute()
                reports = response.data

            if reports and len(reports) > 0:
                found_report = reports[0]
                st.success(f"تم العثور على البلاغ رقم: {found_report['id']}")
                st.divider()
                st.write(f"**حالة البلاغ الحالية:** {found_report['status']}")
                st.write(f"**تاريخ التقديم:** {found_report['date']}")
                st.write(f"**الموقع:** {found_report['city']} - حي {found_report['district']} - شارع {found_report['street']}")
                st.write(f"**عدد الحفريات المكتشفة:** {found_report['detections']}")
                st.divider()

                det_img = base64_to_image(found_report.get("detected_image"))
                if det_img:
                    st.image(det_img, caption="الصورة المحللة للبلاغ", use_container_width=True)
                else:
                    st.info("الصورة غير متاحة لهذا البلاغ.")
            else:
                st.error("لم يتم العثور على بلاغ بهذا الرقم. الرجاء التأكد من الرقم والمحاولة مرة أخرى.")


# 5. صفحة دخول البلدية
elif st.session_state["current_page"] == "دخول البلدية":

    if st.button("العودة للقائمة الرئيسية", key="back_home2"):
        st.session_state["current_page"] = "الرئيسية"
        st.rerun()

    st.markdown('<div class="main-title">بوابة الموظفين - البلدية</div>', unsafe_allow_html=True)

    EMPLOYEE_ID = "2026"
    PASSWORD = "j2026"

    if not st.session_state["logged_in"]:
        st.write("")
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.subheader("تسجيل دخول الموظفين")
            with st.form("login_form"):
                emp_id = st.text_input("الرقم الوظيفي", placeholder="أدخل الرقم الوظيفي")
                pass_input = st.text_input("كلمة السر", type="password", placeholder="أدخل كلمة السر")
                submit_login = st.form_submit_button("تسجيل الدخول", use_container_width=True)

                if submit_login:
                    if emp_id == EMPLOYEE_ID and pass_input == PASSWORD:
                        st.session_state["logged_in"] = True
                        st.success("تم تسجيل الدخول بنجاح")
                        st.rerun()
                    else:
                        st.error("الرقم الوظيفي أو كلمة السر غير صحيحة.")
    else:
        top_col1, top_col2 = st.columns([4, 1])
        with top_col1:
            st.success("مرحباً بك")
        with top_col2:
            if st.button("تسجيل الخروج", use_container_width=True):
                st.session_state["logged_in"] = False
                st.rerun()

        st.divider()

        response = supabase.table("potholes_reports").select("*").order("id", desc=True).execute()
        reports = response.data if response.data else []

        total_reports = len(reports)
        pending_reports = sum(1 for r in reports if r.get("status") == "قيد المعالجة")
        in_progress_reports = sum(1 for r in reports if r.get("status") == "جاري العمل ميدانياً")
        completed_reports = sum(1 for r in reports if r.get("status") == "تمت المعالجة")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي البلاغات", total_reports)
        c2.metric("قيد المعالجة", pending_reports)
        c3.metric("جاري العمل", in_progress_reports)
        c4.metric("تمت المعالجة", completed_reports)

        st.divider()
        st.subheader("قائمة البلاغات الواردة")

        if len(reports) == 0:
            st.info("لا توجد بلاغات مقدمة حتى الآن.")
        else:
            for idx, report in enumerate(reports):
                with st.expander(
                    f"بلاغ رقم {report['id']} - {report.get('city', '')} ({report.get('district', '')}) | الحالة: {report.get('status', '')}"
                ):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        det_img = base64_to_image(report.get("detected_image"))
                        if det_img:
                            st.image(det_img, caption="صورة الحفرية المكتشفة", use_container_width=True)
                        else:
                            st.info("الصورة غير متاحة")
                    with col2:
                        st.write(f"**رقم البلاغ:** {report['id']}")
                        st.write(f"**تاريخ البلاغ:** {report.get('date', '')}")
                        st.write(f"**الشارع:** {report.get('street', '')}")
                        st.write(f"**الحي:** {report.get('district', '')}")
                        st.write(f"**المدينة:** {report.get('city', '')}")
                        st.write(f"**عدد الحفريات:** {report.get('detections', 0)}")
                        st.write(f"**نسبة الثقة:** {report.get('confidence', '')}")
                        st.write("---")

                        status_options = ["قيد المعالجة", "جاري العمل ميدانياً", "تمت المعالجة"]
                        current_status = report.get("status", "قيد المعالجة")
                        current_index = status_options.index(current_status) if current_status in status_options else 0

                        new_status = st.selectbox(
                            "تحديث حالة البلاغ:",
                            status_options,
                            index=current_index,
                            key=f"status_select_{report['id']}_{idx}"
                        )

                        if new_status != current_status:
                            supabase.table("potholes_reports").update({"status": new_status}).eq("id", report["id"]).execute()
                            st.success("تم تحديث حالة البلاغ بنجاح في قاعدة البيانات")
                            st.rerun()
