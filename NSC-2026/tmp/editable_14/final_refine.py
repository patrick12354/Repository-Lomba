from pathlib import Path
p=Path(__file__).with_name('build.mjs')
s=p.read_text(encoding='utf-8')
s=s.replace("{max:8,colors:[C.red,C.red,C.ink]}","{max:9.8,colors:[C.red,C.red,C.ink]}")
s=s.replace("{digits:3,max:.105,colors:[C.red,C.ink]}","{digits:3,max:.14,colors:[C.red,C.ink]}")
s=s.replace("for(let i=0;i<3;i++){const x=370+i*216;", "models.forEach((m,j)=>line(s,328,330+j*72,352,330+j*72,colors[j],3));line(s,352,330,352,618,C.ink,3);line(s,352,426,965,426,C.ink,3);for(let i=0;i<3;i++){const x=370+i*216;")
s=s.replace("models.forEach((m,j)=>connect(s,m,mixer,colors[j],'straight'));", "line(s,x+93,426,x+93,458,C.ink,3);")
p.write_text(s,encoding='utf-8')
print('Adjusted chart clearance and parallel input routing.')
