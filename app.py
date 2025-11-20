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


con = get_connection()


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

