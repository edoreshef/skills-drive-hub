// Render review stills: node scripts/stills.mjs <seconds...> (absolute times in the video)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';

const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'Explainer'});
for (const sec of process.argv.slice(2)) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(Number(sec) * 30));
  const output = `out/stills/t${String(sec).padStart(6, '0')}.jpg`;
  await renderStill({serveUrl, composition, frame, output, imageFormat: 'jpeg', scale: 0.5});
  console.log(output);
}
