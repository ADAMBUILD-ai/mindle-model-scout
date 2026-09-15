import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import process from 'node:process';
import { pipeline } from '@huggingface/transformers';

const modelId = 'onnx-community/sam2.1-hiera-tiny-ONNX';
const revision = '814a066640debee5a91e70aa401fb8e17e030503';
const inputUrl = 'https://huggingface.co/datasets/hf-internal-testing/sam2-fixtures/resolve/main/truck.jpg';
const inputPath = 'sam21-input.jpg';
const outputPath = 'sam21-mask.png';
const evidencePath = 'sam21-inference-evidence.json';
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const evidence = {
  status: 'BLOCKED',
  model_id: modelId,
  revision,
  license: 'apache-2.0',
  source_url: 'https://huggingface.co/' + modelId,
  input_source_url: inputUrl,
  runtime: 'transformers.js@3.8.1 with ONNX Runtime CPU',
  platform: process.platform,
  architecture: process.arch,
  cpu: os.cpus()[0]?.model ?? 'unknown',
  cpu_count: os.cpus().length,
  gpu: 'not requested; CPU-only GitHub Actions runner',
};
try {
  const response = await fetch(inputUrl);
  if (!response.ok) throw new Error('input_download_' + response.status);
  const inputBytes = Buffer.from(await response.arrayBuffer());
  await writeFile(inputPath, inputBytes);
  evidence.input_file = inputPath;
  evidence.input_sha256 = sha256(inputBytes);
  evidence.input_size = inputBytes.length;
  const generator = await pipeline('mask-generation', modelId, { revision });
  const result = await generator(inputPath, { points_per_batch: 16 });
  const mask = result.masks?.[0];
  if (!mask || typeof mask.save !== 'function') throw new Error('mask_output_unavailable');
  await mask.save(outputPath);
  const outputBytes = await readFile(outputPath);
  Object.assign(evidence, {
    status: 'TESTED_PASS',
    mask_count: result.masks.length,
    output_file: outputPath,
    output_sha256: sha256(outputBytes),
    output_size: outputBytes.length,
  });
} catch (error) {
  evidence.error_type = error?.name ?? 'Error';
  evidence.error = String(error?.message ?? error).slice(0, 240);
}
await writeFile(evidencePath, JSON.stringify(evidence, null, 2) + '\n');
console.log(JSON.stringify(evidence));
process.exitCode = evidence.status === 'TESTED_PASS' ? 0 : 1;
