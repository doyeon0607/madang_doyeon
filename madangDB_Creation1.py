import streamlit as st
import duckdb
import pandas as pd
import time

# 1. DB 연결 (복잡한 IP주소, 비밀번호 다 필요없고 이거 한 줄이면 됨)
conn = duckdb.connect(database='madang.db', read_only=False)

# 2. 쿼리 실행 함수 (사용자님이 짠 거랑 똑같은 기능)
def query(sql):
    return conn.execute(sql).fetchall()

# 3. 책 목록 만들기 (반복문 사용 - 기존 스타일 유지)
books = []
result = query("select bookid, bookname from Book")
# 결과가 (1, '축구의 역사') 이런 식의 튜플로 나옴
for res in result:
    # "1,축구의 역사" 형태로 만들어서 리스트에 추가
    books.append(str(res[0]) + "," + res[1])

# 탭 구성
tab1, tab2 = st.tabs(["고객조회", "거래 입력"])

# 변수 초기화
name = ""
custid = 999 # 기본값
result_df = pd.DataFrame()

# --- 탭 1: 고객 조회 ---
name = tab1.text_input("고객명")

if len(name) > 0:
    # SQL을 더하기(+)로 연결하기 (사용자 스타일)
    sql = "select c.custid, c.name, b.bookname, o.orderdate, o.saleprice from Customer c, Book b, Orders o where c.custid = o.custid and o.bookid = b.bookid and c.name = '" + name + "'"
    
    # 데이터프레임으로 바로 가져오기 (컬럼명 에러 안 나게 하려면 이게 제일 쉬움)
    result_df = conn.execute(sql).df()
    tab1.write(result_df)
    
    # 검색 결과가 있을 때만 고객번호 가져오기
    if not result_df.empty:
        custid = result_df['custid'][0]

# --- 탭 2: 거래 입력 ---
tab2.write("고객번호: " + str(custid))
tab2.write("고객명: " + name)

select_book = tab2.selectbox("구매 서적:", books)

if select_book is not None:
    bookid = select_book.split(",")[0]
    
    # 날짜 구하기
    dt = time.localtime()
    dt = time.strftime('%Y-%m-%d', dt)
    
    # 주문번호 구하기 (쿼리 결과에서 값만 쏙 빼오기)
    max_id_list = query("select max(orderid) from orders")
    if max_id_list[0][0] is None:
        orderid = 1
    else:
        orderid = max_id_list[0][0] + 1
    
    price = tab2.text_input("금액")
    
    if tab2.button('거래 입력'):
        # insert 쿼리도 문자열 더하기로 만들기
        sql = "insert into orders (orderid, custid, bookid, saleprice, orderdate) values (" + str(orderid) + "," + str(custid) + "," + str(bookid) + "," + str(price) + ",'" + dt + "')"
        
        # 실행
        conn.execute(sql)
        tab2.write('거래가 입력되었습니다.')
        
        # 확인용
        tab2.write("입력된 데이터 확인:")
        tab2.write(conn.execute("select * from orders where orderid=" + str(orderid)).df())