# HPE NumPy 피처 계산

`pose_predictions.json`의 Halpe-26 포즈를 NumPy 배열로 변환하고, 제공된 PDF에 정리된 러닝 피처 18개를 계산한다. 기존 `scripts/features` 파일과 연결하지 않은 독립 패키지다.

## 제거 방법

이 구현이 만든 파일은 모두 `scripts/features/hpe_numpy_features` 안에만 있다. 되돌릴 때는 이 디렉터리만 삭제하면 되며, 기존 파일을 복원할 필요가 없다.

## 입력

기본 실행 함수는 run 디렉터리에서 다음 파일을 읽는다.

```text
run/test1/
└── outputs/
    ├── pose_predictions.json
    └── details.json
```

`details.json`에는 FPS와 사용자 신장이 있어야 한다. 신장은 아래 키 중 하나를 루트 또는 `runner`, `user`, `profile`, `athlete`, `subject` 객체에 둘 수 있다.

```json
{
  "runner": {"height_cm": 173},
  "video": {"fps": 25.0}
}
```

지원 신장 키는 `height_cm`, `user_height_cm`, `height_m`, `user_height_m`이다. 영상의 픽셀 높이인 `video.height`는 사용자 신장으로 사용하지 않는다.

## 사용법

`PoC` 디렉터리에서 다음과 같이 호출한다.

```python
from scripts.features.hpe_numpy_features.pose_features import extract_features_from_run

features = extract_features_from_run("run/test1")
```

아직 run 메타데이터에 신장이 기록되지 않았다면 기존 파일을 수정하지 않고 호출 인자로 전달할 수 있다.

```python
features = extract_features_from_run(
    "run/test1",
    user_height_m=1.73,
)
```

측정값을 직접 전달하고 중간 NumPy 데이터에 접근하려면 다음 두 단계를 사용한다.

```python
from scripts.features.hpe_numpy_features.pose_features import (
    calculate_features,
    load_pose_sequence,
)

pose = load_pose_sequence(
    "run/test1/outputs/pose_predictions.json",
    user_height_m=1.73,
)
features = calculate_features(pose, fps=25.0, direction=-1)

print(pose.coordinates.shape)  # (frame_count, 26, 2)
print(features)
```

`direction=1`은 화면 오른쪽, `direction=-1`은 화면 왼쪽 진행이다. 생략하면 코와 목의 수평 위치로 바라보는 방향을 추정하고, 판단할 수 없으면 골반 이동 방향을 사용한다.

## NumPy 변환과 정규화

한 프레임에서 `track_id == 0`인 사람만 선택한다. 좌표 선택 순서는 다음과 같다.

1. `observed`가 참이면 `keypoints` 사용
2. 미관측이고 `imputed_keypoints`가 있으면 보간 좌표 사용
3. 둘 다 없으면 `NaN` 사용

주요 배열은 다음과 같다.

- `coordinates_px`: 원본 또는 보간된 픽셀 좌표, `(F, 26, 2)`
- `coordinates`: 골반 원점·신장 단위 정규화 좌표, `(F, 26, 2)`
- `scores`: 키포인트 신뢰도, `(F, 26)`
- `observed`: 직접 관측 여부, `(F, 26)`
- `bboxes`: 사람 영역, `(F, 4)`

정규화 과정은 다음과 같다.

```text
pelvis_center = (left_hip + right_hip) / 2
stature_px = head-neck + neck-pelvis + mean(left_leg, right_leg)
normalized_point = (point_px - pelvis_center_px) / stature_px
```

따라서 골반 중심은 매 프레임 `(0, 0)`이고 사용자 신장은 `1.0`이다. 미터 거리 피처는 `정규화 거리 × user_height_m`으로 계산한다. 한쪽 다리가 누락되면 반대쪽 다리를 사용하며, 신장 추정 자체가 불가능한 프레임은 bbox 높이를 보조값으로 사용한다.

## 착지와 입각기 검출

각 발의 발목·엄지발가락·새끼발가락·뒤꿈치 y 좌표 평균을 발 높이 신호로 사용한다. 영상 좌표에서 아래쪽일수록 y가 크므로, 평활화된 신호의 국소 최댓값을 initial contact로 본다. 같은 발의 두 접촉은 좌우 두 스텝을 사이에 두므로 최소 간격을 `2 × min_step_seconds`로 제한한다. 접촉점 주변에서 발 높이가 유지되는 연속 구간을 입각기로 사용한다.

이 검출은 힘판을 사용한 실제 지면 접촉 측정이 아니라 2D HPE 기반 추정이다.

## 계산 피처

| 피처 | 계산 | 단위 |
|---|---|---|
| `postural_lean_deg` | initial contact에서 지지 발목→양어깨 중심선과 수직선의 진행 방향 기준 각도 평균 | deg |
| `torso_flexion_deg` | 골반 중심→양어깨 중심선과 수직선의 진행 방향 기준 각도 평균 | deg |
| `lean_variability_deg` | 각 initial contact의 `postural_lean_deg` 표준편차 | deg |
| `pelvis_to_ankle_ap_distance` | initial contact에서 골반 중심과 지지 발목의 수평거리 평균 | m |
| `peak_knee_flexion_stance_deg` | 각 입각기에서 `180° - hip-knee-ankle 내각`의 최댓값을 구한 뒤 평균 | deg |
| `tibia_angle_deg` | initial contact에서 정강이와 수평선이 이루는 진행 방향 기준 각도. 수직 정강이는 90° | deg |
| `hip_extension_late_stance_deg` | 입각기 마지막 1/3에서 `180° - shoulder-hip-knee 내각`의 최댓값 평균 | deg |
| `heel_to_com_ap_distance` | initial contact에서 뒤꿈치와 골반 중심(COM 근사)의 수평거리 평균 | m |
| `overstride_asymmetry_pct` | 좌우 `pelvis_to_ankle` 평균거리의 비대칭률 | % |
| `knee_flexion_at_ic_deg` | initial contact에서 착지측 무릎 굴곡각 평균 | deg |
| `max_knee_flexion_stance_deg` | 입각기 최대 무릎 굴곡각. `peak_knee_flexion_stance_deg`와 같은 측정값 | deg |
| `knee_flexion_excursion_deg` | 입각기 최대 무릎 굴곡각 - initial contact 무릎 굴곡각 | deg |
| `foot_inclination_at_ic_deg` | initial contact에서 뒤꿈치→두 발가락 중심선과 수평선의 각도 | deg |
| `cadence_spm` | 전체 initial contact 수 / 영상 시간 × 60 | steps/min |
| `step_time_asymmetry_pct` | 교대 접촉 간격을 도착 발별로 평균한 뒤 계산한 좌우 비대칭률 | % |
| `estimated_stance_time_asymmetry_pct` | 좌우 평균 입각시간의 비대칭률 | % |
| `knee_rom_asymmetry_pct` | 같은 발의 연속 접촉 사이 무릎 굴곡각 범위(max-min)의 좌우 비대칭률 | % |
| `elbow_angle_rom_deg` | 좌우 `180° - shoulder-elbow-wrist 내각` 범위(max-min)의 평균 | deg |

모든 비대칭률은 다음 공식을 사용한다.

```text
abs(left - right) / ((abs(left) + abs(right)) / 2) * 100
```

두 값이 모두 0이면 비대칭률도 0으로 처리한다. 계산에 필요한 좌표나 이벤트가 없으면 해당 값은 `NaN`이다.

## 범위와 한계

- PDF의 참고 범위를 이용한 정상·비정상 판정이나 코칭 문구 생성은 포함하지 않는다.
- 신장 기반 환산은 카메라 원근과 관절 가림의 영향을 받으므로 실제 캘리브레이션 거리보다 정확도가 낮다.
- COM은 별도의 신체분절 모델 없이 양쪽 골반 중심으로 근사한다.
- 측면 2D 좌표만 사용하므로 카메라 회전, 사선 촬영, 깊이 방향 움직임은 보정하지 않는다.
- 결과는 러닝 자세 참고값이며 의료 진단값이 아니다.

## 테스트

프로젝트 루트에서 실행한다.

```bash
PYTHONPATH=PoC/scripts/features .venv/bin/python -m unittest discover \
  -s PoC/scripts/features/hpe_numpy_features/tests -v
```
