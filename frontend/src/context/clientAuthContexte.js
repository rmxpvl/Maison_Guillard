import { createContext } from 'react'

// Shared by ClientAuthProvider (writes it) and useClientAuth (reads it).
export const ClientAuthContexte = createContext(null)
