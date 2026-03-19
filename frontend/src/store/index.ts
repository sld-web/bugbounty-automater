import { create } from 'zustand'

interface AppState {
  programs: any[]
  targets: any[]
  pendingApprovals: number
  setPrograms: (programs: any[]) => void
  setTargets: (targets: any[]) => void
  setPendingApprovals: (count: number) => void
}

export const useAppStore = create<AppState>((set) => ({
  programs: [],
  targets: [],
  pendingApprovals: 0,
  setPrograms: (programs) => set({ programs }),
  setTargets: (targets) => set({ targets }),
  setPendingApprovals: (count) => set({ pendingApprovals: count }),
}))
