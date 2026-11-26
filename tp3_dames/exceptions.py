class ErreurDames(Exception):
    """Erreur liée aux règles du jeu de dames."""


class CoupInvalideError(ErreurDames):
    def __init__(self, depart, arrivee, raison):
        self.depart = depart
        self.arrivee = arrivee
        self.raison = raison
        super().__init__(f"coup {depart}-{arrivee} refusé : {raison}")
