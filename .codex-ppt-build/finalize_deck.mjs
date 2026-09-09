import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";

const workspaceDir = "/Users/hyeon/SeSAC_Project";
const SKILL_DIR = "/Users/hyeon/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations";
const RUNTIME_PYTHON = "/Users/hyeon/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const sourcePath = "/Users/hyeon/Downloads/runners-eye-final-presentation-story-v8.pptx";
const candidatePath = path.join(workspaceDir, ".codex-ppt-build", "candidate.pptx");
const finalPath = path.join(workspaceDir, "deliverables", "runners-eye-final-presentation-avatar-visuals-v9.pptx");
const stagingDir = path.join(workspaceDir, ".codex-finalizer");

const { finalizePresentation } = await import(pathToFileURL(
  path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs"),
).href);

await fs.mkdir(path.dirname(finalPath), { recursive: true });
await fs.mkdir(stagingDir, { recursive: true });

const sourceBytes = await fs.readFile(sourcePath);
const sourceSha256 = createHash("sha256").update(sourceBytes).digest("hex");

const requirements = {
  explicitTotalSlideCount: 11,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
};

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  requiredNativeTableOwnerSlides: [],
  fontPolicy: {
    basis: "reference",
    families: ["Pretendard"],
    referencePath: sourcePath,
    referenceSha256: sourceSha256,
  },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "runners-eye-final-presentation-avatar-visuals-v9.validation.json"),
});

console.log(JSON.stringify(result));
