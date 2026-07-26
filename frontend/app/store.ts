import { create } from 'zustand';

interface WorkspaceState {
  clientId: string;
  jwtToken: string | null;
  userRole: string;
  setClientId: (clientId: string) => void;
  setJwtToken: (token: string | null) => void;
  setUserRole: (userRole: string) => void;
  clearSession: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  clientId: 'client_abc',
  jwtToken: null,
  userRole: typeof window !== 'undefined' ? localStorage.getItem('user_role') || 'Admin' : 'Admin',
  setClientId: (clientId) => set({ clientId }),
  setJwtToken: (jwtToken) => set({ jwtToken }),
  setUserRole: (userRole) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_role', userRole);
    }
    set({ userRole });
  },
  clearSession: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user_role');
    }
    set({ clientId: 'client_abc', jwtToken: null, userRole: 'Admin' });
  }
}));
