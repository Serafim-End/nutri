export function SettingsPage() {
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-2xl font-bold text-white mb-2">Settings</h1>
        <p className="text-slate-400">Configure admin panel and platform settings</p>
      </div>

      {/* Settings sections */}
      <div className="space-y-6">
        {/* General Settings */}
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
          <h2 className="font-display text-lg font-semibold text-white mb-4">General Settings</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-slate-800/50">
              <div>
                <p className="font-medium text-white">Platform Name</p>
                <p className="text-sm text-slate-500">The name displayed across the platform</p>
              </div>
              <input
                type="text"
                defaultValue="NutriMatch"
                disabled
                className="px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-700/50 text-slate-300 text-sm"
              />
            </div>
            <div className="flex items-center justify-between py-3 border-b border-slate-800/50">
              <div>
                <p className="font-medium text-white">Default Currency</p>
                <p className="text-sm text-slate-500">Default currency for new services</p>
              </div>
              <select
                disabled
                className="px-4 py-2 rounded-lg bg-slate-900/50 border border-slate-700/50 text-slate-300 text-sm"
              >
                <option>USD</option>
                <option>EUR</option>
                <option>GBP</option>
              </select>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-white">Maintenance Mode</p>
                <p className="text-sm text-slate-500">Temporarily disable the platform</p>
              </div>
              <button
                disabled
                className="relative inline-flex h-6 w-11 items-center rounded-full bg-slate-700 opacity-50"
              >
                <span className="inline-block h-4 w-4 transform rounded-full bg-slate-400 translate-x-1" />
              </button>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
          <h2 className="font-display text-lg font-semibold text-white mb-4">Notifications</h2>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="w-12 h-12 rounded-xl bg-slate-800/50 flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <p className="text-slate-400 text-sm mb-2">Notification settings coming soon</p>
            <p className="text-slate-500 text-xs">Configure email and Telegram notifications</p>
          </div>
        </div>

        {/* API Settings */}
        <div className="rounded-2xl bg-slate-925/50 border border-slate-800/50 p-6">
          <h2 className="font-display text-lg font-semibold text-white mb-4">API & Integrations</h2>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="w-12 h-12 rounded-xl bg-slate-800/50 flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <p className="text-slate-400 text-sm mb-2">API configuration coming soon</p>
            <p className="text-slate-500 text-xs">Manage API keys and third-party integrations</p>
          </div>
        </div>
      </div>
    </div>
  )
}

