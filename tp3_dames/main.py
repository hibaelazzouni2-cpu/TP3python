from dames import Partie
from exceptions import ErreurDames


def lire_coup(texte):
    morceaux = texte.replace("-", " ").replace("x", " ").split()
    if len(morceaux) != 2:
        raise ValueError("tapez deux cases, par exemple c3 d4")
    return tuple(morceaux)


def main():
    partie = Partie()
    print(partie.plateau)
    while partie.gagnant is None:
        texte = input(f"{partie.trait} > ").strip()
        if texte == "quitter":
            print("Partie abandonnée.")
            return 0
        if texte == "sauver":
            partie.sauvegarder("partie.json")
            print("Partie sauvegardée.")
            continue
        if texte == "reprendre":
            try:
                partie = Partie.charger("partie.json")
                print(partie.plateau)
            except (OSError, ValueError, KeyError) as erreur:
                print(f"Refusé : {erreur}")
            continue
        try:
            depart, arrivee = lire_coup(texte)
            coup = partie.jouer(depart, arrivee)
        except (ErreurDames, ValueError) as erreur:
            print(f"Refusé : {erreur}")
            continue
        print(coup)
        print(partie.plateau)
    print(f"Les {'blancs' if partie.gagnant == 'blanc' else 'noirs'} gagnent !")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
