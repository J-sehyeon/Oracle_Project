import { FileBlob, PresentationFile } from "@oai/artifact-tool";
const p = await PresentationFile.importPptx(await FileBlob.load("/Users/hyeon/Downloads/runners-eye-final-presentation-avatar-visuals-v9.pptx"));
for (let si = 0; si < p.slides.count; si += 1) {
  const s = p.slides.getItem(si);
  console.log(`\nSLIDE ${si+1}`);
  for (let idx=0; idx < (s.shapes?.items?.length ?? 0); idx += 1) {
    const sh=s.shapes.items[idx]; const t=String(sh.text ?? "").replace(/\n/g," | ");
    let fs=null; try { fs=sh.text.fontSize; } catch {}
    const pos=sh.position;
    if (t) console.log(JSON.stringify({idx,id:sh.id,t,fs,pos}));
  }
  const collections = ["images","videos","charts","tables"];
  for (const key of collections) {
    const arr=s[key]?.items ?? [];
    if (arr.length) console.log(JSON.stringify({collection:key,count:arr.length,items:arr.map((x,i)=>({i,id:x.id,name:x.name,pos:x.position ?? x.frame}))}));
  }
}
