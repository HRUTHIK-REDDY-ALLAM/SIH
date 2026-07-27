import { useEffect, useRef, useState } from 'react'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// Plays an invoice's scripted pipeline: marks steps running → done/flagged,
// streams trace lines with realistic delays, and emits the final decision.
// Fully deterministic — same invoice, same show, every time.
export function useUnderwriting(invoice) {
  const [steps, setSteps] = useState(() => invoice.pipeline.map((s) => ({ ...s, status: 'pending' })))
  const [trace, setTrace] = useState([])
  const [result, setResult] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const doneElapsed = useRef(0)

  useEffect(() => {
    let cancelled = false
    setSteps(invoice.pipeline.map((s) => ({ ...s, status: 'pending' })))
    setTrace([])
    setResult(null)
    setElapsed(0)

    const t0 = Date.now()
    const secs = () => (Date.now() - t0) / 1000
    const timer = setInterval(() => {
      if (!cancelled) setElapsed(Math.floor(secs()))
    }, 400)

    const push = (line) => setTrace((t) => [...t, { ...line, ts: secs().toFixed(1) }])

    ;(async () => {
      await sleep(700)
      if (cancelled) return
      push({ k: 'sys', text: `Agent session started · underwriting ${invoice.code} for ₹${invoice.amount.toLocaleString('en-IN')}` })

      for (let i = 0; i < invoice.pipeline.length; i++) {
        const stepDef = invoice.pipeline[i]
        if (cancelled) return
        setSteps((prev) => prev.map((s, j) => (j === i ? { ...s, status: 'running' } : s)))

        for (const line of stepDef.lines) {
          await sleep(line.d)
          if (cancelled) return
          push(line)
        }

        await sleep(320)
        if (cancelled) return
        setSteps((prev) => prev.map((s, j) => (j === i ? { ...s, status: stepDef.result } : s)))

        if (stepDef.halt) {
          setSteps((prev) => prev.map((s, j) => (j > i ? { ...s, status: 'skipped' } : s)))
          push({ k: 'sys', text: 'Pipeline halted — remaining checks skipped.' })
          break
        }
      }

      await sleep(750)
      if (cancelled) return
      clearInterval(timer)
      doneElapsed.current = Math.max(1, Math.floor(secs()))
      setElapsed(doneElapsed.current)
      push({ k: 'sys', text: 'Decision issued. Full reasoning attached to the deal record.' })
      setResult(invoice.decision)
    })()

    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [invoice.id])

  return { steps, trace, result, elapsed }
}
