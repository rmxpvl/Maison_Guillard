import { createContext } from 'react'

// Shared by PanierProvider (writes it) and usePanier (reads it). Kept in its own file so
// PanierContext.jsx exports only a component, which Vite's hot reload needs.
export const PanierContexte = createContext(null)
