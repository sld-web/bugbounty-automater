import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Target,
  Bug,
  CheckCircle,
  Settings,
  Shield,
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Targets', href: '/targets', icon: Target },
  { name: 'Programs', href: '/programs', icon: Bug },
  { name: 'Approvals', href: '/approvals', icon: CheckCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="flex h-screen bg-slate-900">
      <aside className="w-64 bg-slate-800 border-r border-slate-700">
        <div className="flex items-center gap-2 h-16 px-4 border-b border-slate-700">
          <Shield className="w-8 h-8 text-primary-500" />
          <div>
            <h1 className="font-bold text-white">BugBounty</h1>
            <p className="text-xs text-slate-400">Automator</p>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname.startsWith(item.href)
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                )}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
