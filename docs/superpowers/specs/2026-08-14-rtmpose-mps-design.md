# RTMPose MPS 실행 환경 설계

## 목표

프로젝트 루트의 독립 폴더 `RTMPose-MPS/`에 Apple Silicon MPS용 RTMDet-nano + RTMPose-M 실행 환경을 추가한다. 러닝 영상 프레임에서 얼굴 상세점 없이 COCO 17개 신체 관절을 추론하고, 기존 Sapiens2 환경과 출력물을 손상시키지 않는다.

## 선택한 접근

공식 OpenMMLab MMPose/MMDtection 저장소와 공개 설정·체크포인트를 사용한다. 검출기는 RTMDet-nano, 포즈 모델은 RTMPose-M (256×192, COCO 17 keypoints)으로 고정하고, `RTMPOSE_VARIANT=s` 환경 변수로 S 모델을 선택할 수 있게 한다.

Sapiens2의 `.venv-sapiens2`와 별도로 `RTMPose-MPS/.venv-rtmpose`를 둔다. 외부 저장소는 `RTMPose-MPS/mmpose`와 `RTMPose-MPS/mmdetection`에 고정 커밋으로 배치해 공식 프로젝트 구조와 재현성을 보존한다.

## 구성 요소와 데이터 흐름

1. 설치 스크립트는 고정된 upstream 소스를 준비하고 `.venv-rtmpose`에 MPS 호환 의존성을 설치한다.
2. 환경 점검 스크립트는 Python, PyTorch, MPS build/availability, MMPose·MMDetection import, 모델 파일을 확인한다.
3. 모델 다운로드 스크립트는 OpenMMLab의 공식 URL에서 RTMDet-nano와 RTMPose-M/S 가중치를 `RTMPose-MPS/models/` 아래에 저장한다.
4. 실행 스크립트는 이미지 디렉터리를 받아 MPS에서 top-down pose inference를 수행하고, 시각화와 `pose_predictions.json`을 `RTMPose-MPS/outputs/pose/`에 작성한다. JSON은 image path, bbox, bbox score, COCO 17 keypoints, keypoint scores를 포함한다.
5. 프레임 순서가 있는 입력에서는 bounding-box IoU 기반 단일 track id를 함께 기록한다. 검출·관절 confidence가 임계값 아래일 때에는 해당 점을 `observed: false`로 표시하며, 이전 유효 관절의 위치를 `imputed_keypoints`에 별도로 보관한다. 원본 모델 예측은 덮어쓰지 않는다.

## 오류 처리

- 입력 디렉터리, 가상환경, upstream 체크아웃, 가중치가 없으면 실제 실행 전에 정확한 경로와 해결 스크립트를 출력하고 실패한다.
- MPS가 build 또는 runtime에서 사용할 수 없으면 CPU로 조용히 전환하지 않고, 기본값 `RTMPOSE_DEVICE=auto`에서 명확한 오류를 낸다. CPU 실행은 사용자가 `RTMPOSE_DEVICE=cpu`로 명시한 경우에만 허용한다.
- 사람 검출이 없는 프레임은 빈 people 배열을 JSON에 유지한다.

## 검증

- 셸 스크립트 dry-run 테스트로 모델/장치/경로/환경 변수 선택을 검증한다.
- Python 단위 테스트로 17-point JSON 직렬화, track id 부여, 저신뢰 관절 보간 메타데이터를 검증한다.
- 실제 MPS 스모크 테스트는 공식 MMPose demo 이미지에서 17개 관절과 출력 JSON을 확인한다.

## 비목표

- Sapiens2 파일·환경·출력을 수정하거나 제거하지 않는다.
- 얼굴, 손, 전신 133/308 keypoint 추론은 추가하지 않는다.
- 완전히 가려진 사람의 실제 자세를 결정론적으로 복원한다고 주장하지 않는다. 보간 결과는 모델 관측값과 분리된 추정치다.
