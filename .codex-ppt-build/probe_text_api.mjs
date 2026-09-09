import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const p = await PresentationFile.importPptx(await FileBlob.load("/Users/hyeon/Downloads/runners-eye-final-presentation-avatar-visuals-v9.pptx"));
for (const [si, idx] of [[1,2],[4,2],[1,6]]) {
  const sh = p.slides.getItem(si).shapes.items[idx];
  const chain = [];
  let proto = sh;
  while (proto) { chain.push(Object.getOwnPropertyNames(proto)); proto = Object.getPrototypeOf(proto); }
  let snap = null;
  try { snap = sh.toSnapshot(); } catch (e) { snap = {err:String(e)}; }
  let textRangeProto = null;
  try { textRangeProto = Object.getOwnPropertyNames(Object.getPrototypeOf(sh.text)); } catch {}
  let textStyle = null;
  try { textStyle = sh.textStyle; } catch (e) { textStyle = {err:String(e)}; }
  let paragraphs = null;
  try { paragraphs = sh.getParagraphs?.(); } catch (e) { paragraphs = {err:String(e)}; }
  const props = {};
  for (const k of ["fontSize","typeface","bold","color","alignment","verticalAlignment","autoFit","wrap","insets","lineSpacing","style"]) {
    try { props[k] = sh.text[k]; } catch (e) { props[k] = {err:String(e)}; }
  }
  console.log(JSON.stringify({slide:si+1,idx,text:String(sh.text),textValue:sh.text?.text,textType:typeof sh.text,textRangeProto,textStyle,props,paragraphs,chain,snap},null,2));
}
