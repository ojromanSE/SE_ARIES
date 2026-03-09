import Sidebar from '../components/Common/Sidebar'
import Header from '../components/Common/Header'
import { useStore } from '../store/useStore'
import ProjectManager from '../components/ProjectManager'
import ForecastingModule from '../components/Forecasting'
import EconomicsModule from '../components/Economics'

const PLACEHOLDER = ({ label }: { label: string }) => (
  <div className="flex items-center justify-center h-full text-gray-500">
    <div className="text-center">
      <div className="text-4xl mb-3">🚧</div>
      <div className="text-sm font-medium">{label}</div>
      <div className="text-xs mt-1">Coming soon</div>
    </div>
  </div>
)

export default function MainLayout() {
  const { activeModule } = useStore()

  const renderModule = () => {
    switch (activeModule) {
      case 'project-manager': return <ProjectManager />
      case 'forecasting':     return <ForecastingModule />
      case 'economics':       return <EconomicsModule />
      case 'data-manager':    return <PLACEHOLDER label="Data Manager" />
      case 'reserves':        return <PLACEHOLDER label="Reserve Management System (RMS)" />
      case 'settings':        return <PLACEHOLDER label="Settings" />
      default:                return <ProjectManager />
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden">
          {renderModule()}
        </main>
      </div>
    </div>
  )
}
