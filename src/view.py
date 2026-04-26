# src/view.py
import logging

import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from constants import LOGGER_NAME
from src.helpers.helpers_portfolio import price_scaling

logger = logging.getLogger(LOGGER_NAME)


class View:
    """Responsabilité unique : génération des sorties visuelles (graphiques et PDF)."""

    def __init__(self, repo, model):
        """
        :param repo: Instance de Repository contenant les données brutes.
        :param model: Instance de Model contenant les résultats calculés.
        """
        self.repo = repo
        self.model = model
        self.config = repo.config

    def display(self):
        """Génère l'ensemble des graphiques puis le rapport PDF."""
        logger.info("Génération des graphiques et du rapport PDF.")
        self._display_all_charts()
        self._display_pdf_report()
        logger.info("Rapport PDF généré : '%s'.", self.config.get("output_pdf_path"))

    # ------------------------------------------------------------------
    # GRAPHIQUES
    # ------------------------------------------------------------------

    def _display_all_charts(self):
        """Génère les 6 graphiques analytiques du rapport."""
        self._display_prix_nominaux()
        self._display_prix_normalises()
        self._display_correlation()
        self._display_secteurs()
        self._display_croissance_monetaire()
        self._display_frontiere_efficiente()
        logger.info("Tous les graphiques ont été générés.")

    def _display_prix_nominaux(self):
        """Génère le graphique des prix de clôture nominaux."""
        plt.figure(figsize=(10, 4))
        plt.plot(self.repo.df_raw)
        plt.title("Évolution des prix de clôture nominaux")
        plt.tight_layout()
        plt.savefig(self.config.get("graph_prix_nominaux"))
        plt.close()
        logger.info("Graphique prix nominaux généré.")

    def _display_prix_normalises(self):
        """Génère le graphique des prix normalisés (base 1)."""
        plt.figure(figsize=(10, 4))
        plt.plot(price_scaling(self.repo.df_raw_sm.set_index("Date")))
        plt.title("Performance relative – Normalisation base 1")
        plt.tight_layout()
        plt.savefig(self.config.get("graph_prix_normalises"))
        plt.close()
        logger.info("Graphique prix normalisés généré.")

    def _display_correlation(self):
        """Génère la heatmap de la matrice de corrélation."""
        plt.figure(figsize=(8, 6))
        sns.heatmap(self.model.corr_matrix, annot=True, cmap="RdYlGn")
        plt.title("Matrice de corrélation")
        plt.tight_layout()
        plt.savefig(self.config.get("graph_correlation"))
        plt.close()
        logger.info("Graphique corrélation généré.")

    def _display_secteurs(self):
        """Génère le graphique d'allocation sectorielle."""
        plt.figure(figsize=(10, 5))
        sns.barplot(
            data=self.model.final_data, x="Ticker", y="Poids", hue="Secteur"
        )
        plt.title("Allocation sectorielle du portefeuille optimal")
        plt.tight_layout()
        plt.savefig(self.config.get("graph_secteurs"))
        plt.close()
        logger.info("Graphique secteurs généré.")

    def _display_croissance_monetaire(self):
        """Génère le graphique de croissance historique en valeur monétaire."""
        inv = self.repo.initial_investment
        plt.figure(figsize=(10, 4))
        plt.plot(
            self.model.df_monetary["Portfolio Value [$]"],
            color="green",
            linewidth=2,
        )
        plt.title(f"Historique de croissance du capital ({inv:,.0f} $)")
        plt.tight_layout()
        plt.savefig(self.config.get("graph_monetaire"))
        plt.close()
        logger.info("Graphique croissance monétaire généré.")

    def _display_frontiere_efficiente(self):
        """Génère le nuage de points Monte Carlo (frontière efficiente)."""
        mc = self.model.mc_results
        plt.figure(figsize=(10, 5))
        plt.scatter(
            mc["volatility_runs"],
            mc["return_runs"],
            c=mc["sharpe_runs"],
            cmap="viridis",
        )
        plt.scatter(
            mc["optimal_volatility"],
            mc["optimal_return"],
            color="red",
            marker="*",
            s=200,
            label="Portefeuille optimal",
        )
        plt.colorbar(label="Ratio de Sharpe")
        plt.xlabel("Volatilité annualisée")
        plt.ylabel("Rendement annualisé")
        plt.title("Frontière efficiente – Simulation Monte Carlo")
        plt.legend()
        plt.tight_layout()
        plt.savefig(self.config.get("graph_frontiere"))
        plt.close()
        logger.info("Graphique frontière efficiente généré.")

    # ------------------------------------------------------------------
    # RAPPORT PDF
    # ------------------------------------------------------------------

    def _display_pdf_report(self):
        """Génère le rapport PDF complet en 9 sections."""
        mc = self.model.mc_results
        inv = self.repo.initial_investment
        opt_vol = mc["optimal_volatility"]
        opt_ret = mc["optimal_return"]
        opt_sharpe = mc["optimal_sharpe"]
        highest_value = mc["highest_final_value"]
        opt_roi = mc["optimal_roi"]
        avg_corr = self.model.avg_corr
        scenarios = self.model.scenarios

        pdf = _RapportClient()
        pdf.add_page()

        # --- SECTION 1 : PROFIL INVESTISSEUR ---
        pdf.section_title("1. Détermination du Profil d'Investisseur")
        pdf.description(
            f"Sur la base de l'allocation optimale calculée, "
            f"votre profil est identifié comme : {self.model.profil}."
        )
        pdf.analysis(
            f"Votre stratégie privilégie un compromis entre croissance et "
            f"maîtrise du risque. Avec une volatilité cible de "
            f"{opt_vol * 100:.2f}%, le portefeuille est calibré pour "
            f"votre tolérance au marché."
        )

        # --- SECTION 2 : PRIX NOMINAUX ---
        pdf.section_title("2. Évolution des Prix de Clôture Nominaux")
        pdf.description(
            "Observation des trajectoires brutes des cours. Cette vue permet "
            "d'identifier la volatilité faciale et les écarts de valeur marchande."
        )
        pdf.image(self.config.get("graph_prix_nominaux"), x=10, w=180)
        pdf.analysis(
            "L'observation des cours nominaux révèle une forte hétérogénéité "
            "des valeurs de marché. Une action à prix élevé ne présage en rien "
            "d'une surperformance future."
        )

        # --- SECTION 3 : NORMALISATION ---
        pdf.section_title("3. Performance Relative (Normalisation Base 1)")
        pdf.description(
            "La normalisation permet de comparer la croissance réelle de chaque "
            "actif comme si 1$ avait été investi dans chacun d'eux au départ."
        )
        pdf.image(self.config.get("graph_prix_normalises"), x=10, w=180)
        pdf.analysis(
            f"Ce graphique désigne {self.model.ticker_leader} comme le principal "
            f"moteur de richesse du panier, avec une performance de "
            f"{self.model.val_leader:.1f}% sur la période étudiée."
        )

        # --- SECTION 4 : DIVERSIFICATION ---
        pdf.add_page()
        pdf.section_title("4. Diagnostic de Diversification et Corrélations")
        pdf.description(
            "La matrice de corrélation mesure la dépendance statistique. "
            "Une corrélation faible est le socle d'une diversification protectrice."
        )
        pdf.image(self.config.get("graph_correlation"), x=40, w=130)
        if avg_corr < 0.3:
            comment_corr = (
                f"La corrélation moyenne de {avg_corr:.2f} indique une excellente "
                f"diversification. Les actifs évoluent indépendamment, protégeant "
                f"le portefeuille contre les chocs de marché."
            )
        elif avg_corr < 0.6:
            comment_corr = (
                f"La corrélation moyenne de {avg_corr:.2f} suggère une "
                f"diversification correcte. Certains actifs présentent une "
                f"dépendance modérée, à surveiller en cas de volatilité."
            )
        else:
            comment_corr = (
                f"La corrélation moyenne de {avg_corr:.2f} est élevée. "
                f"Le portefeuille est fortement corrélé, augmentant le risque "
                f"global en cas de chute du marché."
            )
        pdf.analysis(comment_corr)

        # --- SECTION 5 : ANALYSE SECTORIELLE ---
        pdf.section_title("5. Analyse Sectorielle (Jointure de Données)")
        pdf.description(
            "Lien entre l'allocation financière et les secteurs d'activité pour "
            "identifier les éventuels risques de concentration industrielle."
        )
        pdf.image(self.config.get("graph_secteurs"), x=10, w=180)
        pdf.analysis(
            f"Le portefeuille présente une exposition dominante au secteur "
            f"{self.model.dom_sect.idxmax()} "
            f"({self.model.dom_sect.max() * 100:.1f}%). "
            f"Cette répartition reflète les opportunités actuelles de croissance."
        )

        # --- SECTION 6 : MONTE CARLO ---
        pdf.add_page()
        pdf.section_title("6. Optimisation Monte Carlo et Frontière Efficiente")
        pdf.description(
            "Simulation de milliers de combinaisons pour identifier le portefeuille "
            "maximisant le Ratio de Sharpe (rendement par unité de risque)."
        )
        pdf.image(self.config.get("graph_frontiere"), x=10, w=180)
        compo = ", ".join(
            f"{row['Ticker']} ({row['Poids'] * 100:.1f}%)"
            for _, row in self.model.final_data.iterrows()
            if row["Poids"] > 0.01
        )
        pdf.analysis(
            f"Le portefeuille optimal (point rouge) atteint un Ratio de Sharpe "
            f"de {opt_sharpe:.2f}. Composition principale : {compo}."
        )

        # --- SECTION 7 : CROISSANCE HISTORIQUE ---
        pdf.section_title("7. Croissance Historique du Portefeuille (en $)")
        pdf.description(
            "Ce graphique traduit la performance passée en valeur monétaire réelle."
        )
        pdf.image(self.config.get("graph_monetaire"), x=10, w=180)
        pdf.analysis(
            f"Depuis 2018, votre capital initial serait passé de "
            f"{inv:,.0f} $ à {highest_value:,.2f} $, soit un ROI de {opt_roi:.2f}%."
        )

        # --- SECTION 8 : PROJECTION ---
        pdf.section_title("8. Projection et Conclusion")
        pdf.description(
            "Estimation de la valeur finale du portefeuille à un horizon de 12 mois."
        )
        pdf.analysis(
            f"Pour un capital initial de {inv:,.2f} USD, la valeur cible est "
            f"estimée à {inv * (1 + opt_ret):,.2f} USD avec une volatilité "
            f"annuelle de {opt_vol * 100:.2f}%."
        )

        # --- SECTION 9 : STRESS TESTING ---
        pdf.section_title("9. Analyse de Scénarios et Stress Testing")
        scenarios_text = (
            f"\nSCÉNARIO BAISSIER (-2 sigma) :\n"
            f"  Valeur projetée : {scenarios['baissier']:,.2f} USD\n"
            f"  Perte potentielle : "
            f"{((scenarios['baissier'] / inv - 1) * 100):.2f}%\n\n"
            f"SCÉNARIO NEUTRE (attendu) :\n"
            f"  Valeur projetée : {scenarios['neutre']:,.2f} USD\n"
            f"  Gain attendu : {((scenarios['neutre'] / inv - 1) * 100):.2f}%\n\n"
            f"SCÉNARIO HAUSSIER (+1 sigma) :\n"
            f"  Valeur projetée : {scenarios['haussier']:,.2f} USD\n"
            f"  Gain potentiel : {((scenarios['haussier'] / inv - 1) * 100):.2f}%\n"
        )
        pdf.description(
            "Projection sur 12 mois selon trois scénarios basés sur "
            "la volatilité historique :"
        )
        pdf.analysis(scenarios_text)
        pdf.analysis(
            f"Dans le pire scénario statistique (probabilité ~2.5%), votre "
            f"capital pourrait descendre à {scenarios['baissier']:,.2f} USD."
        )

        pdf.output(self.config.get("output_pdf_path"))


class _RapportClient(FPDF):
    """Classe PDF interne avec mise en page personnalisée pour le rapport client."""

    def header(self):
        """En-tête affiché sur chaque page."""
        self.set_font("helvetica", "B", 16)
        self.set_text_color(0, 51, 102)
        titre = "EXPERTISE FINANCIÈRE : STRATÉGIE D'ALLOCATION"
        self.cell(
            0, 15,
            titre.encode("latin-1", "replace").decode("latin-1"),
            center=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.ln(5)

    def section_title(self, title: str):
        """Affiche un titre de section sur fond gris clair."""
        self.set_font("helvetica", "B", 12)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(0, 0, 0)
        self.cell(
            0, 10,
            f" {title.upper()}".encode("latin-1", "replace").decode("latin-1"),
            fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
        self.ln(2)

    def description(self, text: str):
        """Affiche un texte descriptif en italique gris."""
        self.set_font("helvetica", "I", 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 6, text.encode("latin-1", "replace").decode("latin-1"))
        self.ln(2)

    def analysis(self, text: str):
        """Affiche un texte d'analyse en bleu marine."""
        self.set_font("helvetica", "", 11)
        self.set_text_color(0, 51, 102)
        self.multi_cell(
            0, 7,
            f"Analyse : {text}".encode("latin-1", "replace").decode("latin-1"),
        )
        self.ln(4)
