import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Target,
  Bug,
  CheckCircle,
  Settings,
  Shield,
  Bell,
  Activity,
  ChevronDown,
  Search,
  Package,
  Database,
  Cpu,
  Key,
  Zap,
  AlertTriangle,
  Wand2,
  Brain,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Targets', href: '/targets', icon: Target },
  { name: 'Programs', href: '/programs', icon: Bug },
  { name: 'Programs Wizard', href: '/programs/wizard', icon: Wand2 },
  { name: 'AI Center', href: '/programs', icon: Brain },
  { name: 'Findings', href: '/findings', icon: AlertTriangle },
  { name: 'Plugins', href: '/plugins', icon: Package },
  { name: 'Approvals', href: '/approvals', icon: CheckCircle },
  { name: 'Intel', href: '/intel', icon: Database },
  { name: 'Testing', href: '/testing', icon: Zap },
  { name: 'Integrations', href: '/integrations', icon: Activity },
];

const adminNavigation = [
  { name: 'Jobs', href: '/jobs', icon: Cpu },
  { name: 'Headers', href: '/headers', icon: Key },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Layout() {
  const location = useLocation();
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <div className="flex h-screen bg-surface overflow-hidden">
      <aside className="w-64 bg-surface flex flex-col border-r border-white/5">
        <div className="h-16 flex items-center gap-3 px-5 border-b border-white/5">
          <div className="w-8 h-8 rounded bg-secondary/20 flex items-center justify-center">
            <Shield className="w-5 h-5 text-secondary" />
          </div>
          <div>
            <h1 className="font-display font-bold text-lg text-primary tracking-tight">
              BugBounty
            </h1>
            <p className="text-[10px] font-mono text-white/40 uppercase tracking-widest">
              Automator
            </p>
          </div>
        </div>

        <nav className="flex-1 py-4 overflow-y-auto">
          <div className="px-3 mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
              <input
                type="text"
                placeholder="Search targets..."
                className="w-full bg-surface-50 border-0 rounded-lg text-xs font-mono py-2 pl-9 pr-4 text-white/70 placeholder:text-white/30 focus:outline-none focus:ring-1 focus:ring-secondary/50"
              />
            </div>
          </div>

          <div className="px-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'nav-item rounded-lg',
                    isActive && 'active'
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>

          <div className="mt-6 px-3">
            <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest px-4 mb-2">
              Admin
            </div>
            <div className="space-y-1">
              {adminNavigation.map((item) => {
                const isActive = location.pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      'nav-item rounded-lg text-white/50',
                      isActive && 'active'
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="mt-6 px-3">
            <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest px-4 mb-2">
              Recent Targets
            </div>
            <div className="space-y-1">
              <Link
                to="/targets/1"
                className="flex items-center gap-2 px-4 py-2 text-xs font-mono text-white/50 hover:text-secondary hover:bg-surface-50/50 rounded transition-colors"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-pulse" />
                api.example.com
              </Link>
              <Link
                to="/targets/2"
                className="flex items-center gap-2 px-4 py-2 text-xs font-mono text-white/50 hover:text-secondary hover:bg-surface-50/50 rounded transition-colors"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-warning" />
                staging.example.com
              </Link>
            </div>
          </div>
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="glass-card-subtle p-3 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-primary font-mono text-xs font-bold">SA</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-display font-medium text-white truncate">
                  Security Admin
                </div>
                <div className="text-[10px] font-mono text-white/40">
                  Level 4 Access
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-white/30" />
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-surface border-b border-white/5 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-white/50 uppercase tracking-wider">
                System Status
              </span>
              <span className="flex items-center gap-1.5 text-xs">
                <span className="w-2 h-2 rounded-full bg-tertiary animate-pulse" />
                <span className="font-mono text-tertiary">ONLINE</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 px-4 py-1.5 glass-card-subtle rounded-lg">
              <span className="text-[10px] font-mono text-white/40 uppercase">
                Active Nodes
              </span>
              <span className="text-xs font-mono text-secondary">12</span>
            </div>

            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 hover:bg-surface-50 rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5 text-white/60" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-error" />
            </button>

            <div className="w-px h-8 bg-white/10" />

            <button className="px-4 py-2 bg-secondary/10 hover:bg-secondary/20 border border-secondary/30 rounded-lg transition-colors">
              <span className="text-xs font-mono text-secondary uppercase tracking-wider">
                Quick Scan
              </span>
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6 bg-surface relative">
          <Outlet />
        </main>

        <footer className="h-8 bg-surface-lowest border-t border-white/5 flex items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-mono text-white/30 uppercase tracking-wider">
              CPU: 23%
            </span>
            <span className="text-[10px] font-mono text-white/30 uppercase tracking-wider">
              RAM: 4.2GB
            </span>
            <span className="text-[10px] font-mono text-white/30 uppercase tracking-wider">
              Network: 1.2MB/s
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-mono text-tertiary">
              Last Sync: 2m ago
            </span>
            <span className="text-[10px] font-mono text-white/30">
              v2.4.1
            </span>
          </div>
        </footer>
      </div>

      {showNotifications && (
        <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
      )}
      <div
        className={cn(
          'fixed top-16 right-4 w-80 z-50 transition-all duration-200',
          showNotifications ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2 pointer-events-none'
        )}
      >
        <div className="glass-panel rounded-lg overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h3 className="font-display text-sm text-primary uppercase tracking-wider">
              Notifications
            </h3>
          </div>
          <div className="max-h-80 overflow-y-auto">
            <div className="p-4 border-b border-white/5 hover:bg-surface-50/50 transition-colors cursor-pointer">
              <div className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-tertiary mt-1.5" />
                <div>
                  <div className="text-xs font-mono text-white">
                    Target scan completed
                  </div>
                  <div className="text-[10px] font-mono text-white/40 mt-1">
                    api.example.com - 3 findings
                  </div>
                </div>
              </div>
            </div>
            <div className="p-4 border-b border-white/5 hover:bg-surface-50/50 transition-colors cursor-pointer">
              <div className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-warning mt-1.5" />
                <div>
                  <div className="text-xs font-mono text-white">
                    Approval required
                  </div>
                  <div className="text-[10px] font-mono text-white/40 mt-1">
                    SQL Injection test pending review
                  </div>
                </div>
              </div>
            </div>
            <div className="p-4 hover:bg-surface-50/50 transition-colors cursor-pointer">
              <div className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-secondary mt-1.5" />
                <div>
                  <div className="text-xs font-mono text-white">
                    Integration synced
                  </div>
                  <div className="text-[10px] font-mono text-white/40 mt-1">
                    HackerOne: 12 new reports
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
