import sys,os,io,json,base64
from PIL import Image
d=sys.argv[1]; names=["factory","wrench","package","truck","gauge","calendar","shield-check","octagon-alert","coins","trending-up","search","cog","flame","droplet","zap","cart"]
out={}
for t in ["precision-line","duotone-solid","blueprint","isometric-plant","soft-clay-3d","enamel-badge"]:
    im=Image.open(f"{d}/sheets/{t}.png").convert("RGB"); W,H=im.size; cw,ch=W//4,H//4
    bg=[sorted(im.getpixel(p)[k] for p in [(4,4),(W-5,4),(4,H-5),(W-5,H-5),(W//2,4),(4,H//2)])[3] for k in range(3)]
    im=Image.merge("RGB",[ch_.point(lambda v,b=bg[k]: min(255,round(v*255/b))) for k,ch_ in enumerate(im.split())])
    os.makedirs(f"{d}/icons/{t}",exist_ok=True); out[t]={}
    for i,n in enumerate(names):
        c=im.crop(((i%4)*cw,(i//4)*ch,(i%4+1)*cw,(i//4+1)*ch)).resize((160,160),Image.LANCZOS)
        c.save(f"{d}/icons/{t}/{n}.png")
        b=io.BytesIO(); c.save(b,"WEBP",quality=88); out[t][n]="data:image/webp;base64,"+base64.b64encode(b.getvalue()).decode()
open(f"{sys.argv[2]}","w").write("const IMG="+json.dumps(out)+";")
print(os.path.getsize(sys.argv[2]))
