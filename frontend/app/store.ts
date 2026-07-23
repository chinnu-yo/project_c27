import { create } from 'zustand';

interface WorkspaceState {
  clientId: string;
  jwtToken: string | null;
  setClientId: (clientId: string) => void;
  setJwtToken: (token: string | null) => void;
  clearSession: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  clientId: 'client_abc', // Default client tracking reference
  jwtToken: null,
  setClientId: (clientId) => set({ clientId }),
  setJwtToken: (jwtToken) => set({ jwtToken }),
  clearSession: () => set({ clientId: 'client_abc', jwtToken: null })
}));
