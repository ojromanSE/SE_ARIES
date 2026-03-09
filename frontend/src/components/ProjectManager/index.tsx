import ProjectTree from './ProjectTree'
import PropertyBrowser from './PropertyBrowser'
import PropertyDetail from './PropertyDetail'
import { useStore } from '../../store/useStore'

export default function ProjectManager() {
  const { selectedPropnum } = useStore()

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Project Tree */}
      <div className="w-64 border-r border-border shrink-0 overflow-hidden flex flex-col">
        <ProjectTree />
      </div>

      {/* Center: Property Browser */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <PropertyBrowser />
      </div>

      {/* Right: Property Detail (when selected) */}
      {selectedPropnum && (
        <div className="w-80 border-l border-border shrink-0 overflow-y-auto bg-gray-900/50">
          <PropertyDetail propnum={selectedPropnum} />
        </div>
      )}
    </div>
  )
}
