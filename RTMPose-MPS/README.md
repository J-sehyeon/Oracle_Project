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

## 모델 출처

- [MMPose RTMPose 공식 데모](https://mmpose.readthedocs.io/en/latest/demos.html)
- [MMPose 설치 문서](https://mmpose.readthedocs.io/en/latest/installation.html)
