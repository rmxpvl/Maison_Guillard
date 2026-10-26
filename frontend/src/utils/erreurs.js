import { ApiError } from '../api/client.js'

// French message for a failed form submission (order or quote).
export function messageErreurApi(erreur) {
  if (!(erreur instanceof ApiError)) return 'Connexion impossible. Vérifiez votre connexion et réessayez.'
  if (erreur.detail) return erreur.detail
  if (erreur.status === 422) return 'Vérifiez les informations saisies.'
  return "L'envoi n'a pas abouti. Réessayez dans un instant."
}
