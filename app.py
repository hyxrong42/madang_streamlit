import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path


@st.cache_resource
def get_connection():
    base_path = Path(__file__).parent
    con = duckdb.connect(database=':memory:')

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
    return con

# 🔹 Cloud와 Streamlit에서 DB 연결 유지
con = get_connection()

# 🔹 Streamlit 화면 구성
st.title("📚 마당 서점 대시보드")

menu = st.sidebar.selectbox(
    "보고 싶은 기능을 선택하세요",
    [
        "테이블 보기",
        "고객별 총 매출",
        "도서별 총 매출",
        "고객 이름 검색"
    ]
)
import duckdb
import pandas as pd

# 메모리 DB / 또는 file.duckdb로 저장 가능
con = duckdb.connect(database=':memory:')

# 📌 CSV 불러와서 테이블 생성
con.execute("""
    CREATE TABLE Customer AS SELECT * FROM read_csv_auto('Customer_madang.csv');
""")

# 📌 네 정보 INSERT (Python에서는 문자열로 넣어야 함)
con.execute("""
    INSERT INTO Customer (custid, name, address, phone)
    VALUES (6, '정혜령', '대한민국 인천', '010-2873-1807')
""")

# 📌 확인
df = con.execute("SELECT * FROM Customer").df()
print(df)

if menu == "테이블 보기":
    st.subheader("Customer 테이블")
    st.dataframe(con.execute("SELECT * FROM Customer").df(), use_container_width=True)

elif menu == "고객별 총 매출":
    st.subheader("고객별 총 매출 TOP 10")
    df = con.execute("""
        SELECT c.name, SUM(o.saleprice) AS total_sales
        FROM Orders o
        JOIN Customer c ON o.custid = c.custid
        GROUP BY c.name
        ORDER BY total_sales DESC
        LIMIT 10
    """).df()
    st.dataframe(df)
    st.bar_chart(df.set_index("name")["total_sales"])

elif menu == "도서별 총 매출":
    st.subheader("도서별 총 매출 TOP 10")
    df = con.execute("""
        SELECT b.bookname, SUM(o.saleprice) AS total_sales
        FROM Orders o
        JOIN Book b ON o.bookid = b.bookid
        GROUP BY b.bookname
        ORDER BY total_sales DESC
        LIMIT 10
    """).df()
    st.dataframe(df)
    st.bar_chart(df.set_index("bookname")["total_sales"])

elif menu == "고객 이름 검색":
    st.subheader("고객 주문 검색")
    name = st.text_input("고객 이름 입력")

    if name:
        # 작은따옴표 들어가면 SQL 깨지는 걸 막기 위한 이스케이프
        safe_name = name.replace("'", "''")

        query = f"""
            SELECT 
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


