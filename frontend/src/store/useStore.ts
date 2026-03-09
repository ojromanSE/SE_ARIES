import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  // Auth
  token: string | null
  user: { username: string; role: string; full_name?: string } | null
  setToken: (token: string | null) => void
  setUser: (user: AppState['user']) => void
  logout: () => void

  // Active selection (ARIES-style: selected property/project/scenario)
  selectedPropnum: string | null
  selectedProjectId: number | null
  selectedScenarioId: number | null
  setSelectedPropnum: (propnum: string | null) => void
  setSelectedProjectId: (id: number | null) => void
  setSelectedScenarioId: (id: number | null) => void

  // UI state
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  activeModule: string
  setActiveModule: (module: string) => void
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Auth
      token: null,
      user: null,
      setToken: (token) => {
        set({ token })
        if (token) localStorage.setItem('aries_token', token)
        else localStorage.removeItem('aries_token')
      },
      setUser: (user) => set({ user }),
      logout: () => {
        set({ token: null, user: null })
        localStorage.removeItem('aries_token')
      },

      // Selections
      selectedPropnum: null,
      selectedProjectId: null,
      selectedScenarioId: null,
      setSelectedPropnum: (propnum) => set({ selectedPropnum: propnum }),
      setSelectedProjectId: (id) => set({ selectedProjectId: id }),
      setSelectedScenarioId: (id) => set({ selectedScenarioId: id }),

      // UI
      sidebarOpen: true,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      activeModule: 'project-manager',
      setActiveModule: (module) => set({ activeModule: module }),
    }),
    {
      name: 'se-aries-store',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        sidebarOpen: state.sidebarOpen,
        activeModule: state.activeModule,
      }),
    }
  )
)
