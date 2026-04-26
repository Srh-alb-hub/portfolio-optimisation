# src/helpers/helpers_portfolio.py
# Fonctions utilitaires pures pour les calculs de portefeuille.

import numpy as np


def price_scaling(raw_prices_df):
    """Normalise les cours boursiers sur une base 1.

    Args:
        raw_prices_df (pd.DataFrame): Cours bruts (Date en index ou colonne).

    Returns:
        pd.DataFrame: Cours normalisés.
    """
    scaled_df = raw_prices_df.copy()
    cols = [c for c in raw_prices_df.columns if c != "Date"]
    for col in cols:
        scaled_df[col] = raw_prices_df[col] / raw_prices_df[col].iloc[0]
    return scaled_df


def generate_portfolio_weights(n: int) -> np.ndarray:
    """Génère n poids aléatoires dont la somme vaut 1.

    Args:
        n (int): Nombre d'actifs.

    Returns:
        np.ndarray: Vecteur de poids normalisé.
    """
    weights = np.random.random(n)
    return weights / weights.sum()
