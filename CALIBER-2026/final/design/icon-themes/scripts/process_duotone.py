"""Cut Duotone sheets into transparent 256px PNGs named after the Lucide icon (kebab-case).
Each pixel is snapped to the nearer brand colour (ink or accent) with alpha = how far it is from the background."""
import os,re,json
import numpy as np
from PIL import Image
D=os.path.dirname(os.path.abspath(__file__))+"/.."; OUT=f"{D}/duotone/png"; os.makedirs(OUT,exist_ok=True)
INK=np.array([22,23,26.]); ACC=np.array([217,72,15.])
FIRST16=["Factory","Wrench","Package","Truck","Gauge","CalendarDays","ShieldCheck","OctagonAlert","Coins","TrendingUp","Search","Cog","Flame","Droplet","Zap","ShoppingCart"]
kebab=lambda n: re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[a-zA-Z])(?=[0-9])','-',n).lower().replace("3-x3","3x3")
def to_rgba(cell):
    a=np.asarray(cell.convert("RGB")).astype(float)
    bg=np.median(np.concatenate([a[:6].reshape(-1,3),a[-6:].reshape(-1,3),a[:,:6].reshape(-1,3),a[:,-6:].reshape(-1,3)]),0)
    out=np.zeros(a.shape[:2]+(4,))
    alphas=[];
    for P in (INK,ACC):
        v=bg-P; t=((bg-a)@v)/(v@v)                     # projection of pixel on bg->P line
        resid=np.linalg.norm(a-(bg-np.clip(t,0,1)[...,None]*v),axis=-1)
        alphas.append((np.clip(t,0,1),resid))
    use_acc=alphas[1][1]<alphas[0][1]
    al=np.where(use_acc,alphas[1][0],alphas[0][0])
    al=np.clip((al-0.06)/0.86,0,1)                     # kill paper noise, firm up solid areas
    out[...,:3]=np.where(use_acc[...,None],ACC,INK); out[...,3]=al*255
    return Image.fromarray(out.astype(np.uint8),"RGBA")
def normalize(im,S=256,live=0.80):
    bb=im.getchannel("A").point(lambda v:255 if v>25 else 0).getbbox()
    im=im.crop(bb); w,h=im.size; k=S*live/max(w,h)
    im=im.resize((max(1,round(w*k)),max(1,round(h*k))),Image.LANCZOS)
    c=Image.new("RGBA",(S,S),(0,0,0,0)); c.paste(im,((S-im.width)//2,(S-im.height)//2)); return c
def cut(path,n):
    im=Image.open(path); W,H=im.size; cw,ch=W//n,H//n
    return [im.crop((x*cw,y*ch,(x+1)*cw,(y+1)*ch)) for y in range(n) for x in range(n)]
jobs=list(zip(FIRST16,cut(f"{D}/sheets/duotone-solid.png",4)))
order=json.load(open(f"{D}/duotone/sheets/order.json"))
cells=[c for k in range(9) for c in cut(f"{D}/duotone/sheets/sheet{k}.png",3)]
jobs+=list(zip(order,cells))
jobs=[(n,Image.open(f"{D}/duotone/sheets/single-Check.png") if n=="Check" else c) for n,c in jobs]
names=[]
for n,c in jobs:
    normalize(to_rgba(c)).save(f"{OUT}/{kebab(n)}.png"); names.append([n,kebab(n)])
json.dump(names,open(f"{D}/duotone/icons.json","w"),indent=0)
print(len(names),"icons ->",OUT)
