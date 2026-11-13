"""Traductions français / arabe pour l'app de paie.

Un dictionnaire plat clé -> {"fr": ..., "ar": ...}. La fonction `t(cle, lang)`
renvoie la chaîne traduite. Les nombres (montants) ne sont pas traduits.
"""

from __future__ import annotations

LANGUES = {"fr": "Français", "ar": "العربية"}

TRADUCTIONS: dict[str, dict[str, str]] = {
    # Titre et navigation
    "titre": {"fr": "Simulateur de paie Tunisie", "ar": "محاكي الأجور تونس"},
    "onglet_bulletin": {"fr": "Bulletin mensuel", "ar": "كشف شهري"},
    "onglet_comparateur": {"fr": "Comparateur", "ar": "مقارنة"},
    "onglet_annuel": {"fr": "Simulation annuelle (IRPP)", "ar": "محاكاة سنوية (الضريبة)"},
    "onglet_bareme": {"fr": "Barème", "ar": "الجدول"},
    "titre_bareme": {"fr": "Barème et paramètres de l'année", "ar": "جدول ومعايير السنة"},
    "bareme_irpp": {"fr": "Barème IRPP (annuel)", "ar": "جدول الضريبة على الدخل (سنوي)"},
    "col_tranche": {"fr": "À partir de (DT/an)", "ar": "ابتداء من (د.ت/سنة)"},
    "col_taux": {"fr": "Taux", "ar": "النسبة"},
    "smig_mensuel": {"fr": "SMIG mensuel (48h)", "ar": "الأجر الأدنى الشهري (48س)"},
    "plafond_abattement": {"fr": "Plafond abattement frais pro. (DT/an)", "ar": "سقف الطرح المهني (د.ت/سنة)"},
    "source_params": {"fr": "Paramètres issus d'OpenFisca-Tunisia, sourcés sur le JORT (parameters.tn.tax-benefit.org).", "ar": "المعايير من OpenFisca-Tunisia، موثقة من الرائد الرسمي."},
    # Panneau latéral — entrées
    "annee": {"fr": "Année de paie", "ar": "سنة الأجر"},
    "regime": {"fr": "Régime de sécurité sociale", "ar": "نظام الضمان الاجتماعي"},
    "sens": {"fr": "Sens du calcul", "ar": "اتجاه الحساب"},
    "brut_net": {"fr": "Brut → Net", "ar": "إجمالي ← صافي"},
    "net_brut": {"fr": "Net → Brut", "ar": "صافي ← إجمالي"},
    "salaire_base": {"fr": "Salaire de base (DT/mois)", "ar": "الأجر الأساسي (د.ت/شهر)"},
    "primes": {"fr": "Primes et indemnités (DT/mois)", "ar": "المنح والتعويضات (د.ت/شهر)"},
    "heures_sup": {"fr": "Heures supplémentaires (nb/mois)", "ar": "الساعات الإضافية (عدد/شهر)"},
    "regime_horaire": {"fr": "Régime hebdomadaire", "ar": "النظام الأسبوعي"},
    "reg_48h": {"fr": "48 h/semaine (+75 %)", "ar": "48 ساعة/أسبوع (+75٪)"},
    "reg_40h": {"fr": "40 h/semaine (+25/50 %)", "ar": "40 ساعة/أسبوع (+25/50٪)"},
    "net_cible": {"fr": "Net à payer souhaité (DT/mois)", "ar": "الصافي المطلوب (د.ت/شهر)"},
    "primes_net": {"fr": "Primes connues (DT/mois)", "ar": "المنح المعروفة (د.ت/شهر)"},
    "situation_familiale": {"fr": "Situation familiale (IRPP)", "ar": "الحالة العائلية (الضريبة)"},
    "chef_famille": {"fr": "Chef de famille", "ar": "رب الأسرة"},
    "nb_enf": {"fr": "Enfants à charge (≤ 4)", "ar": "الأطفال المكفولون (≤ 4)"},
    "nb_enf_sup": {"fr": "Étudiants sans bourse", "ar": "طلبة بدون منحة"},
    "nb_infirme": {"fr": "Enfants handicapés", "ar": "أطفال ذوو إعاقة"},
    "adhesion_compl": {
        "fr": "Retraite complémentaire CNSS (RSNA, > 6×SMIG)",
        "ar": "تقاعد تكميلي (CNSS، > 6×الأجر الأدنى)",
    },
    "calculer": {"fr": "Calculer le bulletin", "ar": "احسب الكشف"},
    "langue": {"fr": "Langue", "ar": "اللغة"},
    # Régimes
    "reg_rsna": {"fr": "Privé non agricole (RSNA)", "ar": "القطاع الخاص غير الفلاحي (RSNA)"},
    "reg_rsa": {"fr": "Salarié agricole (RSA)", "ar": "أجير فلاحي (RSA)"},
    "reg_rsaa": {"fr": "Agricole amélioré (RSAA)", "ar": "فلاحي محسّن (RSAA)"},
    "reg_cnrps": {"fr": "Secteur public (CNRPS)", "ar": "القطاع العام (CNRPS)"},
    "reg_neant": {"fr": "Exonéré / CIVP / export (0 cotisation)", "ar": "معفى / CIVP / تصدير (بدون مساهمة)"},
    # Bulletin
    "titre_bulletin": {"fr": "Fiche de paie — salarié (Tunisie)", "ar": "بطاقة الأجر — أجير (تونس)"},
    "cote_salarie": {"fr": "Côté salarié", "ar": "جهة الأجير"},
    "cote_employeur": {"fr": "Côté employeur", "ar": "جهة المشغّل"},
    "salaire_brut": {"fr": "Salaire brut", "ar": "الأجر الإجمالي"},
    "cnss_salariale": {"fr": "CNSS salariale", "ar": "مساهمة الأجير (CNSS)"},
    "salaire_imposable": {"fr": "Salaire imposable", "ar": "الأجر الخاضع للضريبة"},
    "irpp_ras": {"fr": "IRPP (retenue à la source)", "ar": "الضريبة على الدخل (خصم من المصدر)"},
    "css": {"fr": "CSS (contribution solidarité)", "ar": "المساهمة الاجتماعية التضامنية"},
    "net_a_payer": {"fr": "Net à payer", "ar": "الصافي المستحق"},
    "cnss_patronale": {"fr": "CNSS patronale", "ar": "مساهمة المشغّل (CNSS)"},
    "cout_employeur": {"fr": "Coût total employeur (super-brut)", "ar": "الكلفة الجملية للمشغّل"},
    "detail_cnss": {"fr": "Détail des branches CNSS", "ar": "تفصيل فروع CNSS"},
    "taux_preleve": {"fr": "Taux de prélèvement global", "ar": "نسبة الاقتطاع الجملية"},
    "export_pdf": {"fr": "Télécharger le bulletin (PDF)", "ar": "تحميل الكشف (PDF)"},
    "partager": {"fr": "🔗 Copier le lien de ce scénario", "ar": "🔗 نسخ رابط هذا السيناريو"},
    "lien_copie": {"fr": "Lien copié ✓", "ar": "تم نسخ الرابط ✓"},
    # Branches CNSS
    "br_retraite": {"fr": "Retraite", "ar": "التقاعد"},
    "br_retraite_compl": {"fr": "Retraite complémentaire", "ar": "تقاعد تكميلي"},
    "br_maladie": {"fr": "Assurance maladie", "ar": "التأمين على المرض"},
    "br_maternite": {"fr": "Maternité", "ar": "الأمومة"},
    "br_deces": {"fr": "Décès", "ar": "الوفاة"},
    "br_famille": {"fr": "Prestations familiales", "ar": "المنح العائلية"},
    "br_accident": {"fr": "Accident du travail", "ar": "حوادث الشغل"},
    "br_perte_emploi": {"fr": "Perte d'emploi", "ar": "فقدان الشغل"},
    "br_protection": {"fr": "Protection sociale", "ar": "الحماية الاجتماعية"},
    "br_soins": {"fr": "Soins", "ar": "العلاج"},
    # Comparateur
    "titre_comparateur": {"fr": "Comparer un même salaire de base", "ar": "مقارنة نفس الأجر الأساسي"},
    "par_annee": {"fr": "Par année", "ar": "حسب السنة"},
    "par_regime": {"fr": "Par régime", "ar": "حسب النظام"},
    "col_net": {"fr": "Net", "ar": "صافي"},
    "col_cnss": {"fr": "CNSS", "ar": "CNSS"},
    # Annuel
    "titre_annuel": {"fr": "IRPP annuel et déductions", "ar": "الضريبة السنوية والطرحات"},
    "deductions_annuelles": {"fr": "Déductions annuelles (DT/an)", "ar": "الطرحات السنوية (د.ت/سنة)"},
    "salaire_annuel": {"fr": "Salaire annuel (12 mois)", "ar": "الأجر السنوي (12 شهرا)"},
    "irpp_annuel_du": {"fr": "IRPP annuel dû", "ar": "الضريبة السنوية المستحقة"},
    "ras_prelevee": {"fr": "Retenue à la source déjà prélevée", "ar": "الخصم من المصدر المقتطع"},
    "solde_payer": {"fr": "Solde à payer (régularisation)", "ar": "الرصيد المستحق (تسوية)"},
    "trop_percu": {"fr": "Trop-perçu (restitution)", "ar": "فائض (استرجاع)"},
    "effet_deductions": {"fr": "Effet des déductions", "ar": "أثر الطرحات"},
    "irpp_sans": {"fr": "IRPP sans déduction", "ar": "الضريبة بدون طرح"},
    "irpp_avec": {"fr": "IRPP avec déductions", "ar": "الضريبة مع الطرحات"},
    "economie": {"fr": "Économie d'impôt", "ar": "الاقتصاد الضريبي"},
    # Déductions
    "ded_assurance_vie": {"fr": "Primes d'assurance-vie", "ar": "أقساط التأمين على الحياة"},
    "ded_logement": {"fr": "Intérêts crédit logement", "ar": "فوائد قرض السكن"},
    "ded_cea": {"fr": "Compte épargne en actions (CEA)", "ar": "حساب الادخار في الأسهم"},
    "ded_cei": {"fr": "Compte épargne investissement (CEI)", "ar": "حساب الادخار للاستثمار"},
    "ded_pret_univ": {"fr": "Remboursement prêts universitaires", "ar": "تسديد القروض الجامعية"},
    "ded_dons": {"fr": "Dons", "ar": "الهبات"},
    # Messages
    "note_moteur": {
        "fr": "Calculé par le moteur OpenFisca-Tunisia. Convention : cotisations au taux du mois de paie, barème IRPP des revenus de l'année de paie (retenue à la source).",
        "ar": "محسوب بمحرك OpenFisca-Tunisia. المساهمات حسب نسبة شهر الأجر، وجدول الضريبة حسب سنة الأجر (خصم من المصدر).",
    },
    "note_annuel": {
        "fr": "Les déductions ci-dessous ne réduisent pas la retenue à la source mensuelle : elles jouent au niveau de l'IRPP annuel, en régularisation. Salaire annuel = 12 × salaire de base.",
        "ar": "الطرحات أدناه لا تخفّض الخصم الشهري من المصدر: بل تُحتسب على مستوى الضريبة السنوية عند التسوية. الأجر السنوي = 12 × الأجر الأساسي.",
    },
    "note_comparateur": {
        "fr": "Pour le salaire de base et la situation familiale saisis : net selon l'année (régime courant) et selon le régime (année courante).",
        "ar": "حسب الأجر الأساسي والحالة العائلية المُدخلة: الصافي حسب السنة (النظام الحالي) وحسب النظام (السنة الحالية).",
    },
    "avert_exonere": {
        "fr": "Régime exonéré sélectionné : aucune cotisation sociale. CIVP/stage et entreprise totalement exportatrice ne sont pas paramétrés finement dans le modèle ; le résultat suppose une exonération totale.",
        "ar": "تم اختيار نظام معفى: بدون مساهمات اجتماعية. CIVP/التربص والمؤسسة المصدّرة كليا غير مُعدّة بدقّة في النموذج؛ النتيجة تفترض إعفاء كاملا.",
    },
    "err_net_positif": {"fr": "Saisissez un net à payer strictement positif.", "ar": "أدخل صافيا موجبا تماما."},
    "err_primes_neg": {"fr": "Les primes ne peuvent pas être négatives.", "ar": "لا يمكن أن تكون المنح سالبة."},
    "err_salaire_neg": {"fr": "Le salaire et les primes ne peuvent pas être négatifs.", "ar": "لا يمكن أن يكون الأجر والمنح سالبة."},
    "err_heures_neg": {"fr": "Le nombre d'heures supplémentaires ne peut pas être négatif.", "ar": "لا يمكن أن يكون عدد الساعات الإضافية سالبا."},
    "err_timeout": {
        "fr": "Le calcul a expiré (API trop lente ou injoignable). Réessayez.",
        "ar": "انتهت مهلة الحساب (الواجهة بطيئة أو غير متاحة). أعد المحاولة.",
    },
    "err_connexion": {
        "fr": "Impossible de joindre le moteur de calcul (API injoignable).",
        "ar": "تعذّر الاتصال بمحرك الحساب (الواجهة غير متاحة).",
    },
    "tracabilite": {
        "fr": "Calculé avec OpenFisca-Tunisia v{tn} (moteur v{core}). Barèmes de l'année sélectionnée. Estimation indicative.",
        "ar": "محسوب بـ OpenFisca-Tunisia v{tn} (محرك v{core}). جداول السنة المختارة. تقدير إرشادي.",
    },
}


def t(cle: str, lang: str = "fr") -> str:
    """Renvoie la traduction de `cle` pour `lang` (repli sur fr, puis la clé)."""
    entree = TRADUCTIONS.get(cle)
    if entree is None:
        return cle
    return entree.get(lang) or entree.get("fr") or cle
