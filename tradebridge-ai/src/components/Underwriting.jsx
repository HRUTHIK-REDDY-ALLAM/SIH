import { AlertTriangle, ArrowRight, Bot, Building2, CheckCircle2, Clock, Database, FileCheck2, Gauge, Loader2, MinusCircle, ShieldAlert } from 'lucide-react'
import { useUnderwriting } from '../useUnderwriting'
import { cx, inr, mmss } from '../format'
import { Button, Card, Pill, TraceConsole } from './ui'

const STEP_ICONS = { gather: Database, verify: FileCheck2, fraud: ShieldAlert, buyer: Building2, score: Gauge }

const STATUS = {
  pending: { chip: 'Queued', chipCls: 'bg-slate-100 text-slate-500' },
  running: { chip: 'Running…', chipCls: 'bg-blue-50 text-blue-700' },
  done: { chip: 'Cleared', chipCls: 'bg-emerald-50 text-emerald-700' },
  warn: { chip: 'Caution', chipCls: 'bg-amber-50 text-amber-700' },
  flagged: { chip: 'FLAGGED', chipCls: 'bg-red-600 text-white' },
  skipped: { chip: 'Skipped', chipCls: 'bg-slate-100 text-slate-400' },
}

function StepIcon({ step }) {
  const Icon = STEP_ICONS[step.id]
  const base = 'flex h-11 w-11 items-center justify-center rounded-xl border-2 transition-all shrink-0'
  switch (step.status) {
    case 'running':
      return (
        <span className={cx(base, 'border-blue-500 bg-blue-50 text-blue-600 animate-ring')}>
          <Loader2 className="h-5 w-5 animate-spin" />
        </span>
      )
    case 'done':
      return (
        <span className={cx(base, 'border-emerald-500 bg-emerald-50 text-emerald-600')}>
          <CheckCircle2 className="h-5 w-5 animate-pop" />
        </span>
      )
    case 'warn':
      return (
        <span className={cx(base, 'border-amber-500 bg-amber-50 text-amber-600')}>
          <AlertTriangle className="h-5 w-5 animate-pop" />
        </span>
      )
    case 'flagged':
      return (
        <span className={cx(base, 'border-red-600 bg-red-600 text-white animate-ring-red')}>
          <ShieldAlert className="h-5 w-5 animate-pop" />
        </span>
      )
    case 'skipped':
      return (
        <span className={cx(base, 'border-slate-200 bg-slate-50 text-slate-300')}>
          <MinusCircle className="h-5 w-5" />
        </span>
      )
    default:
      return (
        <span className={cx(base, 'border-slate-200 bg-white text-slate-300')}>
          <Icon className="h-5 w-5" />
        </span>
      )
  }
}

function StepCard({ step, isLast }) {
  const meta = STATUS[step.status]
  return (
    <div className="relative flex gap-4">
      {!isLast && (
        <span className={cx(
          'absolute left-[21px] top-12 bottom-0 w-0.5 rounded',
          step.status === 'done' || step.status === 'warn' ? 'bg-emerald-200'
            : step.status === 'flagged' ? 'bg-red-200' : 'bg-slate-200',
        )} />
      )}
      <StepIcon step={step} />
      <Card className={cx(
        'flex-1 p-4 mb-3 transition-all',
        step.status === 'running' && 'border-blue-300 ring-2 ring-blue-500/15',
        step.status === 'flagged' && 'border-red-400 ring-2 ring-red-500/20 bg-red-50 animate-shake',
        step.status === 'skipped' && 'opacity-55',
      )}>
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className={cx('font-semibold text-sm', step.status === 'flagged' ? 'text-red-800' : 'text-slate-900')}>
              {step.title}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">{step.caption}</div>
          </div>
          <span className={cx('rounded-full px-2.5 py-1 text-[11px] font-bold whitespace-nowrap', meta.chipCls)}>
            {meta.chip}
          </span>
        </div>

        {step.finding && (step.status === 'done' || step.status === 'warn' || step.status === 'flagged') && (
          <p className={cx(
            'mt-2.5 text-[13px] leading-relaxed border-t pt-2.5 animate-rise',
            step.status === 'flagged' ? 'text-red-700 font-semibold border-red-200'
              : step.status === 'warn' ? 'text-amber-700 border-amber-100'
              : 'text-slate-600 border-slate-100',
          )}>
            {step.finding}
          </p>
        )}
        {step.status === 'skipped' && (
          <p className="mt-2.5 text-[13px] text-slate-400 border-t border-slate-100 pt-2.5">
            Skipped — pipeline halted after the fraud flag.
          </p>
        )}
      </Card>
    </div>
  )
}

function ResultBanner({ result, elapsed, onContinue }) {
  const styles = {
    approved: {
      wrap: 'from-emerald-600 to-emerald-700', icon: <CheckCircle2 className="h-7 w-7" />,
      cta: 'View your offer', label: 'APPROVED',
    },
    conditional: {
      wrap: 'from-amber-500 to-amber-600', icon: <AlertTriangle className="h-7 w-7" />,
      cta: 'View conditional offer', label: 'CONDITIONAL',
    },
    declined: {
      wrap: 'from-red-600 to-red-700', icon: <ShieldAlert className="h-7 w-7" />,
      cta: 'See full details', label: 'DECLINED',
    },
  }
  const s = styles[result.outcome]
  return (
    <div className={cx('rounded-2xl bg-gradient-to-r text-white p-5 sm:p-6 shadow-lg animate-rise', s.wrap, result.outcome === 'declined' && 'animate-ring-red')}>
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="flex items-center gap-3.5 flex-1">
          <span className="animate-pop">{s.icon}</span>
          <div>
            <div className="text-[11px] font-bold tracking-widest opacity-80">{s.label}</div>
            <div className="font-bold text-lg leading-snug">{result.headline}</div>
            <div className="text-sm opacity-90 mt-0.5">{result.banner}</div>
          </div>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right text-xs opacity-85 leading-relaxed hidden sm:block">
            Decision in {mmss(elapsed)}<br />vs 15–21 days traditional
          </div>
          <Button variant="ghost" className="!text-slate-900" onClick={onContinue}>
            {s.cta} <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function Underwriting({ invoice, onCancel, onFinish }) {
  const { steps, trace, result, elapsed } = useUnderwriting(invoice)
  const running = !result
  const current = steps.find((s) => s.status === 'running')

  return (
    <div className="space-y-6">
      {/* header row */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="relative">
          <span className={cx(
            'flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-lg shadow-blue-700/30',
            running && 'animate-ring',
          )}>
            <Bot className="h-6 w-6" />
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-slate-900">
            {running ? <span className="thinking">AI agent is underwriting your invoice…</span> : 'Underwriting complete'}
          </h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <Pill tone="blue">{invoice.code}</Pill>
            <span className="font-medium">{invoice.buyer.name}</span>
            <span className="text-slate-300">·</span>
            <span className="font-semibold tabular-nums">{inr(invoice.amount)}</span>
            {running && current && (
              <>
                <span className="text-slate-300">·</span>
                <span className="text-blue-600 font-medium">{current.title}</span>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Pill tone="navy" className="!bg-slate-900 !border-slate-700 !text-white tabular-nums">
            <Clock className="h-3.5 w-3.5" /> {mmss(elapsed)}
          </Pill>
          {running && (
            <button onClick={onCancel} className="text-xs font-medium text-slate-400 hover:text-slate-600 cursor-pointer">
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* pipeline + trace */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
        <div className="lg:col-span-3">
          {steps.map((s, i) => <StepCard key={s.id} step={s} isLast={i === steps.length - 1} />)}
        </div>
        <div className="lg:col-span-2 lg:sticky lg:top-20">
          <TraceConsole lines={trace} live={running} heightClass="h-72 lg:h-[460px]" />
          <p className="mt-2 text-[11px] text-slate-400 text-center">
            Every decision ships with this full reasoning trace — auditable by the exporter and the financier.
          </p>
        </div>
      </div>

      {result && (
        <ResultBanner
          result={result}
          elapsed={elapsed}
          onContinue={() => onFinish({ invoice, decision: result, trace, steps, elapsed })}
        />
      )}
    </div>
  )
}
