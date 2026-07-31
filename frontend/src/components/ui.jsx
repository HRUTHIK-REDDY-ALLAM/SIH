import { useEffect, useRef, useState } from 'react'
import { cx } from '../format'

// ---------------------------------------------------------------- buttons ---
const VARIANTS = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm shadow-blue-600/30',
  hero: 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md shadow-blue-700/30',
  success: 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-600/30',
  ghost: 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-300',
  dark: 'bg-slate-900 hover:bg-slate-800 text-white',
}

export function Button({ variant = 'primary', size = 'md', className, children, ...props }) {
  return (
    <button
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600',
        'active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none cursor-pointer',
        size === 'lg' ? 'px-6 py-3.5 text-base' : 'px-4 py-2.5 text-sm',
        VARIANTS[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

// ------------------------------------------------------------------ cards ---
export function Card({ className, children }) {
  return (
    <div className={cx('bg-white rounded-2xl border border-slate-200 shadow-[0_1px_3px_rgba(15,23,42,0.06)]', className)}>
      {children}
    </div>
  )
}

const PILL_TONES = {
  blue: 'bg-blue-50 text-blue-700 border-blue-200',
  emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  amber: 'bg-amber-50 text-amber-700 border-amber-200',
  red: 'bg-red-50 text-red-700 border-red-200',
  slate: 'bg-slate-100 text-slate-600 border-slate-200',
  navy: 'bg-white/10 text-blue-100 border-white/20',
}

export function Pill({ tone = 'slate', className, children }) {
  return (
    <span className={cx('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap', PILL_TONES[tone], className)}>
      {children}
    </span>
  )
}

export function SectionLabel({ children }) {
  return <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">{children}</div>
}

// ------------------------------------------------------------ score gauge ---
export function ScoreGauge({ score, band, size = 150 }) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => setValue(score), 120)
    return () => clearTimeout(t)
  }, [score])

  const color = score >= 70 ? '#059669' : score >= 45 ? '#d97706' : '#dc2626'
  return (
    <div className="flex flex-col items-center" style={{ width: size }}>
      <svg viewBox="0 0 100 58" style={{ width: size }} aria-label={`Risk score ${score} of 100`}>
        <path d="M8 52 A 42 42 0 0 1 92 52" fill="none" stroke="#e2e8f0" strokeWidth="9" strokeLinecap="round" pathLength="100" />
        <path
          d="M8 52 A 42 42 0 0 1 92 52" fill="none" stroke={color} strokeWidth="9" strokeLinecap="round"
          pathLength="100" strokeDasharray={`${value} 100`} className="gauge-arc"
        />
        <text x="50" y="45" textAnchor="middle" fontSize="21" fontWeight="800" fill="#0f172a">{score}</text>
        <text x="50" y="55" textAnchor="middle" fontSize="7.5" fontWeight="600" fill="#64748b">RISK SCORE / 100</text>
      </svg>
      <span className="mt-1 text-sm font-semibold" style={{ color }}>{band}</span>
    </div>
  )
}

// ------------------------------------------------- Shapley attribution -----
// Renders the exact per-feature contributions the backend computed. Bars are
// signed and scaled against the largest |φ| in the set, so a reader can see at
// a glance which features carried the score and which dragged it down.
export function AttributionChart({ attribution }) {
  if (!attribution?.contributions?.length) return null
  const { contributions, baseValue, baseLabel, method } = attribution
  const max = Math.max(...contributions.map((c) => Math.abs(c.phi)), 1)

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 mb-3">
        <span className="text-xs text-slate-500">
          Baseline <span className="font-semibold text-slate-700 tabular-nums">{baseValue}</span>
          <span className="text-slate-400"> ({baseLabel})</span>
        </span>
        <span className="text-[11px] text-slate-400">points vs baseline</span>
      </div>

      <div className="space-y-2.5">
        {contributions.map((c) => {
          const positive = c.phi >= 0
          const width = `${(Math.abs(c.phi) / max) * 50}%`
          return (
            <div key={c.id}>
              <div className="flex items-baseline justify-between gap-3 text-xs">
                <span className="font-medium text-slate-700 truncate">{c.label}</span>
                <span className={cx('font-bold tabular-nums shrink-0',
                                    positive ? 'text-emerald-600' : 'text-red-600')}>
                  {positive ? '+' : ''}{c.phi.toFixed(1)}
                </span>
              </div>
              {/* signed bar: center line = baseline, right = helps, left = hurts */}
              <div className="mt-1 relative h-2 rounded bg-slate-100">
                <span className="absolute inset-y-0 left-1/2 w-px bg-slate-300" />
                <span
                  className={cx('absolute inset-y-0 rounded transition-all duration-700',
                                positive ? 'bg-emerald-500 left-1/2' : 'bg-red-500')}
                  style={positive ? { width } : { width, right: '50%' }}
                />
              </div>
              {c.detail && <div className="mt-0.5 text-[11px] text-slate-400">{c.detail}</div>}
            </div>
          )
        })}
      </div>

      {method && <p className="mt-3 text-[11px] text-slate-400 leading-relaxed border-t border-slate-100 pt-2">{method}</p>}
    </div>
  )
}

// ------------------------------------------------- regulatory citations -----
export function Citations({ citations, className }) {
  if (!citations?.length) return null
  return (
    <div className={cx('space-y-2', className)}>
      {citations.map((c) => (
        <details key={c.ref} className="group rounded-lg border border-slate-200 bg-slate-50/70">
          <summary className="flex items-center gap-2 cursor-pointer select-none px-3 py-2 text-xs">
            <span className="font-mono font-bold text-blue-700 shrink-0">{c.ref}</span>
            <span className="text-slate-500 truncate">{c.title}</span>
          </summary>
          <p className="px-3 pb-2.5 text-[11px] leading-relaxed text-slate-500 italic">“{c.excerpt}…”</p>
        </details>
      ))}
    </div>
  )
}

// ---------------------------------------------------------- trace console ---
const KIND_STYLE = {
  req:  { glyph: '→', cls: 'text-sky-300' },
  res:  { glyph: '←', cls: 'text-slate-300' },
  calc: { glyph: '∑', cls: 'text-violet-300' },
  ok:   { glyph: '✓', cls: 'text-emerald-300' },
  warn: { glyph: '!', cls: 'text-amber-300' },
  flag: { glyph: '⚠', cls: 'text-red-300 font-semibold' },
  sys:  { glyph: '·', cls: 'text-slate-500 italic' },
}

export function TraceLog({ lines, live = false, heightClass = 'h-72' }) {
  const boxRef = useRef(null)
  useEffect(() => {
    if (live && boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight
  }, [lines, live])

  return (
    <div ref={boxRef} className={cx('trace overflow-y-auto px-4 py-3 font-mono text-[12.5px] leading-relaxed', heightClass)}>
      {lines.map((line, i) => {
        const s = KIND_STYLE[line.k] || KIND_STYLE.sys
        const isLast = i === lines.length - 1
        return (
          <div key={i} className={cx('py-0.5 animate-rise', line.k === 'flag' && 'bg-red-500/10 -mx-2 px-2 rounded')}>
            {line.ts != null && <span className="text-slate-600 mr-2">[{line.ts}s]</span>}
            <span className={cx(s.cls, live && isLast && 'caret')}>
              {s.glyph} {line.text}
            </span>
          </div>
        )
      })}
      {live && lines.length === 0 && <div className="text-slate-500 italic caret">initialising agent…</div>}
    </div>
  )
}

export function TraceConsole({ lines, live, heightClass }) {
  return (
    <div className="rounded-2xl bg-[#0b1730] border border-[#1c3454] overflow-hidden shadow-lg shadow-slate-900/10">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#1c3454]">
        <span className={cx('h-2 w-2 rounded-full', live ? 'bg-emerald-400 animate-soft' : 'bg-slate-500')} />
        <span className="text-xs font-semibold tracking-wide text-slate-300">AGENT REASONING TRACE</span>
        <span className="ml-auto text-[11px] text-slate-500">{live ? 'live' : `${lines.length} events`}</span>
      </div>
      <TraceLog lines={lines} live={live} heightClass={heightClass} />
    </div>
  )
}

// ------------------------------------------------------- loading / errors ---
export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-400">
      <span className="h-8 w-8 rounded-full border-[3px] border-slate-200 border-t-blue-600 animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorBox({ title = 'Something went wrong', detail, onRetry }) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-5 animate-rise">
      <div className="font-bold text-red-800 text-sm">{title}</div>
      {detail && <p className="mt-1 text-sm text-red-700 leading-relaxed">{detail}</p>}
      {onRetry && (
        <Button variant="ghost" className="mt-3" onClick={onRetry}>Try again</Button>
      )}
    </div>
  )
}

// ------------------------------------------------------------------ toast ---
export function useToast() {
  const [toast, setToast] = useState(null)
  const timeoutRef = useRef(null)
  const show = (msg) => {
    clearTimeout(timeoutRef.current)
    setToast(msg)
    timeoutRef.current = setTimeout(() => setToast(null), 4000)
  }
  useEffect(() => () => clearTimeout(timeoutRef.current), [])
  const node = toast ? (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-rise">
      <div className="rounded-xl bg-slate-900 text-white text-sm font-medium px-5 py-3 shadow-xl max-w-md text-center">
        {toast}
      </div>
    </div>
  ) : null
  return { show, node }
}
