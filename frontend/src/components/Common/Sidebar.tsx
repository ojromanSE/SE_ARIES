import { useStore } from '../../store/useStore'
import {
  FolderOpen,
  BarChart2,
  DollarSign,
  Database,
  BookOpen,
  Settings,
  LogOut,
  Activity,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

const NAV_ITEMS = [
  { id: 'project-manager', label: 'Project Manager', icon: FolderOpen },
  { id: 'forecasting',     label: 'Forecasting',     icon: BarChart2 },
  { id: 'economics',       label: 'Economics',        icon: DollarSign },
  { id: 'data-manager',    label: 'Data Manager',     icon: Database },
  { id: 'reserves',        label: 'Reserves (RMS)',   icon: BookOpen },
]

export default function Sidebar() {
  const { sidebarOpen, setSidebarOpen, activeModule, setActiveModule, user, logout } = useStore()

  return (
    <aside
      className="flex flex-col bg-sidebar border-r border-border transition-all duration-200 shrink-0"
      style={{ width: sidebarOpen ? 'var(--sidebar-width)' : '56px' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-3 h-14 border-b border-border">
        <div className="flex items-center justify-center w-8 h-8 rounded bg-aries-700 shrink-0">
          <Activity className="w-4 h-4 text-aries-200" />
        </div>
        {sidebarOpen && (
          <div className="overflow-hidden">
            <div className="text-sm font-bold text-white leading-tight">SE_ARIES</div>
            <div className="text-xs text-gray-400 leading-tight">Petroleum Economics</div>
          </div>
        )}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="ml-auto text-gray-500 hover:text-gray-300 transition-colors shrink-0"
        >
          {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveModule(id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm transition-colors
              ${activeModule === id
                ? 'bg-aries-800/60 text-aries-300 border-r-2 border-aries-400'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
              }`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {sidebarOpen && <span className="truncate">{label}</span>}
          </button>
        ))}
      </nav>

      {/* Bottom — user info & logout */}
      <div className="border-t border-border p-3">
        {sidebarOpen && user && (
          <div className="mb-2">
            <div className="text-xs font-medium text-gray-300 truncate">{user.full_name || user.username}</div>
            <div className="text-xs text-gray-500 truncate capitalize">{user.role}</div>
          </div>
        )}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveModule('settings')}
            className="text-gray-500 hover:text-gray-300 p-1.5 rounded hover:bg-gray-800"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={logout}
            className="text-gray-500 hover:text-red-400 p-1.5 rounded hover:bg-gray-800"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
