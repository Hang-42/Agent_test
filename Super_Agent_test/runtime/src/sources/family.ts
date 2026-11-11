/** Simulation-only local event source for the upstream Super-agent runtime. */
import { createServer } from 'node:http'
import { appendFileSync } from 'node:fs'
import { randomUUID } from 'node:crypto'
import { z } from 'zod'
import type { Runtime } from '../app/runtime.ts'
import type { SourceKind } from './kind.ts'

const family: SourceKind = {
  kind: 'family',
  title: { zh: '家庭仿真', en: 'Family simulation' },
  description: { zh: '仅供本地仿真的事件', en: 'Local simulation events only' },
  schema: z.object({}).strict(), fields: [], health: [],
  policy: {
    schema: z.object({ allowed: z.array(z.object({ id: z.string(), name: z.string().optional() })).default([]) }).strict(),
    fields: [], explicit: { zh: '模拟交互请求', en: 'Simulated interaction requests' },
  },
  channel: {
    async send(_host, message) {
      appendFileSync('/out/replies.jsonl', JSON.stringify(message) + '\n')
      return 'sent'
    },
    link() { return { url: '', label: { zh: '本地仿真', en: 'Local simulation' } } },
  },
}

export function installFamilySource(runtime: Runtime): () => void {
  const unregister = runtime.sources.register(family)
  const server = createServer((req, res) => {
    if (req.method !== 'POST' || req.url !== '/event') { res.writeHead(404).end(); return }
    let body = ''
    req.setEncoding('utf8')
    req.on('data', chunk => { body += chunk; if (body.length > 4096) req.destroy() })
    req.on('end', () => {
      try {
        const data = JSON.parse(body) as { text?: unknown }
        if (typeof data.text !== 'string' || !data.text.trim() || data.text.length > 3000) throw new Error('invalid event')
        const thread = { source: 'family', id: 'simulation' }
        const result = runtime.receive({ id: `family:${randomUUID()}`, source: 'family', threads: [thread],
          actor: { source: 'family', id: 'demo' }, human: true, addressed: 'direct', at: new Date().toISOString(),
          text: data.text, channel: { source: 'family', thread: 'simulation', address: {} }, meta: { synthetic: true } })
        res.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify({ result }))
      } catch { res.writeHead(400).end('invalid event') }
    })
  })
  server.listen(39182, '127.0.0.1')
  return () => { server.close(); unregister() }
}
