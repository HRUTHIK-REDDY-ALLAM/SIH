import { ArrowRight, BadgeCheck, Bot, FileText, Landmark, Sparkles } from 'lucide-react'
import { COMPANY, DASH_STATS, HOW_IT_WORKS, PAST_DEALS } from '../data'
import { inr } from '../format'
import { Button, Card, Pill, SectionLabel } from './ui'

const HOW_ICONS = [FileText, Landmark, Bot, Sparkles]

export default function Dashboard({ activeDeals, onStart }) {
  return (
    <div className="space-y-8">
      {/* greeting */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            Welcome back, {COMPANY.short}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-500">
            <span>{COMPANY.name}</span>
            <span className="text-slate-300">·</span>
            <span>{COMPANY.city}</span>
            <Pill tone="slate">GSTIN {COMPANY.gstin}</Pill>
            <Pill tone="slate">{COMPANY.iec}</Pill>
          </div>
        </div>
        <Pill tone="emerald"><BadgeCheck className="h-3.5 w-3.5" /> Verified exporter</Pill>
      </div>

      {/* hero CTA */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-[#0b1d3a] to-[#1e3a8a] p-6 sm:p-8 text-white flex flex-col md:flex-row md:items-center gap-6">
          <div className="flex-1">
            <div className="text-xs font-semibold uppercase tracking-wider text-blue-300 mb-2">
              Working capital, unlocked
            </div>
            <h2 className="text-xl sm:text-2xl font-bold leading-snug">
              Turn an unpaid export invoice into cash today
            </h2>
            <p className="mt-2 text-sm text-blue-100/90 max-w-xl">
              Have a confirmed invoice to a Singapore buyer? Our AI agent underwrites it live —
              a decision in about 2 minutes instead of 3 weeks, funds from a licensed partner financier.
            </p>
          </div>
          <Button variant="hero" size="lg" onClick={onStart} className="shrink-0">
            Request financing on an invoice <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </Card>

      {/* stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {DASH_STATS.map((s) => (
          <Card key={s.label} className="p-5">
            <div className="text-sm text-slate-500">{s.label}</div>
            <div className="mt-1 text-2xl font-extrabold tracking-tight text-slate-900 tabular-nums">{s.value}</div>
            <div className="mt-0.5 text-xs text-slate-400">{s.sub}</div>
          </Card>
        ))}
      </div>

      {/* deals */}
      <div>
        <SectionLabel>Recent deals</SectionLabel>
        <Card className="divide-y divide-slate-100">
          {activeDeals.map((d) => (
            <div key={d.invoice.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-4">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-60 animate-ping" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-blue-600" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-slate-900 text-sm">
                  {d.invoice.code} · {d.invoice.buyer.name}
                </div>
                <div className="text-xs text-slate-500">
                  Financed today · buyer pays {d.invoice.due} · balance {inr(d.decision.balance)} on settlement
                </div>
              </div>
              <div className="font-bold text-slate-900 tabular-nums">{inr(d.invoice.amount)}</div>
              <Pill tone="blue">Active</Pill>
            </div>
          ))}
          {PAST_DEALS.map((d) => (
            <div key={d.code} className="flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-4">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-slate-900 text-sm">{d.code} · {d.buyer}</div>
                <div className="text-xs text-slate-500">{d.detail}</div>
              </div>
              <div className="font-bold text-slate-900 tabular-nums">{inr(d.amount)}</div>
              <Pill tone="emerald">{d.status}</Pill>
            </div>
          ))}
        </Card>
      </div>

      {/* how it works */}
      <div>
        <SectionLabel>How TradeBridge works</SectionLabel>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {HOW_IT_WORKS.map((h, i) => {
            const Icon = HOW_ICONS[i]
            return (
              <Card key={h.title} className="p-5">
                <div className="flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                    <Icon className="h-4.5 w-4.5" />
                  </span>
                  <span className="text-xs font-bold text-slate-400">STEP {i + 1}</span>
                </div>
                <div className="mt-3 font-semibold text-slate-900 text-sm">{h.title}</div>
                <p className="mt-1 text-xs text-slate-500 leading-relaxed">{h.text}</p>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
