# Error responses shown in Swagger. Shared so each route lists them in one line.
STOCKAGE_INDISPONIBLE = "L'image n'a pas pu être enregistrée pour le moment : réessayez dans un instant"
NON_AUTORISE = {401: {"description": "Jeton absent, invalide ou expiré"}}
CATEGORIE_INTROUVABLE = {404: {"description": "Catégorie introuvable"}}
PRODUIT_INTROUVABLE = {404: {"description": "Produit introuvable"}}
TEINTE_INTROUVABLE = {404: {"description": "Teinte introuvable"}}
PHOTO_INTROUVABLE = {404: {"description": "Photo introuvable"}}
