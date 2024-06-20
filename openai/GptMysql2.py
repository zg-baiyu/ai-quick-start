import streamlit as st
from pymysql import Connection
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url="https://free.gpt.ge/v1/")


def init_db(host: str, port: str, user: str, password: str, database: str) -> Connection:
    return Connection(host=host, port=int(port), user=user, password=password, database=database)


def get_db_schema(conn: Connection, db_name: str):
    sql = f"show tables from {db_name}"
    with conn.cursor() as cursor:
        cursor.execute(sql)
        tables = cursor.fetchall()
        tables_schema = []
        for table in tables:
            sql = f"show create table {table[0]}"
            cursor.execute(sql)
            table_schema = cursor.fetchone()
            tables_schema.append(f"表名：{table[0]}")
        return table_schema


def execute_sql(conn: Connection, sql: str) -> str:
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        return str(cursor.fetchall())
    except Exception as e:
        return str(e)
    finally:
        cursor.close()


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_history.append(
        {"role": "assistant", "content": "你好，我是您的mysql助手，请问有什么可以帮助您？"})

if "chat_final_history" not in st.session_state:
    st.session_state.chat_final_history = []

st.set_page_config(layout="wide")
st.title("chat with mysql")

with st.sidebar:
    st.title("数据库连接信息")
    st.subheader("这是一个NLP2Mysql的Demo程序，请先连接mysql")
    st.text_input("HOST", value="localhost", key="host")
    st.text_input("PORT", value="3306", key="port")
    st.text_input("USER", value="root", key="user")
    st.text_input("PASSWORD", value="123456", key="password", type="password")
    st.text_input("DATABASE", value="chat_mysql", key="database")
    if st.button("连接数据库"):
        with st.spinner("正在连接数据库..."):
            db_conn = init_db(st.session_state.host, st.session_state.port,
                              st.session_state.user,
                              st.session_state.password, st.session_state.database)
            if db_conn not in st.session_state:
                st.session_state.db_conn = db_conn
            st.success("连接成功！")
            promptTemplate = """
            你是一位专业的DBA，根据以下<schema>中的表结构，根拟用户的问题编写SQL语句, 所有的表没有关联关系，不要使用join等表关联语法，
            只返回sql语句即可，不需要其他内容，需要考感对话的历史纪录，sq1语句最后不要加分号. 
            </schema> {schema} <schema > 
            举例:
            问题: 共有多少老师。
            回答: SELECT COUNT(*)FROM teacher
            问题: 1号学生的姓名
            回答： select student name from student WHERE id = 1
        """
            st.session_state.chat_history.append({"role": "system", "content": str(
                promptTemplate.format(schema=get_db_schema(db_conn, st.session_state.database)))})
            prompt_final = """
            你是一位专业的DBA，您正与一位用户进行交互，该用户向您询问有关数据库的问题。
            根据下面的表结构、问题、SQL查询和SQL响应，写自然语言的响应。最终的响应需要表达完整，让用户可以清晰的石清楚结果,
            <SCHEMA>{schema}</SCHEMA>
            举例:
            用户问题:一共有多少老师
            sql查询语句:SELECT COUNT(*) from teacher
            SQL响应:3
            回答:一共有3位老师
            """
            st.session_state.chat_final_history.append({"role": "system", "content": str(
                prompt_final.format(schema=get_db_schema(db_conn, st.session_state.database)))})

for message in st.session_state.chat_history:
    print(message)
    if message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message["content"])
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
for message in st.session_state.chat_final_history:
    if message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message["content"])

user_input = st.chat_input("请输入您的问题")
if user_input is not None:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_final_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    response = client.chat.completions.create(model="gpt-3.5-turbo-16k",
                                              messages=st.session_state.chat_history)
    sql = response.choices[0].message.content
    with st.chat_message("assistant"):
        st.markdown(sql)
    st.session_state.chat_history.append({"role": "assistant", "content": sql})
    st.session_state.chat_final_history.append({"role": "user", "content": sql})
    sql_result = execute_sql(st.session_state.db_conn, sql)
    st.session_state.chat_final_history.append({"role": "assistant", "content": sql_result})

    final_response = client.chat.completions.create(model="gpt-3.5-turbo-16k",
                                                    messages=st.session_state.chat_final_history)
    with st.chat_message("assistant"):
        st.markdown(final_response.choices[0].message.content)
    st.session_state.chat_final_history.append({"role": "assistant", "content": final_response.choices[0].message.content})
print(st.session_state.chat_final_history)