import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { plan } from './planner.js';
import { markdownReport, svgReport } from './report.js';

const args = process.argv.slice(2);
if (!args[0] || (args.length !== 1 && !(args.length === 3 && args[1] === '--out'))) {
  console.error('Usage: node cli.js input.json [--out directory]');
  process.exitCode = 2;
} else {
  try {
    const input = JSON.parse(await readFile(args[0], 'utf8'));
    const result = plan(input);
    const out = args[2] ?? 'plan-output';
    await mkdir(out, { recursive: true });
    await writeFile(join(out, 'plan.json'), JSON.stringify(result, null, 2) + '\n');
    await writeFile(join(out, 'plan.md'), markdownReport(result));
    await writeFile(join(out, 'plan.svg'), svgReport(input, result));
    console.log(markdownReport(result));
    console.log(`Saved JSON, Markdown, and SVG to ${out}`);
  } catch (error) {
    console.error(`Cannot create plan: ${error.message}`);
    process.exitCode = 1;
  }
}
