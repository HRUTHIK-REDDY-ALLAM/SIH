import { useEffect, useState } from 'react'
import { api, tokens } from './api'
import { APP } from './data'
import Header from './components/Header'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import SelectInvoice from './components/SelectInvoice'
import Consent from './components/Consent'
import Underwriting from './components/Underwriting'
import Offer from './components/Offer'
import Declined from './components/Declined'
import Disbursed from './components/Disbursed'
import Financier from './components/Financier'
import { Spinner } from './components/ui'

export default function App() {
  const [booting, setBooting] = useState(true)
  const [user, setUser] = useState(null)
  const [view, setView] = useState('exporter') // exporter | financier
  const [screen, setScreen] = useState('dashboard')
  const [invoice, setInvoice] = useState(null) // invoice being processed
  const [run, setRun] = useState(null) // deal payload driving offer/declined/disbursed

  const token = tokens.get('msme')

  useEffect(() => {
    const stored = tokens.get('msme')
    if (!stored) {
      setBooting(false)
      return
    }
    api('/api/auth/me', { token: stored })
      .then((u) => setUser(u))
      .catch(() => tokens.clear('msme'))
      .finally(() => setBooting(false))
  }, [])

  const handleLogin = (newToken, newUser) => {
    tokens.set('msme', newToken)
    setUser(newUser)
    setScreen('dashboard')
  }

  const reset = async () => {
    try { await api('/api/admin/reset', { method: 'POST' }) } catch { /* backend down — still clear */ }
    tokens.clearAll()
    window.location.reload()
  }

  const finishRun = (payload) => {
    setRun(payload)
    setScreen(payload.decision?.outcome === 'declined' ? 'declined' : 'offer')
  }

  const openDeal = async (dealId) => {
    const payload = await api(`/api/deals/${dealId}`, { token })
    setRun(payload)
    if (payload.decision?.outcome === 'declined' || payload.deal.status === 'declined') setScreen('declined')
    else if (payload.deal.status === 'financed' || payload.deal.status === 'repaid') setScreen('disbursed')
    else setScreen('offer')
  }

  const screens = {
    dashboard: (
      <Dashboard token={token} onStart={() => setScreen('select')} onOpenDeal={openDeal} />
    ),
    select: (
      <SelectInvoice
        token={token}
        onBack={() => setScreen('dashboard')}
        onPick={(inv) => { setInvoice(inv); setScreen('consent') }}
      />
    ),
    consent: (
      <Consent token={token} invoice={invoice}
               onBack={() => setScreen('select')} onDone={() => setScreen('underwriting')} />
    ),
    underwriting: (
      <Underwriting token={token} invoice={invoice}
                    onCancel={() => setScreen('select')} onFinish={finishRun} />
    ),
    offer: (
      <Offer token={token} run={run} onUpdated={setRun}
             onAccepted={(payload) => { setRun(payload); setScreen('disbursed') }}
             onHome={() => setScreen('dashboard')} />
    ),
    declined: <Declined run={run} onHome={() => setScreen('dashboard')} />,
    disbursed: <Disbursed run={run} onHome={() => setScreen('dashboard')} />,
  }

  let content
  if (booting) content = <Spinner label={`Connecting to ${APP.name}…`} />
  else if (view === 'financier') content = <Financier />
  else if (!user) content = <Login onLogin={handleLogin} />
  else content = screens[screen]

  return (
    <div className="min-h-screen flex flex-col">
      <Header view={view} onView={setView} onReset={reset} />

      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-8">
        <div key={view === 'financier' ? 'financier' : `${screen}-${user ? 'in' : 'out'}`} className="animate-rise">
          {content}
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white/60">
        <div className="max-w-6xl mx-auto px-4 py-4 text-center text-[11px] leading-relaxed text-slate-400">
          {APP.name} ({APP.meaning}) is a decisioning agent, not a lender — credit is disbursed by RBI-licensed
          financiers via {APP.itfs}. Full-stack prototype: FastAPI + LangGraph + PostgreSQL/Redis backend with a real
          lien registry, hash-anchored invoice fingerprinting, trade-graph cycle detection, Shapley score attribution
          and RAG-grounded compliance · external data sources (GSTN, Account Aggregator, ACRA, payment rails) are
          mock adapters over synthetic data.
        </div>
      </footer>
    </div>
  )
}
