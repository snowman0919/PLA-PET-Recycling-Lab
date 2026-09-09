#set page(width:420mm,height:297mm,margin:0mm)
#set text(font:"Noto Sans CJK KR")
#let manifest=json("drawing_manifest.json")
#for (i,p) in manifest.pages.enumerate() {
  if i>0 { pagebreak() }
  place(top+left, image(p.file,width:420mm,height:297mm))
}
