from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from lxml import etree as E
import copy,hashlib,posixpath
base=Path(__file__).parent
ref=ZipFile(r'C:\Users\Raphael Angelo\Downloads\Black and Beige Grunge Crime Investigation Report Presentation.pptx')
src=ZipFile(base/'candidate.pptx')
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
doc=E.fromstring(src.read('ppt/presentation.xml'))
fontlist=copy.deepcopy(E.fromstring(ref.read('ppt/presentation.xml')).find('p:embeddedFontLst',ns))
rels=E.fromstring(src.read('ppt/_rels/presentation.xml.rels'))
refrels=E.fromstring(ref.read('ppt/_rels/presentation.xml.rels'))
extra={}
for i,node in enumerate(fontlist.findall('p:embeddedFont',ns)):
 for style in list(node)[1:]:
  old=style.get('{'+ns['r']+'}id');rel=next(x for x in refrels if x.get('Id')==old);new='rIdEmbeddedFont'+str(i)
  style.set('{'+ns['r']+'}id',new);newrel=copy.deepcopy(rel);newrel.set('Id',new);rels.append(newrel)
  extra['ppt/'+rel.get('Target')]=ref.read('ppt/'+rel.get('Target'))
doc.append(fontlist)
doc.set('embedTrueTypeFonts','true')
doc.set('saveSubsetFonts','1')
cts=E.fromstring(src.read('[Content_Types].xml'));ctns='http://schemas.openxmlformats.org/package/2006/content-types'
if not any(n.get('Extension')=='fntdata' for n in cts):E.SubElement(cts,'{'+ctns+'}Default',Extension='fntdata',ContentType='application/x-fontdata')
updated={'ppt/presentation.xml':E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True),'ppt/_rels/presentation.xml.rels':E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True),'[Content_Types].xml':E.tostring(cts,xml_declaration=True,encoding='UTF-8',standalone=True)}
seen={};duplicates={}
for name in src.namelist():
 if name.startswith('ppt/media/'):
  digest=hashlib.sha256(src.read(name)).hexdigest()
  if digest in seen:duplicates[name]=seen[digest]
  else:seen[digest]=name
for name in src.namelist():
 if name.endswith('.rels') and name not in updated:
  root=E.fromstring(src.read(name));changed=False
  owner=posixpath.dirname(posixpath.dirname(name))
  for rel in root:
   if rel.get('TargetMode')=='External':continue
   target=posixpath.normpath(posixpath.join(owner,rel.get('Target',''))).lstrip('/')
   if target in duplicates:
    rel.set('Target',posixpath.relpath(duplicates[target],owner));changed=True
  if changed:updated[name]=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
for node in list(cts):
 if node.get('PartName','').lstrip('/') in duplicates:cts.remove(node)
updated['[Content_Types].xml']=E.tostring(cts,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(base/'candidate-fonts.pptx','w',ZIP_DEFLATED) as out:
 for name in src.namelist():
  if name not in duplicates:out.writestr(name,updated.get(name,src.read(name)))
 for name,data in extra.items():out.writestr(name,data)
print('Embedded all 5 fonts; removed',len(duplicates),'duplicate media objects without changing appearance.')
