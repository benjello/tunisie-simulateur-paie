# Registre des désaccords et décisions

Chaque ligne du bulletin de paie peut être calculée différemment selon les
simulateurs en ligne. On recense ici les divergences constatées, la position
de chaque approche, et la **décision tranchée par le droit**.

Les simulateurs ne sont pas nommés publiquement (voir `sources_locales/`).

---

## D1 — Taux de cotisation CNSS salariale à partir de 2025 : 9,18 % ou 9,68 % ?

**Constat.** Certains simulateurs retiennent 9,18 % comme taux salarial CNSS
(régime non agricole), d'autres 9,68 %.

**Droit.** La loi de finances 2025 (loi n° 2024-48 du 9 décembre 2024, art. 17)
crée le « Fonds d'assurance contre la perte d'emploi pour des motifs
économiques », financé notamment par « des frais d'adhésion au taux de 0,5 %
supportés par chacun de l'employeur et l'employé et dus sur la masse salariale
déclarée auprès de la CNSS ». Ces 0,5 % s'ajoutent, à compter du 1ᵉʳ janvier
2025, au taux salarial historique de 9,18 %.

**Décision.**
- Revenus ≤ 2024 : taux salarial **9,18 %**.
- Revenus ≥ 2025 : taux salarial **9,68 %** (9,18 % + 0,5 % perte d'emploi).
- Côté patronal, symétriquement : 16,57 % jusqu'en 2024, **17,07 %** à partir
  de 2025.

Un simulateur resté à 9,18 % pour 2025 n'est pas « faux » dans l'absolu : son
résultat correspond aux **revenus ≤ 2024**. Le cas de test est alors calé sur
une année où sa règle est valide.

**Vérifié dans OpenFisca-Tunisia.** La cotisation `perte_d_emploi_salarie`
(0,5 %, datée 2025-01-01, sourcée LF2025 art. 17) est bien intégrée à
`cotisations_salarie` ; la somme des branches RSNA donne 9,18 % jusqu'en 2024
et 9,68 % à partir de 2025.

---

## D2 — La cotisation « perte d'emploi » (0,5 %) est-elle déductible du revenu imposable ?

**Constat.** Question directement liée à D1 : faut-il calculer la base
imposable IRPP sur « brut − 9,18 % » ou « brut − 9,68 % » en 2025 ? Les
simulateurs restés à 9,18 % déduisent de fait 9,18 % ; déduire 9,68 % change
légèrement l'IRPP et le net.

**Droit.** L'art. 17 LF2025 qualifie ces 0,5 % de cotisation obligatoire
« due sur la masse salariale déclarée auprès de la CNSS ». À ce titre, elle
relève des cotisations sociales obligatoires déductibles du revenu imposable
(art. 26 du Code de l'IRPP et de l'IS). Plusieurs cabinets comptables
confirment que la CNSS salariale 2025 déductible est bien de 9,68 %.

**Décision.** La cotisation perte d'emploi est **déductible**. Base imposable
2025 = brut − 9,68 %. OpenFisca-Tunisia applique cette règle
(`salaire_imposable = assiette − cotisations_salarie`, perte d'emploi
comprise).

**Conséquence sur la validation.** Un simulateur « 2025 » qui déduit 9,18 %
reproduit en réalité un bulletin **revenus ≤ 2024** côté assiette, et ne peut
servir de référence 2025 que s'il a aussi mis à jour le barème. Voir D3.

---

## D3 — Millésime du barème IRPP appliqué à la retenue à la source

**Constat.** La retenue mensuelle d'IRPP de l'année N est un acompte sur
l'impôt des revenus N. Le barème à appliquer est celui des **revenus N**, fixé
par la loi de finances correspondante. Un simulateur peut, en transition,
combiner une règle CNSS d'une année et un barème d'une autre.

**Droit.** Le barème LF2025 (8 tranches : 0 % / 15 % / 25 % / 30 % / 33 % /
36 % / 38 % / 40 %) s'applique « aux revenus réalisés à partir du 1ᵉʳ janvier
2025 ». Il est donc le barème de la retenue à la source des paies 2025.

**Décision.** Convention de test : paie année N → **cotisations au taux du mois
N** + **barème IRPP des revenus N**. OpenFisca applique ces deux règles au
même millésime (`parameters(period.start)` sur le mois de paie).

**Observation de validation.** Avec le barème des revenus 2025 et une assiette
sur 9,18 %, OpenFisca reproduit **au millième** l'IRPP d'un simulateur de
référence (cas R-série, célibataire) — ce qui isole D2 comme seul écart
résiduel : l'assiette (9,18 % vs 9,68 %), pas le barème ni l'abattement.

---

## Abattement et déductions (conformes, pas de désaccord)

- **Abattement frais professionnels** : 10 % de l'imposable, plafonné à
  2 000 DT/an depuis les revenus 2017 (art. 26 § I CGI, LF2017 art. 14 § 2).
- **Déductions familiales** (annuelles) : chef de famille 300 DT ; enfants à
  charge par rang ; étudiant sans bourse et enfant infirme majorés. Modélisées
  dans OpenFisca (`deduction_famille`).
- **CSS** : 0,5 % (2023-2025) de la base au-delà du seuil de première tranche
  imposée. **Prolongée à 0,5 % en 2026** (art. 87 LF2026, loi n° 2025-17 du
  12 déc. 2025) — la suppression annoncée a été écartée en commission des
  finances. OpenFisca reconduit le droit 2025 en 2026 (barème IRPP, CNSS 9,68 %,
  CSS 0,5 %), résultats conformes. Point de vigilance : ajouter dans OpenFisca
  une référence datée 2026-01-01 (même taux 0,5 %, réf. art. 87 LF2026) pour
  tracer explicitement la prolongation, même si le chiffre ne change pas.

Ces éléments sont cohérents entre les simulateurs et la loi : pas de décision
à trancher, seulement à tester.
