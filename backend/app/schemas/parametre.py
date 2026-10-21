from pydantic import BaseModel, ConfigDict


class ParametreIn(BaseModel):
    email_commande_actif: bool


class ParametreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_commande_actif: bool
