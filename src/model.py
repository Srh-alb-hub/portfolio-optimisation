# src/model.py
import logging

import numpy as np
import pandas as pd

from constants import LOGGER_NAME
from src.helpers.helpers_portfolio import generate_portfolio_weights, price_scaling

logger = logging.getLogger(LOGGER_NAME)


class Model:
    """Responsabilité unique : logique métier et calculs financiers."""

    def __init__(self, repo):
        """
        :param repo: Instance de Repository contenant les données brutes.
        """
        self.repo = repo
        self.mc_results = None
        self.corr_matrix = None
        self.avg_corr = None
        self.ticker_leader = None
        self.val_leader = None
        self.profil = None
        self.scenarios = None
        self.df_monetary = None
        self.final_data = None
        self.dom_sect = None

    def process_data(self):
        """Exécute l'ensemble des calculs financiers."""
        logger.info("Début des calculs financiers.")
        self.mc_results = self._run_monte_carlo()
        self.corr_matrix, self.avg_corr = self._compute_correlation_analysis()
        self.ticker_leader, self.val_leader = self._compute_relative_performance()
        self.profil = self._compute_investor_profile()
        self.scenarios = self._compute_stress_scenarios()
        self._build_sector_data()
        self.df_monetary = self._compute_asset_allocation(
            self.repo.df_raw_sm,
            self.mc_results["optimal_weights"],
            self.repo.initial_investment,
        )
        self.df_monetary.set_index("Date", inplace=True)
        logger.info("Calculs financiers terminés.")

    # ------------------------------------------------------------------
    # Monte Carlo
    # ------------------------------------------------------------------

    def _run_monte_carlo(self) -> dict:
        """Exécute la simulation Monte Carlo pour trouver le portefeuille optimal.

        :return: Dictionnaire contenant les résultats de toutes les simulations
                 et les métriques du portefeuille optimal.
        """
        df = self.repo.df_raw_sm
        n_assets = len(self.repo.tickers)
        initial_investment = self.repo.initial_investment
        rf_rate = self.repo.rf_rate
        sim_runs = self.repo.sim_runs

        logger.info("Lancement de %d simulations Monte Carlo.", sim_runs)

        weights_runs = np.zeros((sim_runs, n_assets))
        sharpe_runs = np.zeros(sim_runs)
        return_runs = np.zeros(sim_runs)
        volatility_runs = np.zeros(sim_runs)
        roi_runs = np.zeros(sim_runs)
        final_value_runs = np.zeros(sim_runs)

        for i in range(sim_runs):
            weights = generate_portfolio_weights(n_assets)
            weights_runs[i] = weights
            exp_ret, vol, sharpe, final_val, roi = self._compute_portfolio_metrics(
                df, weights, initial_investment, rf_rate
            )
            return_runs[i] = exp_ret
            volatility_runs[i] = vol
            sharpe_runs[i] = sharpe
            final_value_runs[i] = final_val
            roi_runs[i] = roi

        max_idx = sharpe_runs.argmax()
        optimal_weights = weights_runs[max_idx]
        opt_return, opt_vol, opt_sharpe, highest_value, opt_roi = (
            self._compute_portfolio_metrics(
                df, optimal_weights, initial_investment, rf_rate
            )
        )

        logger.info(
            "Simulation terminée. Sharpe optimal : %.4f | Volatilité : %.4f%%.",
            opt_sharpe,
            opt_vol * 100,
        )

        return {
            "weights_runs": weights_runs,
            "sharpe_runs": sharpe_runs,
            "return_runs": return_runs,
            "volatility_runs": volatility_runs,
            "roi_runs": roi_runs,
            "final_value_runs": final_value_runs,
            "optimal_weights": optimal_weights,
            "optimal_return": opt_return,
            "optimal_volatility": opt_vol,
            "optimal_sharpe": opt_sharpe,
            "highest_final_value": highest_value,
            "optimal_roi": opt_roi,
        }

    # ------------------------------------------------------------------
    # Calculs de portefeuille
    # ------------------------------------------------------------------

    def _compute_asset_allocation(
        self, df: pd.DataFrame, weights: np.ndarray, initial_investment: float
    ) -> pd.DataFrame:
        """Calcule la valeur monétaire et les rendements journaliers du portefeuille.

        :param df: Prix historiques avec colonne 'Date'.
        :param weights: Vecteur de poids des actifs.
        :param initial_investment: Capital initial en USD.
        :return: DataFrame enrichi avec 'Portfolio Value [$]' et
                 'Portfolio Daily Return [%]'.
        """
        portfolio_df = df.copy()
        scaled_df = price_scaling(df)
        stock_columns = [c for c in df.columns if c != "Date"]

        for i, stock in enumerate(stock_columns):
            portfolio_df[stock] = (
                scaled_df[stock] * weights[i] * initial_investment
            )

        portfolio_df["Portfolio Value [$]"] = portfolio_df[stock_columns].sum(axis=1)
        portfolio_df["Portfolio Daily Return [%]"] = (
            portfolio_df["Portfolio Value [$]"].pct_change() * 100
        )
        return portfolio_df.fillna(0)

    def _compute_portfolio_metrics(
        self,
        df: pd.DataFrame,
        weights: np.ndarray,
        initial_investment: float,
        rf_rate: float,
    ) -> tuple:
        """Calcule les métriques annualisées d'un portefeuille.

        :param df: Prix historiques avec colonne 'Date'.
        :param weights: Vecteur de poids des actifs.
        :param initial_investment: Capital initial en USD.
        :param rf_rate: Taux sans risque annualisé.
        :return: (rendement_annualisé, volatilité, sharpe, valeur_finale, roi_pct)
        """
        portfolio_df = self._compute_asset_allocation(df, weights, initial_investment)
        portfolio_values = portfolio_df["Portfolio Value [$]"]

        roi = (
            (portfolio_values.iloc[-1] - portfolio_values.iloc[0])
            / portfolio_values.iloc[0]
            * 100
        )

        daily_returns = portfolio_df.drop(
            columns=["Date", "Portfolio Value [$]", "Portfolio Daily Return [%]"]
        ).pct_change(1)

        ann_return = np.sum(weights * daily_returns.mean()) * 252
        ann_cov = daily_returns.cov() * 252
        ann_volatility = np.sqrt(weights.T @ ann_cov @ weights)
        sharpe = (ann_return - rf_rate) / ann_volatility

        return ann_return, ann_volatility, sharpe, portfolio_values.iloc[-1], roi

    # ------------------------------------------------------------------
    # Analyses complémentaires
    # ------------------------------------------------------------------

    def _compute_correlation_analysis(self) -> tuple:
        """Calcule la matrice de corrélation et la corrélation moyenne.

        :return: (corr_matrix, avg_corr)
        """
        corr_matrix = self.repo.returns.corr()
        upper_tri = corr_matrix.values[
            np.triu_indices_from(corr_matrix.values, k=1)
        ]
        avg_corr = upper_tri.mean()
        logger.debug("Corrélation moyenne : %.4f.", avg_corr)
        return corr_matrix, avg_corr

    def _compute_relative_performance(self) -> tuple:
        """Identifie l'actif le plus performant sur la période.

        :return: (ticker_leader, performance_pct)
        """
        perf_rel = self.repo.df_raw.iloc[-1] / self.repo.df_raw.iloc[0]
        ticker_leader = perf_rel.idxmax()
        val_leader = (perf_rel.max() - 1) * 100
        return ticker_leader, val_leader

    def _compute_investor_profile(self) -> str:
        """Détermine le profil investisseur selon la volatilité optimale.

        :return: 'Équilibré' ou 'Dynamique'.
        """
        seuil = self.repo.config.get("seuil_volatilite_equilibre", 0.25)
        return (
            "Équilibré"
            if self.mc_results["optimal_volatility"] <= seuil
            else "Dynamique"
        )

    def _compute_stress_scenarios(self) -> dict:
        """Calcule trois scénarios de stress à horizon 12 mois.

        :return: Dictionnaire avec valeurs projetées baissier/neutre/haussier.
        """
        inv = self.repo.initial_investment
        ret = self.mc_results["optimal_return"]
        vol = self.mc_results["optimal_volatility"]
        return {
            "baissier": inv * (1 + ret - 2 * vol),
            "neutre": inv * (1 + ret),
            "haussier": inv * (1 + ret + vol),
        }

    def _build_sector_data(self):
        """Construit les données sectorielles et la dominance par secteur."""
        weights_df = pd.DataFrame({
            "Ticker": self.repo.tickers,
            "Poids": self.mc_results["optimal_weights"],
        })
        self.final_data = self.repo.get_sector_data(weights_df)
        self.dom_sect = self.final_data.groupby("Secteur")["Poids"].sum()
