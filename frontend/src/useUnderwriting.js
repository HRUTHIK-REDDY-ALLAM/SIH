import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { FALLBACK_STEPS } from './data'

// Creates a real financing deal on the backend, then polls it. Everything the
// UI renders — steps, trace, decision — is read back from the server's audit
// log, so the animation IS the database content.
export function useUnderwriting(invoice, token) {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState(null)
  const startedRef = useRef(false)

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true
    let stopped = false
    let timer

    ;(async () => {
      try {
        const { deal_id } = await api('/api/deals', {
          method: 'POST',
          body: { invoice_id: invoice.id },
          token,
        })
        const tick = async () => {
          if (stopped) return
          try {
            const data = await api(`/api/deals/${deal_id}`, { token })
            if (stopped) return
            setPayload(data)
            if (data.deal.status === 'running') timer = setTimeout(tick, 600)
          } catch (e) {
            if (!stopped) setError(e.message)
          }
        }
        tick()
      } catch (e) {
        if (!stopped) setError(e.message)
      }
    })()

    return () => {
      stopped = true
      clearTimeout(timer)
    }
  }, [invoice.id, token])

  const running = !payload || payload.deal.status === 'running'
  return {
    steps: payload?.steps ?? FALLBACK_STEPS,
    trace: payload?.trace ?? [],
    result: !running ? payload.decision : null,
    elapsed: payload?.deal.elapsed ?? 0,
    payload,
    error,
  }
}
