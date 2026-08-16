# RTMPose on Apple Silicon MPS

이 폴더는 기존 `Sapiens2/`와 독립된 RTMPose 실행 환경이다. 기본 조합은 사람 검출용 **RTMDet-nano**와 COCO 17개 신체 관절용 **RTMPose-M**(256×192)이다. 얼굴·손의 상세 keypoint는 출력하지 않는다.

## 구성

| 항목 | 값 |
| --- | --- |
| 실행 장치 | Apple Metal Performance Shaders (MPS) |
| 검출 모델 | RTMDet-nano person, OpenMMLab 공식 checkpoint |
| 포즈 모델 | RTMPose-M, COCO 17 body keypoints, 256×192 |
| 대안 포즈 모델 | `RTMPOSE_VARIANT=s`의 RTMPose-S |
| MMPose upstream | `v1.3.2` |
| MMDetection upstream | `v3.2.0` |

`auto` 장치는 MPS를 반드시 요구한다. CPU 실행은 `RTMPOSE_DEVICE=cpu`를 명시했을 때만 허용한다.

## 설치와 모델 다운로드

```bash
./scripts/install_rtmpose_mps.sh
./scripts/download_rtmpose_models.sh
./scripts/check_rtmpose_environment.sh
```

공식 MMPose의 설치 관계(MMPose 1.x, MMDetection 3.x, MMCV 2.x)를 유지한다. upstream clone과 모델 파일은 이 저장소에 커밋되지 않는다.

## 실행

```bash
./scripts/run_rtmpose_pose.sh /absolute/path/to/images
./scripts/run_rtmpose_pose.sh /absolute/path/to/images /absolute/path/to/output
RTMPOSE_VARIANT=s ./scripts/run_rtmpose_pose.sh /absolute/path/to/images
```

기본 출력은 `outputs/pose/`다. `pose_predictions.json`에는 프레임별 사람 bbox, 17개 원본 keypoint, score, 관측 여부, 가림/저신뢰 시 별도 추정한 keypoint, track id가 기록된다. `imputed_keypoints`는 원본 모델 예측을 수정하지 않는다.

## 예측 결과를 원본 이미지에 그리기

프로젝트의 `RTMPose-MPS` 폴더에서 다음 명령을 실행한다.

```bash
.venv-rtmpose/bin/python scripts/render_pose_predictions.py \
  outputs/test1/pose_predictions.json \
  inputs/videos/test1/frames \
  outputs/test1/rendered
```

세 인자는 순서대로 `pose_predictions.json`, 원본 이미지 폴더, 출력 이미지 폴더다. JSON의 `frames[].image_path`에서 파일명만 가져와 원본 이미지 폴더에서 같은 이름의 파일을 찾는다. 출력 이미지는 원본과 같은 파일명·해상도·확장자로 저장한다.

- 초록색 점과 선: 현재 프레임에서 관측된 keypoint
- 주황색 점과 선: `imputed_keypoints`로 보정된 가림 또는 저신뢰 keypoint
- 점이 없는 관절: 관측값과 보정값이 모두 없는 keypoint

### `render_pose_predictions.py` 로직

| 코드 | 역할 |
| --- | --- |
| `parse_args()` | JSON 파일, 원본 이미지 폴더, 출력 폴더의 세 CLI 인자를 읽는다. |
| `select_draw_points(person)` | 각 관절에서 `observed`가 참이고 score가 유효한 숫자이면 원본 keypoint를 선택한다. 아니면 `imputed_keypoints`를 선택하고, 둘 다 없으면 그리지 않는다. |
| `draw_person(image, person)` | COCO-17 골격선을 먼저 그리고 관절점을 그린다. 보정점이 포함된 골격선은 주황색으로 표시한다. |
| `render_predictions(...)` | JSON을 읽고 프레임별 원본 이미지를 찾아 모든 사람의 pose를 적용한 뒤 같은 이름으로 저장한다. |
| `main()` | 렌더링을 실행하고 처리한 이미지 수와 출력 폴더를 표시한다. 오류가 나면 문제가 된 경로를 출력한다. |

이 렌더러는 RTMDet·RTMPose 모델을 다시 불러오지 않는다. 이미 생성된 JSON을 OpenCV로 시각화만 하므로 MPS 설정과 무관하게 실행할 수 있다.

## 모델 출처

- [MMPose RTMPose 공식 데모](https://mmpose.readthedocs.io/en/latest/demos.html)
- [MMPose 설치 문서](https://mmpose.readthedocs.io/en/latest/installation.html)
