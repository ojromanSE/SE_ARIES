import { useStore } from '../../store/useStore'
import { Search, Bell, HelpCircle } from 'lucide-react'

const MODULE_TITLES: Record<string, string> = {
  'project-manager': 'Project Manager',
  'forecasting':     'Forecasting & Decline Curve Analysis',
  'economics':       'Economic Simulator',
  'data-manager':    'Data Manager',
  'reserves':        'Reserve Management System (RMS)',
  'settings':        'Settings',
}

export default function Header() {
  const { activeModule, selectedPropnum } = useStore()

  return (
    <header className="h-14 bg-header border-b border-border flex items-center px-4 gap-4 shrink-0">
      {/* Module title */}
      <div className="flex-1">
        <h1 className="text-sm font-semibold text-white">
          {MODULE_TITLES[activeModule] || activeModule}
        </h1>
        {selectedPropnum && (
          <div className="text-xs text-gray-400">
            Property: <span className="text-aries-400 font-mono">{selectedPropnum}</span>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="relative hidden md:block">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
        <input
          type="text"
          placeholder="Search properties..."
          className="bg-gray-800 border border-gray-700 text-gray-300 text-sm pl-8 pr-3 py-1.5 rounded-md
                     focus:outline-none focus:ring-1 focus:ring-aries-500 focus:border-aries-500 w-64
                     placeholder-gray-600"
        />
      </div>

      {/* Icons */}
      <div className="flex items-center gap-1">
        <button className="text-gray-500 hover:text-gray-300 p-2 rounded hover:bg-gray-800" title="Help">
          <HelpCircle className="w-4 h-4" />
        </button>
        <button className="text-gray-500 hover:text-gray-300 p-2 rounded hover:bg-gray-800" title="Notifications">
          <Bell className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
