import json,os,sys,base64,urllib.request,concurrent.futures as cf
OUT=sys.argv[1]; MODEL=os.environ.get("M","gpt-image-2.5-sunburst")
ICONS=["factory building with chimney","wrench","cardboard parts box","delivery truck","pressure gauge dial","calendar","shield with check mark","octagon warning sign with exclamation","stack of coins","rising trend line chart","magnifying glass","gear cog","flame","water droplet","lightning bolt","shopping cart"]
grid="\n".join(f"Row {r+1}: "+", ".join(ICONS[r*4:r*4+4]) for r in range(4))
BASE=("Create an icon set sprite sheet for an industrial spare-part inventory and maintenance planning web app. "
"Layout: EXACTLY 4 columns by 4 rows of equal square cells filling the whole canvas, one icon per cell, each icon centered with generous padding (~22% margin) inside its cell. "
"No text, no labels, no numbers, no grid lines, no borders between cells. All 16 icons must share one identical, coherent visual style, stroke weight, perspective and lighting.\n"
f"Icons in reading order:\n{grid}\n"
"App palette: warm off-white #f5f4f1 background, ink charcoal #16171a, accent burnt orange #d9480f, supporting status colours green #2a9a5a, amber #e39a12, blue #3b6fd4, purple #7c4ddb, teal #0e9384.\nSTYLE: ")
THEMES={
"precision-line":"Bespoke precision monoline icons. Single uniform 2.5px-equivalent charcoal stroke, rounded caps and joins, geometric construction on a 24px grid, with exactly one small burnt-orange accent detail per icon (a part, a dot, a highlight). Flat, no fills, no shading. Crafted, Swiss, engineered feel - distinctly not a generic icon library. Plain #f5f4f1 background.",
"duotone-solid":"Bold duotone solid glyphs. Chunky filled charcoal shapes with a secondary burnt-orange fill layer, slightly rounded corners, small negative-space cutouts for detail. Flat, no gradients, no outlines. Confident and legible at 20px. Plain #f5f4f1 background.",
"soft-clay-3d":"Soft matte 3D clay icons, gently rounded inflated forms, subtle soft studio lighting from top-left, soft contact shadow under each object. Colours: mostly warm cream and charcoal with burnt-orange and muted status-colour accents. Tactile, friendly, premium. Plain #f5f4f1 background.",
"isometric-plant":"Isometric technical mini-illustrations, true 30-degree isometric projection, crisp flat faces with three tones per object (light top, mid, dark side), thin charcoal edge lines, burnt-orange accents. Looks like pieces of a 3D factory plant model. Plain #f5f4f1 background.",
"blueprint":"Engineering technical-drawing style: fine charcoal hairline outlines like a CAD/blueprint schematic, with tiny construction details (centre marks, dimension ticks, hatching on cut faces), and a burnt-orange highlight on one key element. No fills except light hatching. Precise and analytical. Plain #f5f4f1 background.",
"enamel-badge":"Industrial enamel badge icons: each glyph is a white solid pictogram centred on a rounded-square tile filled with a flat colour, like safety signage. Rotate tile colours through burnt orange, charcoal, green, amber, blue, teal, purple. Subtle inner bevel highlight on the tile edge, no text. Tiles sit on plain #f5f4f1 background.",
}
def gen(name):
    p=os.path.join(OUT,f"{name}.png")
    if os.path.exists(p): return name,"cached"
    body=json.dumps({"model":MODEL,"prompt":BASE+THEMES[name],"size":"1024x1024","quality":"high"}).encode()
    req=urllib.request.Request("https://api.openai.com/v1/images/generations",body,{"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"],"Content-Type":"application/json"})
    try: d=json.load(urllib.request.urlopen(req,timeout=600))
    except urllib.error.HTTPError as e: return name,e.read().decode()[:300]
    open(p,"wb").write(base64.b64decode(d["data"][0]["b64_json"])); return name,"ok"
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(gen,THEMES): print(*r,flush=True)
json.dump({"icons":ICONS,"themes":THEMES},open(os.path.join(OUT,"meta.json"),"w"),indent=1)
