import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, Building2, CalendarDays, CheckCircle2 } from 'lucide-react'
import { api } from '../api'
import { cx, inr } from '../format'
import { Button, Card, ErrorBox, Pill, Spinner } from './ui'

export default function SelectInvoice({ token, onBack, onPick }) {
  const [invoices, setInvoices] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api('/api/invoices', { token }).then(setInvoices).catch((e) => setError(e.message))
  }, [token])

  useEffect(() => { load() }, [load])

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors cursor-pointer">
        <ArrowLeft className="h-4 w-4" /> Dashboard
      </button>

      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">Select an invoice to finance</h1>
        <p className="mt-1.5 text-sm text-slate-500">
          Unpaid, confirmed export invoices to your Singapore buyers — served live from the invoices table.
        </p>
      </div>

      {error && <ErrorBox title="Could not load invoices" detail={error} onRetry={load} />}
      {!error && invoices === null && <Spinner label="Loading invoices…" />}
      {invoices?.length === 0 && (
        <Card className="p-8 text-center text-sm text-slate-500">
          No pending invoices left — every receivable is already financed or settled.
          Use the ↻ button in the header to reset the demo data.
        </Card>
      )}

      <div className="space-y-4" role="radiogroup" aria-label="Invoices">
        {(invoices ?? []).map((inv) => {
          const isSel = selected?.id === inv.id
          return (
            <Card
              key={inv.id}
              role="radio"
              aria-checked={isSel}
              tabIndex={0}
              onClick={() => setSelected(inv)}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && setSelected(inv)}
              className={cx(
                'p-5 cursor-pointer transition-all hover:border-blue-300 hover:shadow-md',
                isSel && 'border-blue-600 ring-2 ring-blue-600/20 shadow-md',
              )}
            >
              <div className="flex items-start gap-4">
                <span className={cx(
                  'mt-1 flex h-5 w-5 items-center justify-center rounded-full border-2 transition-colors shrink-0',
                  isSel ? 'border-blue-600 bg-blue-600' : 'border-slate-300',
                )}>
                  {isSel && <CheckCircle2 className="h-4 w-4 text-white animate-pop" />}
                </span>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-slate-500">{inv.code}</span>
                    <Pill tone={inv.tagTone}>{inv.tag}</Pill>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2 font-semibold text-slate-900">
                    <Building2 className="h-4 w-4 text-slate-400 shrink-0" />
                    <span className="truncate">{inv.buyer.name}</span>
                    <Pill tone="slate" className="hidden sm:inline-flex">SG</Pill>
                  </div>
                  <div className="mt-1 text-xs text-slate-500">{inv.goods}</div>
                  <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1">
                      <CalendarDays className="h-3.5 w-3.5" /> Due {inv.due} · {inv.tenor}
                    </span>
                    <span className="font-mono">{inv.irn}</span>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <div className="text-lg font-extrabold tracking-tight text-slate-900 tabular-nums">{inr(inv.amount)}</div>
                  <div className="text-[11px] text-slate-400">unpaid</div>
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      <div className="flex justify-end">
        <Button size="lg" disabled={!selected} onClick={() => onPick(selected)}>
          Continue with {selected ? selected.code : 'an invoice'} <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
