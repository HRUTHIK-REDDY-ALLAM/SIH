import { useCallback, useEffect, useState } from 'react'
import { Banknote, BookOpen, Bot, Check, ChevronDown, Landmark, LogOut, RefreshCw, Scale3d, ShieldAlert, ShieldCheck, X } from 'lucide-react'
import { api, tokens } from '../api'
import { APP, DEMO_ACCOUNTS } from '../data'
import { cx, inr } from '../format'
import { AttributionChart, Button, Card, Citations, ErrorBox, Pill, ScoreGauge, SectionLabel, Spinner, TraceConsole, useToast } from './ui'

const STATUS_PILL = {
  repaid: { label: 'Settled', tone: 'emerald' },
  financed: { label: 'Financed', tone: 'blue' },
  approved: { label: 'Approved', tone: 'emerald' },
  conditional: { label: 'Conditional', tone: 'amber' },
  manual_review: { label: 'Needs review', tone: 'amber' },
  declined: { label: 'Declined', tone: 'red' },
  running: { label: 'Underwriting', tone: 'slate' },
  error: { label: 'Failed', tone: 'red' },
}

function FinLogin({ onToken }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [email, setEmail] = useState(DEMO_ACCOUNTS.financier.email)
  const [password, setPassword] = useState(DEMO_ACCOUNTS.financier.password)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { token, user } = await api('/api/auth/login', { method: 'POST', body: { email, password } })
      if (user.role !== 'financier') throw new Error('That account is not a financier account.')
      tokens.set('financier', token)
      onToken(token)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="max-w-md mx-auto pt-8 space-y-4">
      <div className="text-center">
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 flex items-center justify-center gap-2.5">
          <Landmark className="h-6 w-6 text-blue-700" /> {APP.financier}
        </h1>
        <p className="mt-1.5 text-sm text-slate-500">Partner-financier sign-in — separate role, separate session.</p>
      </div>
      <Card className="p-6">
        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="text-xs font-semibold text-slate-600">Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                   className="mt-1 w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-2 focus:outline-blue-600" />
          </label>
          <label className="block">
            <span className="text-xs font-semibold text-slate-600">Password</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                   className="mt-1 w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-2 focus:outline-blue-600" />
          </label>
          {error && <ErrorBox title="Sign-in failed" detail={error} />}
          <Button size="lg" className="w-full" disabled={busy} type="submit">
            {busy ? 'Signing in…' : 'Enter the deal desk'}
          </Button>
        </form>
      </Card>
    </div>
  )
}

function DealCard({ item, token, onUpdated, showToast }) {
  const { deal, invoice, decision, trace, facts, msme } = item
  const d = decision ?? {}
  const declined = deal.status === 'declined'
  const pill = STATUS_PILL[deal.status] ?? { label: deal.status, tone: 'slate' }
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)

  const act = async (path, body) => {
    setBusy(true)
    try {
      const updated = await api(`/api/financier/deals/${deal.id}/${path}`, { method: 'POST', body, token })
      onUpdated(updated)
    } catch (e) {
      showToast(e.message)
    } finally {
      setBusy(false)
    }
  }

  const reviewable = deal.status === 'manual_review' || deal.status === 'conditional'

  return (
    <Card className={cx('overflow-hidden', declined && 'border-red-300')}>
      <div className={cx('px-5 py-4 border-b flex flex-wrap items-center gap-3',
                         declined ? 'bg-red-50 border-red-100' : 'bg-slate-50 border-slate-100')}>
        {declined
          ? <ShieldAlert className="h-5 w-5 text-red-600 shrink-0" />
          : <ShieldCheck className="h-5 w-5 text-emerald-600 shrink-0" />}
        <div className="flex-1 min-w-0">
          <div className="font-bold text-slate-900 text-sm">
            #{deal.id} · {invoice.code} · {msme} → {invoice.buyer.name}
          </div>
          <div className="text-xs text-slate-500">{invoice.goods}</div>
        </div>
        <div className="font-extrabold text-slate-900 tabular-nums">{inr(invoice.amount)}</div>
        <Pill tone={pill.tone}>{pill.label}</Pill>
      </div>

      <div className="p-5 flex flex-col md:flex-row gap-6">
        <div className="flex-1 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5">
            {(facts ?? []).map(([k, v]) => (
              <div key={k}>
                <div className="text-[11px] text-slate-400 font-medium">{k}</div>
                <div className={cx('text-[13px] font-semibold',
                                   String(v).startsWith('MATCH') ? 'text-red-600' : 'text-slate-800')}>
                  {v}
                </div>
              </div>
            ))}
          </div>

          {d.reasons?.length > 0 && (
            <div className={cx('rounded-xl border px-4 py-3 text-[13px] leading-relaxed',
                               declined ? 'bg-red-50 border-red-200 text-red-700' : 'bg-blue-50 border-blue-100 text-slate-600')}>
              <span className="inline-flex items-center gap-1.5 font-bold text-slate-800 mr-1">
                <Bot className="h-3.5 w-3.5 text-blue-600" /> Agent:
              </span>
              {d.reasons[0]}
            </div>
          )}

          {d.overridden && (
            <div className="text-xs text-slate-500">
              <span className="font-semibold text-slate-700">Override:</span> {d.overridden.action} by {d.overridden.by}
              {d.overridden.note && <> — “{d.overridden.note}”</>}
            </div>
          )}

          {/* actions write back to the database */}
          {reviewable && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <input
                value={note} onChange={(e) => setNote(e.target.value)} placeholder="Decision note (optional)"
                className="flex-1 min-w-40 rounded-xl border border-slate-300 px-3 py-2 text-xs focus:outline-2 focus:outline-blue-600"
              />
              <Button variant="success" disabled={busy} onClick={() => act('override', { action: 'approve', note })}>
                <Check className="h-4 w-4" /> Approve
              </Button>
              <Button variant="ghost" disabled={busy} className="!text-red-600 !border-red-200"
                      onClick={() => act('override', { action: 'decline', note })}>
                <X className="h-4 w-4" /> Decline
              </Button>
            </div>
          )}
          {deal.status === 'financed' && (
            <Button variant="dark" disabled={busy} onClick={() => act('simulate-repayment')}>
              <Banknote className="h-4 w-4" /> {busy ? 'Settling…' : 'Simulate buyer payment'}
            </Button>
          )}
        </div>

        <div className="flex md:flex-col items-center justify-center gap-2 shrink-0">
          {declined ? (
            <div className="text-center px-6">
              <div className="text-3xl font-extrabold text-red-600">✕</div>
              <div className="text-xs font-bold text-red-600 mt-1">
                {d.evidence ? 'FRAUD BLOCK' : 'DECLINED'}
              </div>
              {d.evidence && <div className="text-[11px] text-slate-400 mt-0.5">{d.evidence.ref}</div>}
            </div>
          ) : deal.score != null ? (
            <ScoreGauge score={deal.score} band={deal.band} size={130} />
          ) : null}
        </div>
      </div>

      {(d.attribution || d.citations?.length > 0) && (
        <details className="group border-t border-slate-100">
          <summary className="flex items-center gap-2 cursor-pointer select-none px-5 py-3 text-xs font-semibold text-slate-500 hover:bg-slate-50">
            <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" />
            Score attribution & regulatory grounding
          </summary>
          <div className="px-5 pb-5 grid grid-cols-1 md:grid-cols-2 gap-6">
            {d.attribution && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Scale3d className="h-4 w-4 text-blue-600" />
                  <span className="font-bold text-slate-900 text-xs">Score attribution</span>
                </div>
                <AttributionChart attribution={d.attribution} />
              </div>
            )}
            {d.citations?.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  <span className="font-bold text-slate-900 text-xs">Regulatory grounding</span>
                </div>
                <Citations citations={d.citations} />
              </div>
            )}
          </div>
        </details>
      )}

      {(trace?.length ?? 0) > 0 && (
        <details className="group border-t border-slate-100">
          <summary className="flex items-center gap-2 cursor-pointer select-none px-5 py-3 text-xs font-semibold text-slate-500 hover:bg-slate-50">
            <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" />
            Audit trace ({trace.length} events)
          </summary>
          <div className="px-5 pb-5">
            <TraceConsole lines={trace} live={false} heightClass="h-64" />
          </div>
        </details>
      )}
    </Card>
  )
}

export default function Financier() {
  const [token, setToken] = useState(tokens.get('financier'))
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const { show, node: toastNode } = useToast()

  const load = useCallback(() => {
    if (!token) return
    setError(null)
    api('/api/financier/deals', { token })
      .then(setData)
      .catch((e) => {
        if (e.status === 401 || e.status === 403) {
          tokens.clear('financier')
          setToken(null)
        } else setError(e.message)
      })
  }, [token])

  useEffect(() => { load() }, [load])

  if (!token) return <FinLogin onToken={setToken} />
  if (error) return <ErrorBox title="Could not load the deal desk" detail={error} onRetry={load} />
  if (!data) return <Spinner label="Loading the deal desk…" />

  const replaceDeal = (updated) => {
    setData((prev) => ({
      ...prev,
      deals: prev.deals.map((x) => (x.deal.id === updated.deal.id ? updated : x)),
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2.5">
            <Landmark className="h-6 w-6 text-blue-700" /> {data.mandate.lender} — deal desk
          </h1>
          <p className="mt-1.5 text-sm text-slate-500">
            Every deal the agent underwrote, with its score, evidence and full audit trace — decision-ready.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={load}><RefreshCw className="h-4 w-4" /> Refresh</Button>
          <Button variant="ghost" onClick={() => { tokens.clear('financier'); setToken(null) }}>
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        </div>
      </div>

      <Card className="p-4 flex flex-wrap items-center gap-x-6 gap-y-2 bg-gradient-to-r from-[#0b1d3a] to-[#13294f] border-blue-900 text-white">
        <span className="text-xs font-bold tracking-widest text-blue-300">DELEGATED MANDATE</span>
        <span className="text-sm">{data.mandate.text}</span>
        <Pill tone="navy" className="ml-auto">Powered by {APP.name}</Pill>
      </Card>

      <div className="space-y-5">
        <SectionLabel>Underwritten deals ({data.deals.length})</SectionLabel>
        {data.deals.map((item) => (
          <DealCard key={item.deal.id} item={item} token={token} onUpdated={replaceDeal} showToast={show} />
        ))}
      </div>
      {toastNode}
    </div>
  )
}
