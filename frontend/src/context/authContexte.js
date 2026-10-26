import { createContext } from 'react'

// Shared by AuthProvider (writes it) and useAuth (reads it).
export const AuthContexte = createContext(null)
