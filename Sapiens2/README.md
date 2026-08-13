# Sapiens2 on Apple Silicon

이 프로젝트 루트에는 Meta의 공식 [Sapiens2](https://github.com/facebookresearch/sapiens2) 포즈 추론 환경이 구성되어 있다. 기본 모델은 공개 포즈 모델 중 가장 작은 **Sapiens2-0.4B**이며, Apple Metal(MPS)에서 원본 **FP32** 체크포인트를 그대로 실행한다.

## 현재 구성

| 항목 | 값 |
|---|---|
| Mac 실행 장치 | Apple MPS, 미지원 연산만 CPU fallback |
| Python | 3.12.12 (`.venv-sapiens2`) |
| PyTorch | 2.13.0 |
| Sapiens2 upstream | `7e5bae88456ac418ff0e58e74106c9fe192055d4` |
| 포즈 모델 | `facebook/sapiens2-pose-0.4b` / 308 keypoints |
| 사람 검출기 | `facebook/detr-resnet-101-dc5` |
| 체크포인트 정밀도 | 포즈: FP32 424 tensors, DETR: FP32 785 tensors + 정상 I64 BatchNorm counters 4개 |

Sapiens2-0.4B의 공식 입력 해상도는 1024×768(H×W), 파라미터 수는 약 3.98억 개다. 0.1B는 포즈 체크포인트가 공개되지 않았기 때문에 0.4B가 현재 사용할 수 있는 최소 포즈 모델이다.

## 바로 실행

환경과 파일을 먼저 확인한다.

```bash
./scripts/check_sapiens2_environment.sh
```

이미지가 들어 있는 디렉터리를 넘겨 포즈 추론을 실행한다.

```bash
./scripts/run_sapiens2_pose.sh /absolute/path/to/images
```

출력 위치를 지정하려면 두 번째 인자를 사용한다.

```bash
./scripts/run_sapiens2_pose.sh /absolute/path/to/images /absolute/path/to/output
```

장치를 명시할 수도 있다. `auto`가 기본값이며 MPS를 우선 선택한다.

```bash
SAPIENS2_DEVICE=mps ./scripts/run_sapiens2_pose.sh /absolute/path/to/images
SAPIENS2_DEVICE=cpu ./scripts/run_sapiens2_pose.sh /absolute/path/to/images
```

기본 출력은 `outputs/sapiens2/pose/`에 저장된다. 입력 이미지별 시각화 PNG/JPEG와 `pose_predictions.json`에 bbox, 308개 좌표, 308개 점수가 기록된다.

## 러닝 피처 추출

`filter_to_coco17.py`가 만든 `sapiens2_body18_v1` 좌표 JSON에서 12개 러닝 피처를 계산한다. 기본 FPS는 25이며, 결과에는 IC/TO 검출 프레임도 포함돼 결과를 검토할 수 있다.

```bash
./.venv-sapiens2/bin/python scripts/running_features.py \
  --input-json outputs/test1_coco17_frames/coco17_predictions.json \
  --output-json outputs/test1_running_features.json \
  --fps 25
```

실측 길이 보정값이 없으므로 수직 동요(FEAT-06)와 오버스트라이드(FEAT-08)는 `% body_reference` 단위다. 이는 어깨 중심→골반 중심과 양 다리 길이로 만든 영상별 기준 길이에 대한 비율이다. 선택적으로 `--height-cm 175`를 주면 같은 비율을 신장에 비례해 환산한 `estimated_cm`도 출력한다. 이 값은 카메라 캘리브레이션 기반 실측 cm가 아니라 근사치다.

FEAT-12(VLR)는 force plate의 지면반발력 데이터가 필요하므로 포즈 좌표만으로는 `null`로 반환된다.

## 모델 다시 받기

```bash
./scripts/download_sapiens2_models.sh
```

다운로드 스크립트는 Hugging Face의 Meta 공식 저장소만 사용한다. 다운로드 후 전체 가중치를 메모리에 적재하지 않고 `safetensors` 헤더를 검사하며, weight/bias에 정수형 또는 저비트 dtype이 있으면 실패한다. BatchNorm의 정상적인 `num_batches_tracked` I64 카운터만 예외다.

## 양자화 정책

이 환경에서는 양자화를 사용하지 않는다.

- 포즈 모델은 공식 FP32 파일(`sapiens2_0.4b_pose.safetensors`)을 사용한다.
- FP16/BF16 자동 캐스팅도 기본으로 켜지 않는다.
- 저비트 로더나 비공식 변환 체크포인트를 설치하지 않는다.
- 48GB 통합 메모리에서는 0.4B FP32가 안전한 시작점이다. 가중치 파일은 약 1.6GB지만, DETR와 중간 activation 때문에 실제 사용량은 더 크다.

정밀도를 바꾸고 싶다면 먼저 별도 품질 평가를 만든 뒤 opt-in 방식으로 추가해야 한다. 포즈의 작은 관절·얼굴·손 키포인트는 양자화 오차에 특히 민감할 수 있다.

## 환경 재구축

현재 환경을 지우지 않고 재현할 때 사용할 명령은 다음과 같다. `uv`가 설치되어 있어야 한다.

```bash
git clone https://github.com/facebookresearch/sapiens2.git
git -C sapiens2 checkout 7e5bae88456ac418ff0e58e74106c9fe192055d4
uv venv --python 3.12 .venv-sapiens2
UV_CACHE_DIR="$PWD/.cache/uv" uv pip install \
  --python .venv-sapiens2/bin/python \
  -e ./sapiens2 pytest huggingface_hub
./scripts/download_sapiens2_models.sh
```

## 확인된 스모크 테스트

공식 데모 이미지 `sapiens2/demo/data/000017.png`를 MPS에서 실행해 다음을 확인했다.

- 사람 1명 검출
- 308개 keypoints 및 308개 confidence scores 생성
- 결과 이미지: `outputs/sapiens2/smoke/000017.png`
- 결과 JSON: `outputs/sapiens2/smoke/smoke_predictions.json`

초기 모델 로딩 이후 해당 이미지의 추론 진행 구간은 약 3.85초였다. 실행 환경과 입력에 따라 달라질 수 있다.

## 라이선스 주의

Sapiens2는 일반적인 오픈소스 라이선스가 아니라 별도의 `Sapiens2 License`를 사용한다. 특히 감시, 생체정보 처리, 개인 식별·재식별, 적법한 권리·동의 없는 건강/민감정보 추론, 무허가 의료·전문 업무 등의 사용을 금지한다. 제품 적용 전 반드시 [공식 라이선스](sapiens2/LICENSE.md) 전문을 검토해야 한다.
