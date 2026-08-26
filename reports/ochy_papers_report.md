# Ochy 관련 논문 6편 분석과 Halpe26 기반 프로젝트 적용 보고서

작성일: 2026-08-25  
분석 범위: 사용자가 제공한 로컬 PDF 6편과 `/Users/hyeon/SeSAC_Project`의 현재 코드·문서  
외부 웹 검증: 수행하지 않음

## 0. 읽는 방법과 근거 수준

이 보고서는 다음 표기를 사용한다.

- **논문 사실**: 해당 문헌의 방법, 결과, 저자가 직접 제시한 해석이다.
- **프로젝트 해석**: 논문 사실을 현재 프로젝트의 Halpe26 2D HPE 파이프라인에 연결한 판단이다.
- **가능**: Halpe26 관절점과 영상 FPS만으로 정의에 가깝게 계산할 수 있다.
- **조건부 가능**: 계산은 가능하지만 카메라 시점, 보정, 보행 이벤트 검출, COM 근사 등의 추가 가정이 필요하다.
- **불가**: 2D HPE만으로 논문의 원래 정의를 재현할 수 없다. 힘판, 호흡가스, EMG, 3D 좌표 등의 별도 센서가 필요하다.

중요한 전제는 **HPE로 어떤 수치를 계산할 수 있다는 것과 그 수치로 좋고 나쁨을 판정할 수 있다는 것은 별개**라는 점이다. 특히 접지시간, 몸통 기울기, 착지 유형은 문헌 안에서도 상충하거나 제한된 근거로 분류된다(S2, pp. 3–5, 8–11; S4, pp. 5–8).

## 1. 요약 결론

### 1.1 Ochy의 목적

**명시된 목적**은 스마트폰 수준의 단일 60 Hz 측면 영상에서 러닝의 시공간 피처와 관절각을 추정하고, 범용 자세 모델보다 러닝 전용 모델이 더 정확하고 견고한지를 검증하는 것이다. Ochy 검증 보고서는 step frequency, ground contact time, swing time과 hip, knee, ankle, elbow 굴곡·신전각을 marker-based motion capture와 비교했다(S3, pp. 2–5).

**방향성에 대한 프로젝트 해석**은 다음과 같다.

1. 고가의 실험실 장비를 대체하거나 보완하는 **접근 가능한 현장형 러닝 분석**을 지향한다.
2. 범용 HPE보다 **러닝에 특화된 학습 데이터와 모델**을 중시한다.
3. 평균 오차뿐 아니라 leg swapping, 좌우 혼동, 누락처럼 자동화 확장성을 해치는 **실패율과 견고성**을 중요한 품질로 본다.
4. “이상적인 단일 자세”를 강제하기보다는 속도와 개인별 패턴을 포함하는 **맥락 기반 피드백**이 문헌 전체의 방향과 더 잘 맞는다.

1–3은 Ochy 보고서의 문제 설정과 논의에서 직접 도출되며, 4는 S2와 S4를 함께 읽은 해석이다.

### 1.2 가장 중요한 인사이트

- Ochy가 가장 강하게 검증한 값은 **step frequency**와 **knee angle**이다. Ochy의 step frequency ICC는 0.972, knee angle ICC는 0.79였다. 반면 swing time ICC는 0.332, ankle angle ICC는 0.16, elbow angle ICC는 0.11로 낮았다(S3, pp. 7–10).
- 60 Hz 영상에서 시간 이벤트 오차는 대략 1–2 프레임만 발생해도 GCT와 swing time에 큰 비율 오차를 만든다. Ochy의 GCT MAE 0.030 s는 약 1.8프레임이고, swing time MAE 0.032 s는 약 1.9프레임이다(S3, pp. 6–7, 13).
- Fellin 등은 force plate 없이 footstrike를 찾을 때 heel의 최소 수직 위치 또는 수직속도 부호 변화가 가장 일관됐고, toe-off에는 peak knee extension이 가장 정확했다고 보고했다. 그러나 footstrike는 약 22.4–24.6 ms 늦게 잡히는 체계적 오프셋이 있었다(S5, pp. 4–6).
- 경제성은 단일 피처로 설명되지 않는다. Moore의 리뷰는 GCT, swing time, trunk lean을 상충 근거로 분류했고, 일반적 경제적 자세 처방을 주의해야 한다고 결론냈다(S2, pp. 10–11).
- Lussiana 등은 짧은 접지시간을 가진 그룹과 긴 접지시간을 가진 그룹이 서로 다른 역학을 보였지만 10–14 km/h에서 에너지 비용은 유의하게 다르지 않았다고 보고했다. 즉 “접지시간은 짧을수록 좋다”는 규칙은 이 논문과 맞지 않는다(S4, pp. 4–8).
- Folland 등은 97명의 이질적 러너에서 기술 변수가 running economy 변동의 39%, 경기력 변동의 31%를 설명했다고 보고했다. 하지만 횡단면 상관 연구이므로 개인에게 같은 방향의 개입 효과를 보장하지 않는다(S6, pp. 7–11).
- 따라서 제품은 절대적인 좋음/나쁨 판정보다 **측정 신뢰도 → 속도·환경 맥락 → 개인의 반복 측정 변화 → 제한된 코칭 가설** 순으로 제시하는 것이 안전하다.

## 2. Ochy 서비스의 목적, 마인드, 방향성

### 2.1 서비스가 해결하려는 문제

전통적 marker-based motion capture는 정확하지만 비싸고, 설치 시간이 길며, 실험실에 묶여 있다. Ochy는 스마트폰 수준의 단일 카메라로 이 장벽을 낮추려 한다(S3, p. 3). 제품 관점에서 이는 다음 흐름이다.

```text
일반 영상 촬영
  → 러닝 전용 2D pose 추정
  → gait event와 관절각 계산
  → 실험실 장비 대비 오차·일치도 검증
  → 코치와 러너가 현장에서 사용할 수 있는 피드백
```

### 2.2 Ochy가 품질을 보는 방식

Ochy 보고서의 검증 기준은 세 층으로 나뉜다.

| 품질 층 | 검증 내용 | 제품 의미 |
|---|---|---|
| 추적 견고성 | 좌우 다리 뒤바뀜, 관절 오인식, 누락 | 자동 분석 성공률 |
| 시간 피처 정확도 | step frequency, GCT, swing time의 MAE·ICC·Bland–Altman | gait event 신뢰도 |
| 관절각 정확도 | hip, knee, ankle, elbow 각도의 frame-wise MAE·ICC | 자세 피드백 신뢰도 |

108개 trial 중 MediaPipe는 21개에서 하나 이상의 시공간 값을 계산하지 못했고 Ochy는 1개에서 실패했다. 이는 평균 정확도뿐 아니라 **분석 가능률**이 서비스 확장성의 핵심이라는 것을 보여준다(S3, pp. 6, 13).

### 2.3 Ochy의 마인드에 대한 해석

- **접근성**: 단일 카메라와 소비자용 프레임레이트를 의도적으로 사용한다.
- **도메인 특화**: 범용 모델의 성능 한계를 러닝 전용 데이터와 학습으로 해결하려 한다.
- **현장 타당성**: treadmill보다 어려운 overground 환경에서 검증했다.
- **자동화 우선**: 수동 관절 교정이나 손상된 구간 제거가 확장성을 떨어뜨린다고 본다.
- **검증 중심**: MAE뿐 아니라 ICC, Bland–Altman, 실패 사례를 함께 다룬다.

단, S3은 저자 이름과 학술지 출판 정보가 없는 Ochy 자체 2025년 보고서다. 표본도 9명으로 작다. 따라서 서비스 성능에 관한 유용한 1차 자료이지만, 독립 연구진의 동료평가 재현 검증과 같은 무게로 취급해서는 안 된다.

## 3. 논문별 리뷰

### S1. Skejø et al. (2021), *Running in circles: Describing running kinematics using Fourier series*

**의도와 실험**  
78명(남 48, 여 30; 아마추어부터 엘리트)이 treadmill에서 1.67–5.56 m/s로 수행한 285 trial을 9-camera 3D motion capture, 300 Hz로 기록했다. 104개 해부학적 관절각 중 독립적인 85개 각도에 대해 stride 주파수를 FFT로 찾고, 평균 stride를 Fourier series로 압축했다(S1, pp. 1–2).

**핵심 결과**  
5개 coefficient pair를 사용하면 85개 각도 모두 RMSD 0.5° 미만이었고 80/85개 각도에서 Pearson r > 0.99였다. 논문은 최소 5쌍을 권고한다. 이는 관절당 11개 계수와 기본주파수로 표현할 수 있어, 101점 time series보다 약 10배 작다고 계산했다(S1, pp. 3–4).

**핵심 피처**

- stride/fundamental frequency
- 관절각별 Fourier 상수항 `a0`
- 1–5차 cosine/sine 계수 `ai`, `bi`
- 근사 RMSD와 원 신호 상관계수

**Halpe26 추출 가능성**  
조건부 가능. Halpe26으로 만든 hip, knee, ankle, elbow 등의 2D 각도 시계열을 같은 발의 연속 접촉 사이로 분할한 뒤 5쌍 Fourier 계수를 계산할 수 있다. 다만 논문은 3D 85관절각 전체를 다뤘고 현재 프로젝트는 단일 측면 2D이므로 표현 대상이 훨씬 적다. 이 방법은 “좋은 자세” 피처라기보다 **주기 파형의 압축·비교 표현**이다.

**한계**

- treadmill, 3D marker 기반 결과라 overground 2D HPE에 그대로 동등하지 않다.
- 평균 stride로 압축하므로 stride-to-stride 변동과 비정상 이벤트를 지울 수 있다.
- 순수 kinematic 연구이며 kinetics에서는 미분 시 작은 오차가 증폭될 수 있다.
- 0.5°와 r > 0.99 임계값은 저자의 주관적 최소 중요 차이에 기반한다.

### S2. Moore (2016), *Is There an Economical Running Technique?*

**의도**  
running economy(RE)에 영향을 주는 수정 가능한 내적·외적 biomechanical factor, 훈련에 따른 변화, 일반적 경제적 자세를 처방할 수 있는지 검토한 리뷰다(S2, pp. 1–2).

**리뷰가 정리한 비교적 유리한 피처**

- 선호 stride length부터 최대 3% 짧은 범위
- 낮은 vertical oscillation
- 높은 leg stiffness
- 낮은 lower-limb moment of inertia
- toe-off에서 덜 신전된 다리
- 큰 stride angle
- propulsion에서 GRF와 leg axis 정렬
- 자연스러운 arm swing 유지
- propulsion의 낮은 lower-limb muscle activation
- 낮은 thigh agonist–antagonist coactivation
- firm하면서 compliant한 shoe–surface 상호작용, barefoot 또는 가벼운 신발(<440 g)

**상충·불충분 근거**

- 상충: GCT, swing time, impact force, anterior–posterior force, trunk lean, biarticular coactivation, orthotics
- 제한/불명: foot–CoM 수평거리, braking time, 접지 중 잃은 속도, impulse, swing-phase 동작, footstrike pattern, breast kinematics, vastus medialis preactivation

**의도에 대한 해석**  
이 리뷰의 핵심은 정답 자세 목록을 만드는 것이 아니라, 다양한 연구를 정리하면서 **일반 처방의 근거가 아직 약함**을 보여주는 것이다. 특히 서로 얽힌 변수를 따로 분석한 횡단면 연구와 짧은 개입 연구가 많아, 개인별·장기·통합 연구를 요구한다(S2, pp. 9–11).

**Halpe26 추출 가능성**

- 가능/조건부: stride rate, GCT, swing time, vertical pelvis oscillation, foot–pelvis 수평거리, toe-off의 knee/ankle/hip angle, stride angle 근사, arm swing ROM, trunk lean, footstrike angle.
- 불가: RE 자체, GRF와 impulse, leg stiffness의 원 정의, muscle activation/coactivation, lower-limb inertia, 신발·노면 물성.

**한계**

- 체계적 메타분석이 아니라 서술적 리뷰이며 변수마다 근거 품질과 대상군이 다르다.
- 집단 간 연관성을 개인의 교정 목표로 직접 바꾸기 어렵다.
- propulsion을 강조하지만 HPE만으로 GRF·근활성이라는 핵심 기전을 측정할 수 없다.

### S3. Ochy (2025), *Precision of a smartphone application to perform running form analysis*

**의도와 실험**  
건강한 recreational runner 9명(남 6, 여 3)이 overground에서 각 4회의 slow, comfortable, fast trial, 총 108 trial을 수행했다. reference는 23대 IR camera, 42 marker, 240 Hz motion capture와 500 Hz force plate였고, 입력 영상은 소비자 스마트폰을 대표하는 60 Hz 단일 sagittal view였다(S3, pp. 4–5).

**핵심 피처와 결과**

| 피처 | Ochy MAE | Ochy ICC/상관 | 해석 |
|---|---:|---:|---|
| Step frequency | 1.907 steps/min | ICC 0.972, r 0.972 | 가장 강한 시공간 결과 |
| GCT | 0.030 s | ICC 0.680, r 0.849 | 중간~좋은 일치, 약 2프레임 오차 |
| Swing time | 0.032 s | ICC 0.332, r 0.431 | 절대 일치는 낮음 |
| Knee angle | — | ICC 0.79 | 관절 중 가장 좋음 |
| Hip angle | — | ICC 0.48 | 낮음~중간 |
| Ankle angle | — | ICC 0.16 | 낮음 |
| Elbow angle | — | ICC 0.11 | 낮음 |

Ochy는 MediaPipe보다 모든 표의 MAE가 낮고, knee와 ankle MAE 차이는 통계적으로 유의했다. hip과 elbow의 model 효과는 유의하지 않았다(S3, pp. 7–11).

**Halpe26 추출 가능성**  
모든 평가 피처의 계산에 필요한 관절점은 Halpe26에 있다. 그러나 footstrike/toe-off는 힘판이 아니라 kinematic heuristic으로 추정해야 하며, ankle은 heel/toe의 가림·신발 대비에 민감하다. 현재 프로젝트에 가장 우선하여 이식할 값은 cadence와 knee-angle 기반 값이고, swing time·ankle·elbow는 낮은 confidence로 표시해야 한다.

**한계**

- 9명, 단일 연구, Ochy 자체 보고서이며 독립적 재현 검증이 아니다.
- 60 Hz는 빠른 foot event에 부족할 수 있다.
- overground 검출은 treadmill보다 불안정했다.
- camera calibration과 timing correction을 적용하지 않았다.
- 신발 색과 배경 대비가 heel/ankle/toe 검출에 영향을 줄 가능성이 관찰됐다.
- 관절각 전체 ICC 0.38은 “전체 관절이 임상급으로 정확하다”는 해석을 지지하지 않는다.

### S4. Lussiana et al. (2019), *The implications of time on the ground on running economy: less is not always better*

**의도와 실험**  
훈련된 러너 54명에서 duty factor(DF)를 측정한 후 극단의 40명, 즉 DF_low 20명과 DF_high 20명을 분석했다. 남녀는 각 그룹 12/8명이었다. treadmill 10, 12, 14 km/h에서 energy cost를, 10–18 km/h에서 200 Hz 3D kinematics를 측정했다(S4, pp. 2–4).

**핵심 피처**

- contact time `tc`, aerial time `ta`, swing time `ts`
- duty factor `DF = tc / (ts + tc)`
- 접지·공중기 내 COM 하강/상승 시간과 대칭성
- 전체·접지·공중기의 vertical COM displacement
- 접지 중 forward COM displacement
- energy cost(kcal·kg⁻¹·km⁻¹)

**핵심 결과**  
DF_low는 짧은 접지와 긴 공중기, 더 큰 수직 COM 이동, 더 대칭적인 step을 보였다. DF_high는 긴 접지, 짧은 공중기, 작은 수직 이동과 큰 전방 이동을 보였다. 그럼에도 10–14 km/h에서 두 그룹의 energy cost에는 유의한 차이가 없었다. 저자들은 elastic-energy 재사용형과 수직 일을 줄이는 전진형이라는 **서로 다른 두 경제적 전략**을 제안했다(S4, pp. 4–8).

**Halpe26 추출 가능성**

- 조건부 가능: `tc`, `ta`, `ts`, DF, pelvis를 COM proxy로 둔 수직·수평 변위, phase symmetry.
- 불가: energy cost와 실제 elastic energy.

**한계**

- DF 연구가 적고 신발을 통제하지 않았다.
- segment inertia는 개인 MRI가 아닌 표준 회귀식이었다.
- biomechanics만으로 elastic energy 저장·반환을 직접 증명하지 않았다.
- 극단 그룹 비교이므로 연속적인 개인 변화나 교정의 인과를 보여주지 않는다.

### S5. Fellin et al. (2010), *Comparison of methods for kinematic identification of footstrike and toe-off during overground and treadmill running*

**의도와 실험**  
recreational rearfoot striker 40명(남 20)을 overground 20명, treadmill 20명으로 나누어 모두 3.35 m/s에서 달리게 했다. 120 Hz 또는 200 Hz 3D motion capture의 다섯 kinematic event method를 20 N vGRF threshold와 비교했다(S5, pp. 1–3).

**비교한 이벤트 피처**

1. Peak knee extension
2. Heel/toe minimum vertical position
3. Foot–sacrum AP displacement extrema
4. Heel/toe vertical velocity zero crossing
5. Foot/shank sagittal angular acceleration minima

**핵심 결과**

- footstrike: distal heel의 최소 수직 위치와 수직속도 음→양 변화가 가장 일관됐다. force 기준보다 22.4–24.6 ms 늦었다.
- toe-off: peak knee extension이 가장 정확했으며 overground 4.9 ms, treadmill 5.2 ms의 absolute error였다.
- 각가속도법은 일부 평균 오차가 작아도 변동성이 커서 부적절했다.
- treadmill이라고 event 오차의 표준편차가 체계적으로 작아지지는 않았다.

**Halpe26 추출 가능성**  
heel, toe, ankle, knee, hip이 모두 있어 구현 가능하다. 다만 2D HPE 좌표는 marker보다 노이즈가 크므로 미분 기반 속도·가속도는 특히 민감하다. 따라서 발 높이/수직속도 후보와 knee extension toe-off를 함께 사용하고, 이벤트별 confidence와 프레임 오차를 결과에 포함하는 편이 좋다.

**한계**

- 전원 rearfoot striker이고 속도가 3.35 m/s로 고정됐다.
- overground와 treadmill은 같은 사람이 아니며 sampling rate도 다르다.
- 3D marker 좌표의 결과를 2D markerless HPE에 직접 등치할 수 없다.
- 신발 압축 자체가 heel 기반 footstrike의 체계적 지연을 만들었다.

### S6. Folland et al. (2017), *Running Technique is an Important Component of Running Economy and Performance*

**의도와 실험**  
건강한 endurance runner 97명(여 47; elite 29, recreational 68)이 treadmill에서 단계적 속도로 달렸다. 10-camera 240 Hz 3D kinematics, respiratory gas, lactate turn point를 측정하고 10–12 km/h의 24개 kinematic variable과 running economy, 최근 12개월 season-best performance의 관계를 분석했다(S6, pp. 1–5).

**피처군**

- vertical oscillation: pelvis/whole-body COM, ground contact/whole stride
- braking: pelvis/COM 최소 AP 속도와 접지 중 속도 범위
- posture: pelvis transverse rotation, 평균·범위 trunk lean
- stride: normalized stride length, stride rate, GCT, swing time, DF
- lower limb: foot/shank/thigh touchdown angle, knee/hip stance ROM, stance·swing knee angle, swing hip angle

**핵심 결과**

- pelvis vertical oscillation during ground contact, minimum stance knee angle, minimum horizontal pelvis velocity가 RE 변동의 39.4%를 설명했다.
- shank touchdown angle, minimum horizontal pelvis velocity, DF, mean trunk lean이 performance 변동의 30.5%를 설명했다.
- 낮은 pelvis vertical oscillation과 적은 horizontal braking은 RE·vLTP·경기력과 일관되게 연결됐다.
- 짧은 GCT와 낮은 DF는 경기력과 관련됐지만 RE와는 관련되지 않았다.
- 더 짧은 normalized stride와 높은 stride rate는 더 좋은 RE와 관련됐다.

**Halpe26 추출 가능성**

- 가능/조건부: pelvis vertical oscillation, pelvis AP velocity, trunk lean, normalized stride length, stride rate, GCT, swing time, DF, foot/shank/thigh touchdown angle, knee/hip ROM.
- 조건부 또는 불가: whole-body COM은 segment 질량 모델이 없으므로 pelvis proxy에 그친다. pelvis transverse rotation은 단일 sagittal 2D에서 불가하다. RE, vLTP, race performance는 별도 입력이 필요하다.

**한계**

- 상관과 회귀는 인과를 확정하지 않는다.
- 10–12 km/h treadmill 자세와 다양한 실제 race pace·환경을 연결했다.
- 많은 상호연관 피처 중 일부만 회귀에 남았으므로 단일 피처 해석은 위험하다.
- 결과가 집단 수준이어서 개인의 최적 변화 방향과 같다고 보장할 수 없다.

## 4. 전체 피처 분류

### 4.1 부위·목적·대상자·Halpe26 가능성

| 피처 대상 부위/단계 | 대표 피처 | 실험 대상자 | 연구 목적 | 근거 | Halpe26 |
|---|---|---|---|---|---|
| 전신 주기 | stride frequency, 5-pair Fourier coefficients | 78명, amateur–elite, treadmill | 전체 관절 파형 압축 | S1 | 조건부 가능 |
| 시공간 | cadence/step frequency | 9 recreational overground; 리뷰 및 97 endurance | 모델 정확도, RE·경기력 | S2, S3, S6 | 가능 |
| 시공간 | GCT | 여러 집단 리뷰; 9 recreational; 40 trained; 97 endurance | 정확도, RE, 전략, 경기력 | S2–S4, S6 | 조건부 가능 |
| 시공간 | swing/aerial time | 동일 | 정확도, RE, DF 전략 | S2–S4, S6 | 조건부 가능 |
| 시공간 | duty factor | 40 trained, 97 endurance | 전역 러닝 전략·경기력 | S4, S6 | 조건부 가능 |
| 시공간 | stride length/height | 리뷰, 97 endurance | RE·overstride | S2, S6 | 조건부 가능 |
| 이벤트 | heel height minimum/vertical velocity | 40 recreational rearfoot | footstrike 검출 | S5 | 가능하나 노이즈 민감 |
| 이벤트 | peak knee extension | 40 recreational rearfoot | toe-off 검출 | S5 | 가능 |
| 이벤트 | foot–sacrum AP extrema | 40 recreational rearfoot | FS/TO 검출 비교 | S5 | 조건부 가능 |
| 이벤트 | foot/shank angular acceleration | 40 recreational rearfoot | FS/TO 검출 비교 | S5 | 가능하나 비권장 |
| 골반/COM 수직 | pelvis/COM oscillation | 리뷰, 40 trained, 97 endurance | RE와 전략 | S2, S4, S6 | pelvis는 가능, COM은 근사 |
| 골반/COM 수평 | forward displacement, minimum velocity, velocity range | 40 trained, 97 endurance | 전진 전략·braking | S4, S6 | 카메라 고정·좌표 보정 시 조건부 |
| 골반 3D | transverse rotation | 97 endurance | RE·경기력 | S6 | 단일 측면 2D 불가 |
| 몸통 | mean lean, lean ROM | 리뷰, 97 endurance | RE·경기력 | S2, S6 | 가능, 근거 방향은 주의 |
| 착지 다리 | foot/shank/thigh touchdown angle | 97 endurance | RE·경기력 | S6 | 가능 |
| 발 | footstrike pattern/foot angle | 리뷰, 40 rearfoot, 97 endurance | RE·event | S2, S5, S6 | 조건부 가능 |
| 무릎 | IC angle, stance maximum/ROM, swing flexion | 9 recreational, 97 endurance | 모델 정확도, RE·경기력 | S3, S6 | 가능, 관절 중 신뢰도 우선 |
| 엉덩이 | flexion/extension, stance ROM, swing maximum | 9 recreational, 97 endurance | 모델 정확도, RE | S3, S6 | 가능하나 2D 한계 |
| 발목 | dorsiflexion/plantarflexion, toe-off angle | 리뷰, 9 recreational | RE, 모델 정확도 | S2, S3 | 가능하나 낮은 신뢰도 |
| 팔 | elbow angle/ROM, arm swing 유지 | 리뷰, 9 recreational | RE, 모델 정확도 | S2, S3 | 가능하나 검증 ICC 낮음 |
| 좌우 대칭 | step/GCT/ROM asymmetry | Ochy 실패 양상과 프로젝트 확장 | 견고성·개인 모니터링 | 직접 기준은 제한적 | 계산 가능, 판정 기준 없음 |
| 운동역학 | GRF, impulse, leg stiffness, joint moment | 리뷰 | RE 기전 | S2 | 불가 |
| 근신경 | EMG activation/coactivation | 리뷰 | RE 기전 | S2 | 불가 |
| 생리 | VO₂/energy cost, vLTP | 40 trained, 97 endurance | RE·경기력 | S2, S4, S6 | 불가, 별도 센서 필요 |
| 외부 환경 | 신발 질량·쿠션·노면 compliance | 리뷰 | RE | S2 | 영상만으로 불가 |

### 4.2 달리기 목적별 묶음

#### 경제성(running economy)

우선 관찰할 수 있는 HPE 피처는 pelvis vertical oscillation, braking proxy, normalized stride length, cadence, stance knee/hip ROM, toe-off leg extension, trunk stability다. 그러나 RE의 직접 측정값은 호흡가스 기반 energy cost이며, HPE 피처만으로 RE를 확정할 수 없다.

#### 경기력

Folland에서 shank angle at touchdown, minimum pelvis velocity, DF, trunk lean이 설명 변수로 남았다. 이는 집단 상관 모델이며, 개인의 기록 향상을 보장하는 처방식이 아니다. 실제 pace, vLTP, race distance를 함께 저장해야 의미가 커진다.

#### 러닝 폼 설명·압축

Fourier coefficient는 관절각 파형을 compact embedding으로 만들고 runner·속도·세션 간 패턴 비교에 적합하다. 정상/비정상 임계값이 아니라 유사도, 변화량, 안정성을 위한 표현이다.

#### 이벤트 검출과 측정 신뢰도

heel trajectory와 peak knee extension은 모든 시간 피처의 기반이다. cadence, GCT, swing, DF를 내기 전에 FS/TO 이벤트의 confidence와 예상 frame error를 먼저 계산해야 한다.

#### 부상 위험

제공된 6편은 주로 경제성·경기력·측정 검증을 다루며, 특정 부상 진단 임계값을 제공하지 않는다. 따라서 이 자료만으로 부상 위험 등급이나 의료적 판정을 만들면 안 된다.

## 5. 현재 프로젝트와 Ochy 방향성의 접점

### 5.1 프로젝트의 현재 흐름

현재 프로젝트는 `PoC/scripts/main.sh`에서 HPE → features → Agent를 순서대로 실행한다. HPE는 RTMDet과 RTMPose-M Halpe26을 사용하여 `pose_predictions.json`을 만들고, primary runner를 `track_id == 0`으로 유지한다. 관절점 score 0.5 미만은 이전 프레임 좌표를 보조값으로 기록한다.

독립 패키지 `PoC/scripts/features/hpe_numpy_features/`는 JSON을 `(F, 26, 2)` NumPy 배열로 만들고, 양쪽 골반 중심을 원점으로 하며 pose에서 구한 image stature를 1로 정규화한다. 실제 미터 값은 이 정규화 비율에 사용자의 실제 키를 곱해 구한다. Agent는 제공된 피처와 논문 근거만 사용하고 의학 진단을 하지 않도록 프롬프트가 구성돼 있다.

### 5.2 일치하는 부분

| 방향 | Ochy | 현재 프로젝트 | 일치도 |
|---|---|---|---|
| 낮은 장비 장벽 | 1대 60 Hz sagittal camera | 일반 영상 입력의 2D HPE | 높음 |
| 러닝 전용 분석 | running-specific model | Halpe26에서 러닝 피처 추출 | 중간: pose model 자체는 범용 |
| 자동화 | 추적 실패율·artifact 강조 | track_id, score, imputed 좌표 저장 | 높음 |
| 설명 가능한 결과 | 시공간·관절각 | 명명된 18개 피처와 보고서 | 높음 |
| 과학적 근거 | force/mocap 비교 | 논문 근거를 Agent에 제공 | 방향은 높음, 자체 검증은 미완 |
| 현장 배포 | single-camera overground | run 폴더별 영상 처리 | 높음 |

### 5.3 차이와 리스크

1. **모델 특화 정도**: Ochy는 pose estimator 자체를 러닝에 맞게 학습했다. 현재 프로젝트의 RTMPose Halpe26은 범용 body dataset 기반이므로 후처리만 러닝 전용이다.
2. **이벤트 검증 부재**: 현재 이벤트는 발 keypoint y의 국소 최댓값과 주변 구간을 이용하는 heuristic이다. force plate에 대한 프레임 오차가 아직 측정되지 않았다.
3. **COM 정의 차이**: 논문의 whole-body COM은 15–17 segment와 관성 파라미터를 사용한다. 현재 `양 골반 중심`은 pelvis proxy이며 COM과 동일하지 않다.
4. **거리 보정**: pose 기반 image stature로 픽셀을 정규화하고 실제 키를 곱하는 방식은 원근·카메라 각도·깊이 이동을 제거하지 못한다. “m” 단위 표시는 실제 calibrated distance보다 강한 인상을 줄 수 있다.
5. **imputation 오염**: 이전 프레임 유지 방식은 추적이 사라질 때 속도 0인 plateau를 만들어 event, ROM, velocity 피처를 왜곡할 수 있다.
6. **2D 한계**: pelvis transverse rotation, 3D hip motion, GRF alignment처럼 문헌의 중요한 요인은 측면 2D에서 재현할 수 없다.
7. **근거-피처 연결**: 현재 Agent는 `PAPERS[0]` 하나를 넣는다. 피처별로 source, page, population, direction, evidence type을 구조화하지 않으면 과잉 일반화 위험이 있다.

## 6. 프로젝트를 위한 우선 인사이트

### 6.1 피처보다 먼저 측정 품질을 출력해야 한다

각 수치에 다음 메타데이터를 붙이는 것이 Ochy의 견고성 철학과 가장 잘 맞는다.

- 관측 프레임 비율과 imputed 프레임 비율
- left/right keypoint score의 median과 하위 분위수
- 검출된 동일 발 contact 수와 교대 순서 위반 수
- FS/TO confidence
- 분석 가능한 stride 수
- 신발·배경 대비 또는 foot keypoint dropout 비율

이 품질이 낮으면 값 대신 `insufficient_evidence`를 반환하는 편이 잘못된 정밀 숫자보다 낫다.

### 6.2 우선순위는 검증 강도에 따라 나눠야 한다

**1차 피처**

- cadence/step frequency
- knee angle at IC, stance maximum, stance ROM
- pelvis vertical oscillation/height
- trunk lean의 평균과 변동성

**2차 피처**

- GCT, swing time, DF
- shank/foot angle at touchdown
- pelvis AP braking proxy
- hip angle/ROM

**실험적 피처**

- ankle angle
- elbow ROM을 경제성 판정에 사용
- 미터 단위 pelvis–foot 거리
- COM 명칭을 붙인 골반 proxy
- 각가속도 기반 event

1차/2차도 임상적 정확도 등급이 아니라 이 문헌 세트에서의 상대적 구현 우선순위다.

### 6.3 좋음/나쁨 대신 비교 축을 제공해야 한다

권장 표현은 다음과 같다.

- 동일 사용자, 동일 속도, 동일 촬영 조건에서 지난 세션 대비 변화
- 좌우 차이와 그 측정 신뢰도
- 같은 세션의 stride-to-stride variability
- 논문 집단 범위와의 단순 위치 표시(판정이 아님)
- 상충 근거가 있는 피처에는 `evidence_conflicting`

예를 들어 GCT는 “짧아서 좋음”이 아니라 “이 세션에서 0.24 s, 지난 세션 0.25 s, 속도 차이 +0.2 m/s, event confidence 중간; 경제성과의 방향은 문헌상 상충”으로 표현하는 편이 근거에 맞다.

### 6.4 개인화에 필요한 최소 컨텍스트

- 키, 성별/연령은 기술통계 비교용으로만 사용
- 실측 또는 추정 running speed
- treadmill/overground
- 촬영 FPS와 셔터/blur 품질
- 신발과 노면
- 훈련 수준과 주간 거리
- 분석 목적: 경제성, 경기력, 폼 안정성, 재활 모니터링

속도를 기록하지 않으면 Ochy와 S4에서 확인된 speed effect를 통제할 수 없다. 키만으로 거리를 환산하는 것보다 속도와 camera calibration을 확보하는 것이 더 중요한 다음 단계다.

### 6.5 제품 방향 제안

이 프로젝트가 Ochy와 가장 잘 만나는 지점은 **“실험실 밖에서도 반복 가능한 러닝 관찰”**이다. 이를 유지하려면 제품의 핵심 산출물을 단일 점수보다 다음 세 층으로 설계하는 것이 좋다.

1. **측정층**: pose quality, gait events, 시공간·관절각과 불확실성
2. **해석층**: 속도·개인·환경으로 조건화한 문헌 근거와 상충 여부
3. **행동층**: 한 번에 한 가지의 검증 가능한 연습 가설과 재측정 계획

이 구조는 문헌이 지적한 “여러 변수를 동시에 바꾸는 전역 자세 교정”의 실패와 단일 피처 과잉해석을 피하면서, 현재 Agent 파이프라인의 장점을 살린다.

## 7. Halpe26 구현 매핑

현재 코드가 사용하는 주요 index는 다음과 같다.

| 부위 | Left | Right | 활용 |
|---|---:|---:|---|
| Shoulder | 5 | 6 | trunk, lean, hip angle |
| Elbow | 7 | 8 | elbow ROM |
| Wrist | 9 | 10 | elbow/arm swing |
| Hip | 11 | 12 | pelvis center, hip/knee angle |
| Knee | 13 | 14 | knee angle, toe-off 후보 |
| Ankle | 15 | 16 | shank, foot, contact |
| Big/small toe | 20/22 | 21/23 | foot angle, contact |
| Heel | 24 | 25 | footstrike, foot angle |
| Head/neck/pelvis helper | 17/18/19 | — | image stature 보조 |

### 권장 명명 주의

- `pelvis_center`를 `COM`이라고 단정하지 말고 `pelvis_proxy_com`처럼 구분한다.
- 신장 기반 환산 거리는 `estimated_m` 또는 `height_scaled_distance_m`로 표시한다.
- `stance_time`은 힘판이 없으므로 `estimated_stance_time`으로 표시한다.
- `initial_contact`는 `estimated_initial_contact`로 표시한다.

## 8. 최종 판단

Ochy가 지향하는 것은 스마트폰 한 대로 실험실 biomechanical analysis를 완전히 대체하는 것이라기보다, **제약된 장비에서도 반복 가능하고 자동화 가능한 러닝 분석을 최대한 정확하게 만드는 것**으로 보는 편이 타당하다. 제공된 문헌 전체는 다음 제품 원칙을 지지한다.

1. 러닝 전용 학습과 이벤트 검증이 범용 HPE 후처리보다 중요하다.
2. cadence와 knee angle은 우선순위가 높고, swing time·ankle·elbow는 보수적으로 다뤄야 한다.
3. GCT나 trunk lean 하나로 좋고 나쁨을 판정하지 않는다.
4. 속도·숙련도·환경·개인 내 변화를 함께 본다.
5. HPE가 직접 측정하지 못하는 RE, GRF, EMG, elastic energy를 추론 사실처럼 쓰지 않는다.
6. 수치와 함께 관측 품질과 불확실성을 제품의 1급 결과로 제공한다.

현재 프로젝트는 입력 영상→Halpe26→피처→근거 기반 보고서라는 큰 방향에서 Ochy와 잘 맞는다. 가장 큰 다음 과제는 피처 수를 늘리는 것이 아니라 **event 검출의 gold-standard 검증, 측정 신뢰도 출력, 피처별 근거 구조화, 속도·촬영 조건 메타데이터화**다.

## 9. 분석 문헌

- **S1** — Skejø, S. D., et al. (2021). *Running in circles: Describing running kinematics using Fourier series*. Journal of Biomechanics, 115, 110187. `1-s2.0-S0021929020306114-main.pdf`
- **S2** — Moore, I. S. (2016). *Is There an Economical Running Technique? A Review of Modifiable Biomechanical Factors Affecting Running Economy*. Sports Medicine, 46, 793–807. `40279_2016_Article_474.pdf`
- **S3** — Ochy (2025). *Precision of a smartphone application to perform running form analysis*. `Ochy_AI_Validation.pdf`
- **S4** — Lussiana, T., et al. (2019). *The implications of time on the ground on running economy: less is not always better*. Journal of Experimental Biology, 222, jeb192047. `jeb192047.pdf`
- **S5** — Fellin, R. E., et al. (2010). *Comparison of methods for kinematic identification of footstrike and toe-off during overground and treadmill running*. Journal of Science and Medicine in Sport, 13(6), 646–650. `nihms-348188.pdf`
- **S6** — Folland, J. P., et al. (2017). *Running Technique is an Important Component of Running Economy and Performance*. Medicine & Science in Sports & Exercise, 49(7), 1412–1423. `running-technique-is-an-important-component-of-running.pdf`

## 10. 프로젝트에서 확인한 파일

- `README.md`, `PoC/README.md`
- `PoC/scripts/main.sh`
- `PoC/scripts/hpe/hpe_model.py`, `PoC/scripts/hpe/pose_track.py`
- `PoC/scripts/features/hpe_numpy_features/pose_features.py`, `README.md`
- `PoC/scripts/Agent/Running_coach.py`, `PoC/scripts/Agent/prompts.py`

