import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const p = await PresentationFile.importPptx(await FileBlob.load("/Users/hyeon/Downloads/runners-eye-final-presentation-avatar-visuals-v9.pptx"));
for (const [si, indexes] of [[1,[0,2,4,6]],[4,[0,2,4,8,10]],[5,[0,2,4,5]],[6,[0,2,4,5]],[7,[0,2,4,5]],[8,[0,2,4,5]],[9,[0,2,4,5]]]) {
  const s = p.slides.getItem(si);
  for (const idx of indexes) {
    const sh = s.shapes.items[idx];
    let textData = null;
    try { textData = sh.data?.text ?? null; } catch {}
    console.log(JSON.stringify({
      slide: si+1, idx, id: sh.id, name: sh.name,
      proto: Object.getOwnPropertyNames(Object.getPrototypeOf(sh)),
      dataKeys: Object.keys(sh.data ?? {}),
      position: sh.position,
      text: sh.text?.text ?? "",
      textData,
      rawData: sh.data,
    }));
  }
}
