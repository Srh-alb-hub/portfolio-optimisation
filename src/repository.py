# src/repository.py
import logging

import pandas as pd
import yfinance as yf

from constants import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


class Repository:
    """Responsabilité unique : acquisition et chargement des données brutes."""

    def __init__(self, config: dict):
        """
        :param config: Dictionnaire de configuration chargé depuis config.yaml.
        """
        self.config = config
        self.tickers = None
        self.initial_investment = None
        self.rf_rate = None
        self.sim_runs = None
        self.df_raw = None
        self.df_raw_sm = None
        self.returns = None
        self.sector_data = None

    def get_data(self):
        """Collecte les saisies utilisateur et télécharge les données historiques."""
        self._get_user_inputs()
        self._get_historical_prices()
        logger.info(
            "Données prêtes – %d actifs, %d observations.",
            len(self.tickers),
            len(self.df_raw),
        )

    def _get_user_inputs(self):
        """Collecte les paramètres saisis par l'utilisateur en console."""
        print("\n--- Analyse de Portefeuille ---")
        tickers_input = input("Entrez les Tickers (ex: AMZN,JPM,META,PG,GOOGL) : ")
        self.tickers = [t.strip().upper() for t in tickers_input.split(",")]
        self.initial_investment = float(
            input("Entrez le Montant à investir (ex: 100000) : ")
        )
        self.rf_rate = float(input("Entrez le Taux sans risque (ex: 0.03) : "))
        self.sim_runs = int(
            input(
                f"Entrez le nombre de Simulations Monte Carlo "
                f"(ex: {self.config.get('sim_runs_default', 1000)}) : "
            )
        )
        logger.info(
            "Paramètres utilisateur – Tickers : %s | Capital : %.2f | "
            "Taux sans risque : %.3f | Simulations : %d",
            self.tickers,
            self.initial_investment,
            self.rf_rate,
            self.sim_runs,
        )

    def _get_historical_prices(self):
        """Télécharge les prix de clôture historiques via yfinance."""
        date_debut = self.config.get("date_debut", "2018-01-01")
        logger.info(
            "Téléchargement des données pour %s depuis %s.", self.tickers, date_debut
        )
        df = yf.download(self.tickers, start=date_debut)["Close"].dropna()
        if df.empty:
            raise ValueError(
                f"Aucune donnée récupérée pour les tickers : {self.tickers}"
            )
        self.df_raw = df
        self.df_raw_sm = df.reset_index()
        self.returns = df.pct_change().dropna()

    def get_sector_data(self, weights_df: pd.DataFrame) -> pd.DataFrame:
        """Construit le DataFrame poids + secteurs pour chaque ticker.

        Tente une jointure avec le CSV local, puis interroge yfinance
        pour les tickers sans secteur.

        :param weights_df: DataFrame avec colonnes ['Ticker', 'Poids'].
        :return: DataFrame enrichi avec la colonne 'Secteur'.
        """
        referentiel_path = self.config.get("referentiel_secteurs_path", "referentiel_secteurs.csv")
        traductions = self.config.get("traductions_secteurs", {})

        try:
            ref = pd.read_csv(referentiel_path)
            joined = pd.merge(weights_df, ref, on="Ticker", how="left")
            logger.info("Référentiel secteurs chargé depuis '%s'.", referentiel_path)
        except FileNotFoundError:
            logger.warning(
                "Fichier '%s' introuvable. Fallback sur yfinance.", referentiel_path
            )
            joined = weights_df.copy()
            joined["Secteur"] = None

        for idx, row in joined.iterrows():
            if pd.isna(row["Secteur"]) or row["Secteur"] == "Non Défini":
                joined.at[idx, "Secteur"] = self._get_sector_from_yfinance(
                    row["Ticker"], traductions
                )

        self.sector_data = joined
        return joined

    def _get_sector_from_yfinance(self, ticker: str, traductions: dict) -> str:
        """Récupère le secteur d'un ticker via l'API yfinance.

        :param ticker: Symbole boursier.
        :param traductions: Dictionnaire de traduction secteur EN -> FR.
        :return: Secteur en français.
        """
        try:
            info = yf.Ticker(ticker).info
            raw_sector = info.get("sector", "Divers")
            secteur = traductions.get(raw_sector, raw_sector)
            logger.debug("Secteur récupéré pour %s : %s.", ticker, secteur)
            return secteur
        except Exception as exc:
            logger.warning(
                "Impossible de récupérer le secteur pour %s : %s.", ticker, exc
            )
            return "Autres Secteurs"
