import { Settings as SettingsIcon, Key, Bell, Database, Shield } from 'lucide-react'

export default function Settings() {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">
          Configure your bug bounty automator
        </p>
      </div>

      <div className="max-w-2xl space-y-6">
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">API Keys</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                className="input w-full"
                placeholder="sk-..."
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">
                HackerOne API Token
              </label>
              <input
                type="password"
                className="input w-full"
                placeholder="Enter token..."
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">
                Shodan API Key
              </label>
              <input
                type="password"
                className="input w-full"
                placeholder="Enter key..."
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Bell className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">Notifications</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white">Slack Notifications</p>
                <p className="text-sm text-slate-400">
                  Receive approval requests via Slack
                </p>
              </div>
              <input type="checkbox" className="toggle" />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-white">Email Notifications</p>
                <p className="text-sm text-slate-400">
                  Get notified via email
                </p>
              </div>
              <input type="checkbox" className="toggle" />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">
                Slack Webhook URL
              </label>
              <input
                type="text"
                className="input w-full"
                placeholder="https://hooks.slack.com/..."
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Database className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">Database</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                Database URL
              </label>
              <input
                type="text"
                className="input w-full"
                value="postgresql://bugbounty:***@localhost:5432/bugbounty_db"
                disabled
              />
            </div>

            <button className="btn btn-secondary">Run Migrations</button>
          </div>
        </div>

        <div className="flex justify-end">
          <button className="btn btn-primary">Save Settings</button>
        </div>
      </div>
    </div>
  )
}
