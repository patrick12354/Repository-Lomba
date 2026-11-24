import path from 'node:path';
import {pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
const root='C:/Users/Raphael Angelo/Code/Competitions/NSC UB';
const skill='C:/Users/Raphael Angelo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const ref='C:/Users/Raphael Angelo/Downloads/Black and Beige Grunge Crime Investigation Report Presentation.pptx';
process.env.RUNTIME_NODE_MODULES='C:/Users/Raphael Angelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.join(root,'tmp/pptx_build/candidate-fonts.pptx'),finalPath:path.join(root,'deliverables/presentation/BERKAS_734_LENGKAP.pptx'),pythonExecutable:'C:/Users/Raphael Angelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','18288000,10287000','--validate-heading-fit'],explicitTotalSlideCount:23,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'reference',families:['Rustic Printed Stamp','Poppins Bold','Poppins Light','Gloria Hallelujah'],referencePath:ref,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(ref)).digest('hex')},verifyArtifactToolImport:true,receiptPath:path.join(root,'tmp/pptx_build/validation-v2.json')});console.log(JSON.stringify(result));



