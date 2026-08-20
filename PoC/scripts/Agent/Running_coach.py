from dotenv import load_dotenv
import os
import argparse

import json
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

parser = argparse.ArgumentParser()
parser.add_argument("project_dir", type=Path)
parser.add_argument("run_folder", type=str)
args = parser.parse_args()

PROJECT_DIR = args.project_dir
RUN_FOLDER = args.run_folder
RUN_DIR = PROJECT_DIR / "PoC" / "run" / RUN_FOLDER

load_dotenv(PROJECT_DIR / ".env")
api_key = os.environ.get("_OPENAI_API_KEY")




def main(features_path: Path):
    # 1. feature_extract 결과
    with open(features_path, "r", encoding="utf-8") as file:
        features = json.load(file)


    # 2. 관련 논문에서 미리 정리한 근거
    paper_evidence = """
논문 참고값:
- 직립 자세: 1.7±0.7°
- 적당한 전경사: 4.3±0.8°
- 큰 전경사: 평균 8.2°, 범위 6.1–11.5°

판단 원칙:
- 1.7°에 가까우면 직립 자세
- 4.3°에 가까우면 적당한 전경사
- 6.1° 이상이면 큰 전경사 가능성
- 11.5°를 넘으면 논문에서 관찰된 최대 범위를 초과했다고 표시
- 음수이면 진행 방향 반대쪽으로 기울어진 후경사로 해석
- 경계값은 정상·비정상으로 단정하지 말고 가장 가까운 참고 조건으로 설명
- 큰 전경사는 러닝 경제성 저하와 둔근·햄스트링 부담 증가 가능성을 안내
- 이 값 하나만으로 발목 중심 전경사인지 허리 중심 전경사인지, 또는 부상 위험이 있는지는 판단하지 말 것

다음 형식으로 3문장 이내로 답하라.

1. 자세 분류: 직립 / 적당한 전경사 / 큰 전경사 / 연구 범위 밖
2. 해석: 논문 참고값과 비교한 의미
3. 코칭: 유지 또는 전경사를 조금 줄이거나 늘리는 짧고 실행 가능한 조언
"""


    # 3. 프롬프트
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            당신은 러닝 자세 분석 리포트를 작성하는 AI입니다.

            제공된 피처값과 논문 근거만 사용하세요.
            이상 구간, 판단 근거, 개선 피드백을 작성하세요.
            논문에서 확인되지 않은 내용은 만들지 마세요.
            의학적 진단은 하지 마세요.
            """,
        ),
        (
            "human",
            """
            [피처값]
            {features}

            [논문 근거]
            {paper_evidence}

            위 자료를 바탕으로 러닝 자세 분석 리포트를 작성하세요.
            """,
        ),
    ])


    # 4. LLM
    model = ChatOpenAI(
        model="gpt-5-nano",
        temperature=0,
        api_key=api_key
    )


    # 5. LangChain 구성
    chain = prompt | model | StrOutputParser()


    # 6. 실행
    report = chain.invoke({
        "features": json.dumps(
            features,
            ensure_ascii=False,
            indent=2,
        ),
        "paper_evidence": paper_evidence,
    })


    # 7. 결과 저장
    with open(features_path.parent / "running_report.md", "w", encoding="utf-8") as file:
        file.write(report)

    print(report)

if __name__ == "__main__":
    features_path = RUN_DIR / "outputs" / "feature_results.json"
    main(features_path)