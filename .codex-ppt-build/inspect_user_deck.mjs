import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const source = "/Users/hyeon/Downloads/runners-eye-final-presentation-avatar-visuals-v9.pptx";
const deck = await PresentationFile.importPptx(await FileBlob.load(source));

function simplify(value) {
  if (value == null) return value;
  if (typeof value !== "object") return value;
  const out = {};
  for (const key of Object.keys(value)) {
    try {
      const item = value[key];
      if (["parent", "slide", "presentation", "children"].includes(key)) continue;
      if (typeof item === "function") continue;
      if (item == null || ["string", "number", "boolean"].includes(typeof item)) out[key] = item;
      else if (["position", "frame", "style", "fill", "line"].includes(key)) out[key] = JSON.parse(JSON.stringify(item));
    } catch {}
  }
  return out;
}

for (let si = 0; si < deck.slides.count; si += 1) {
  const slide = deck.slides.getItem(si);
  const items = slide.shapes?.items ?? [];
  console.log(JSON.stringify({ slide: si + 1, slideId: slide.id, shapeCount: items.length }));
  for (let i = 0; i < items.length; i += 1) {
    const sh = items[i];
    let txt = "";
    try { txt = sh.text?.text ?? sh.text ?? ""; } catch {}
    if (typeof txt !== "string") {
      try { txt = sh.text?.toString?.() ?? ""; } catch { txt = ""; }
    }
    let textStyle = null;
    try { textStyle = simplify(sh.text?.style); } catch {}
    console.log(JSON.stringify({
      slide: si + 1,
      index: i,
      id: sh.id,
      name: sh.name,
      type: sh.type ?? sh.geometry,
      position: sh.position ?? sh.frame ?? null,
      text: txt.slice(0, 300),
      textStyle,
      keys: Object.keys(sh).filter((k) => !k.startsWith("_")).slice(0, 40),
    }));
  }
}
