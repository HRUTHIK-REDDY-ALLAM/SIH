import { useState } from 'react'
import { APP } from './data'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import SelectInvoice from './components/SelectInvoice'
import Consent from './components/Consent'
import Underwriting from './components/Underwriting'
import Offer from './components/Offer'
import Declined from './components/Declined'
import Disbursed from './components/Disbursed'
import Financier from './components/Financier'

export default function App() {
  const [view, setView] = useState('exporter') // exporter | financier
  const [screen, setScreen] = useState('dashboard') // dashboard select consent underwriting offer declined disbursed
  const [invoice, setInvoice] = useState(null) // invoice being processed
  const [run, setRun] = useState(null) // last completed underwriting run
  const [deals, setDeals] = useState([]) // all completed runs (financier view)
  const [activeDeals, setActiveDeals] = useState([]) // accepted deals (dashboard)

  const reset = () => {
    setView('exporter')
    setScreen('dashboard')
    setInvoice(null)
    setRun(null)
    setDeals([])
    setActiveDeals([])
  }

  const finishRun = (payload) => {
    setRun(payload)
    setDeals((d) => [payload, ...d.filter((x) => x.invoice.id !== payload.invoice.id)])
    setScreen(payload.decision.outcome === 'declined' ? 'declined' : 'offer')
  }

  const acceptOffer = () => {
    setActiveDeals((a) => [run, ...a.filter((x) => x.invoice.id !== run.invoice.id)])
    setScreen('disbursed')
  }

  const screens = {
    dashboard: <Dashboard activeDeals={activeDeals} onStart={() => setScreen('select')} />,
    select: (
      <SelectInvoice
        onBack={() => setScreen('dashboard')}
        onPick={(inv) => { setInvoice(inv); setScreen('consent') }}
      />
    ),
    consent: <Consent invoice={invoice} onBack={() => setScreen('select')} onDone={() => setScreen('underwriting')} />,
    underwriting: <Underwriting invoice={invoice} onCancel={() => setScreen('select')} onFinish={finishRun} />,
    offer: <Offer run={run} onAccept={acceptOffer} onBack={() => setScreen('underwriting')} />,
    declined: <Declined run={run} onHome={() => setScreen('dashboard')} />,
    disbursed: <Disbursed run={run} onHome={() => setScreen('dashboard')} />,
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header view={view} onView={setView} onReset={reset} />

      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-8">
        <div key={view === 'financier' ? 'financier' : screen} className="animate-rise">
          {view === 'financier' ? <Financier deals={deals} /> : screens[screen]}
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white/60">
        <div className="max-w-6xl mx-auto px-4 py-4 text-center text-[11px] leading-relaxed text-slate-400">
          {APP.name} is a decisioning agent, not a lender — credit is disbursed by RBI-licensed partner financiers.
          Hackathon prototype · all data is synthetic · no real GSTN, Account Aggregator, bank or registry connections.
        </div>
      </footer>
    </div>
  )
}
