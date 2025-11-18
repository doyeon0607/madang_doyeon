import streamlit as st
import duckdb
import pandas as pd
import time

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="마당 서점 POS", layout="wide")
st.title("📚 마당 서점 포스(POS) 시스템")

# --- 2. DB 연결 (한 번만 연결) ---
# try-except 블록을 쓰지 않아도 되지만, 파일 경로 확인을 위해 안전하게 작성
try:
    conn = duckdb.connect(database='madang.db', read_only=False)
except Exception as e:
    st.error(f"데이터베이스 연결 오류: {e}")
    st.stop()

# --- 3. Session State 설정 (중요!) ---
# Streamlit은 탭을 이동하면 변수가 초기화되므로, 고객 정보를 기억하기 위해 사용
if 'selected_cust_id' not in st.session_state:
    st.session_state['selected_cust_id'] = None
if 'selected_cust_name' not in st.session_state:
    st.session_state['selected_cust_name'] = ""

# --- 4. 데이터 준비 ---
# 책 목록 가져오기
try:
    books_data = conn.execute("select bookid, bookname from Book").fetchall()
    book_options = [f"{row[0]}, {row[1]}" for row in books_data]
except:
    st.error("Book 테이블을 찾을 수 없습니다. DB 생성 코드를 먼저 실행해주세요.")
    book_options = []

# --- 5. 탭 구성 ---
tab1, tab2 = st.tabs(["🔍 고객 조회", "💳 거래 입력"])

# === 탭 1: 고객 조회 ===
with tab1:
    name_input = st.text_input("고객명 검색", placeholder="예: 김도연")
    
    if name_input:
        sql = f"""
            SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice 
            FROM Customer c
            JOIN Orders o ON c.custid = o.custid
            JOIN Book b ON o.bookid = b.bookid
            WHERE c.name = '{name_input}'
        """
        result_df = conn.execute(sql).df()
        
        if not result_df.empty:
            st.write(f"**{name_input}** 님의 거래 내역입니다.")
            st.dataframe(result_df)
            
            # ★ 검색된 고객 정보를 앱이 기억하도록 저장 (Session State)
            found_id = result_df['custid'][0]
            st.session_state['selected_cust_id'] = found_id
            st.session_state['selected_cust_name'] = name_input
            st.success(f"고객 선택됨: {name_input} (ID: {found_id}) -> '거래 입력' 탭으로 이동하세요.")
        else:
            st.warning("해당 이름의 고객이나 거래 내역이 없습니다.")
            # 거래 내역은 없지만 고객 테이블에는 있을 수 있으므로 확인
            cust_check = conn.execute(f"SELECT custid, name FROM Customer WHERE name='{name_input}'").df()
            if not cust_check.empty:
                found_id = cust_check['custid'][0]
                st.session_state['selected_cust_id'] = found_id
                st.session_state['selected_cust_name'] = name_input
                st.info(f"거래 내역은 없지만 고객 명단에 있습니다. (ID: {found_id})")

# === 탭 2: 거래 입력 ===
with tab2:
    st.header("새로운 주문 입력")
    
    # 저장된 고객 정보 불러오기
    current_cust_id = st.session_state['selected_cust_id']
    current_cust_name = st.session_state['selected_cust_name']

    if current_cust_id:
        st.success(f"현재 선택된 고객: **{current_cust_name}** (ID: {current_cust_id})")
        target_custid = current_cust_id
    else:
        st.info("고객이 선택되지 않았습니다. '고객 조회' 탭에서 검색하거나 아래에 직접 입력하세요.")
        target_custid = st.number_input("고객 번호 직접 입력", value=0)

    # 입력 폼
    col1, col2 = st.columns(2)
    with col1:
        select_book = st.selectbox("구매할 책 선택", book_options)
    with col2:
        price = st.text_input("판매 금액 (원)", value="0")

    if st.button('결제 및 거래 입력'):
        if target_custid > 0 and select_book and price:
            bookid = select_book.split(",")[0]
            dt = time.strftime('%Y-%m-%d', time.localtime())
            
            # 주문번호 생성
            max_id = conn.execute("SELECT MAX(orderid) FROM Orders").fetchone()[0]
            new_orderid = 1 if max_id is None else max_id + 1
            
            # DB 입력
            insert_sql = f"""
                INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) 
                VALUES ({new_orderid}, {target_custid}, {bookid}, {price}, '{dt}')
            """
            conn.execute(insert_sql)
            
            st.balloons()
            st.success(f"✅ 주문 완료! (주문번호: {new_orderid})")
            
            # 결과 확인
            st.write("▼ 방금 입력된 데이터")
            st.dataframe(conn.execute(f"SELECT * FROM Orders WHERE orderid = {new_orderid}").df())
        else:
            st.error("고객 번호와 금액을 확인해주세요.")
