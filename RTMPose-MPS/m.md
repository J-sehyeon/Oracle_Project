SAPIENS2_DEVICE=mps ./scripts/run_sapiens2_pose.sh \     
  "$PWD/inputs/videos/test1/frames" \                                               
  "$PWD/outputs/test1_frames"  

.venv-sapiens2/bin/python scripts/filter_to_coco17.py \
  --input-json "$PWD/outputs/test1_frames/test1_frames_predictions.json" \
  --frames-dir "$PWD/inputs/videos/test1/frames" \
  --output-dir "$PWD/outputs/test1_coco17_frames"