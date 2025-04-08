from langchain_core.messages import HumanMessage

from utils import load_question_json, save_answer_json

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


def get_eval_result(graph):

    results = load_question_json("data/questions")

    for i, result in tqdm(enumerate(results), desc="Processing results"):
        inputs = []
        for question in result["questions"]:
            inputs.append(
                {
                    "messages": [HumanMessage(content=question)],
                    "user_database_env": "duckdb",
                    "best_practice_query": "",
                }
            )
        response = graph.batch(inputs)
        answers = []
        for res in response:
            refined_input_content = (
                res["refined_input"].content
                if hasattr(res["refined_input"], "content")
                else res["refined_input"]
            )
            answers.append(
                {
                    "user_database_env": res["user_database_env"],
                    "answer_SQL": res["generated_query"],
                    "answer_explanation": res["messages"][-1].content,
                    "question_refined": refined_input_content,
                    "searched_tables": res["searched_tables"],
                }
            )
        result["answers"] = answers

        save_answer_json(result, "data/eval_result", i)


if __name__ == "__main__":
    # graph = load_graph()

    # graph = builder.compile() # 예시
    graph = ""  # langgraph 모델 load하여 사용하세요

    get_eval_result(graph)
