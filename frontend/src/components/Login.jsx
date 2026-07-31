import { useState } from 'react'
import { ArrowRight, KeyRound, Landmark, Lock } from 'lucide-react'
import { api } from '../api'
import { APP, DEMO_ACCOUNTS } from '../data'
import { Button, Card, ErrorBox, Pill } from './ui'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState(DEMO_ACCOUNTS.msme.email)
  const [password, setPassword] = useState(DEMO_ACCOUNTS.msme.password)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e?.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { token, user } = await api('/api/auth/login', {
        method: 'POST',
        body: { email, password },
      })
      onLogin(token, user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-md mx-auto pt-10 space-y-5">
      <div className="text-center">
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">Sign in to {APP.name}</h1>
        <p className="mt-1.5 text-sm text-slate-500">
          Real accounts, real sessions — OAuth2/JWT served by the FastAPI backend.
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            <span className="text-xs font-semibold text-slate-600">Email</span>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-2 focus:outline-blue-600"
              autoComplete="username"
            />
          </label>
          <label className="block">
            <span className="text-xs font-semibold text-slate-600">Password</span>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-2 focus:outline-blue-600"
              autoComplete="current-password"
            />
          </label>
          {error && <ErrorBox title="Sign-in failed" detail={error} />}
          <Button size="lg" className="w-full" disabled={busy} type="submit">
            <Lock className="h-4 w-4" /> {busy ? 'Signing in…' : 'Sign in'} <ArrowRight className="h-4 w-4" />
          </Button>
        </form>

        <div className="mt-5 border-t border-slate-100 pt-4 space-y-2">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Demo accounts</div>
          <button
            onClick={() => { setEmail(DEMO_ACCOUNTS.msme.email); setPassword(DEMO_ACCOUNTS.msme.password) }}
            className="w-full flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5 text-left text-xs hover:bg-slate-50 cursor-pointer"
          >
            <KeyRound className="h-3.5 w-3.5 text-blue-600 shrink-0" />
            <span className="font-semibold text-slate-700">{DEMO_ACCOUNTS.msme.label}</span>
            <span className="ml-auto font-mono text-slate-400">{DEMO_ACCOUNTS.msme.email}</span>
          </button>
          <div className="flex items-start gap-2 text-[11px] text-slate-400 px-1">
            <Landmark className="h-3.5 w-3.5 mt-px shrink-0" />
            The Financier tab has its own sign-in ({DEMO_ACCOUNTS.financier.email} · same password).
          </div>
        </div>
      </Card>

      <div className="flex justify-center">
        <Pill tone="slate">Password for both demo accounts: demo1234</Pill>
      </div>
    </div>
  )
}
