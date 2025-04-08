from dotenv import load_dotenv
import os

from datahub_cls.metadata_fetcher import (
    DatahubMetadataFetcher,
    get_all_tables_info,
)

from utils import save_persona_json, pretty_print_persona
from persona_class import PersonaList


from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def drop_empty_tables(tables_df):
    drop_empty_tables = tables_df[
        tables_df["table_description"].apply(lambda x: x != "")
    ]
    return drop_empty_tables[["table_name", "table_description"]]


def get_table_des_string(tables_df):
    return_string = "table name : table description\n---\n"
    for _, row in tables_df.iterrows():
        return_string += f"{row['table_name']} : {row['table_description']}\n---\n"
    return return_string


def generate_persona(tables_df):
    tables_df = drop_empty_tables(tables_df)
    description_string = get_table_des_string(tables_df)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    system_prompt = """주어진 Tabel description들을 참고하여 Text2SQL 서비스로 질문을 할만한 패르소나를 생성하세요"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
        ]
    )

    chain = prompt | llm.with_structured_output(PersonaList)
    return chain.invoke({"input": description_string})


def main():
    # 데이터허브 서버 연결
    fetcher = DatahubMetadataFetcher(gms_server=os.getenv("DATAHUB_SERVER"))
    tables_df = get_all_tables_info(fetcher)
    personas = generate_persona(tables_df)
    print(pretty_print_persona(personas))
    save_persona_json(personas, "data/persona/personas.json")


if __name__ == "__main__":
    main()
