# app_test.py
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import qrcode
import io
from datetime import datetime, timedelta
import base64
import openpyxl
from openpyxl.drawing.image import Image as ExcelImage
import tempfile
import os

# LOT NO 변환 함수
def convert_lot_no(date_str):
    date = datetime.strptime(date_str, "%Y/%m/%d")
    year_code = {
        2020: 'K', 2021: 'L', 2022: 'M', 2023: 'A', 2024: 'B',
        2025: 'C', 2026: 'D', 2027: 'E', 2028: 'F', 2029: 'G',
        2030: 'H', 2031: 'J'
    }
    month_code = {
        1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F',
        7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'M'
    }
    y = date.year
    m = date.month
    d = date.day
    y_char = year_code.get(y, 'Z')
    m_char = month_code.get(m, 'Z')
    return f"{y_char}{m_char}{d:02d}"

# 라벨 이미지 생성 함수
def generate_label_image(company, code, prod_date, lot_no, serial_no, item_no, spec, qty, delivery_date, order_no):
    font_path = "NanumGothic.ttf"
    font = ImageFont.truetype(font_path, 18)
    width, height = 600, 335
    label_img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(label_img)

    cell_h = 40
    x1, x2, x3, x4 = 20, 160, 400, 580
    y = [20 + i * cell_h for i in range(8)]

    draw.rectangle([(x1, y[0]), (x4, y[7])], outline="black", width=2)
    for i in range(1, 8):
        draw.line([(x1, y[i]), (x4, y[i])], fill="black", width=2)

    draw.line([(x2, y[0]), (x2, y[7])], fill="black", width=2)
    draw.line([(x3, y[0]), (x3, y[1])], fill="black", width=2)
    draw.line([(x3, y[6]), (x3, y[7])], fill="black", width=2)

    def center_text(text, x1, y1, x2, y2):
        bbox = font.getbbox(text)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = x1 + (x2 - x1 - w) / 2
        y = y1 + (y2 - y1 - h) / 2
        draw.text((x, y), text, font=font, fill="black")

    center_text("업체명", x1, y[0], x2, y[1])
    center_text(company, x2, y[0], x3, y[1])
    center_text(code, x3, y[0], x4, y[1])
    center_text("생산일자", x1, y[1], x2, y[2])
    center_text(prod_date, x2, y[1], x3, y[2])
    center_text("품번", x1, y[2], x2, y[3])
    center_text(item_no, x2, y[2], x3, y[3])
    center_text("부품규격", x1, y[3], x2, y[4])
    center_text(spec, x2, y[3], x3, y[4])
    center_text("LOT No.", x1, y[4], x2, y[5])
    center_text(lot_no, x2, y[4], x3, y[5])
    center_text("수량", x1, y[5], x2, y[6])
    center_text(qty, x2, y[5], x3, y[6])
    center_text("납품일자", x1, y[6], x2, y[7])
    center_text(delivery_date, x2, y[6], x3, y[7])

    qr_data = f"{lot_no}{serial_no}{code}#{item_no}#{qty}#{order_no}"
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    cell_left, cell_top = x3, y[1]
    cell_right, cell_bottom = x4, y[7]
    cell_width = cell_right - cell_left
    cell_height = cell_bottom - cell_top

    qr_target_size = min(cell_width, cell_height) - 10
    qr_img = qr_img.resize((qr_target_size, qr_target_size))
    qr_x = cell_left + (cell_width - qr_target_size) // 2
    qr_y = cell_top + (cell_height - qr_target_size) // 2

    draw.rectangle([(cell_left, cell_top), (cell_right, cell_bottom)], fill="white")
    draw.rectangle([(cell_left, cell_top), (cell_right, cell_bottom)], outline="black", width=2)
    label_img.paste(qr_img, (qr_x, qr_y))

    qr_text_bbox = font.getbbox(qr_data)
    qr_text_w = qr_text_bbox[2] - qr_text_bbox[0]
    qr_text_x = (width - qr_text_w) // 2
    qr_text_y = y[7] + 5
    draw.text((qr_text_x, qr_text_y), qr_data, font=font, fill="black")

    return label_img, qr_data

# Streamlit UI
logo = Image.open("logo.png")
st.image(logo, width=100)

st.title("[테스트용] QR 부품 식별표 생성기")

with st.form("label_form"):
    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("업체명")
        item_no = st.text_input("품번")
        spec = st.text_input("부품규격")
        qty = st.text_input("수량")
    with col2:
        code = st.text_input("업체코드")
        prod_date = st.date_input("생산일자", format="YYYY/MM/DD")
        delivery_date = st.date_input("납품일자", format="YYYY/MM/DD")
        order_no = st.text_input("발주번호")

    submitted = st.form_submit_button("라벨 생성하기")

if submitted:
    prod_date_str = prod_date.strftime("%Y/%m/%d")
    delivery_date_str = delivery_date.strftime("%Y/%m/%d")
    lot_no = convert_lot_no(prod_date_str)
    korea_time = datetime.utcnow() + timedelta(hours=9)
    serial_no = korea_time.strftime("%y%m%d%H%M%S")

    img, qr_text = generate_label_image(
        company, code, prod_date_str, lot_no, serial_no,
        item_no, spec, qty, delivery_date_str, order_no
    )

    st.image(img, caption="생성된 라벨 미리보기", use_container_width=False)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")

    st.download_button(
        label="라벨 이미지 다운로드",
        data=buffered.getvalue(),
        file_name="label.png",
        mime="image/png"
    )

    # --- 엑셀 템플릿 기반 라벨 생성 및 다운로드 ---
    template_path = "라벨 엑셀 양식.xlsx"
    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    ws["B1"] = company
    ws["B2"] = prod_date_str
    ws["B3"] = item_no
    ws["B4"] = spec
    ws["B5"] = lot_no
    ws["B6"] = qty
    ws["B7"] = delivery_date_str
    ws["C1"] = code

# 셀 크기 기반 QR 이미지 생성 및 중앙 배치 + 테두리 추가
    import tempfile
    tmp_qr_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    from PIL import ImageDraw

    qr_width_px = 136  # C열 너비 16.25 * 7.5
    qr_height_px = 145  # 행 높이 18 * 6 * 1.33

    qr_img = qrcode.make(qr_text)
    qr_img = qr_img.resize((qr_width_px - 4, qr_height_px - 4))  # 안쪽 여백 확보

    final_img = Image.new("RGB", (qr_width_px, qr_height_px), "white")
    draw = ImageDraw.Draw(final_img)
    draw.rectangle([(0, 0), (qr_width_px - 1, qr_height_px - 1)], outline="black", width=1)

    offset_x = (qr_width_px - qr_img.width) // 2
    offset_y = (qr_height_px - qr_img.height) // 2
    final_img.paste(qr_img, (offset_x, offset_y))

    final_img.save(tmp_qr_path)
    img_for_excel = ExcelImage(tmp_qr_path)
    img_for_excel.width = qr_width_px
    img_for_excel.height = qr_height_px

    ws.add_image(img_for_excel, "C2")

    # QR코드 구성 텍스트를 병합 셀 A8:B8:C8에 삽입
    ws.merge_cells("A8:C8")
    ws["A8"] = qr_text

    excel_io = io.BytesIO()
    wb.save(excel_io)

    st.download_button(
        label="라벨 엑셀 다운로드",
        data=excel_io.getvalue(),
        file_name=f"label_{serial_no}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    try:
        os.remove(tmp_qr_path)
    except:
        pass
