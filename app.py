import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
import time

# 🔹 DuckDB 연결 + CSV 로 테이블 생성
@st.cache_resource
def get_connection():
    base_path = Path(__file__).parent
    con = duckdb.connect(database=':memory:')

    # CSV → 테이블 생성
    con.execute(
        "CREATE TABLE Book AS SELECT * FROM read_csv_auto(?);",
        [str(base_path / "Book_madang.csv")]
    )
    con.execute(
        "CREATE TABLE Customer AS SELECT * FROM read_csv_auto(?);",
        [str(base_path / "Customer_madang.csv")]
    )
    con.execute(
        "CREATE TABLE Orders AS SELECT * FROM read_csv_auto(?);",
        [str(base_path / "Orders_madang.csv")]
    )

    # 🔹 정혜령 정보 추가 (중복 방지를 위해 같은 custid 먼저 삭제 후 삽입)
    con.execute("DELETE FROM Customer WHERE custid = 6;")
    con.execute("""
        INSERT INTO Customer (custid, name, address, phone)
        VALUES (6, '정혜령', '대한민국 인천', '010-2873-1807')
    """)

    return con


# 🔹 전역 연결 객체 (세션 동안 유지)
con = get_connection()

# 🔹 타이틀
st.title("📚 마당 서점 대시보드")

# 🔹 사이드바 메뉴
menu = st.sidebar.selectbox(
    "보고 싶은 기능을 선택하세요",
    [
        "테이블 보기",
        "고객별 총 매출",
        "도서별 총 매출",
        "고객 이름 검색"  # → 여기에서 탭(고객조회 / 거래 입력) 제공
    ]
)

# ---------------------- 테이블 보기 ----------------------
if menu == "테이블 보기":
    st.subheader("Customer 테이블")
    st.dataframe(con.execute("SELECT * FROM Customer").df(), use_container_width=True)

# ---------------------- 고객별 총 매출 ----------------------


# ---------------------- 고객 이름 검색 + 거래 입력 (탭) ----------------------
elif menu == "고객 이름 검색":
    st.subheader("고객 주문 검색 및 거래 입력")

    tab1, tab2 = st.tabs(["고객조회", "거래 입력"])

    # ====== 🟢 탭 1: 고객조회 ======
    with tab1:
        name = st.text_input("고객명 입력")

        if name:
            safe_name = name.replace("'", "''")
            query = f"""
                SELECT 
                    c.custid,
                    c.name,
                    b.bookname,
                    o.orderdate,
                    o.saleprice
                FROM Orders o
                JOIN Customer c ON o.custid = c.custid
                JOIN Book b ON o.bookid = b.bookid
                WHERE lower(c.name) LIKE '%' || lower('{safe_name}') || '%'
                ORDER BY o.orderdate;
            """
            df = con.execute(query).df()
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                custid = df["custid"].iloc[0]
                st.success(f"📌 첫 번째 검색 결과 기준 고객번호: {custid}")
            else:
                st.warning("❌ 해당 이름의 주문 기록이 없습니다.")

    # ====== 🟡 탭 2: 거래 입력 ======
    with tab2:
        st.subheader("📗 새로운 주문 입력")

        # 고객번호 / 고객명 입력
        custid_input = st.text_input("고객번호 입력 (예: 6)")
        name_input = st.text_input("고객명 (선택, 메모용)")

        # 도서 선택용 데이터
        books_df = con.execute("SELECT bookid, bookname FROM Book").df()
        book_option = st.selectbox(
            "구매 서적 선택",
            books_df.apply(lambda row: f"{row['bookid']}, {row['bookname']}", axis=1)
            if not books_df.empty else []
        )

        price_input = st.text_input("금액 입력 (예: 15000)")

        if st.button("💾 거래 입력"):
            if not custid_input or not book_option or not price_input:
                st.error("⚠️ 고객번호, 도서, 금액을 모두 입력해주세요.")
            else:
                try:
                    bookid = int(book_option.split(",")[0].strip())
                    custid_val = int(custid_input.strip())
                    price_val = int(price_input.strip())
                except ValueError:
                    st.error("⚠️ 고객번호, 도서 ID, 금액은 숫자로 입력해주세요.")
                else:
                    # 오늘 날짜
                    dt = time.strftime("%Y-%m-%d", time.localtime())

                    # orderid 자동 생성
                    orderid = con.execute(
                        "SELECT COALESCE(MAX(orderid), 0) + 1 FROM Orders"
                    ).fetchone()[0]

                    insert_sql = f"""
                        INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate)
                        VALUES ({orderid}, {custid_val}, {bookid}, {price_val}, '{dt}');
                    """
                    con.execute(insert_sql)

                    st.success("🎉 거래가 성공적으로 입력되었습니다!")
                    st.write(f"- 주문번호: {orderid}")
                    st.write(f"- 고객번호: {custid_val}")
                    if name_input:
                        st.write(f"- 고객명: {name_input}")
                    st.write(f"- 도서 ID: {bookid}")
                    st.write(f"- 금액: {price_val}원")
                    st.write(f"- 주문일자: {dt}")
