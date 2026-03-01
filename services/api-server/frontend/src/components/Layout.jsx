import { useState, useEffect, useRef, useCallback } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard, Zap, GitMerge, Map, Bell, Building2,
  Menu, X, Search, Wifi, WifiOff,
} from 'lucide-react'
import toast, { Toaster } from 'react-hot-toast'

const NAV = [
  { to: '/dashboard',   label: 'Dashboard',   Icon: LayoutDashboard },
  { to: '/leads',       label: 'Leads',        Icon: Zap },
  { to: '/pipeline',    label: 'Pipeline',     Icon: GitMerge },
  { to: '/maps',        label: 'Market Map',   Icon: Map },
  { to: '/alerts',      label: 'Alerts',       Icon: Bell },
  { to: '/contractors', label: 'Contractors',  Icon: Building2 },
]

function NavItem({ to, label, Icon }) {
  return (
    <NavLink to={to}
      className={({ isActive }) => clsx(
        'flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors',
        isActive
          ? 'border-l-2 border-primary-700 bg-primary-50 text-primary-700 font-semibold pl-[10px]'
          : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50 font-medium'
      )}>
      <Icon className="h-4 w-4 shrink-0" />
      {label}
    </NavLink>
  )
}

function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <div className="fixed inset-0 z-20 bg-black/30 lg:hidden" onClick={onClose} />}
      <aside className={clsx(
        'fixed inset-y-0 left-0 z-30 flex w-56 flex-col border-r border-gray-200 bg-white pt-14 lg:static lg:translate-x-0 lg:inset-auto transition-transform duration-200',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        <button onClick={onClose} className="absolute right-3 top-3 p-1 text-gray-400 hover:text-gray-600 lg:hidden">
          <X className="h-5 w-5" />
        </button>
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
          {NAV.map(n => <NavItem key={n.to} {...n} />)}
        </nav>
        <div className="px-4 py-4 border-t border-gray-100">
          <p className="text-xs text-gray-300">BuildScope v0.2</p>
        </div>
      </aside>
    </>
  )
}

function Navbar({ onMenuToggle, wsConnected }) {
  const [q, setQ] = useState('')
  return (
    <header className="fixed inset-x-0 top-0 z-40 h-14 flex items-center gap-4 border-b border-gray-200 bg-white px-4 lg:px-6">
      <button onClick={onMenuToggle} className="p-1.5 text-gray-500 hover:bg-gray-100 rounded lg:hidden">
        <Menu className="h-5 w-5" />
      </button>

      {/* Logo */}
      <NavLink to="/dashboard" className="flex items-center gap-2 shrink-0 text-primary-700 font-bold text-[15px]">
        <div className="flex h-7 w-7 items-center justify-center rounded bg-primary-700">
          <Building2 className="h-4 w-4 text-white" />
        </div>
        BuildScope
      </NavLink>

      {/* Search */}
      <div className="flex-1 max-w-xs hidden sm:block">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
          <input value={q} onChange={e => setQ(e.target.value)}
            placeholder="Search leads, contractors…"
            className="input-base pl-8 py-1.5 text-sm" />
        </div>
      </div>

      {/* Status */}
      <div className="ml-auto flex items-center gap-3">
        <span className={clsx('hidden sm:flex items-center gap-1.5 text-xs',
          wsConnected ? 'text-emerald-600' : 'text-gray-400')}>
          {wsConnected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
          {wsConnected ? 'Live' : 'Offline'}
        </span>
      </div>
    </header>
  )
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)
  const email = localStorage.getItem('pipeline_email') || ''
  const location = useLocation()

  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  const connectWs = useCallback(() => {
    if (!email) return
    try {
      const ws = new WebSocket(`ws://${window.location.host}/api/ws/alerts?email=${encodeURIComponent(email)}`)
      ws.onopen = () => setWsConnected(true)
      ws.onclose = () => { setWsConnected(false); setTimeout(connectWs, 5000) }
      ws.onerror = () => ws.close()
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data)
          if (data.type === 'new_lead') {
            toast.custom((t) => (
              <div className={clsx('flex items-start gap-3 bg-white rounded-lg px-4 py-3 shadow-card-hover border border-gray-100', t.visible ? 'opacity-100' : 'opacity-0')}>
                <Zap className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-gray-900">New lead matched</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{data.lead?.title?.slice(0, 60)}</p>
                </div>
              </div>
            ), { duration: 5000 })
          }
        } catch {}
      }
      wsRef.current = ws
    } catch {}
  }, [email])

  useEffect(() => { connectWs(); return () => wsRef.current?.close() }, [connectWs])

  return (
    <div className="flex h-screen flex-col bg-background">
      <Navbar onMenuToggle={() => setSidebarOpen(o => !o)} wsConnected={wsConnected} />
      <div className="flex flex-1 overflow-hidden pt-14">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 overflow-y-auto p-5 lg:p-7">
          <Outlet />
        </main>
      </div>
      <Toaster position="bottom-right"
        toastOptions={{ className: 'text-sm font-medium', style: { fontFamily: 'Inter, system-ui, sans-serif', borderRadius: '8px', fontSize: '13px' } }} />
    </div>
  )
}
