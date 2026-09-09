import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter
from typing import Pattern

from utils import *

# Parser
parser = argparse.ArgumentParser()
parser.add_argument("coach_folder", type=Path)
parser.add_argument("run_folder", type=str)
args = parser.parse_args()

COACH_DIR = args.coach_folder
RUN_FOLDER = args.run_folder
RUN_DIR = COACH_DIR / "run" / RUN_FOLDER

# 루트 디렉토리 바로 아래의 pose_predictions.json 지정
OUTPUTS_DIR = RUN_DIR / "outputs"

hpe = OUTPUTS_DIR / "pose_predictions.json"
with hpe.open(mode="r", encoding='utf-8') as file:
    pose_data = json.load(file)

details = OUTPUTS_DIR / "details.json"
with details.open(mode="r", encoding='utf-8') as file:
    detail_data = json.load(file)

user = RUN_DIR / "user_info.json"
with user.open(mode="r", encoding='utf-8') as file:
    user_data = json.load(file)

ps = PoseSequence(pose_data, detail_data, user_data)

# 피처 추출을 위한 값 계산
ps.cal_stride()
ps.pixel2m()

def cadence_pace(ps: PoseSequence):
    fps = ps.details['video']['fps']
    gct_frame = ps.gct()
    try:
        if len(gct_frame) > 2:
            start = gct_frame[0][0]
            end = gct_frame[1][0]
        else:
            start = ps.strides.frame.iloc[0]
            end = ps.strides.frame.iloc[4]
        interval = end - start
        m_per_pixel = (ps.pixel2m(frame=start) + ps.pixel2m(frame=end)) / 2
        distance_pixel = ps.df[f'{ps.direction}_heel_x'].loc[[start, end]].diff()[end]
    except:
        print("케이던스 검출 불가")
        return None, None

    time = interval / fps
    
    return (2 / time) * 60, (time / (distance_pixel * m_per_pixel) * 1000) / 60

def feature1(ps: PoseSequence):
    strides = ps.gct()

    # 각 스트라이드별로 골반의 수직 진동 평균
    res = 0
    for i in range(len(strides)):
        start, end = strides[i]
        res += ps.df["hip_center_y"][start:end].agg(['min', 'max']).diff()['max']
        
    # APO: Amplitude of pelvis oscillation : 골반 진동 진폭
    apo_pixel = res / len(strides)
    d = float(apo_pixel * ps.m_per_pixel / ps.user['height'])

    if d < 0.039:
        res = {
            "value": d,
            "range": {
                "section": "낮은 수직 진동",
                "criterion": "d < 0.039",
                "percent": d * 100,
            },
            "instruction": (
                '골반이 위아래로 적게 움직이는 편이에요. 지금의 달리기 리듬을 유지하세요.'
            ),
            "outcome": (
                '에너지를 적게 쓰고 잘 달리는 능력과 관련된 방향이에요.'
            ),
        }

    elif d <= 0.053:
        res = {
            "value": d,
            "range": {
                "section": "일반적인 수직 진동",
                "criterion": "0.039 ≤ d ≤ 0.053",
                "percent": d * 100,
            },
            "instruction": (
                '연구에 참여한 사람들에게서 흔히 나타난 범위예요. 한 걸음의 길이, 발이 땅에 닿아 있는 시간, 속도를 줄이는 동작을 함께 확인하세요.'
            ),
            "outcome": (
                '평균적인 범위예요. 다만 위아래로 더 많이 움직일수록 에너지를 더 쓰는 경향이 있어요.'
            ),
        }

    else:
        res = {
            "value": d,
            "range": {
                "section": "높은 수직 진동",
                "criterion": "d > 0.053",
                "percent": d * 100,
            },
            "instruction": (
                '위로 튀는 동작을 줄여보세요. 한 걸음이 너무 길거나 발이 땅에 오래 닿아 있는지, 발이 땅에 닿아 있을 때 무릎과 엉덩이 관절이 크게 움직이는지 확인하세요.'
            ),
            "outcome": (
                '에너지를 많이 쓰고, 젖산이 빠르게 늘기 시작하는 달리기 속도가 낮으며, 기록이 좋지 않은 것과 관련된 방향이에요.'
            ),
        }

    # 논문 표본의 관찰 범위 검사
    if not 0.028 <= d <= 0.061:
        res["range"]["warning"] = (
            "논문에서 관찰된 범위인 0.028~0.061을 벗어났습니다. "
            "측정값과 정규화 단위를 확인하세요."
        )

    res['description'] = (
        "- **골반 수직 진동(ΔzP)**: 골반이 위아래로 움직인 거리입니다. `최고 골반 높이 - 최저 골반 높이`로 계산합니다.",
        "- **GC(Ground Contact)**: 발이 지면에 닿는 착지 시점부터 발이 떨어지는 이지 시점까지입니다.",
        "- **ΔzPGC,H**: 접지 중 골반 수직 이동 거리를 신장으로 나눈 값입니다. 예를 들어 `0.046`은 신장의 `4.6%`만큼 움직였다는 뜻입니다.",
        "- **LEc(Locomotory Energy Cost)**: 1kg의 체중으로 1km를 달리는 데 필요한 에너지입니다. 낮을수록 달리기 경제성이 좋습니다.",
        "- **vLTP**: 젖산이 빠르게 증가하기 시작하는 시점의 달리기 속도입니다. 일반적으로 높을수록 지구력 수행능력이 좋습니다.",
        "- **SB time**: 최근 시즌의 최고 경기 기록입니다.",

        "논문 표본의 평균은 신장의 `4.6%`, 표준편차는 `0.7%`, 전체 관찰 범위는 `2.8~6.1%`였습니다.", 
        "신장 170cm라면 각각 약 `7.8cm`, `1.2cm`, `4.8~10.4cm`에 해당합니다.", 
        "이 구간은 논문의 공식 절단값이 아니라 표본의 `평균 ± 1SD`를 이용한 실무용 분류입니다."
    )
    return res

def feature2(ps: PoseSequence, tolerance: float = 10.0):
    """
    elbow:
        프레임별 팔꿈치 각도가 들어 있는 기존 NumPy 배열

    tolerance:
        논문의 목표 각도와 비교할 때 적용하는 허용오차
    """
    elbow = ps.joint_angle(f'{ps.direction}_elbow', smooth=True, negative=False)

    # 팔꿈치 각도를 측정하기 좋은 구간 선정
    indices = (
    np.where(ps.df[f'{ps.direction}_elbow_x'] < ps.df[['hip_center_x', 'neck_x']].mean(axis=1))[0]
    if ps.direction == "right"
    else
    np.where(ps.df[f'{ps.direction}_elbow_x'] > ps.df[['hip_center_x', 'neck_x']].mean(axis=1))[0]
    )
    groups = np.split(
        indices,
        np.where(np.diff(indices) != 1)[0] + 1
    )
    middle_frame = (len(ps.df) - 1) / 2

    selected_group = min(
        groups,
        key=lambda group: abs(np.mean(group) - middle_frame)
    )
    

    elbow_array = np.asarray(elbow[selected_group[0]:selected_group[-1]])
    valid_elbow = elbow_array[np.isfinite(elbow_array)]

    if valid_elbow.size == 0:
        return {
            "value": elbow_array,
            "range": {
                "min": None,
                "max": None,
                "amplitude": None,
                "section": "측정 불가",
                "paper_reference": None,
            },
            "instruction": '사용할 수 있는 팔꿈치 각도 측정값이 없어요. 자세를 분석한 결과를 확인하세요.',
            "outcome": '판단할 수 없어요.',
        }

    min_value = float(valid_elbow.min())
    max_value = float(valid_elbow.max())
    mean_value = float(valid_elbow.mean())
    range_value = max_value - min_value

    def near(value, target):
        return abs(value - target) <= tolerance

    def make_result(section, paper_reference, instruction, outcome):
        return {
            # 기존 NumPy 배열을 그대로 포함
            "value": elbow_array,

            # 측정값과 해당 구간
            "range": {
                "min": min_value,
                "max": max_value,
                "mean": mean_value,
                "amplitude": range_value,
                "section": section,
                "paper_reference": paper_reference,
            },

            "instruction": instruction,
            "outcome": outcome,
        }

    # Trial 7: 50°-110° 진동
    # 논문에서 심박수와 RPE가 가장 높았던 조건
    if near(min_value, 50) and near(max_value, 110):
        res = make_result(
            section="50°-110° 진동 구간",
            paper_reference="Trial 7",
            instruction=(
                '팔꿈치가 움직이는 범위가 너무 커요. 가장 작게 굽혀지는 각도를 약 70°까지 높여, 너무 많이 굽히지 않도록 하세요.'
            ),
            outcome=(
                '연구에서 최대 심박수 대비 비율(%MHR, 약 87%)과 스스로 느끼는 힘든 정도(RPE, 약 15.2)가 가장 높고, 같은 시간 동안 내딛는 걸음 수가 가장 적었던, 에너지를 효율적으로 쓰지 못한 구간이에요.'
            ),
        )

    # Trial 8: 70°-90° 진동
    # 트레드밀 실험에서 가장 경제적이었던 조건
    elif near(min_value, 70) and near(max_value, 90):
        res = make_result(
            section="70°-90° 진동 구간",
            paper_reference="Trial 8",
            instruction='매우 좋아요. 지금의 팔꿈치 움직임을 유지하세요.',
            outcome=(
                '연구에서 최대 심박수 대비 비율(%MHR, 약 82%)과 스스로 느끼는 힘든 정도(RPE, 약 13.3)가 가장 낮았던, 에너지를 가장 효율적으로 쓴 구간이에요.'
            ),
        )

    # Trial 9: 70°-110° 진동
    # 트레드밀에서 두 번째로 경제적이었던 조건
    elif near(min_value, 70) and near(max_value, 110):
        res = make_result(
            section="70°-110° 진동 구간",
            paper_reference="Trial 9",
            instruction=(
                '좋아요. 팔꿈치가 약 90°를 중심으로 자연스럽게 움직이도록 유지하세요.'
            ),
            outcome=(
                '연구에서 최대 심박수 대비 비율(%MHR, 약 83%)과 스스로 느끼는 힘든 정도(RPE, 약 13.8)가 두 번째로 낮았던, 에너지를 효율적으로 쓴 구간이에요.'
            ),
        )

    # Trial 3: 팔꿈치를 약 90°로 고정한 조건
    elif range_value <= tolerance * 2 and near(mean_value, 90):
        res = make_result(
            section="약 90° 고정 구간",
            paper_reference="Trial 3",
            instruction=(
                '팔꿈치를 90°로 고정하지 말고, 약 70°-90° 사이에서 자연스럽게 움직이세요.'
            ),
            outcome=(
                '최대 심박수 대비 비율(%MHR)은 약 85%, 스스로 느끼는 힘든 정도(RPE)는 약 14.1로, 팔꿈치를 70°-90° 사이로 움직일 때보다 에너지를 더 썼던 구간이에요.'
            ),
        )

    # 논문 조건보다 더 큰 움직임
    elif min_value < 45 or max_value > 115 or range_value > 60:
        res = make_result(
            section="과도한 가동범위",
            paper_reference="논문 실험 범위 밖",
            instruction=(
                '팔꿈치가 너무 크게 움직여요. 90°를 중심으로 움직이면서 가장 작은 각도는 약 70°, 가장 큰 각도는 약 110° 안에 들도록 범위를 줄이세요.'
            ),
            outcome=(
                '연구에서 직접 측정하지 않은 범위예요. 팔꿈치가 크게 움직이면 에너지를 더 쓰는 것과 관련이 있을 수 있어요.'
            ),
        )

    # 논문에서 직접 비교하지 않은 중간 구간
    else:
        res = make_result(
            section="기타 구간",
            paper_reference="논문에서 직접 비교하지 않은 구간",
            instruction=(
                '90°를 중심으로 팔꿈치를 움직이세요. 러닝머신에서 달릴 때는 우선 70°-90° 사이로 움직이는 것을 목표로 해보세요.'
            ),
            outcome='이 최소 각도와 최대 각도의 조합을 직접 비교한 연구 결과는 없어요.',
        )
    res["description"] = (
        "**MHR (Maximum Heart Rate, 최대 심박수)**",
        "운동할 때 도달할 수 있는 최대 심박수입니다. 논문의 `%MHR`은 현재 심박수가 최대 심박수의 몇 퍼센트인지 나타냅니다. 값이 높을수록 심혈관 부담과 운동 강도가 크다는 의미입니다.",
        "%MHR=\frac{\text{운동 중 심박수}}{\text{최대 심박수}}\times100",
        "**RPE (Rating of Perceived Exertion, 운동자각도)**",
        "운동자가 주관적으로 느끼는 힘든 정도입니다. 이 논문은 일반적으로 `6~20` 척도를 사용하며, 값이 높을수록 더 힘들다는 뜻입니다.",
        "- 약 `13`: 다소 힘듦",
        "- 약 `15`: 힘듦",
        "- 약 `17`: 매우 힘듦",
        "따라서 이 논문에서는 **MHR과 RPE가 낮을수록 같은 속도로 달릴 때 상대적으로 경제적인 팔 동작**으로 해석합니다."
    )

    return res

def feature3(ps: PoseSequence):
    df = ps.df
    gct = ps.gct()

    shoulder_center_x = (
    df["left_shoulder_x"] + df["right_shoulder_x"]) / 2
    shoulder_center_y = (
    df["left_shoulder_y"] + df["right_shoulder_y"]) /2 
    hip_center_x = (
    df["left_hip_x"] + df["right_hip_x"]) / 2
    hip_center_y = (
    df["left_hip_y"] + df["right_hip_y"]) /2 

    dx = shoulder_center_x - hip_center_x
    # dx 가 음수일 경우(일부러 뒤로 젖히는 사람) -> 에러코드에 정리
    dy = shoulder_center_y - hip_center_y
    length = np.sqrt(dx**2 + dy**2)

    cos_theta = dy / length
    cos_theta = np.clip(cos_theta, -1.0 , 1.0)
    trunk_angle = np.degrees(np.arccos(cos_theta))

    res = 0
    for i in range(len(gct)):
        start, end = gct[i]
        res += trunk_angle.loc[start:end].mean()
    mean_trunk_angle = res / len(gct)
    d = float(mean_trunk_angle)

    if 0 <= d < 7.9:
        res = {
            'value': d,
            'boundary': [0, 7.9],
            "instruction": '상체를 많이 기울이세요.',
            "outcome": '무릎뼈와 허벅지뼈 사이 관절에 걸리는 압력(PFJ stress)이 높아요.'
        }
    elif 7.9 <= d < 10.9:
        res = {
            'value': d,
            'boundary': [7.9, 10.9],
            "instruction": '상체를 조금 기울이세요.',
            "outcome": '무릎뼈와 허벅지뼈 사이 관절에 걸리는 압력(PFJ stress)이 보통이에요.'
        }
    elif 10.9 <= d < 18.9:
        res = {
            'value': d,
            'boundary': [10.9, 18.9],
            "instruction": '좋아요.',
            "outcome": '무릎뼈와 허벅지뼈 사이 관절에 걸리는 압력(PFJ stress)이 낮아요.'
        }
    elif 18.9 <= d:
        res = {
            'value': d,
            'boundary': [18.9],
            "instruction": '상체를 세우세요.',
            "outcome": '상체가 많이 기울어진 상태예요.'
        }
    res["description"] = "*PFJ stress: patellofemoral joint stress (슬개대퇴관절 stress)"

    return res
    # stride 구하는 이것을 위로 옮기는것이 시간에 영향을 끼칠지 ?


def feature4(ps: PoseSequence):
    df = ps.df
    gct = ps.gct()

    dx = df["neck_x"] - df["left_ankle_x"]
    dy = df["neck_y"] - df["left_ankle_y"]
    length = np.sqrt(dx**2 + dy**2)

    cos_theta = dy / length
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    postural_angle = np.degrees(np.arccos(cos_theta))


    res = 0
    for i in range(len(gct)):
        start, end = gct[i]
        res += postural_angle.loc[start:end].mean()
    mean_postural_angle = res / len(gct)

    d = float(mean_postural_angle)

    if 0 <= d < 1.7:
        res = {
            'value': d,
            "boundary": [0, 1.7],
            "instruction": '몸을 조금 더 기울이세요.',
            "outcome": '몸이 쓰는 에너지(대사비용)가 적고, 엉덩이 관절과 무릎이 굽혀지는 각도가 작아요.'
        }
    elif 1.7 <= d < 4.3:
        res = {
            'value': d,
            "boundary": [1.7, 4.3],
            "instruction": '좋아요.',
            "outcome": '몸이 쓰는 에너지(대사비용)가 적어요.'
        }
    elif 4.3 <= d < 8.2:
        res = {
            'value': d,
            "boundary": [4.3, 8.2],
            "instruction": '몸을 조금 더 세우세요.',
            "outcome": '몸이 쓰는 에너지(대사비용)가 많고, 엉덩이 관절과 무릎이 굽혀지는 각도가 커요.'
        }
    elif 8.2 <= d:
        res = {
            'value': d,
            "boundary": [8.2, None],
            "instruction": '몸을 많이 세우세요.',
            "outcome": '몸이 쓰는 에너지(대사비용)가 매우 많고, 엉덩이 관절과 무릎이 굽혀지는 각도가 매우 커요.'
        }

    res["description"] = "대사비용: 활동을 수행하기 위해 신체가 소비하는 대사 에너지의 양"

    return res


def numpy_json_default(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    if isinstance(obj, np.generic):
        return obj.item()

    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable"
    )

if __name__ == "__main__":
    cadence, pace = cadence_pace(ps=ps)
    features = {
        'cadence': cadence,
        'pace': pace,
        'Amplitude of pelvis oscillation': feature1(ps=ps),
        'Elbow angle': feature2(ps=ps),
        'Trunk flexion angle': feature3(ps=ps),
        'Postural lean angle': feature4(ps=ps)
    }

    feature_path = OUTPUTS_DIR / "feature_results.json"
    feature_path.write_text(
            json.dumps(
                features,
                ensure_ascii=False,
                indent=2,
                default=numpy_json_default,
            ),
            encoding="utf-8",
    )