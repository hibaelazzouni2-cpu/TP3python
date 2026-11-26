"""TP3 : jeu de dames international simplifié, en programmation objet."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from exceptions import CoupInvalideError

COLONNES = "abcdefghij"
DIAGONALES = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def adversaire(couleur):
    return "noir" if couleur == "blanc" else "blanc"


@dataclass(frozen=True)
class Case:
    colonne: str
    ligne: int

    def __post_init__(self):
        if not isinstance(self.colonne, str) or len(self.colonne) != 1 or self.colonne not in COLONNES:
            raise ValueError(f"colonne invalide : {self.colonne!r}")
        if not isinstance(self.ligne, int) or not 1 <= self.ligne <= 10:
            raise ValueError(f"ligne invalide : {self.ligne!r}")

    @classmethod
    def depuis_nom(cls, nom):
        try:
            return cls(nom[0], int(nom[1:]))
        except (ValueError, IndexError, TypeError):
            raise ValueError(f"nom de case invalide : {nom!r}") from None

    @property
    def est_noire(self):
        return (COLONNES.index(self.colonne) + self.ligne) % 2 == 1

    def decaler(self, dc, dl):
        col = COLONNES.index(self.colonne) + dc
        lig = self.ligne + dl
        if 0 <= col < 10 and 1 <= lig <= 10:
            return Case(COLONNES[col], lig)
        return None

    def __str__(self):
        return f"{self.colonne}{self.ligne}"


def en_case(case):
    return case if isinstance(case, Case) else Case.depuis_nom(case)


def ordre(case):
    case = en_case(case)
    return (case.ligne, COLONNES.index(case.colonne))


class Piece(ABC):
    COULEURS = ("blanc", "noir")
    LETTRE = "?"
    NOM = "pièce"
    FEMININ = False

    def __init__(self, couleur):
        if couleur not in self.COULEURS:
            raise ValueError(f"couleur invalide : {couleur!r}")
        self._couleur = couleur

    @property
    def couleur(self):
        return self._couleur

    @property
    def sens(self):
        return 1 if self.couleur == "blanc" else -1

    @property
    def symbole(self):
        return self.LETTRE.upper() if self.couleur == "blanc" else self.LETTRE.lower()

    def est_adverse(self, autre):
        return isinstance(autre, Piece) and autre.couleur != self.couleur

    def promouvoir(self, case):
        return self

    @abstractmethod
    def deplacements(self, case, plateau):
        pass

    @abstractmethod
    def prises(self, case, plateau):
        pass

    def __repr__(self):
        return f"{type(self).__name__}({self.couleur!r})"

    def __str__(self):
        couleur = ("blanche" if self.couleur == "blanc" else "noire") if self.FEMININ else self.couleur
        return f"{self.NOM} {couleur}"


class Pion(Piece):
    LETTRE = "P"
    NOM = "pion"

    def deplacements(self, case, plateau):
        case = en_case(case)
        resultats = set()
        for dc in (-1, 1):
            cible = case.decaler(dc, self.sens)
            if cible is not None and plateau[cible] is None:
                resultats.add(cible)
        return resultats

    def prises(self, case, plateau):
        case = en_case(case)
        resultats = {}
        for dc, dl in DIAGONALES:
            milieu = case.decaler(dc, dl)
            arrivee = case.decaler(2 * dc, 2 * dl)
            if (milieu is not None and arrivee is not None
                    and self.est_adverse(plateau[milieu])
                    and plateau[arrivee] is None):
                resultats[arrivee] = milieu
        return resultats

    def promouvoir(self, case):
        case = en_case(case)
        if case.ligne == (10 if self.couleur == "blanc" else 1):
            return Dame(self.couleur)
        return self


class Dame(Piece):
    LETTRE = "D"
    NOM = "dame"
    FEMININ = True

    def deplacements(self, case, plateau):
        case = en_case(case)
        resultats = set()
        for dc, dl in DIAGONALES:
            suivante = case.decaler(dc, dl)
            while suivante is not None and plateau[suivante] is None:
                resultats.add(suivante)
                suivante = suivante.decaler(dc, dl)
        return resultats

    def prises(self, case, plateau):
        case = en_case(case)
        resultats = {}
        for dc, dl in DIAGONALES:
            suivante = case.decaler(dc, dl)
            while suivante is not None and plateau[suivante] is None:
                suivante = suivante.decaler(dc, dl)
            if suivante is None or not self.est_adverse(plateau[suivante]):
                continue
            milieu = suivante
            suivante = suivante.decaler(dc, dl)
            while suivante is not None and plateau[suivante] is None:
                resultats[suivante] = milieu
                suivante = suivante.decaler(dc, dl)
        return resultats


class Plateau:
    def __init__(self):
        self._pieces = {}

    def placer(self, case, piece):
        case = en_case(case)
        if not case.est_noire:
            raise ValueError(f"{case} est une case blanche")
        if case in self._pieces:
            raise ValueError(f"{case} est déjà occupée")
        self._pieces[case] = piece

    def __getitem__(self, case):
        return self._pieces.get(en_case(case))

    def __contains__(self, case):
        return en_case(case) in self._pieces

    def __len__(self):
        return len(self._pieces)

    def __iter__(self):
        return iter(sorted(self._pieces, key=ordre))

    def compter(self, couleur):
        return sum(self[c].couleur == couleur for c in self)

    def __repr__(self):
        return f"<Plateau : {self.compter('blanc')} blancs, {self.compter('noir')} noirs>"

    def __str__(self):
        lignes = []
        for ligne in range(10, 0, -1):
            symboles = []
            for colonne in COLONNES:
                case = Case(colonne, ligne)
                if case.est_noire:
                    piece = self[case]
                    symboles.append(piece.symbole if piece is not None else ".")
                else:
                    symboles.append(" ")
            lignes.append(f"{ligne:>2}  " + " ".join(symboles))
        lignes.append("    " + " ".join(COLONNES))
        return "\n".join(lignes)

    @classmethod
    def depuis_dict(cls, donnees):
        plateau = cls()
        symboles = {"P": (Pion, "blanc"), "p": (Pion, "noir"),
                    "D": (Dame, "blanc"), "d": (Dame, "noir")}
        for nom, symbole in donnees.items():
            classe, couleur = symboles[symbole]
            plateau.placer(nom, classe(couleur))
        return plateau

    @classmethod
    def position_initiale(cls):
        plateau = cls()
        for ligne in range(1, 11):
            if ligne not in (1, 2, 3, 4, 7, 8, 9, 10):
                continue
            couleur = "blanc" if ligne <= 4 else "noir"
            for colonne in COLONNES:
                case = Case(colonne, ligne)
                if case.est_noire:
                    plateau.placer(case, Pion(couleur))
        return plateau

    def prises_possibles(self, couleur):
        resultats = {}
        for case in self:
            piece = self[case]
            if piece.couleur == couleur:
                prises = piece.prises(case, self)
                if prises:
                    resultats[case] = prises
        return resultats

    def coups_possibles(self, couleur):
        prises = self.prises_possibles(couleur)
        if prises:
            coups = [(depart, arrivee) for depart, d in prises.items() for arrivee in d]
        else:
            coups = [(depart, arrivee) for depart in self
                     if self[depart].couleur == couleur
                     for arrivee in self[depart].deplacements(depart, self)]
        return sorted(coups, key=lambda coup: (ordre(coup[0]), ordre(coup[1])))

    def deplacer(self, depart, arrivee):
        depart, arrivee = en_case(depart), en_case(arrivee)
        piece = self[depart]
        if piece is None:
            raise CoupInvalideError(depart, arrivee, "aucune pièce sur la case de départ")
        prises = self.prises_possibles(piece.couleur)
        milieu = None
        if prises:
            if arrivee not in prises.get(depart, {}):
                raise CoupInvalideError(depart, arrivee, "la prise est obligatoire")
            milieu = prises[depart][arrivee]
        elif arrivee not in piece.deplacements(depart, self):
            raise CoupInvalideError(depart, arrivee, "déplacement interdit")
        prise = self[milieu] if milieu is not None else None
        del self._pieces[depart]
        if milieu is not None:
            del self._pieces[milieu]
        self._pieces[arrivee] = piece.promouvoir(arrivee)
        return prise

    def vers_dict(self):
        return {str(case): self[case].symbole for case in self}


@dataclass(frozen=True)
class Coup:
    numero: int
    couleur: str
    depart: str
    arrivee: str
    prise: bool = False

    def __str__(self):
        return f"{self.numero}. {self.depart}{'x' if self.prise else '-'}{self.arrivee}"


class Partie:
    def __init__(self, plateau=None):
        self.plateau = plateau if plateau is not None else Plateau.position_initiale()
        self.trait = "blanc"
        self.historique = []

    def jouer(self, depart, arrivee):
        piece = self.plateau[depart]
        if piece is not None and piece.couleur != self.trait:
            nom = "blancs" if self.trait == "blanc" else "noirs"
            raise CoupInvalideError(depart, arrivee, f"c'est aux {nom} de jouer")
        prise = self.plateau.deplacer(depart, arrivee)
        coup = Coup(len(self.historique) + 1, self.trait,
                    str(en_case(depart)), str(en_case(arrivee)), prise is not None)
        self.historique.append(coup)
        self.trait = adversaire(self.trait)
        return coup

    @property
    def gagnant(self):
        return None if self.plateau.coups_possibles(self.trait) else adversaire(self.trait)

    def sauvegarder(self, chemin):
        with open(chemin, "w", encoding="utf-8") as fichier:
            json.dump({"trait": self.trait, "pieces": self.plateau.vers_dict()},
                      fichier, ensure_ascii=False, indent=2)

    @classmethod
    def charger(cls, chemin):
        with open(chemin, "r", encoding="utf-8") as fichier:
            donnees = json.load(fichier)
        partie = cls(Plateau.depuis_dict(donnees["pieces"]))
        partie.trait = donnees["trait"]
        return partie
