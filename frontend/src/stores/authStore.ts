import { create } from 'zustand';

interface AuthState {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;

  setAuth: (token: string, username: string) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  username: null,
  isAuthenticated: false,

  setAuth: (token, username) => {
    sessionStorage.setItem('token', token);
    sessionStorage.setItem('username', username);
    set({ token, username, isAuthenticated: true });
  },

  logout: () => {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('username');
    set({ token: null, username: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const token = sessionStorage.getItem('token');
    const username = sessionStorage.getItem('username');
    if (token && username) {
      set({ token, username, isAuthenticated: true });
    }
  },
}));
