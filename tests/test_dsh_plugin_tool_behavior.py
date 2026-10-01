"""用真 Node 加载插件，验证子命令分发、会话工作区注入、退出码与进程失败返回。

不依赖 DSH 宿主：用真实的 python3（当前测试解释器）执行随包脚本，
只把 ctx 的服务面（tools / subprocess / sandboxPolicy）按 Cordis 契约模拟出来。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
FIXTURE = ROOT / "packages" / "dsh-ggb-master" / "skills" / "ggb-master" / "fixtures" / "kepler-baseline.xml"

SCRIPT = r'''
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { apply, inject } from './packages/dsh-ggb-master/tools/index.js';

const PYTHON = process.argv[1];
const cwd = process.argv[2];
const fixture = process.argv[3];

let tool;
const requests = [];
const services = {
  tools: { register(t) { tool = t } },
  subprocess: {
    async resolveExecutable(candidate) { return candidate },
    spawn(spec) {
      requests.push(spec);
      let stdout = '', stderr = '';
      const child = spawn(spec.argv[0], spec.argv.slice(1), { cwd: spec.cwd, env: { ...process.env, ...spec.env } });
      child.stdout.on('data', b => stdout += b);
      child.stderr.on('data', b => stderr += b);
      const abort = () => child.kill('SIGTERM');
      if (spec.signal.aborted) abort();
      else spec.signal.addEventListener('abort', abort, { once: true });
      const done = new Promise((resolve, reject) => {
        child.on('error', reject);
        child.on('close', (exitCode) => {
          spec.signal.removeEventListener('abort', abort);
          if (spec.signal.aborted) reject(new Error('timeout'));
          else resolve({ exitCode });
        });
      });
      return { done, collected: {
        stdout: { readFrom() { return { text: stdout, lossy: false } } },
        stderr: { readFrom() { return { text: stderr, lossy: false } } },
      } };
    },
  },
};

// 模拟 Cordis：未声明 inject 的属性访问立即抛错；可选服务用 get 查询。
let policyLookups = 0;
const ctx = new Proxy({ get(name) {
  assert.equal(name, 'sandboxPolicy');
  policyLookups++;
  return services[name];
} }, { get(target, prop, receiver) {
  if (Reflect.has(target, prop)) return Reflect.get(target, prop, receiver);
  if (!inject.includes(prop)) throw new Error(`cannot get property "${prop}" without inject`);
  return services[prop];
} });

assert.deepEqual(inject, ['tools', 'subprocess']);
assert.throws(() => ctx.sandboxPolicy, /without inject/);
apply(ctx, { command: PYTHON, timeoutMs: 60000 });
const exec = { agent: { session: { header: { cwd } } } };

// 1) 子命令分发到随包脚本；cwd 与 GGB_ROOT 都取自会话工作区。
let result = await tool.execute({ args: ['check', fixture, '--quiet'] }, exec);
assert.equal(result.exitCode, 0, result.stderr);
assert.match(result.stdout, /OK/);
assert.equal(requests[0].argv[0], PYTHON);
assert.ok(requests[0].argv[1].endsWith('scripts/ggb_check.py'), requests[0].argv[1]);
assert.equal(requests[0].cwd, cwd);
assert.equal(requests[0].env.GGB_ROOT, cwd);
assert.equal(policyLookups, 1);

// 2) sandboxPolicy 给出的工作区优先，并逐次重新查询。
const second = join(cwd, 'B');
mkdirSync(second);
let policyCalls = 0;
services.sandboxPolicy = { resolve({ session }) { policyCalls++; assert.equal(session, exec.agent.session); return { workspaceRoot: second } } };
result = await tool.execute({ args: ['check', fixture, '--quiet'] }, exec);
assert.equal(result.exitCode, 0, result.stderr);
assert.equal(requests[1].cwd, second);
assert.equal(requests[1].env.GGB_ROOT, second);
assert.equal(policyCalls, 1);
assert.equal(policyLookups, 2);

// 3) 未知子命令、缺失工作区、cwd 不一致都必须被拒。
await assert.rejects(() => tool.execute({ args: ['nope'] }, exec), /未知子命令/);
await assert.rejects(() => tool.execute({ args: ['check', fixture] }, {}), /工作区/);
await assert.rejects(() => tool.execute({ args: ['check', fixture], cwd: '/tmp' }, exec), /cwd 必须/);

// 4) 退路：直接点名随包脚本仍然可用，但不许跳出 scripts/。
result = await tool.execute({ args: ['ggb_check.py', fixture, '--quiet'] }, exec);
assert.equal(result.exitCode, 0, result.stderr);
await assert.rejects(() => tool.execute({ args: ['../../evil.py'] }, exec), /未知子命令/);

// 5) 退出码与 stderr 原样带回。
result = await tool.execute({ args: ['check', '/definitely/missing.xml', '--quiet'] }, exec);
assert.equal(result.exitCode, 2);
assert.match(result.stderr, /文件不存在/);

// 6) 显式配置不存在的解释器：明确报错，不静默回退。
let attempted = [];
services.subprocess.resolveExecutable = async command => { attempted.push(command); throw new Error('not found') };
apply(ctx, { command: '/explicit/missing/python3' });
await assert.rejects(() => tool.execute({ args: ['check', fixture] }, exec), /Python 解释器/);
assert.deepEqual(attempted, ['/explicit/missing/python3']);

// 7) 超时保留已收集诊断，退出码为 -1。
services.subprocess.resolveExecutable = async candidate => candidate;
apply(ctx, { command: PYTHON, timeoutMs: 1 });
result = await tool.execute({ args: ['selftest'] }, exec);
assert.equal(result.exitCode, -1);
assert.match(result.stderr, /timeout/);

// 8) 外部取消必须传播取消语义，不能包装成普通技术失败。
apply(ctx, { command: PYTHON, timeoutMs: 60000 });
const cancelController = new AbortController();
const cancelPromise = tool.execute({ args: ['selftest'] }, { ...exec, signal: cancelController.signal });
setTimeout(() => cancelController.abort(), 20);
await assert.rejects(cancelPromise, /用户已取消/);

// 9) reject 后仍读取完整收集结果，并保留截断标记。
ctx.subprocess.spawn = () => ({
  collected: {
    stdout: { readFrom() { return { text: 'partial', lossy: true } } },
    stderr: { readFrom() { return { text: 'diagnostic', lossy: false } } },
  },
  done: Promise.reject(new Error('broken')),
});
result = await tool.execute({ args: ['check', fixture] }, exec);
assert.equal(result.stdout, 'partial');
assert.equal(result.truncated, true);
assert.match(result.stderr, /diagnostic\nbroken/);
'''


def test_native_tool_behavior(tmp_path):
    if NODE is None:
        if os.environ.get("CI"):
            pytest.fail("CI 必须安装 Node 并执行插件行为测试")
        pytest.skip("本地缺少 Node")
    result = subprocess.run(
        [NODE, "--input-type=module", "-e", SCRIPT, sys.executable, str(tmp_path.resolve()), str(FIXTURE)],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
