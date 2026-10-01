/**
 * dsh-ggb-master 的原生工具半侧。
 *
 * 这里只做「子命令 → 随包脚本」的分发 + 受管子进程 + 结构化返回，不含任何课件
 * 规划或构造判断：判断由宿主 agent 按 ggb-master skill 完成，确定性由随包 Python
 * 脚本完成（`scripts/` 的 CLI 永远是退路——插件坏了，bash 里照样能跑）。
 *
 * 本模块刻意不 import 任何 @deepseek-ai/* 包，避免 profile 内解析不到随 DSH
 * 安装的包；只用 Node 内建模块。
 */
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { isAbsolute, join } from 'node:path'

export const name = 'ggb-tools'

/** 依赖宿主平面的工具注册表与子进程服务（两者都在 dsh-base 里随宿主挂载）。 */
export const inject = ['tools', 'subprocess']

/** 子命令 → 随包脚本；脚本位于本包 skills/ggb-master/scripts/。 */
const COMMANDS = {
  init: 'project_manager.py',
  check: 'ggb_check.py',
  pack: 'ggb_pack.py',
  unpack: 'ggb_unpack.py',
  'macro-preview': 'ggb_macro_preview.py',
  'html-demo-check': 'html_demo_check.py',
  selftest: 'selftest.py',
}

/** 随包脚本目录：包被复制进 profile 后依然自洽（不依赖施工仓库）。 */
const SCRIPTS_DIR = fileURLToPath(new URL('../skills/ggb-master/scripts/', import.meta.url))

const DESCRIPTION = [
  '运行 ggb-master 确定性工具链（随包 Python 脚本），参数在子命令之后原样透传，返回退出码与标准输出 / 错误。',
  'init <课件名> [--force] 建 projects/<课件名>/ 骨架；',
  'check <geogebra.xml> [--fix] [--json] [--quiet] 五层质量门（结构 / 引用 / 拓扑 / 数值 / JS）；',
  'pack <项目目录> -o exports/<课件名>.ggb [--skip-check] 打包（内部再跑一次质量门）；',
  'unpack <已有.ggb> [-o <目录>] [--force] 解包供 Modify 路线补丁；',
  'macro-preview <宏.ggt 或 macros/> [--json] 取用宏前的一键预览；',
  'selftest [--corpus <真实 .ggb 目录>] 工具链自检；html-demo-check <html|json> HTML 定妆件校验。',
  '首个参数也可直接写脚本文件名（如 ggb_check.py）作为退路。',
  '课件规划与构造判断不要放进这里：它是确定性工具，不会调用任何模型。',
].join(' ')

/** 把一次收集读数转成文本，缺失读数为空串。 */
function readText(reader) {
  if (reader === undefined) return { text: '', lossy: false }
  const read = reader.readFrom(0)
  return { text: read?.text ?? '', lossy: Boolean(read?.lossy) }
}

/** 收尾渲染：退出码 + 两路输出，供模型直接阅读。 */
function render(args, value) {
  const argv = Array.isArray(args?.args) ? args.args.join(' ') : ''
  const lines = ['$ ggb ' + argv, 'exitCode: ' + value.exitCode]
  if (value.truncated) lines.push('（输出超过上限，已截断）')
  if (value.stdout.length > 0) lines.push('--- stdout ---', value.stdout)
  if (value.stderr.length > 0) lines.push('--- stderr ---', value.stderr)
  return [{ type: 'text', text: lines.join('\n') }]
}

/** 首个参数 → 随包脚本绝对路径；未知子命令返回 undefined。 */
function resolveScript(sub) {
  const mapped = COMMANDS[sub]
  if (mapped !== undefined) return join(SCRIPTS_DIR, mapped)
  // 退路：允许直接点名随包脚本，但仍然不许跳出本包的 scripts/。
  if (typeof sub === 'string' && sub.endsWith('.py') && !sub.includes('/') && !sub.includes('\\')) {
    return join(SCRIPTS_DIR, sub)
  }
  return undefined
}

/**
 * 注册 ggb 工具。
 * @param ctx - 携带 tools / subprocess 服务的上下文。
 * @param config - command（Python 解释器路径或 PATH 名）、timeoutMs、maxOutputBytes。
 */
export function apply(ctx, config = {}) {
  const command = typeof config.command === 'string' && config.command.length > 0 ? config.command : undefined
  const timeoutMs = Number.isFinite(config.timeoutMs) && config.timeoutMs > 0 ? config.timeoutMs : 300000
  const maxOutputBytes = Number.isFinite(config.maxOutputBytes) && config.maxOutputBytes > 0 ? config.maxOutputBytes : 65536

  ctx.tools.register({
    name: 'ggb',
    description: DESCRIPTION,
    parameters: {
      type: 'object',
      additionalProperties: false,
      required: ['args'],
      properties: {
        args: {
          type: 'array',
          items: { type: 'string' },
          description: '子命令及其参数，按 CLI 原样写成数组，例如 ["check", "projects/<课件名>/geogebra.xml", "--fix"]、["pack", "projects/<课件名>/", "-o", "exports/<课件名>.ggb"]、["unpack", "exports/<课件名>.ggb", "-o", "projects/<课件名>-modify/"]。',
        },
        cwd: {
          type: 'string',
          description: '兼容参数；必须与当前会话工作区一致。工作区每次调用从会话取得，同时注入 GGB_ROOT。',
        },
      },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        required: ['exitCode', 'stdout', 'stderr', 'truncated'],
        properties: {
          exitCode: { type: 'integer', description: '进程退出码；未能取得时为 -1。' },
          stdout: { type: 'string' },
          stderr: { type: 'string' },
          truncated: { type: 'boolean', description: '输出是否超过收集上限。' },
        },
      },
      render,
    },
    timeoutMs,
    isConcurrencySafe: () => false,
    async execute(args, exec) {
      const argv = Array.isArray(args?.args) ? args.args.map(String) : []
      const sub = argv[0]
      const script = resolveScript(sub)
      if (script === undefined) {
        throw new Error('ggb: 未知子命令 ' + String(sub) + '，可用：' + Object.keys(COMMANDS).join(' / ') + '（或直接给随包脚本文件名）')
      }
      if (!existsSync(script)) {
        throw new Error('ggb: 随包脚本缺失 ' + script + '（插件包可能未完整复制）')
      }
      const session = exec?.agent?.session
      const headerCwd = session?.header?.cwd
      if (typeof headerCwd !== 'string' || !isAbsolute(headerCwd)) {
        throw new Error('ggb: 当前会话缺少绝对工作区路径，请先打开工作区')
      }
      // 可选服务通过 get 查询；Cordis 会拒绝直接读取未声明 inject 的属性。
      const policy = ctx.get('sandboxPolicy')
      const cwd = policy?.resolve({ session })?.workspaceRoot ?? headerCwd
      if (args?.cwd && (!isAbsolute(args.cwd) || args.cwd !== cwd)) {
        throw new Error('ggb: cwd 必须等于当前会话工作区绝对路径')
      }
      let executable
      const candidates = command ? [command] : ['python3', 'python']
      for (const candidate of candidates) {
        try {
          executable = await ctx.subprocess.resolveExecutable(candidate)
          if (executable) break
        } catch {
          // 明确配置不回退，自动发现可继续尝试下一个候选。
        }
      }
      if (!executable) {
        throw new Error('ggb: 未找到 Python 解释器，请确认 PATH 上有 python3（或在 profile patch 里显式配置 command 绝对路径）')
      }
      if (exec?.signal?.aborted) {
        const cancelled = new Error('ggb: 用户已取消')
        cancelled.name = 'AbortError'
        throw cancelled
      }
      const timeoutSignal = AbortSignal.timeout(timeoutMs)
      const signals = []
      if (exec?.signal) signals.push(exec.signal)
      signals.push(timeoutSignal)
      const handle = ctx.subprocess.spawn({
        argv: [executable, script, ...argv.slice(1)],
        cwd,
        // GGB_ROOT 是 skill 声明的路径约定；PYTHONDONTWRITEBYTECODE 避免污染随包目录。
        env: { GGB_ROOT: cwd, PYTHONDONTWRITEBYTECODE: '1' },
        stdio: {
          stdin: 'ignore',
          stdout: { maxBytes: maxOutputBytes },
          stderr: { maxBytes: maxOutputBytes },
        },
        graceMs: 5000,
        signal: signals.length === 1 ? signals[0] : AbortSignal.any(signals),
      })

      try {
        const outcome = await handle.done
        if (exec?.signal?.aborted) {
          const cancelled = new Error('ggb: 用户已取消')
          cancelled.name = 'AbortError'
          throw cancelled
        }
        const stdout = readText(handle.collected.stdout)
        const stderr = readText(handle.collected.stderr)
        return {
          exitCode: typeof outcome?.exitCode === 'number' ? outcome.exitCode : -1,
          stdout: stdout.text,
          stderr: stderr.text,
          truncated: stdout.lossy || stderr.lossy,
        }
      } catch (error) {
        if (exec?.signal?.aborted) {
          const cancelled = new Error('ggb: 用户已取消')
          cancelled.name = 'AbortError'
          throw cancelled
        }
        const stdout = readText(handle.collected.stdout)
        const stderr = readText(handle.collected.stderr)
        return {
          exitCode: -1,
          stdout: stdout.text,
          stderr: (stderr.text.length > 0 ? stderr.text + '\n' : '') + String(error?.message ?? error),
          truncated: stdout.lossy || stderr.lossy,
        }
      }
    },
  })
}
