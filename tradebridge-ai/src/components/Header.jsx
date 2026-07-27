import { RotateCcw } from 'lucide-react'
import { APP } from '../data'
import { cx } from '../format'

// India ↔ Singapore suspension-bridge motif with a "comet" gliding across —
// data and money crossing the corridor.
function BridgeMotif() {
  return (
    <div className="hidden md:flex items-center gap-2 select-none" aria-hidden="true">
      <span className="text-[11px] font-bold tracking-wide text-blue-200">IN</span>
      <svg viewBox="0 0 220 40" className="w-40 lg:w-52 h-9">
        {/* deck */}
        <line x1="6" y1="32" x2="214" y2="32" stroke="#3b5a83" strokeWidth="2" strokeLinecap="round" />
        {/* main cable */}
        <path d="M10 32 Q110 -8 210 32" fill="none" stroke="#4a6b96" strokeWidth="1.6" />
        {/* suspender cables */}
        {[40, 75, 110, 145, 180].map((x, i) => {
          const y = 32 - 20 * (1 - Math.pow((x - 110) / 100, 2))
          return <line key={i} x1={x} y1={y} x2={x} y2="31" stroke="#3b5a83" strokeWidth="1" />
        })}
        {/* travelling light */}
        <path d="M10 32 Q110 -8 210 32" fill="none" stroke="#7cc0ff" strokeWidth="2.4" strokeLinecap="round" pathLength="100" className="comet" />
        {/* endpoints */}
        <circle cx="10" cy="32" r="3.5" fill="#7cc0ff" />
        <circle cx="210" cy="32" r="3.5" fill="#7cc0ff" />
      </svg>
      <span className="text-[11px] font-bold tracking-wide text-blue-200">SG</span>
    </div>
  )
}

function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <svg viewBox="0 0 32 32" className="h-9 w-9 rounded-xl shadow-md shadow-blue-900/40" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#1d4ed8" />
        <path d="M5 21 Q16 7 27 21" stroke="#bfdbfe" strokeWidth="2.2" fill="none" />
        <line x1="10.5" y1="15.6" x2="10.5" y2="22" stroke="#bfdbfe" strokeWidth="1.4" />
        <line x1="16" y1="13.4" x2="16" y2="22" stroke="#bfdbfe" strokeWidth="1.4" />
        <line x1="21.5" y1="15.6" x2="21.5" y2="22" stroke="#bfdbfe" strokeWidth="1.4" />
        <line x1="4" y1="22" x2="28" y2="22" stroke="#ffffff" strokeWidth="2" />
      </svg>
      <div className="leading-tight">
        <div className="font-extrabold text-[17px] tracking-tight text-white">{APP.name}</div>
        <div className="text-[11px] text-blue-200 hidden sm:block">{APP.tagline}</div>
      </div>
    </div>
  )
}

export default function Header({ view, onView, onReset }) {
  return (
    <header className="sticky top-0 z-40 bg-gradient-to-r from-[#0a1730] via-[#0c2044] to-[#0f2a56] border-b border-blue-900/60">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center gap-4">
        <Logo />
        <div className="flex-1 flex justify-center"><BridgeMotif /></div>

        <span className="hidden sm:inline-flex items-center rounded-full border border-amber-400/40 bg-amber-400/10 px-2.5 py-1 text-[11px] font-semibold text-amber-300 whitespace-nowrap">
          Prototype · synthetic data
        </span>

        <nav className="flex items-center rounded-xl bg-white/10 p-1" aria-label="View">
          {[
            { id: 'exporter', label: 'Exporter' },
            { id: 'financier', label: 'Financier' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => onView(tab.id)}
              className={cx(
                'px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer',
                view === tab.id ? 'bg-white text-slate-900 shadow-sm' : 'text-blue-100 hover:text-white',
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <button
          onClick={onReset}
          title="Reset demo"
          className="p-2 rounded-lg text-blue-200 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
