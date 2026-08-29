import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

def visualize(_df: pd.Series, fps: float) -> None:
    time = (_df.index.to_numpy() - 2) / fps
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(time, _df, label=_df.name, color="tab:blue", linewidth=1.5)
    ax.set_title("")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("pixel")
    ax.legend()
    ax.grid(alpha=0.3)

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
