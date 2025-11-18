import duckdb

conn = duckdb.connect(database='madang.db')
conn.sql("create table Customer as select * from 'Customer_madang.csv'")
conn.sql("create table Book as select * from 'Book_madang.csv'")
conn.sql("create table Orders as select * from 'Orders_madang.csv'")
conn.close()

import duckdb
conn = duckdb.connect(database='madang.db')

def query(sql, retunrType='df'):
       if retunrType == 'df':
              return conn.execute(sql).df()
       else:
              return conn.execute(sql).fetchall()

#query("select * from Book", "df")
query("select * from Book", "list")

conn.execute("select * from Orders").fetchall()

conn.execute("INSERT INTO Customer VALUES (6, '김도연', '인천시 미추홀구', '010-1111-1111')")

# 잘 들어갔는지 확인 (방금 넣은 이름으로 검색)
conn.sql("SELECT * FROM Customer WHERE name = '김도연'").show()



import streamlit as st
import duckdb
import pandas as pd
import time

# 1. DuckDB 연결 (read_only=False여야 데이터 입력 가능)
conn = duckdb.connect(database='madang.db', read_only=False)

# 2. 쿼리 실행 함수 (DuckDB 스타일로 변경)
def query(sql):
    return conn.execute(sql).fetchall()

st.title("📚 마당 서점 포스(POS) 시스템")

# 책 목록 미리 가져오기 (콤보박스용)
# DuckDB는 리스트 컴프리헨션으로 간단하게 처리 가능
books_data = conn.execute("select bookid, bookname from Book").fetchall()
# "1, 축구의 역사" 형태로 문자열 만들기
book_options = [f"{row[0]}, {row[1]}" for row in books_data]

# 탭 구성
tab1, tab2 = st.tabs(["🔍 고객 조회", "💳 거래 입력"])

# 변수 초기화
name_input = ""
selected_custid = None # custid를 저장할 변수

# --- 탭 1: 고객 조회 ---
with tab1:
    name_input = st.text_input("고객명 검색")
    
    if name_input:
        # SQL Injection 방지를 위해 f-string 사용 (간단한 버전)
        sql = f"""
            SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice 
            FROM Customer c
            JOIN Orders o ON c.custid = o.custid
            JOIN Book b ON o.bookid = b.bookid
            WHERE c.name = '{name_input}'
        """
        
        # 결과가 있는지 확인
        result_df = conn.execute(sql).df()
        
        if not result_df.empty:
            st.write(f"**{name_input}** 님의 거래 내역입니다.")
            st.dataframe(result_df)
            
            # 조회된 고객의 ID를 저장 (거래 입력 탭에서 쓰기 위해)
            selected_custid = result_df['custid'][0]
        else:
            st.warning("해당 이름의 고객이나 거래 내역이 없습니다.")

# --- 탭 2: 거래 입력 ---
with tab2:
    st.header("새로운 주문 입력")
    
    # 고객 정보 표시 (탭 1에서 검색했으면 자동 입력)
    if selected_custid:
        st.success(f"선택된 고객: {name_input} (ID: {selected_custid})")
        target_custid = selected_custid
    else:
        st.info("먼저 '고객 조회' 탭에서 고객을 검색해주세요.")
        target_custid = st.number_input("또는 고객 번호 직접 입력", value=0)

    # 책 선택
    select_book = st.selectbox("구매할 책 선택:", book_options)
    
    # 가격 입력
    price = st.text_input("판매 금액 (원)")

    if st.button('거래 입력'):
        if target_custid > 0 and select_book and price:
            # 1. 데이터 준비
            bookid = select_book.split(",")[0]
            dt = time.strftime('%Y-%m-%d', time.localtime())
            
            # 2. 주문번호 자동 생성 (최대값 + 1)
            # DuckDB에서 결과가 NULL(첫 주문)일 경우 0으로 처리하는 로직 추가
            max_id = conn.execute("SELECT MAX(orderid) FROM Orders").fetchone()[0]
            new_orderid = 1 if max_id is None else max_id + 1
            
            # 3. INSERT 실행
            insert_sql = f"""
                INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) 
                VALUES ({new_orderid}, {target_custid}, {bookid}, {price}, '{dt}')
            """
            conn.execute(insert_sql)
            
            st.balloons() # 성공 축하 효과
            st.success(f"주문이 완료되었습니다! (주문번호: {new_orderid})")
            
            # 확인을 위해 방금 넣은 데이터 보여주기
            st.write("입력된 데이터:")
            st.dataframe(conn.execute(f"SELECT * FROM Orders WHERE orderid = {new_orderid}").df())
            
        else:
            st.error("고객 번호와 가격을 정확히 입력해주세요.")