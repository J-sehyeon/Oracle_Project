import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, savgol_filter
from typing import Pattern

class PoseSequence:
    def __init__(self, pose_data: dict, detail_data: dict, user_data: dict):
        """
        json 데이터를 불러온 뒤 바로 이 클래스의 인자로 입력하면 됩니다.
        y좌표는 0의 기준이 위에서 아래로 바뀝니다.
        """
        # bbox, keypoints들의 y좌표 반전.
        df = hpe2pd(pose_data)
        _cols = df.columns[df.columns.str.contains("_y|up|down")]
        df.loc[:, _cols] = detail_data["video"]["height"] - df[_cols]

        # direction
        dir_index = 0 if (df["nose_x"] - df["neck_x"])[0] > 0 else 1

        self.df = df
        self.details = detail_data
        self.user = user_data["user"]
        self.direction = "left" if dir_index else "right"
        self.strides = []
        self.m_per_pixel = None

    def cal_stride(self) -> None:
        """
        self.stride에 1스트라이드의 시작, 끝 프레임 기록
        """
        if self.strides:
            print('이미 stride가 계산되어 있습니다.')
            print('Stride :', self.strides)
            return
        df = self.df
        dir = self.direction
        left_knee_angle = knee_flexion_angle(
            [df[f"{dir}_hip_x"], df[f"{dir}_hip_y"]],
            [df[f"{dir}_knee_x"], df[f"{dir}_knee_y"]],
            [df[f"{dir}_ankle_x"], df[f"{dir}_ankle_y"]]
        )
        y = np.asarray(left_knee_angle, dtype=float)
        y_smooth = savgol_filter(
            y,
            window_length=5,
            polyorder=2
        )
        # 데이터 범위에 비례해 prominence 설정
        signal_range = np.percentile(y_smooth, 95) - np.percentile(y_smooth, 5)
        prominence = signal_range * 0.10    # 곱해지는 숫자가 클수록 큰 봉우리만 검출

        # 최댓값
        max_indices, max_properties = find_peaks(
            y_smooth,
            prominence=prominence,
            distance=10,
        )

        # 최솟값: 신호에 -를 붙여서 봉우리로 변환
        min_indices, min_properties = find_peaks(
            -y_smooth,
            prominence=prominence,
            distance=10,
        )

        _max = {
            "frame": max_indices,
            "class": np.ones_like(max_indices)
        }
        _min = {
            "frame": min_indices,
            "class": np.zeros_like(min_indices)
        }
        extremum = pd.concat([pd.DataFrame(_max), pd.DataFrame(_min)]).sort_values('frame')

        assert len(extremum) >= 2, "온전한 스트라이드가 검출되지 않았습니다."
        # 올바른 스트라이드 검출
        for i in range(1, len(extremum)):
            previous = extremum["class"].iloc[i - 1]
            current = extremum["class"].iloc[i]

            assert {previous, current} == {0, 1}, (
                f"예외: {i-1}, {i}행의 값이 {previous}, {current}입니다.\n올바른 스트라이드가 검출되지 않았습니다. 검출 파라미터 변경 필요."
            )
        for i in range(len(extremum) // 4 + 1):
            self.strides.append(extremum['frame'].iloc[4 * i : 4 * i + 5].to_list())

    def pixel2m(self):
        """
        사용자의 키 정보를 사용해 1pixel을 m단위로 변경한다.
        이 때 사용하는 이미지는 TD시점이다.
        """
        def _point(df, name):
            return df[[f"{name}_x", f"{name}_y"]].to_numpy(dtype=float)
        def _distance(a, b):
            return np.linalg.norm(a - b, axis=0)
        
        # 사용할 이미지 선택
        image = self.df.loc[self.strides[0][0]]

        ankle = _point(image, f"{self.direction}_ankle")
        knee = _point(image, f"{self.direction}_knee")
        hip = _point(image, f"{self.direction}_hip")

        hip_center = _point(image, "hip_center")
        neck = _point(image, "neck")
        head = _point(image, "head")

        leg_length = (
            _distance(ankle, knee)
            + _distance(knee, hip)
        )
        torso_length = _distance(hip_center, neck)
        head_length = _distance(neck, head)

        height_px = leg_length + torso_length + head_length
        self.m_per_pixel = self.user['height'] / height_px
        print(f"사용자의 키를 기반으로 계산한 픽셀당 meter는 {self.m_per_pixel} / pixel 입니다.")

        return

    def gct(self, next: int = 0):
        """
        {side}의 heel이 지면에 접촉하고 big_toe가 지면에서 떼어지는 순간까지의 인덱스 출력
        next는 스트라이드의 구간을 한 단계 미뤄야 할 가능성이 있기 때문에 그 때의 설계를 위해 남긴 더미.
        """
        n = len(self.strides) - (0 if len(self.strides[-1]) == 5 else 1)
        res = []
        for i in range(n):
            start = self.strides[i][0]
            end = self.strides[i][-1]

            df = self.df.loc[start:end+1]

            heel = f"{self.direction}_heel"
            td = int(df[f"{heel}_y"].idxmin())

            toe = f"{self.direction}_big_toe"
            min_value = df[f"{toe}_y"].min()

            inside = df[f"{toe}_y"].between(min_value, min_value + 5)
            to = df.index[~inside & inside.shift(1, fill_value=False)].to_list()[0]

            res.append([td, to])
        return res

Halpe_26_keypoints = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle",
    17: "head",
    18: "neck",
    19: "hip_center",
    20: "left_big_toe",
    21: "right_big_toe",
    22: "left_small_toe",
    23: "right_small_toe",
    24: "left_heel",
    25: "right_heel",
}

def hpe2pd(pose_data: dict) -> pd.DataFrame:
    """
    hpe json 데이터를 pandas DataFrame으로 변경
    Returns:
        pd.DataFrame has bbox(4), keypoints(26)
    """
    rows = []
    
    for frame in pose_data["frames"]:
        row = {}

        if frame['people'] == []:
            # 사람이 포착되지 않음.
            continue
        bbox = frame['people'][0]["bbox"]
        row["bbox_left"], row["bbox_up"], row["bbox_right"], row["bbox_down"] = bbox

        for i, xy in enumerate(frame['people'][0]['keypoints']):
            row[f"{Halpe_26_keypoints[i]}_x"] = xy[0]
            row[f"{Halpe_26_keypoints[i]}_y"] = xy[1]
        rows.append(row)
    
    return pd.DataFrame.from_records(rows)

def vel_acc(df: pd.DataFrame, keypoints: list[str] = None,fps: float = 60.0):
    """
    정해진 형식의 df에서 구하고자 하는 키포인트의 속력(vel)과 가속력(acc)를 구한다.
    Returns:
        pd.DataFrame
    """
    if fps <= 0:
        raise ValueError("fps는 0보다 커야 합니다.")
    
    if keypoints is None:
        keypoints = list(Halpe_26_keypoints.values())

    dt = 1 / fps

    res = pd.DataFrame()

    for key in keypoints:
        vx = df[f"{key}_x"].diff() / dt
        vy = df[f"{key}_y"].diff() / dt
        ax = vx.diff() / dt
        ay = vy.diff() / dt
        res[f"{key}_vel"] = np.hypot(vx, vy)
        res[f"{key}_acc"] = np.hypot(ax, ay)

    return res.iloc[2:]

def visualize_time(_df: pd.DataFrame, fps: float) -> None:
    if type(_df) == pd.Series:
        _df = _df.to_frame()
    time = (_df.index.to_numpy() - 2) / fps

    fig, axes = plt.subplots(figsize=(12, 6))
    for col in _df.columns:
        axes.plot(time, _df[col], label=col, linewidth=1.5)
    axes.set_title("Time Series Analysis")
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("pixel")
    axes.legend()
    axes.grid(alpha=0.3)

    fig.tight_layout()
    plt.show()

def visualize_xy(_df: pd.DataFrame) -> None:
    if type(_df) == pd.Series:
        raise RuntimeError("x, y가 주어져야 합니다.")
    columns = set('_'.join(col.split('_')[:-1]) for col in _df.columns)

    fig, axes = plt.subplots(figsize=(12, 6))
    for col in columns:
        axes.plot(_df[f"{col}_x"], _df[f"{col}_y"], label=col, linewidth=1.5)
    axes.set_title("Trace Analysis")
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.legend()
    axes.grid(alpha=0.3)

    fig.tight_layout()
    plt.show()

def knee_flexion_angle(
    hip,
    knee,
    ankle,
    orientation: float = 1.0,
) -> np.ndarray:
    """
    무릎 굴곡 각도를 계산한다.

    반환값:
        정상 굴곡: 양수
        완전 신전: 0
        반대 방향 과신전: 음수

    orientation:
        촬영 방향 때문에 부호가 반대이면 -1.0을 전달한다.
    """
    thigh = (
        np.asarray(hip, dtype=float)
        - np.asarray(knee, dtype=float)
    ).T

    shank = (
        np.asarray(ankle, dtype=float)
        - np.asarray(knee, dtype=float)
    ).T

    thigh_norm = np.linalg.norm(thigh, axis=1)
    shank_norm = np.linalg.norm(shank, axis=1)

    valid = (
        np.isfinite(thigh_norm)
        & np.isfinite(shank_norm)
        & (thigh_norm > 1e-8)
        & (shank_norm > 1e-8)
    )

    result = np.full(len(thigh), np.nan, dtype=float)

    dot = np.sum(thigh[valid] * shank[valid], axis=1)

    cross = (
        thigh[valid, 0] * shank[valid, 1]
        - thigh[valid, 1] * shank[valid, 0]
    )

    # 무릎을 중심으로 한 두 벡터의 방향 포함 각도
    signed_joint_angle = np.degrees(
        np.arctan2(cross, dot)
    )

    direction = np.where(signed_joint_angle >= 0, 1.0, -1.0)

    result[valid] = (
        orientation
        * direction
        * (180.0 - np.abs(signed_joint_angle))
    )

    # 부동소수점으로 생기는 극소값 제거
    result[np.isclose(result, 0.0, atol=1e-8)] = 0.0

    return result
