/**
 * Script to apply multi-simulation pattern to all simulation pages.
 * Adds: SimulationCountSelector in config step, SimulationTabBar after stepper,
 * useMultiSimulation hook, and N-parallel simulation launch.
 */
const fs = require('fs');
const path = require('path');

const SIMS_DIR = path.join(__dirname, 'src/app/(dashboard)/dashboard/simulations');

// All simulation page directories
const SIM_PAGES = [
  'acordao', 'eleitoral', 'jec', 'jecrim', 'judge', 'jury',
  'stf', 'stj', 'stm', 'trabalho', 'trt', 'tst-trabalho', 'turma-recursal',
  // militar already done
];

const IMPORTS_TO_ADD = `import SimulationCountSelector from '@/components/simulations/SimulationCountSelector';
import SimulationTabBar from '@/components/simulations/SimulationTabBar';
import { useMultiSimulation } from '@/hooks/use-multi-simulation';`;

function processPage(pageName) {
  const filePath = path.join(SIMS_DIR, pageName, 'page.tsx');
  if (!fs.existsSync(filePath)) {
    console.log(`  SKIP: ${filePath} not found`);
    return false;
  }

  let content = fs.readFileSync(filePath, 'utf8');

  // Skip if already modified
  if (content.includes('SimulationCountSelector')) {
    console.log(`  SKIP: ${pageName} already has multi-sim`);
    return false;
  }

  // 1. Add imports - find the last import line and add after it
  const importLines = content.split('\n');
  let lastImportIdx = -1;
  for (let i = 0; i < importLines.length; i++) {
    if (importLines[i].match(/^import\s/) || importLines[i].match(/^\} from ['"]/) || importLines[i].match(/^  Select|^  Tabs|^  Badge/)) {
      lastImportIdx = i;
    }
    // Stop at first non-import, non-blank after imports
    if (lastImportIdx > 0 && i > lastImportIdx + 1 && importLines[i].trim() !== '' && !importLines[i].match(/^import/) && !importLines[i].match(/^\}/) && !importLines[i].match(/^  /)) {
      break;
    }
  }

  // Find the actual last import statement end
  const lines = content.split('\n');
  let insertAfter = -1;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('import ') || (line.startsWith("} from '") && i > 0)) {
      insertAfter = i;
    }
    // Once we hit const/interface/function after imports, stop
    if (insertAfter > 0 && (line.startsWith('const ') || line.startsWith('interface ') || line.startsWith('function ') || line.startsWith('export default') || line.startsWith('export function') || line.startsWith('// --') || line.startsWith('// ='))) {
      break;
    }
  }

  if (insertAfter === -1) {
    console.log(`  ERROR: Could not find import insertion point in ${pageName}`);
    return false;
  }

  lines.splice(insertAfter + 1, 0, IMPORTS_TO_ADD);
  content = lines.join('\n');

  // 2. Add useMultiSimulation hook - find the function body
  // Look for patterns like:
  //   const { toast } = useToast();
  //   const [currentStep, ...
  // Insert multiSim hook after useToast
  content = content.replace(
    /const \{ toast \} = useToast\(\);(\s*\n)/,
    `const { toast } = useToast();\n  const multiSim = useMultiSimulation();\n`
  );

  // 3. Add SimulationCountSelector before the end of config step's closing </div>
  // Strategy: find the last </div> before renderStep1 and add the selector before the last few closing tags
  // Look for the pattern: caracteres (minimo 20) ... </div> ... </div> ... renderStep1
  const countSelectorHtml = `\n        <div className="pt-4 border-t mt-4">\n          <SimulationCountSelector value={multiSim.simulationCount} onChange={multiSim.setSimulationCount} />\n        </div>`;

  // Find where config step ends - look for the pattern after "caracteres (minimo 20)"
  // Different pages have different structures but all have a "caracteres" line near end of config
  const caracteresIdx = content.lastIndexOf('caracteres (minimo');
  if (caracteresIdx > -1) {
    // Find the next </div> after this, then add before the second-to-last closing structure
    let searchFrom = caracteresIdx;
    // Find the closing </div> sequence - we want to add before the last 2-3 </div>s
    // Look for </div>\n      </div>\n    </div>  pattern
    const afterCaracteres = content.substring(searchFrom);
    const divClosePattern = /(<\/div>\s*\n\s*<\/div>\s*\n\s*<\/div>\s*\n\s*\);)/;
    const match = afterCaracteres.match(divClosePattern);
    if (match) {
      const insertPos = searchFrom + afterCaracteres.indexOf(match[0]);
      content = content.substring(0, insertPos) + countSelectorHtml + '\n      ' + content.substring(insertPos);
    } else {
      // Simpler pattern: add before the last </div></div> sequence in the config renderer
      // Find renderStep0 function and add before its closing
      const step0Match = content.match(/(caracteres \(minimo \d+\)[^]*?<\/p>\s*\n\s*<\/div>\s*\n\s*<\/div>)/);
      if (step0Match) {
        const idx = content.indexOf(step0Match[0]);
        const endOfMatch = idx + step0Match[0].length;
        content = content.substring(0, endOfMatch) + countSelectorHtml + content.substring(endOfMatch);
      }
    }
  }

  // 4. Modify startSimulation call to run N times
  // Look for patterns like:
  //   setTimeout(() => startSimulation(), 300);
  // or: startSimulation()
  // and wrap with loop

  // Find the nextStep function and modify it
  // Replace the direct startSimulation call with a loop version
  content = content.replace(
    /setTimeout\(\(\) => startSimulation\(\), 300\)/g,
    `(() => { multiSim.resetTabs(multiSim.simulationCount); for (let i = 0; i < multiSim.simulationCount; i++) { setTimeout(() => { multiSim.updateTabStatus(i, 'running'); startSimulation().then(() => multiSim.updateTabStatus(i, 'completed')).catch(() => multiSim.updateTabStatus(i, 'error')); }, i * 200); } })()`
  );

  // 5. Add SimulationTabBar after renderStepper() in return JSX
  content = content.replace(
    /(\{renderStepper\(\)\})\n(\s*<div className="flex-1)/,
    `$1\n      {currentStep > 0 && multiSim.simulationCount > 1 && (\n        <SimulationTabBar tabs={multiSim.tabs} activeIndex={multiSim.activeSimIndex} onTabChange={multiSim.setActiveSimIndex} />\n      )}\n$2`
  );

  // 6. Also handle cases where stepper is inline (not {renderStepper()})
  // Some pages use {renderStepper()} directly

  // 7. Reset simulation should also reset multiSim
  content = content.replace(
    /const resetSimulation = useCallback\(\(\) => \{/,
    'const resetSimulation = useCallback(() => {\n    multiSim.setSimulationCount(1);'
  );

  // Make startSimulation async if it's not already (for .then() chaining)
  // Most are already async, but check
  if (!content.includes('const startSimulation = useCallback(async')) {
    content = content.replace(
      'const startSimulation = useCallback((',
      'const startSimulation = useCallback(async ('
    );
  }

  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`  OK: ${pageName} updated`);
  return true;
}

console.log('Applying multi-simulation pattern to all pages...\n');

let success = 0;
let skip = 0;
let fail = 0;

for (const page of SIM_PAGES) {
  console.log(`Processing: ${page}`);
  try {
    if (processPage(page)) {
      success++;
    } else {
      skip++;
    }
  } catch (err) {
    console.log(`  ERROR: ${err.message}`);
    fail++;
  }
}

console.log(`\nDone: ${success} updated, ${skip} skipped, ${fail} failed`);
