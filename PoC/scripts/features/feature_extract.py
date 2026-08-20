from pathlib import Path
import json
print("현 작업 위치:", Path.cwd())

from pathlib import Path

# 노트북이 실행된 현재 위치(프로젝트 루트) 지정
project_root = Path.cwd()

# 루트 디렉토리 바로 아래의 pose_predictions.json 지정
json_path = project_root / "PoC" / "run" / "test1" / "outputs" / "pose_predictions.json"

print("프로젝트 루트:", project_root)
print("JSON 경로:", json_path)
print("파일 존재:", json_path.exists())

if json_path.exists():
    print("파일 크기(MB):", round(json_path.stat().st_size / 1024**2, 2))

with json_path.open(mode= "r", encoding= 'utf-8') as file:
    pose_data= json.load(file)
print('최상위 자료형:', type(pose_data))
print('최상위 키:', pose_data.keys())

# model_info= pose_data["model"]
frames= pose_data['frames']

# print('모델 정보')
# for key,value in model_info.items():
#     print(f" - {key}:{value}")

print("="*50)
print('전체 프레임 수:', len(frames))

first_frame= frames[0]

first_frame= frames[0]

# 배열 크기 확인
import numpy as np

first_person= first_frame["people"][0]

print('사람 데이터 키:')
for key in first_person.keys():
    print("-", key)

keypoints= np.asarray(first_person["keypoints"], dtype=float)
keypoint_scores= np.asarray(first_person["keypoint_scores"],dtype=float)
observed = np.asarray(first_person["observed"], dtype=bool)

# 26개 좌표에 키포인트의 이름 붙이기
Halpe_26_keypoints= {
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

print("키포인트 개수:", len(Halpe_26_keypoints))

# 첫 프레임의 데이터 좌표 DF로 변환
import pandas as pd
first_person_df= pd.DataFrame({
    "keypoint_id":range(26), # Halpe-26의 관절 인덱스
    "keypoint_name": [
        Halpe_26_keypoints[index]
        for index in range(26)
    ], # keypoint_name은 관절 이름이다 총 26개
    "x": keypoints[:,0], # x,y는 영상의 픽셀 좌표(2차원인거 직접 확인가능)
    "y": keypoints[:,1],
    "score": keypoint_scores, # 키포인트 신뢰도(keypoint_scores: 아마 벡터 유사도 같은 값)
    "observed": observed, # 직접 관측 여부 (boolean값) True나 False인데 대부분 True
    "imputed_keypoint": first_person["imputed_keypoints"] # 관측 실패 시 보간 좌표로 다 NULL값
})

first_person_df

rows= []

for frame_index, frame in enumerate(frames):
    image_path= frame["image_path"]

    # 주 러너만 선택(track_id=0)하여 main_runner에 저장
    main_runner= next(
        (
            person for person in frame["people"]
            if person["track_id"] == 0 # track_id가 0이면 저장하고
        ),
        None, # 아니면 0 (파이썬 리스트 컴프리헨션)
    )

    if main_runner is None:
        continue

    for keypoint_id in range(26): # [각 value,관절 인덱스]
        raw_x, raw_y= main_runner["keypoints"][keypoint_id]
        score= main_runner["keypoint_scores"][keypoint_id]
        is_observed= main_runner["observed"][keypoint_id]
        imputed= main_runner["imputed_keypoints"][keypoint_id]

        if is_observed: # 모델이 해당 프레임 관절을 잘 찾았다면(bbox값이 크다면)
            x= raw_x
            y= raw_y
            coordinate_source= "observed"
        elif imputed is not None:
            x,y= imputed # 관측 실패시 Null로 보간 채움
        else:
            x= np.nan
            y= np.nan
            coordinate_source= "missing" # 이도 저도 아닌 값 (결측치)

        # 현재 프레임의 현 keypoint 정보를 하나의 rows(행)으로 만들어 리스트에 append
        rows.append({
            "frame_index": frame_index,
            "frame_number": frame_index +1,
            "image_path": image_path,
            "track_id": main_runner["track_id"],
            "bbox_score": main_runner["bbox_score"],
            "keypoint_id": keypoint_id,
            "keypoint_name": Halpe_26_keypoints[keypoint_id],
            "raw_x": raw_x,
            "raw_y": raw_y,
            "score":score,
            "observed": is_observed,
            # imputed에 보간 좌표가 있다면(not None) x를 저장하고 아니면 결측처리
            # 보간되지 않으면 imputed값이 None이라 imputed_x,y 모두 NaN나옴
            "imputed_x": imputed[0] if imputed is not None else np.nan,
            "imputed_y": imputed[1] if imputed is not None else np.nan,
            "x":x,
            "y":y,
            "coordinate_source": coordinate_source,
             # 최종 분석 좌표인 x,y가 어디서 나온 값인지 기록하는 col로 위에서 정의한 3가지 값이 저장


        })
rows


# rows 리스트를 DF로 변환
keypoints_df= pd.DataFrame(rows)

# 가독성 up
keypoints_df.groupby("keypoint_name")["coordinate_source"].value_counts().unstack(fill_value=0)

# pivot_table을 이용해 긴 형태의 DF를 계산, 비율 구하기 쉽게 바꾸자
x_pv_df= keypoints_df.pivot(
    index= "frame_number", # 하나의 프레임을 하나의 행으로 배치
    columns= "keypoint_name", # 관절 이름들은 col로 배치
    values= "x", # 각 칸에 x좌표 입력
)

x_pv_df.head()

# y좌표 같은 방식으로 변환
y_pv_df= keypoints_df.pivot(
    index= "frame_number",
    columns= "keypoint_name",
    values="y"
)


# x, y열을 구분하기 위해 관절 이름뒤에 _를 붙여 정의
x_pv_df= x_pv_df.add_suffix("_x")
y_pv_df= y_pv_df.add_suffix("_y")

# 이 두개를 프레임 번호 기준으로 합치기->같은 프레임 번호 행끼리 연결됨
frame_keypoints_df= x_pv_df.join(y_pv_df)

# 프레임 메타데이터 표 만들기
frame_metadata_df= keypoints_df[[
    "frame_number",
    "image_path",
    "track_id",
    "bbox_score"
]].drop_duplicates(subset= "frame_number").set_index("frame_number")
# 동일 프레임 정보가 26번 반복되는데 프레임 번호를 기준으로 중복을 제거하여 한 프레임당 한 행만 남긴다.
# 그리고 프레임 번호를 인덱스로 지정함 그래야 가독성도 좋고 안전히 합치기 가능
frame_metadata_df.head()


# 프레임 메타데이터 + 관절좌표를 합친다. 프레임 번호 기준으로
frame_data_df= frame_metadata_df.join(
    frame_keypoints_df,
    how= "inner" # 양쪽 모두다 있는 프레임만 유지
)

f1_df= frame_data_df.copy()

# 어꺠 평균좌표(상체 기울기를 Halpe에서는 이렇게 대체해야 함)
f1_df["shoulder_center_x"]= (
    f1_df["left_shoulder_x"] + f1_df["right_shoulder_x"]
) / 2

f1_df["shoulder_center_y"] = (
    f1_df["left_shoulder_y"]
    + f1_df["right_shoulder_y"]
) / 2

# f1_df에서 양쪽 발목 x,y 좌표를 가져온다.
ankle_check = f1_df[
    [
        "left_ankle_x",
        "left_ankle_y",
        "right_ankle_x",
        "right_ankle_y",
    ]
].copy()

ankle_check.head()

# 한 프레임에서 튀는 좌표를 약하게 완화하는 전처리(약한 평활화)
ankle_check["left_ankle_y_smooth"]= ankle_check["left_ankle_y"]\
    .rolling(window=3, center=True).median()
# window=3 -> 현 프레임과 앞뒤 프레임을 함께 확인
# center=True: 현재 프레임을 중심으로 계산
# median() 세 값의 가운데 값을 사용
ankle_check["right_ankle_y_smooth"]= ankle_check["right_ankle_y"]\
    .rolling(window=3, center=True).median()

# 상위 5개 값만 출력
ankle_check[
    [
        "left_ankle_y",
        "left_ankle_y_smooth",
        "right_ankle_y",
        "right_ankle_y_smooth",
    ]
].head(5)

# 발목의 봉우리 찾기
from scipy.signal import find_peaks
# 사이파이의 find_peaks를 이용해 주변보다 값이 큰 봉우리를 찾는다.

left_ankle_series= ankle_check["left_ankle_y_smooth"].dropna()
right_ankle_series= ankle_check["right_ankle_y_smooth"].dropna()

# 본격적으로 봉우리 탐색
left_peak_spots,_ = find_peaks(
    left_ankle_series.to_numpy(),
    distance=15, # 봉우리끼리 최소 15프레임 이상 떨어지도록 제한,
    prominence= 20, # 주변보다 최소 약 20픽셀이상 뚜렷한 봉우리만 선택
)

right_peak_spots,_ = find_peaks(
    right_ankle_series.to_numpy(),
    distance=15, # 봉우리끼리 최소 15프레임 이상 떨어지도록 제한,
    prominence= 20, # 주변보다 최소 약 20픽셀이상 뚜렷한 봉우리만 선택
)

# 봉우리 프레임
left_peak_frames= left_ankle_series.index[
    left_peak_spots
]

right_peak_frames= left_ankle_series.index[
    right_peak_spots
]

print("왼발 후보 프레임:", left_peak_frames.tolist())
print("오른발 후보 프레임:", right_peak_frames.tolist())

print("왼발 후보 개수:", len(left_peak_frames))
print("오른발 후보 개수:", len(right_peak_frames))


# 양쪽 후보들 합치기
left_events = pd.DataFrame({
    "frame_number": left_peak_frames,
    "support_side": "left", # 해당 프레임에서 아래 쪽에 있는 발
})

right_events = pd.DataFrame({
    "frame_number": right_peak_frames,
    "support_side": "right",
})

support_events= pd.concat(
    [left_events, right_events],
    ignore_index=True
).sort_values("frame_number").reset_index(drop=True)

# 이전 후보와 현재 후바 사이의 프레임 수 칼럼 추가(frame_interval)
support_events["frame_interval"] = support_events["frame_number"].diff()

support_events

support_features = (
    support_events
    .set_index("frame_number")
    .join(
        f1_df[
            [
                "shoulder_center_x",
                "shoulder_center_y",
                "left_ankle_x",
                "left_ankle_y",
                "right_ankle_x",
                "right_ankle_y",
            ]
        ]
    )
)


support_features["support_ankle_x"] = np.where(
    support_features["support_side"] == "left",
    support_features["left_ankle_x"],
    support_features["right_ankle_x"],
)

support_features["support_ankle_y"] = np.where(
    support_features["support_side"] == "left",
    support_features["left_ankle_y"],
    support_features["right_ankle_y"],
)


running_direction = -1

# 지지발목(Ankle)에서 어깨 중심으로 이어지는 선의 전방 기울기 계산
support_features["postural_lean_deg"]= np.degrees(
    np.arctan2(
        running_direction * (
            support_features["shoulder_center_x"] -
            support_features["support_ankle_x"]
        ),
        support_features["support_ankle_y"] -
        support_features["shoulder_center_y"]
    )
)

print(support_features["postural_lean_deg"].mean().round(2))