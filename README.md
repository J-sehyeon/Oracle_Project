## PoC 디렉토리 구조

```markdown
PoC/
├── .venv/
├── models/                   # 사용하는 모델의 정보와 onnx 저장 루트
│		├── detectors
│		│ 	└── end2end.onnx      # 사람의 bounding box 추론 모델
│		└── pose
│				└── end2end.onnx      # bbox에서 HPE 추론 모델
├── runs/                     # 파이프라인의 데이터가 저장되는 루트
│		└── test1/                # 케이스별 격리
│		    ├── input.mp4         # 원본 영상
│		    ├── inputs/           # 원본 영상의 프레임(이미지)이 저장되는 루트
│		    │   ├── 00000001.png
│		    │   └── 00000500.png
│		    └── outputs/          # 파이프라인의 산출물 저장 루트
│		        ├── pose_predictions.json # HPE 데이터
│		        ├── details.json  # 해당 케이스의 상세 정보
│		        ├── rendered/     # 스켈레톤이 렌더링된 이미지
│		        │   ├── 00000001.png
│		        │   └── 00000500.png
│		        ├── rendered.mp4. # 스켈레톤이 렌더링된 영상
│           ├── feature_results.json  # 논문과 데이터 기반 피쳐 추출 결과
│           └── running_report.md     # agent가 생성한 보고서
├── scripts/
│		├── main.sh               # 전체 파이프라인 실행 쉘 스크립트
│		├── hpe/
│		│		├── run_main.sh           # HPE 파이프라인 실행 쉘
│		│		├── extract_frames.py     # details.json, inputs/ 생성
│		│		├── hpe_model.py          # pose_predictions.json 생성
│		│		├── pose_track.py         # 모델의 출력 보조
│		│		├── render.py             # rendered/ 생성
│		│		└── compose_video.py      # rendered.mp4 생성
│		│
│		├── features/
│		│		├── features.sh           # features 추출 실행 스크립트
│   │   ├── papers.py             # 논문 저장 파일
│		│		└── feature_extract.py
│		└── Agent/
│				├── agent.sh              # agent 실행 스크립트
│       ├── prompts.py            # agent prompt 저장
│				└── Running_coach.py
│
└── README.md
```

## PoC의 파이프라인 실행 순서

### 셀 스크립트 실행 순서

`main.sh` : 파이프라인 전체 실행 스크립트. `hpe.sh, features.sh, agent.sh` 세 개의 스크립트를 순차적으로 실행한다.

```bash
./scripts/main.sh test1 --extract --device cpu
```

### HPE 파이프라인

#### Step1

최초 실행 전에 `run/` 하위에 **실행할 폴더**(`test1` 이라 하자.)를 생성한다.
그 폴더 내부에 **분석하고자 하는 영상**을 담기만 하면 준비는 끝난다.
단 `run/` 외의 폴더들은 위와 같은 상태이어야 한다.

#### Step2

```bash
cd PoC
scripts/run_main.sh test1 --extract --device cpu
```

위 명령어를 통해 파이프라인의 전체 과정을 실행시킨다.

`scripts/run_main.sh` : 실행할 쉘
`test1` : 파이프라인 산출물 저장 루트 지정
`--extract` : 비디오에서 영상 추출 여부
`—device cpu` : 디바이스 설정. cpu, cuda, mps 총 3개의 선택지 존재.

#### Step3

run_main.sh의 실행 순서

1. 영상에서 이미지 추출 + detail.json 작성
2. HPE모델 실행 → pose_predictions.json 생성
3. HPE데이터를 inputs 이미지 위에 렌더링하여 `rendered/` 생성
4. `rendered/` 와 detail.json을 사용해 rendered.mp4 생성

---

### Features 파이프라인

#### Step1

feature_extract.py 내부에서 features를 추출하여 `feature_results.json` 을 생성한다.

```json
{
  "feature1": 2.89
}
```

---

### Agent 파이프라인

#### Step1

`features/` 에서 각 피쳐별 논문 근거를 불러와 `paper_evidence`를 생성한다.
그리고 사용자의 피쳐값과 논문 근거를 입력으로 받는 프롬프트를 생성하고 chain을 만든다.

#### Step2

invoke 하여서 `running_report.md` 생성

---