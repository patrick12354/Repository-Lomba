"""Generate the remaining Lucide icons in the Duotone Solid style, 9 per 3x3 sheet,
using sheets/duotone-solid.png as the style reference (images/edits)."""
import os,sys,json,base64,requests,concurrent.futures as cf
D=os.path.dirname(os.path.abspath(__file__))+"/.."; OUT=f"{D}/duotone/sheets"; os.makedirs(OUT,exist_ok=True)
MODEL="gpt-image-2.5-sunburst"
ICONS=[("Activity","heartbeat pulse line"),("Anchor","ship anchor"),("Archive","archive storage box with lid"),
("ArrowLeft","arrow pointing left"),("ArrowLeftRight","two arrows pointing left and right (swap)"),("ArrowRight","arrow pointing right"),
("ArrowUpRight","diagonal arrow pointing up-right"),("BadgeCheck","rosette badge with check mark"),("Box","single 3D cube box"),
("Boxes","stack of three cube boxes"),("BrickWall","brick wall"),("Bug","bug insect"),
("Cable","cable with plug connectors at both ends"),("CalendarClock","calendar with a small clock"),("CalendarX2","calendar with an X mark"),
("ChartColumn","column bar chart"),("ChartLine","line chart with axes"),("Check","check mark"),
("CheckCheck","double check mark"),("CheckCircle2","circle with check mark"),("ChevronDown","chevron pointing down"),
("ChevronRight","chevron pointing right"),("ChevronsLeft","double chevron pointing left"),("ChevronsRight","double chevron pointing right"),
("Circle","plain ring circle"),("CircleAlert","circle with exclamation mark"),("CircleCheck","solid filled circle with check mark cutout"),
("CircleDashed","dashed circle ring"),("CircleDot","ring with a dot in the centre (radio button)"),("Clock","clock face"),
("Clock3","clock face with hands at 3 o'clock"),("Compass","navigation compass"),("Copy","two overlapping documents (copy)"),("CornerDownRight","arrow going down then turning right"),
("Disc","disc / record"),("Droplets","two water droplets"),("Eye","eye"),
("Fan","industrial fan with blades in a ring"),("Filter","funnel filter"),("GitFork","branching fork diagram with three nodes"),
("Grid3x3","3 by 3 grid of squares"),("History","clock with counter-clockwise arrow (history)"),("Hourglass","hourglass"),
("Layers","three stacked layers"),("Lightbulb","light bulb"),("Link2","horizontal chain link"),
("ListFilter","three horizontal lines decreasing in length (filter list)"),("ListTodo","checklist with checkboxes"),("Loader2","loading spinner arc"),
("MapPin","map location pin"),("Minus","minus sign"),("PackageCheck","parcel box with check mark"),
("Plug","electric plug"),("Plus","plus sign"),("Receipt","receipt paper with zigzag bottom edge"),
("Repeat","repeat loop arrows"),("RotateCcw","counter-clockwise circular arrow"),("RotateCw","clockwise circular arrow"),
("Route","route path between two points"),("Ruler","ruler"),("Scale","balance scale"),
("Scroll","paper scroll"),("ShieldAlert","shield with exclamation mark"),("Sigma","sigma summation symbol"),
("Siren","emergency siren alarm light"),("SlidersHorizontal","horizontal sliders with knobs"),("Snowflake","snowflake"),
("Spline","smooth curve with two control-point handles"),("SprayCan","spray paint can"),("Tag","price tag"),
("Target","target bullseye"),("Thermometer","thermometer"),("ToggleLeft","toggle switch"),
("TrendingDown","falling trend line with arrow"),("Undo2","undo arrow curving left"),("Unlink","broken chain link"),
("Wallet","wallet"),("Waves","wavy water lines"),("Wind","wind gust lines"),
("Workflow","workflow: two boxes connected by an elbow line"),("X","X close mark")]
assert len(ICONS)==81
def prompt(batch):
    rows="\n".join(f"Row {r+1}: "+", ".join(d for _,d in batch[r*3:r*3+3]) for r in range(3))
    return ("The attached image is the reference icon set for an industrial spare-part inventory app. "
    "Create a NEW sprite sheet of 9 more icons in EXACTLY the same style: bold duotone solid glyphs, chunky filled charcoal #16171a shapes "
    "with a secondary burnt-orange #d9480f fill layer, slightly rounded corners, small negative-space cutouts, flat, no gradients, no outlines, "
    "same visual weight and size as the reference. Plain off-white #f5f4f1 background.\n"
    "Layout: EXACTLY 3 columns by 3 rows of equal square cells filling the canvas, one icon per cell, centred with ~25% margin. "
    "No text, labels, grid lines or borders.\n"+rows)
def gen(k):
    p=f"{OUT}/sheet{k}.png"
    if os.path.exists(p): return k,"cached"
    batch=ICONS[k*9:k*9+9]
    for attempt in range(3):
        r=requests.post("https://api.openai.com/v1/images/edits",headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"]},
            files={"image[]":("ref.png",open(f"{D}/sheets/duotone-solid.png","rb"),"image/png")},
            data={"model":MODEL,"prompt":prompt(batch),"size":"1024x1024","quality":"high"},timeout=600)
        if r.ok: open(p,"wb").write(base64.b64decode(r.json()["data"][0]["b64_json"])); return k,"ok"
        err=r.text[:300]
    return k,err
if __name__=="__main__":
    with cf.ThreadPoolExecutor(9) as ex:
        for res in ex.map(gen,range(9)): print(*res,flush=True)
    json.dump([n for n,_ in ICONS],open(f"{OUT}/order.json","w"))
