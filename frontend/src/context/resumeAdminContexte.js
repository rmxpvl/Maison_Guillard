import { createContext } from 'react'

// The list of requests, loaded once by RouteAdmin and shared by the menu (counters), the
// « Aujourd'hui » page and the Demandes tab, so they always agree.
export const ResumeAdminContexte = createContext(null)
