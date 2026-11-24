from pathlib import Path
p=Path(__file__).with_name('build.mjs')
s=p.read_text(encoding='utf-8')
s=s.replace("const cc=[...cats].reverse(),vv=[...vals].reverse(),colorsRev=colors?[...colors].reverse():[];", "const cc=[...cats].reverse(),vv=[...vals].reverse(),colorsRev=colors?[...colors].reverse():[],numSize=digits===3?27:35;")
s=s.replace("fontSize:35,fill:C.ink,bold:true,typeface:F.sans", "fontSize:numSize,fill:C.ink,bold:true,typeface:F.sans")
s=s.replace("textStyle:{fill:C.ink,fontSize:35,bold:true}", "textStyle:{fill:C.ink,fontSize:numSize,bold:true}")
p.write_text(s,encoding='utf-8')
print('Adjusted three-decimal chart labels for native PowerPoint fit.')
