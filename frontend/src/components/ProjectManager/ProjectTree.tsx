import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FolderOpen, Folder, Plus, ChevronRight, ChevronDown, Trash2 } from 'lucide-react'
import { projectsApi, scenariosApi } from '../../utils/api'
import { useStore } from '../../store/useStore'
import type { Project, Scenario } from '../../types'
import LoadingSpinner from '../Common/LoadingSpinner'

export default function ProjectTree() {
  const { selectedProjectId, selectedScenarioId, setSelectedProjectId, setSelectedScenarioId } = useStore()
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [showNewProject, setShowNewProject] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const queryClient = useQueryClient()

  const { data: projects, isLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => (await projectsApi.list()).data,
  })

  const createProject = useMutation({
    mutationFn: (name: string) => projectsApi.create({
      project_name: name,
      default_discount_rate: 10.0,
      consolidation_method: 'SUM',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setNewProjectName('')
      setShowNewProject(false)
    },
  })

  const deleteProject = useMutation({
    mutationFn: (id: number) => projectsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })

  const toggleExpand = (id: number) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (isLoading) return <LoadingSpinner size="sm" />

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Projects</span>
        <button
          onClick={() => setShowNewProject(true)}
          className="text-gray-400 hover:text-white p-1 rounded hover:bg-gray-700"
          title="New Project"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* New project input */}
      {showNewProject && (
        <div className="px-3 py-2 border-b border-border bg-gray-800/50">
          <input
            type="text"
            placeholder="Project name..."
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && newProjectName.trim()) createProject.mutate(newProjectName.trim())
              if (e.key === 'Escape') setShowNewProject(false)
            }}
            className="input-field text-xs"
            autoFocus
          />
          <div className="flex gap-1 mt-1">
            <button
              onClick={() => newProjectName.trim() && createProject.mutate(newProjectName.trim())}
              className="btn-primary text-xs py-1 px-2"
              disabled={!newProjectName.trim()}
            >
              Create
            </button>
            <button onClick={() => setShowNewProject(false)} className="btn-secondary text-xs py-1 px-2">Cancel</button>
          </div>
        </div>
      )}

      {/* Tree */}
      <div className="flex-1 overflow-y-auto py-1">
        {projects?.length === 0 && (
          <div className="px-4 py-6 text-xs text-gray-500 text-center">
            No projects yet.<br />Click + to create one.
          </div>
        )}
        {projects?.map((project) => (
          <ProjectNode
            key={project.id}
            project={project}
            isSelected={selectedProjectId === project.id}
            isExpanded={expanded.has(project.id)}
            onSelect={() => { setSelectedProjectId(project.id); setSelectedScenarioId(null) }}
            onToggle={() => toggleExpand(project.id)}
            onDelete={() => deleteProject.mutate(project.id)}
            selectedScenarioId={selectedScenarioId}
            onSelectScenario={setSelectedScenarioId}
          />
        ))}
      </div>
    </div>
  )
}

function ProjectNode({
  project, isSelected, isExpanded, onSelect, onToggle, onDelete,
  selectedScenarioId, onSelectScenario,
}: {
  project: Project
  isSelected: boolean
  isExpanded: boolean
  onSelect: () => void
  onToggle: () => void
  onDelete: () => void
  selectedScenarioId: number | null
  onSelectScenario: (id: number) => void
}) {
  const { data: scenarios } = useQuery<Scenario[]>({
    queryKey: ['scenarios', project.id],
    queryFn: async () => (await scenariosApi.list(project.id)).data,
    enabled: isExpanded,
  })

  return (
    <div>
      <div
        className={`flex items-center gap-1 px-2 py-1.5 text-xs cursor-pointer group
          ${isSelected ? 'bg-aries-900/40 text-aries-300' : 'text-gray-300 hover:bg-gray-800/50 hover:text-white'}`}
      >
        <button onClick={onToggle} className="p-0.5 text-gray-500 hover:text-white">
          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </button>
        <span onClick={onSelect} className="flex items-center gap-1.5 flex-1 min-w-0">
          {isExpanded ? <FolderOpen className="w-3.5 h-3.5 text-yellow-500 shrink-0" /> : <Folder className="w-3.5 h-3.5 text-yellow-500 shrink-0" />}
          <span className="truncate">{project.project_name}</span>
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          className="hidden group-hover:block text-gray-500 hover:text-red-400 p-0.5"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>

      {isExpanded && (
        <div className="pl-6">
          {scenarios?.map((scen) => (
            <div
              key={scen.id}
              onClick={() => onSelectScenario(scen.id)}
              className={`flex items-center gap-1.5 px-2 py-1 text-xs cursor-pointer rounded
                ${selectedScenarioId === scen.id ? 'text-aries-300 bg-aries-900/30' : 'text-gray-400 hover:text-white hover:bg-gray-800/40'}`}
            >
              <div className="w-2 h-2 rounded-full bg-aries-600 shrink-0" />
              <span className="truncate">{scen.scenario_name}</span>
              {scen.is_base_case && <span className="ml-auto badge-blue text-[10px]">Base</span>}
            </div>
          ))}
          <AddScenarioButton projectId={project.id} />
        </div>
      )}
    </div>
  )
}

function AddScenarioButton({ projectId }: { projectId: number }) {
  const [adding, setAdding] = useState(false)
  const [name, setName] = useState('')
  const queryClient = useQueryClient()

  const create = useMutation({
    mutationFn: (scenName: string) => scenariosApi.create(projectId, {
      scenario_name: scenName,
      oil_price: 70,
      gas_price: 3.0,
      discount_rate: 10.0,
      tax_rate: 0.05,
      project_id: projectId,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios', projectId] })
      setName('')
      setAdding(false)
    },
  })

  if (!adding) {
    return (
      <button
        onClick={() => setAdding(true)}
        className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-300 px-2 py-1"
      >
        <Plus className="w-3 h-3" />
        Add Scenario
      </button>
    )
  }

  return (
    <div className="px-2 py-1">
      <input
        type="text"
        placeholder="Scenario name..."
        value={name}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && name.trim()) create.mutate(name.trim())
          if (e.key === 'Escape') setAdding(false)
        }}
        className="input-field text-xs"
        autoFocus
      />
    </div>
  )
}
