import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Users/hyeon/SeSAC_Project";
const buildDir = path.join(workspaceDir, ".codex-ppt-build");
const assetDir = "/private/tmp/runners-eye-ppt-build/assets/ppt/media";
const demoPoster = "/private/tmp/runners-eye-ppt-build/assets/demo-poster.png";
const outputPath = path.join(buildDir, "candidate.pptx");

await fs.mkdir(buildDir, { recursive: true });

const W = 1280;
const H = 720;
const FONT = "Pretendard";
const C = {
  bg: "#070A08",
  panel: "#101512",
  panel2: "#151B17",
  line: "#283029",
  white: "#F5F7F5",
  muted: "#98A099",
  lime: "#B9FF2C",
  limeSoft: "#26350E",
  amber: "#F4C84B",
  cyan: "#42D9D0",
};

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

function addText(slide, value, left, top, width, height, size = 24, color = C.white, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    typeface: FONT,
    fontSize: size,
    bold: opts.bold ?? false,
    color,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: opts.autoFit ?? "none",
    wrap: "square",
    lineSpacing: opts.lineSpacing ?? 1.0,
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return shape;
}

function addRect(slide, left, top, width, height, fill = C.panel, stroke = C.line, radius = 10, strokeWidth = 1) {
  return slide.shapes.add({
    geometry: radius > 0 ? "roundRect" : "rect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: stroke, width: strokeWidth },
    borderRadius: radius,
  });
}

function addRule(slide, left, top, width, color = C.line, weight = 1) {
  return slide.shapes.add({
    geometry: "line",
    position: { left, top, width, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function addLine(slide, left, top, width, height, color = C.line, weight = 1, style = "solid") {
  return slide.shapes.add({
    geometry: "line",
    position: { left, top, width, height },
    fill: "none",
    line: { style, fill: color, width: weight },
  });
}

function addDashedRect(slide, left, top, width, height, stroke = C.line, radius = 8, strokeWidth = 1) {
  return slide.shapes.add({
    geometry: radius > 0 ? "roundRect" : "rect",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "dashed", fill: stroke, width: strokeWidth },
    borderRadius: radius,
  });
}

function addDiamond(slide, left, top, width, height, fill = C.panel, stroke = C.line, strokeWidth = 1) {
  return slide.shapes.add({
    geometry: "diamond",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: stroke, width: strokeWidth },
  });
}

async function addImage(slide, filePath, left, top, width, height, fit = "contain", alt = "") {
  const blob = new Uint8Array(await fs.readFile(filePath));
  return slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit,
    position: { left, top, width, height },
  });
}

function addHeader(slide, page, title, section = "러너스아이 · 최종 결과 발표") {
  slide.background.fill = C.bg;
  addText(slide, section, 42, 24, 360, 20, 10, C.lime, { bold: true });
  addText(slide, String(page).padStart(2, "0"), 1194, 24, 42, 20, 10, C.muted, { align: "right" });
  addText(slide, title, 42, 72, 1138, 52, 31, C.white, { bold: true });
  addRule(slide, 42, 132, 1194, C.line, 1);
}

function addLabel(slide, number, label, x, y, width = 160) {
  addText(slide, number, x, y, 28, 24, 11, C.lime, { bold: true });
  addText(slide, label, x + 36, y - 1, width - 36, 26, 17, C.white, { bold: true });
}

// 01. Cover
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addRect(slide, 0, 0, 18, H, C.lime, C.lime, 0, 0);
  addText(slide, "러너스아이", 72, 60, 260, 28, 13, C.lime, { bold: true });
  addText(slide, "달리는 순간,\n데이터로 읽습니다", 72, 132, 560, 135, 48, C.white, { bold: true, lineSpacing: 0.95 });
  addText(slide, "러닝 영상을 자세 데이터와 실행 가능한 피드백으로 바꾸는 서비스", 72, 300, 650, 36, 20, C.muted);
  addRule(slide, 72, 370, 490, C.lime, 3);
  addText(slide, "팀 테무 꽃보다 남자", 72, 400, 280, 26, 15, C.white, { bold: true });
  addText(slide, "박재혁   정승인   정세현   박주환   유한나", 72, 438, 540, 26, 15, C.muted);
  addRect(slide, 882, 78, 282, 568, C.panel, C.line, 18, 1);
  await addImage(slide, path.join(assetDir, "image.png"), 908, 90, 228, 540, "contain", "러너스아이 홈 화면");
  addText(slide, "RUNNERS EYE", 953, 654, 150, 18, 10, C.muted, { align: "center" });
  slide.speakerNotes.textFrame.setText("약 20초. 서비스 이름과 한 문장 설명만 전달한다. Source: 기존 발표자료 1장.");
}

// 02. Team roles
{
  const slide = presentation.slides.add();
  addHeader(slide, 2, "팀 구성과 역할", "01 · 소개");
  addText(slide, "발표 전 각 담당 영역을 입력할 수 있도록 역할 칸을 비워 두었습니다", 42, 152, 760, 28, 15, C.muted);
  const members = ["박재혁", "정승인", "정세현", "박주환", "유한나"];
  const positions = [
    [66, 222], [440, 222], [814, 222], [252, 426], [626, 426],
  ];
  for (let i = 0; i < members.length; i += 1) {
    const [x, y] = positions[i];
    addText(slide, String(i + 1).padStart(2, "0"), x, y, 36, 24, 12, C.lime, { bold: true });
    addText(slide, members[i], x, y + 34, 250, 38, 26, C.white, { bold: true });
    addRule(slide, x, y + 98, 300, C.lime, 2);
    addText(slide, "역할  ____________________", x, y + 116, 300, 30, 16, C.muted);
  }
  slide.speakerNotes.textFrame.setText("팀원 역할 정보는 제공 자료에 없어 빈칸으로 유지한다. 발표 전 담당 업무를 한 줄씩 입력한다.");
}

// 03. Service overview
{
  const slide = presentation.slides.add();
  addHeader(slide, 3, "러너스아이 서비스", "02 · 서비스 소개");
  addText(slide, "측면 러닝 영상 한 번으로 자세 측정, 설명, 변화 기록까지 연결합니다", 42, 152, 760, 32, 18, C.muted);
  const steps = [
    ["01", "영상 입력", "측면 전신이 보이는 짧은 MP4와 사용자 키"],
    ["02", "자세 분석", "관절 좌표에서 네 가지 러닝 자세 특성값 계산"],
    ["03", "리포트와 기록", "측정값, 개선 피드백, 스켈레톤 영상을 저장"],
  ];
  let y = 230;
  for (const [n, t, d] of steps) {
    addText(slide, n, 58, y, 36, 24, 12, C.lime, { bold: true });
    addText(slide, t, 112, y - 4, 210, 30, 22, C.white, { bold: true });
    addText(slide, d, 112, y + 38, 470, 46, 16, C.muted);
    addRule(slide, 112, y + 98, 445, C.line, 1);
    y += 130;
  }
  addRect(slide, 708, 175, 218, 463, C.panel, C.line, 16, 1);
  addRect(slide, 962, 175, 218, 463, C.panel, C.line, 16, 1);
  await addImage(slide, path.join(assetDir, "image2.png"), 730, 188, 174, 438, "contain", "러닝 영상 업로드 화면");
  await addImage(slide, path.join(assetDir, "image4.png"), 984, 188, 174, 438, "contain", "분석 결과 화면");
  addText(slide, "업로드", 760, 644, 120, 22, 12, C.muted, { align: "center" });
  addText(slide, "분석 결과", 1010, 644, 126, 22, 12, C.muted, { align: "center" });
  slide.speakerNotes.textFrame.setText("약 40초. Source: 기존 발표자료 4~7장과 앱 화면 이미지. 진단 서비스가 아니라 러닝 자세 분석 및 피드백 서비스로 설명한다.");
}

// 04. Demo video placeholder
{
  const slide = presentation.slides.add();
  addHeader(slide, 4, "서비스 시연", "03 · 시연 영상");
  addRect(slide, 42, 164, 820, 462, "#020302", C.line, 10, 1);
  await addImage(slide, demoPoster, 52, 174, 800, 442, "cover", "HPE 결과 영상 포스터");
  addText(slide, "▶", 388, 326, 92, 92, 64, C.lime, { bold: true, align: "center", valign: "middle" });
  addText(slide, "VIDEO PLACEHOLDER", 58, 586, 210, 18, 10, C.lime, { bold: true });
  addText(slide, "발표용 서비스 시연 영상으로 교체", 895, 182, 315, 34, 20, C.white, { bold: true });
  const checks = ["영상 선택과 분석 요청", "진행 상태 확인", "자세 점수와 핵심 피드백", "기록 화면 재조회"];
  let y = 256;
  for (let i = 0; i < checks.length; i += 1) {
    addLabel(slide, String(i + 1).padStart(2, "0"), checks[i], 900, y, 300);
    addRule(slide, 900, y + 38, 286, C.line, 1);
    y += 72;
  }
  addRect(slide, 892, 560, 304, 70, C.panel2, C.amber, 8, 1);
  addText(slide, "현재는 Coach 출력 영상의 대표 프레임입니다\n영상 파일을 받으면 같은 영역에 교체합니다", 910, 574, 268, 42, 13, C.amber, { bold: true });
  slide.speakerNotes.textFrame.setText("서비스 시연 영상 파일이 제공되지 않아 교체 가능한 영상 영역으로 구성했다. 현재 포스터는 Coach/run/test12/outputs/output.mp4의 대표 프레임이다.");
}

// 05. Video to HPE, features and Agent
{
  const slide = presentation.slides.add();
  addHeader(slide, 5, "영상에서 분석 리포트까지", "04 · 분석 파이프라인");
  addText(slide, "러닝 영상의 관절 좌표를 추출하고 움직임 피처를 계산해 에이전트 입력으로 전달합니다", 42, 150, 940, 26, 16, C.muted);
  const arrow = { type: "arrow", width: "med", length: "med" };

  const videoStage = addRect(slide, 42, 190, 250, 330, C.panel, C.line, 12, 1);
  addText(slide, "01", 58, 206, 28, 16, 10, C.lime, { bold: true });
  await addImage(slide, path.join(buildDir, "avatar-video-v1.png"), 52, 234, 230, 218, "contain", "주석이 없는 3D 러너 아바타 영상 프레임");
  addRect(slide, 137, 310, 60, 60, C.bg, C.lime, 30, 2);
  addText(slide, "▶", 147, 322, 40, 36, 26, C.lime, { bold: true, align: "center", valign: "middle" });
  addText(slide, "MP4 · 측면 러닝 영상", 64, 476, 206, 20, 12, C.white, { bold: true, align: "center" });

  const hpeStage = addRect(slide, 342, 190, 250, 330, C.panel, C.line, 12, 1);
  addText(slide, "02", 358, 206, 28, 16, 10, C.lime, { bold: true });
  await addImage(slide, path.join(buildDir, "avatar-hpe-v1.png"), 352, 234, 230, 218, "contain", "3D 러너 아바타의 전신 관절 키포인트와 스켈레톤");
  addText(slide, "26개 관절 좌표 · confidence", 358, 476, 218, 20, 12, C.white, { bold: true, align: "center" });

  const featureStage = addRect(slide, 642, 190, 250, 330, C.panel, C.line, 12, 1);
  addText(slide, "03", 658, 206, 28, 16, 10, C.lime, { bold: true });
  addRect(slide, 652, 234, 110, 218, "#020302", C.line, 8, 1);
  await addImage(slide, path.join(buildDir, "avatar-angle-v1.png"), 658, 240, 98, 206, "cover", "3D 러너 아바타의 정밀 팔꿈치 관절 각도 시각화");
  addRect(slide, 772, 234, 110, 218, "#020302", C.line, 8, 1);
  await addImage(slide, path.join(buildDir, "avatar-speed-v1.png"), 778, 240, 98, 206, "cover", "3D 러너 아바타의 프레임 간 이동 속도 시각화");
  addRect(slide, 697, 304, 52, 18, C.bg, C.cyan, 5, 1);
  addText(slide, "102.4°", 702, 309, 42, 10, 7, C.cyan, { bold: true, align: "center" });
  addText(slide, "t₀   t₁   t₂", 786, 250, 82, 12, 7, C.muted, { bold: true, align: "center" });
  addRect(slide, 660, 426, 94, 20, C.bg, C.cyan, 5, 1);
  addText(slide, "관절 각도  θ", 668, 431, 78, 11, 8, C.cyan, { bold: true, align: "center" });
  addRect(slide, 780, 426, 94, 20, C.bg, C.lime, 5, 1);
  addText(slide, "속도  Δp / Δt", 788, 431, 78, 11, 8, C.lime, { bold: true, align: "center" });
  addText(slide, "프레임 간 좌표 변화 계산", 658, 476, 218, 20, 12, C.white, { bold: true, align: "center" });

  const agentStage = addRect(slide, 942, 190, 296, 330, C.panel, C.line, 12, 1);
  addText(slide, "04", 958, 206, 28, 16, 10, C.lime, { bold: true });
  const agentNode = addDiamond(slide, 958, 298, 82, 82, C.limeSoft, C.lime, 2);
  addText(slide, "AI\nAGENT", 974, 319, 50, 36, 12, C.white, { bold: true, align: "center" });
  const dashboard = addRect(slide, 1056, 230, 166, 244, "#020302", C.line, 8, 1);
  await addImage(slide, path.join(assetDir, "image9.png"), 1062, 236, 154, 232, "cover", "러닝 통계와 피처 추이 화면");
  slide.shapes.connect(agentNode, dashboard, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  addText(slide, "통계 · 판정 · 코칭 리포트", 958, 484, 264, 18, 12, C.white, { bold: true, align: "center" });

  slide.shapes.connect(videoStage, hpeStage, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(hpeStage, featureStage, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(featureStage, agentNode, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });
  addText(slide, "KEYPOINTS", 282, 328, 70, 12, 7, C.lime, { bold: true, align: "center" });
  addText(slide, "FEATURES", 582, 328, 70, 12, 7, C.lime, { bold: true, align: "center" });
  addText(slide, "VALUES", 882, 328, 70, 12, 7, C.cyan, { bold: true, align: "center" });

  const labels = [
    [42, "영상", "Video"],
    [342, "HPE 데이터 추출", "Pose Estimation"],
    [642, "피처 계산", "Angle · Velocity"],
    [942, "에이전트 분석", "Report"],
  ];
  for (const [x, ko, en] of labels) {
    addText(slide, en.toUpperCase(), x, 552, x === 942 ? 296 : 250, 16, 9, C.lime, { bold: true, align: "center" });
    addText(slide, ko, x, 578, x === 942 ? 296 : 250, 30, 20, C.white, { bold: true, align: "center" });
  }
  addText(slide, "main.sh는 HPE, 피처 계산, 에이전트를 순차 실행합니다", 42, 650, 1196, 20, 12, C.muted, { align: "center" });
  slide.speakerNotes.textFrame.setText("Source: Coach/run/test12/transformed.mp4, Coach/run/test12/outputs/output.mp4, 기존 발표자료의 피처 이미지와 기록 화면, Coach/scripts/main.sh. 영상, HPE, 피처, 에이전트의 4단계 흐름을 한 장에 합쳤다.");
}

// 06. Style-only recreation of the supplied analysis-pipeline image
{
  const slide = presentation.slides.add();
  addHeader(slide, 6, "Coach 분석 파이프라인", "04 · 분석 파이프라인");
  const arrow = { type: "arrow", width: "med", length: "med" };

  // The original composition is intentionally retained: input at left, the
  // HPE stack above, interpolation at right, circular return, then Agent below.
  const video = addRect(slide, 42, 314, 118, 58, C.panel, C.line, 9, 1);
  addText(slide, "영상 입력", 58, 333, 86, 20, 14, C.white, { bold: true, align: "center" });
  const split = addRect(slide, 204, 300, 158, 86, C.panel2, C.lime, 10, 2);
  addText(slide, "프레임 단위로 분할", 220, 329, 126, 22, 14, C.white, { bold: true, align: "center" });

  const analysisGroup = addRect(slide, 468, 164, 224, 238, C.panel2, C.line, 12, 1);
  const detect = addDiamond(slide, 500, 180, 160, 62, C.panel, C.line, 1);
  addText(slide, "detection", 530, 201, 100, 18, 12, C.white, { bold: true, align: "center" });
  const spec = addDiamond(slide, 500, 254, 160, 62, C.panel, C.line, 1);
  addText(slide, "촬영 규격 검사", 524, 275, 112, 18, 12, C.white, { bold: true, align: "center" });
  const pose = addDiamond(slide, 500, 328, 160, 62, C.limeSoft, C.lime, 2);
  addText(slide, "human pose\nestimation", 528, 342, 104, 34, 11, C.white, { bold: true, align: "center" });

  const buffer = addRect(slide, 754, 204, 180, 96, C.panel, C.line, 10, 1);
  addText(slide, "5개 프레임 임시 저장", 770, 220, 148, 18, 12, C.white, { bold: true, align: "center" });
  addText(slide, "t-2 frame\nt-1 frame\nt frame\nt+1 frame\nt+2 frame", 790, 245, 108, 48, 9, C.muted, { bold: true, align: "center", lineSpacing: 0.9 });

  const interpolation = addRect(slide, 942, 268, 296, 180, C.panel2, C.line, 10, 1);
  addText(slide, "Interpolation", 1030, 282, 120, 18, 13, C.lime, { bold: true, align: "center" });
  addRule(slide, 1008, 306, 164, C.lime, 2);
  addLine(slide, 970, 350, 228, 0, C.muted, 1);
  addText(slide, "Frame", 1198, 342, 36, 16, 9, C.muted, { bold: true });
  const gx = [982, 1028, 1074, 1120, 1166];
  const gy = [400, 384, 374, 388, 410];
  slide.shapes.add({
    geometry: "custom",
    position: { left: 982, top: 366, width: 184, height: 50 },
    customPaths: [{ width: 184, height: 50, commands: [
      { moveTo: { x: 0, y: 34 } }, { lineTo: { x: 46, y: 18 } },
      { lineTo: { x: 92, y: 8 } }, { lineTo: { x: 138, y: 22 } },
      { lineTo: { x: 184, y: 44 } },
    ] }],
    fill: "none",
    line: { style: "solid", fill: C.white, width: 2 },
  });
  for (let i = 0; i < gx.length; i += 1) {
    addLine(slide, gx[i], 338, 0, 88, C.line, 1, "dashed");
    addRect(slide, gx[i] - 4, gy[i] - 4, 8, 8, i === 2 ? C.bg : C.lime, i === 2 ? C.cyan : C.lime, 4, 2);
    addText(slide, ["t-2", "t-1", "t", "t+1", "t+2"][i], gx[i] - 16, 326, 32, 12, 8, C.muted, { bold: true, align: "center" });
  }
  addRect(slide, 1070, 324, 8, 8, C.bg, "#FF675F", 4, 2);
  addLine(slide, 1074, 332, 0, 32, "#FF675F", 1, "dashed");
  addText(slide, "↓", 1065, 342, 18, 18, 14, "#FF675F", { bold: true, align: "center" });

  const save = addRect(slide, 638, 464, 184, 68, C.panel, C.line, 10, 1);
  addText(slide, "t-2 frame\n비디오에 저장", 660, 480, 140, 38, 12, C.white, { bold: true, align: "center" });
  const features = addRect(slide, 618, 554, 232, 70, C.panel2, C.line, 10, 1);
  addText(slide, "Human Pose Estimation\n데이터에서 피처 추출", 640, 572, 188, 38, 12, C.white, { bold: true, align: "center" });
  const agent = addDiamond(slide, 916, 552, 152, 72, C.limeSoft, C.lime, 2);
  addText(slide, "Agent", 956, 578, 72, 18, 13, C.white, { bold: true, align: "center" });
  const report = addRect(slide, 1114, 558, 124, 60, C.panel, C.line, 9, 1);
  addText(slide, "Report", 1136, 578, 80, 18, 13, C.white, { bold: true, align: "center" });
  const prompt = addRect(slide, 850, 640, 284, 66, C.panel, C.amber, 9, 1);
  addText(slide, "prompts", 866, 650, 70, 14, 9, C.amber, { bold: true });
  addText(slide, "당신은 러닝 자세 분석 리포트를 작성하는 AI 입니다.   {INSTRUCTION}   {features}", 866, 670, 252, 28, 8, C.white, { bold: true, autoFit: "shrink" });

  slide.shapes.connect(video, split, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(split, analysisGroup, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(detect, spec, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.lime, width: 1.5 }, tail: arrow });
  slide.shapes.connect(spec, pose, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.lime, width: 1.5 }, tail: arrow });
  slide.shapes.connect(analysisGroup, buffer, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(buffer, interpolation, { kind: "straight", fromSide: "right", toSide: "top", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(interpolation, save, { kind: "straight", fromSide: "bottom", toSide: "right", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });
  slide.shapes.connect(save, split, { kind: "elbow4", fromSide: "left", toSide: "bottom", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });
  slide.shapes.connect(save, features, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(features, agent, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(agent, report, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: arrow });
  slide.shapes.connect(prompt, agent, { kind: "straight", fromSide: "top", toSide: "bottom", line: { style: "dashed", fill: C.amber, width: 1.5 }, tail: arrow });
  addText(slide, "t+3 frame load", 352, 258, 110, 16, 9, C.lime, { bold: true, align: "center" });
  slide.speakerNotes.textFrame.setText("Source: 사용자 제공 codex-clipboard-2ed76b86-2e47-4cdc-b27d-c352b1b25716.png. 내용, 객체 위치, 보간 그래프, 화살표 방향과 연결 관계는 변경하지 않고 선·배경·폰트·강조색만 발표자료 스타일로 변경했다.");
}

// 07. Features
{
  const slide = presentation.slides.add();
  addHeader(slide, 7, "네 가지 자세 피처 추출", "04 · 분석 파이프라인");
  addText(slide, "pose_predictions.json, details.json, user_info.json을 PoseSequence로 묶어 네 가지 피처를 계산합니다", 42, 152, 1040, 30, 17, C.muted);
  const pics = ["image5.png", "image6.png", "image7.png", "image8.png"];
  const labels = [
    ["골반 수직 진동", "접지 중 골반 높이 변화 ÷ 신장"],
    ["팔꿈치 각도", "한 스트라이드의 각도 범위"],
    ["몸통 굴곡", "어깨 중심과 골반 중심의 기울기"],
    ["전방 자세 기울기", "목과 발목을 잇는 선의 각도"],
  ];
  for (let i = 0; i < 4; i += 1) {
    const x = 42 + i * 302;
    addRect(slide, x, 206, 264, 330, "#020302", C.line, 10, 1);
    await addImage(slide, path.join(assetDir, pics[i]), x + 10, 216, 244, 310, "contain", labels[i][0]);
    addText(slide, String(i + 1).padStart(2, "0"), x, 554, 30, 22, 11, C.lime, { bold: true });
    addText(slide, labels[i][0], x + 38, 550, 220, 28, 18, C.white, { bold: true });
    addText(slide, labels[i][1], x + 38, 586, 220, 42, 13, C.muted);
  }
  addText(slide, "OUTPUT", 42, 656, 70, 18, 10, C.lime, { bold: true });
  addText(slide, "cal_stride, pixel2m, gct 이후 feature1~4 실행 · feature_results.json 저장", 128, 653, 920, 22, 13, C.white, { bold: true });
  slide.speakerNotes.textFrame.setText("Source: Coach/scripts/features/feature_extract.py, Coach/scripts/features/utils.py. 네 함수 feature1~feature4와 PoseSequence의 cal_stride, gct, pixel2m을 설명한다.");
}

// 08. Agent
{
  const slide = presentation.slides.add();
  addHeader(slide, 8, "판정 로직과 Coach 에이전트", "04 · 분석 파이프라인");
  addText(slide, "수치 계산과 문장 생성을 분리해 결과의 근거를 추적할 수 있습니다", 42, 152, 820, 30, 17, C.muted);

  addText(slide, "DETERMINISTIC", 58, 214, 180, 18, 11, C.lime, { bold: true });
  addText(slide, "피처 계산과 구간 판정", 58, 248, 360, 34, 24, C.white, { bold: true });
  addText(slide, "feature_results.json에 측정값, 기준 구간,\n행동 지시, 결과 해석을 구조화해 저장", 58, 300, 448, 74, 17, C.muted, { lineSpacing: 1.15 });
  addRect(slide, 58, 402, 438, 154, C.panel, C.line, 10, 1);
  addText(slide, "{\n  value,\n  range 또는 boundary,\n  instruction, outcome\n}", 80, 424, 240, 110, 15, C.white, { bold: true, lineSpacing: 1.05 });
  addText(slide, "4개 피처", 360, 442, 104, 24, 13, C.lime, { bold: true, align: "right" });
  addText(slide, "Rule Base 결과", 332, 482, 132, 24, 13, C.muted, { align: "right" });

  addRect(slide, 566, 205, 2, 396, C.lime, C.lime, 0, 0);

  addText(slide, "LANGCHAIN", 626, 214, 150, 18, 11, C.lime, { bold: true });
  addText(slide, "gpt-5-nano가 리포트 작성", 626, 248, 500, 34, 24, C.white, { bold: true });
  addText(slide, "현재 Coach 코드는 feature_results.json만 모델에 전달합니다.\n모델은 수치를 다시 계산하지 않고 설명 문장을 작성합니다", 626, 300, 540, 74, 17, C.muted, { lineSpacing: 1.15 });
  const flow1 = addRect(slide, 626, 416, 168, 94, C.panel2, C.line, 10, 1);
  addText(slide, "입력", 644, 432, 50, 18, 11, C.lime, { bold: true });
  addText(slide, "feature_results.json", 644, 466, 134, 26, 13, C.white, { bold: true });
  const flow2 = addRect(slide, 852, 416, 168, 94, C.limeSoft, C.lime, 10, 2);
  addText(slide, "모델", 870, 432, 50, 18, 11, C.lime, { bold: true });
  addText(slide, "gpt-5-nano", 870, 466, 134, 26, 15, C.white, { bold: true });
  const promptInput = addRect(slide, 852, 378, 168, 28, C.panel, C.amber, 6, 1);
  addText(slide, "PERSONA + INSTRUCTION", 862, 386, 148, 12, 9, C.amber, { bold: true, align: "center" });
  const flow3 = addRect(slide, 1078, 416, 146, 94, C.panel2, C.line, 10, 1);
  addText(slide, "출력", 1094, 432, 50, 18, 11, C.lime, { bold: true });
  addText(slide, "running_report.md", 1094, 466, 114, 28, 12, C.white, { bold: true });
  slide.shapes.connect(flow1, flow2, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
  slide.shapes.connect(flow2, flow3, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
  slide.shapes.connect(promptInput, flow2, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "dashed", fill: C.amber, width: 1 }, tail: { type: "arrow", width: "sm", length: "sm" } });
  addRect(slide, 626, 560, 598, 62, C.panel, C.amber, 8, 1);
  addText(slide, "현재 Coach 구현 모델  gpt-5-nano · 기존 PPT의 모델 표기를 코드 기준으로 업데이트", 646, 580, 558, 24, 13, C.amber, { bold: true });
  slide.speakerNotes.textFrame.setText("Source: Coach/scripts/Agent/Running_coach.py, Coach/scripts/Agent/prompts.py. 현재 모델명은 gpt-5-nano이며 feature_results.json을 입력으로 running_report.md를 생성한다.");
}

// 09. Style-only recreation of the supplied service-architecture image
{
  const slide = presentation.slides.add();
  addHeader(slide, 9, "러너스 피드 영상 분석 서비스 기술 아키텍처", "05 · 인프라");
  const arrow = { type: "arrow", width: "sm", length: "sm" };

  // Original zones and nesting.
  addDashedRect(slide, 20, 144, 1240, 424, C.line, 8, 1);
  addText(slide, "러너스 피드 서비스 영역", 34, 150, 154, 15, 9, C.lime, { bold: true });
  addDashedRect(slide, 28, 170, 150, 382, C.line, 8, 1);
  addText(slide, "사용자 / 외부 네트워크", 40, 180, 128, 16, 9, C.white, { bold: true, align: "center" });
  addDashedRect(slide, 196, 170, 838, 382, C.line, 8, 1);
  addDashedRect(slide, 214, 190, 802, 164, C.line, 8, 1);
  addText(slide, "웹 · API 계층", 566, 180, 120, 16, 10, C.white, { bold: true, align: "center" });
  addDashedRect(slide, 296, 382, 492, 158, C.line, 8, 1);
  addText(slide, "비동기 추론 파이프라인", 430, 365, 210, 16, 10, C.white, { bold: true, align: "center" });
  addDashedRect(slide, 800, 382, 206, 158, C.line, 8, 1);
  addDashedRect(slide, 1050, 170, 196, 382, C.line, 8, 1);
  addText(slide, "데이터 · 결과 저장소", 1068, 180, 160, 16, 9, C.white, { bold: true, align: "center" });

  const user = addRect(slide, 56, 222, 94, 58, C.panel, C.line, 9, 1);
  addText(slide, "MP4 선택\n+ 분석 이름 입력", 68, 234, 70, 34, 10, C.white, { bold: true, align: "center" });
  const browser = addRect(slide, 52, 314, 102, 62, C.panel2, C.line, 9, 1);
  addText(slide, "Browser", 66, 335, 74, 20, 13, C.white, { bold: true, align: "center" });

  const next = addRect(slide, 238, 218, 136, 72, C.panel, C.line, 8, 1);
  addText(slide, "NEXT.js", 256, 237, 100, 22, 16, C.white, { bold: true, align: "center" });
  addText(slide, "Next.js UI", 254, 268, 104, 14, 9, C.muted, { bold: true, align: "center" });
  const nginx = addRect(slide, 454, 218, 112, 72, C.panel, C.line, 8, 1);
  addText(slide, "NGINX", 470, 238, 80, 20, 15, C.white, { bold: true, align: "center" });
  addText(slide, "Nginx", 470, 268, 80, 14, 9, C.muted, { bold: true, align: "center" });
  const api = addRect(slide, 648, 218, 146, 72, C.limeSoft, C.lime, 8, 2);
  addText(slide, "FastAPI", 666, 237, 110, 22, 16, C.white, { bold: true, align: "center" });
  addText(slide, "API", 684, 268, 74, 14, 9, C.lime, { bold: true, align: "center" });

  const db = addRect(slide, 316, 424, 104, 74, C.panel, C.line, 8, 1);
  addText(slide, "PostgreSQL", 326, 449, 84, 18, 12, C.white, { bold: true, align: "center" });
  const redis = addRect(slide, 448, 424, 96, 74, C.panel, C.line, 8, 1);
  addText(slide, "Redis", 464, 449, 64, 18, 13, C.white, { bold: true, align: "center" });
  const celery = addRect(slide, 572, 424, 96, 74, C.panel, C.line, 8, 1);
  addText(slide, "Celery", 586, 449, 68, 18, 13, C.white, { bold: true, align: "center" });
  const worker = addRect(slide, 696, 408, 80, 106, C.limeSoft, C.lime, 8, 2);
  addText(slide, "Inference\nWorker", 706, 432, 60, 36, 12, C.white, { bold: true, align: "center" });
  addText(slide, "GPU", 716, 486, 40, 14, 9, C.lime, { bold: true, align: "center" });

  const procNames = ["15-1. OpenCV", "15-2. RTMPose", "15-3. Metrics & Evidence", "15-4. Ollama", "15-5. Joint Overlay Renderer", "15-6. Result Packager"];
  const procBoxes = [];
  for (let i = 0; i < procNames.length; i += 1) {
    const y = 392 + i * 23;
    const p = addRect(slide, 812, y, 182, 19, i === 3 ? C.panel : C.bg, i === 3 ? C.amber : C.line, 4, 1);
    procBoxes.push(p);
    addText(slide, procNames[i], 818, y + 4, 170, 11, i === 2 || i === 4 ? 7 : 8, i === 3 ? C.amber : C.white, { bold: true, align: "center" });
  }

  const raw = addRect(slide, 1070, 216, 156, 92, C.panel, C.line, 8, 1);
  addText(slide, "OCI Raw Bucket", 1082, 237, 132, 18, 12, C.white, { bold: true, align: "center" });
  addText(slide, "OCI Object Storage", 1082, 271, 132, 15, 9, C.muted, { align: "center" });
  const results = addRect(slide, 1070, 432, 156, 98, C.panel, C.line, 8, 1);
  addText(slide, "OCI Results Bucket", 1080, 454, 136, 18, 11, C.white, { bold: true, align: "center" });
  addText(slide, "OCI Object Storage", 1082, 490, 132, 15, 9, C.muted, { align: "center" });
  const resultBendTop = slide.shapes.add({ geometry: "rect", position: { left: 1022, top: 318, width: 2, height: 2 }, fill: "none", line: { fill: "none", width: 0 } });
  const resultBendBottom = slide.shapes.add({ geometry: "rect", position: { left: 1022, top: 480, width: 2, height: 2 }, fill: "none", line: { fill: "none", width: 0 } });

  // API/control paths (white/lime), video/result data (cyan), optional path (amber).
  slide.shapes.connect(user, browser, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(browser, next, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  slide.shapes.connect(next, nginx, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  slide.shapes.connect(nginx, api, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  slide.shapes.connect(api, raw, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  slide.shapes.connect(next, api, { kind: "elbow3", fromSide: "bottom", toSide: "left", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });
  slide.shapes.connect(next, api, { kind: "elbow5", fromSide: "bottom", toSide: "bottom", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(api, db, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(api, celery, { kind: "elbow", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(db, redis, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(redis, celery, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  slide.shapes.connect(celery, worker, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  slide.shapes.connect(api, worker, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(raw, worker, { kind: "elbow4", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });
  slide.shapes.connect(worker, procBoxes[0], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1.5 }, tail: arrow });
  for (let i = 0; i < procBoxes.length - 1; i += 1) {
    slide.shapes.connect(procBoxes[i], procBoxes[i + 1], { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: i === 2 ? "dashed" : "solid", fill: i === 2 ? C.amber : C.white, width: 1 }, tail: arrow });
  }
  slide.shapes.connect(procBoxes[5], results, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });
  slide.shapes.connect(worker, db, { kind: "elbow4", fromSide: "bottom", toSide: "bottom", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(api, resultBendTop, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1 } });
  slide.shapes.connect(resultBendTop, resultBendBottom, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "solid", fill: C.white, width: 1 } });
  slide.shapes.connect(resultBendBottom, results, { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(browser, api, { kind: "elbow5", fromSide: "bottom", toSide: "left", line: { style: "solid", fill: C.white, width: 1 }, tail: arrow });
  slide.shapes.connect(api, browser, { kind: "elbow4", fromSide: "bottom", toSide: "right", line: { style: "solid", fill: C.cyan, width: 2 }, tail: arrow });

  addText(slide, "POST\n/api/uploads", 386, 224, 60, 28, 8, C.white, { bold: true, align: "center" });
  addText(slide, "X-API-Key", 574, 236, 66, 13, 8, C.white, { align: "center" });
  addText(slide, "5. 임시 업로드 URL 생성", 842, 236, 190, 13, 8, C.white, { align: "center" });
  addText(slide, "6. PUT video/mp4 (직접 업로드)", 354, 300, 312, 14, 8, C.cyan, { bold: true, align: "center" });
  addText(slide, "7. POST /uploads/complete", 326, 322, 222, 13, 8, C.white, { align: "center" });
  addText(slide, "8. HEAD / size / type 검증", 704, 314, 186, 13, 8, C.white, { align: "center" });
  addText(slide, "9. POST /jobs", 364, 342, 154, 13, 8, C.white, { align: "center" });
  addText(slide, "10. Job INSERT · QUEUED", 304, 400, 150, 13, 8, C.white, { align: "center" });
  addText(slide, "11. 추론 작업 발행", 468, 400, 132, 13, 8, C.white, { align: "center" });
  addText(slide, "12. 작업 전달", 660, 452, 62, 26, 8, C.white, { align: "center" });
  addText(slide, "13. PROCESSING", 424, 512, 126, 13, 8, C.white, { align: "center" });
  addText(slide, "14. input.mp4 다운로드", 770, 360, 146, 13, 8, C.cyan, { align: "center" });
  addText(slide, "16. JSON ×3 + MP4 업로드", 976, 514, 112, 24, 8, C.cyan, { align: "center" });
  addText(slide, "17. SUCCESS + object names", 416, 532, 170, 13, 8, C.white, { align: "center" });
  addRect(slide, 184, 460, 92, 38, C.panel, C.amber, 6, 1);
  addText(slide, "2.5초 폴링\n최대 1시간", 196, 468, 68, 24, 8, C.amber, { bold: true, align: "center" });
  addText(slide, "18. GET /jobs/{job_id} 폴링", 190, 508, 118, 26, 8, C.white, { align: "center" });
  addText(slide, "19. 임시 결과 URL 제공 + 리포트 읽기", 1004, 356, 204, 24, 8, C.white, { align: "center" });
  addText(slide, "20. 결과 영상 + 측정·근거·AI 해설", 214, 548, 272, 14, 8, C.cyan, { bold: true });

  // Original bottom row: observability, optional capability, and legend.
  addDashedRect(slide, 184, 590, 492, 96, C.line, 8, 1);
  addText(slide, "관찰 가능성", 366, 576, 126, 16, 10, C.white, { bold: true, align: "center" });
  const obs = ["API 로그", "추론 로그", "작업 메트릭", "GPU 메트릭", "알림 (실패)"];
  for (let i = 0; i < obs.length; i += 1) {
    const x = 198 + i * 94;
    addRect(slide, x, 612, 80, 44, C.panel, C.line, 6, 1);
    addText(slide, obs[i], x + 6, 626, 68, 16, 8, i === 4 ? C.amber : C.white, { bold: true, align: "center" });
  }
  addDashedRect(slide, 712, 596, 218, 72, C.amber, 8, 1);
  addText(slide, "선택 기능", 782, 584, 78, 16, 9, C.amber, { bold: true, align: "center" });
  addText(slide, "Ollama AI 내러티브 생성 (선택)", 734, 622, 174, 18, 9, C.white, { bold: true, align: "center" });
  addLine(slide, 974, 608, 42, 0, C.white, 2);
  addText(slide, "API / 제어 흐름", 1022, 601, 100, 15, 8, C.white);
  addLine(slide, 974, 636, 42, 0, C.cyan, 2);
  addText(slide, "영상 / 결과 데이터", 1022, 629, 108, 15, 8, C.cyan);
  addLine(slide, 974, 664, 42, 0, C.amber, 2, "dashed");
  addText(slide, "선택 기능", 1022, 657, 80, 15, 8, C.amber);
  slide.speakerNotes.textFrame.setText("Source: 사용자 제공 codex-clipboard-681490a5-34db-4f1f-b879-3fff821df989.png. 원본의 영역 중첩, 객체 위치, 5~20번 흐름, 방향, 저장소, 관찰 가능성, 선택 기능을 유지하고 선·배경·폰트·강조색만 발표자료 스타일로 변경했다.");
}

// 10. Worker and operations
{
  const slide = presentation.slides.add();
  addHeader(slide, 10, "분석 Worker와 결과 전달", "05 · 인프라");
  addText(slide, "GPU Worker가 분석 산출물을 패키징하고, 결과 URL과 리포트를 API로 돌려줍니다", 42, 152, 920, 30, 17, C.muted);
  addText(slide, "GPU INFERENCE WORKER", 42, 204, 210, 20, 11, C.lime, { bold: true });
  const pipeline = [
    ["OpenCV", "input.mp4"],
    ["RTMPose", "관절 좌표"],
    ["Metrics & Evidence", "피처 · 근거"],
    ["Joint Overlay", "결과 영상"],
    ["Result Packager", "JSON ×3 + MP4"],
  ];
  const pipes = [];
  for (let i = 0; i < pipeline.length; i += 1) {
    const x = 42 + i * 226;
    const [title, detail] = pipeline[i];
    const box = addRect(slide, x, 244, 188, 104, i === 2 ? C.limeSoft : C.panel, i === 2 ? C.lime : C.line, 10, i === 2 ? 2 : 1);
    pipes.push(box);
    addText(slide, String(i + 1).padStart(2, "0"), x + 16, 260, 28, 18, 10, C.lime, { bold: true });
    addText(slide, title, x + 16, 290, 158, 24, i === 2 ? 15 : 18, C.white, { bold: true });
    addText(slide, detail, x + 16, 322, 158, 18, 11, C.muted);
  }
  for (const [from, to] of [[0, 1], [1, 2], [3, 4]]) {
    slide.shapes.connect(pipes[from], pipes[to], { kind: "straight", fromSide: "right", toSide: "left", line: { style: "solid", fill: C.lime, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
  }
  const ollama = addRect(slide, 534, 374, 240, 72, C.panel, C.amber, 10, 1);
  addText(slide, "OPTIONAL", 552, 388, 70, 16, 9, C.amber, { bold: true });
  addText(slide, "Ollama AI narrative", 552, 414, 190, 20, 14, C.white, { bold: true });
  addText(slide, "선택 기능 · Metrics 이후 실행", 792, 398, 240, 24, 12, C.amber, { bold: true });
  slide.shapes.connect(pipes[2], ollama, { kind: "straight", fromSide: "bottom", toSide: "top", line: { style: "dashed", fill: C.amber, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });
  slide.shapes.connect(ollama, pipes[3], { kind: "elbow", fromSide: "right", toSide: "bottom", line: { style: "dashed", fill: C.amber, width: 2 }, tail: { type: "arrow", width: "med", length: "med" } });

  addRect(slide, 42, 478, 540, 136, C.panel2, C.line, 10, 1);
  addText(slide, "RESULT DELIVERY", 62, 496, 160, 18, 10, C.lime, { bold: true });
  addText(slide, "OCI Results Bucket", 62, 528, 240, 28, 20, C.white, { bold: true });
  addText(slide, "JSON 3개와 MP4 업로드 → FastAPI가 임시 결과 URL과 리포트 제공", 62, 568, 490, 30, 13, C.muted, { bold: true });

  addRect(slide, 616, 478, 608, 136, C.panel, C.line, 10, 1);
  addText(slide, "OBSERVABILITY", 636, 496, 150, 18, 10, C.lime, { bold: true });
  const obs = ["API 로그", "추론 로그", "작업 메트릭", "GPU 메트릭", "실패 알림"];
  for (let i = 0; i < obs.length; i += 1) {
    const x = 636 + (i % 3) * 184;
    const y = 530 + Math.floor(i / 3) * 42;
    addRect(slide, x, y, 164, 30, C.panel2, C.line, 6, 1);
    addText(slide, obs[i], x + 10, y + 7, 144, 16, 11, i === 4 ? C.amber : C.white, { bold: true, align: "center" });
  }
  addText(slide, "Worker 상태는 PostgreSQL에 PROCESSING → SUCCESS와 object name으로 기록", 42, 646, 890, 20, 13, C.white, { bold: true });
  slide.speakerNotes.textFrame.setText("Source: /Users/hyeon/Downloads/시스템아키텍쳐.png. Ollama는 원본 구조도에서 선택 기능이다. 현재 Coach 코드의 리포트 에이전트는 앞 슬라이드처럼 LangChain + gpt-5-nano이며, 두 구현을 동일 구성요소로 오해하지 않도록 분리해 설명한다.");
}

// 11. Close
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addRect(slide, 0, 0, 18, H, C.lime, C.lime, 0, 0);
  addText(slide, "러너스아이", 72, 62, 220, 24, 13, C.lime, { bold: true });
  addText(slide, "러닝 영상을 자세 데이터로 바꾸고,", 72, 180, 920, 58, 37, C.white, { bold: true });
  addText(slide, "측정값과 개선 피드백을 하나의 리포트로 연결했습니다", 72, 246, 1050, 58, 37, C.white, { bold: true });
  addRule(slide, 72, 348, 650, C.lime, 3);
  addText(slide, "영상 기반 관절 추정", 72, 388, 248, 30, 17, C.muted);
  addText(slide, "논문 기반 피처 판정", 342, 388, 248, 30, 17, C.muted);
  addText(slide, "이해할 수 있는 리포트", 612, 388, 270, 30, 17, C.muted);
  addText(slide, "감사합니다", 72, 600, 220, 36, 28, C.lime, { bold: true });
  addText(slide, "Q&A", 1090, 600, 120, 36, 28, C.white, { bold: true, align: "right" });
  slide.speakerNotes.textFrame.setText("약 20초. 핵심 문장을 읽고 Q&A로 전환한다.");
}

await (await PresentationFile.exportPptx(presentation)).save(outputPath);
console.log(outputPath);
