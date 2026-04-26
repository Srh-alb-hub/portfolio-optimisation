# 📈 Portfolio Optimisation – Monte Carlo & Rapport PDF

> Outil d'optimisation de portefeuille financier par simulation Monte Carlo.  
> Génère automatiquement un rapport PDF professionnel avec analyses quantitatives et graphiques.

---

## 👥 Conceptrice du projet 

| Nom | Université |
|-----|-----------|
| Sarah Alibay | Paris 1 Panthéon-Sorbonne |

---

## 📌 Description

Ce projet applique la **théorie moderne du portefeuille de Markowitz** en combinant :

- **Simulation Monte Carlo** : génération de N combinaisons aléatoires de poids pour identifier l'allocation maximisant le ratio de Sharpe
- **Données historiques** : prix de clôture quotidiens depuis 2018 via l'API Yahoo Finance (`yfinance`)
- **Rapport PDF automatique** : 9 sections avec graphiques, métriques quantitatives et analyses qualitatives accessibles aux investisseurs non-experts

### Analyses produites

- Évolution des prix nominaux et normalisés (base 1)
- Matrice de corrélation et diagnostic de diversification
- Allocation sectorielle (jointure CSV + API yfinance)
- Frontière efficiente Monte Carlo
- Croissance historique du portefeuille en valeur monétaire
- Projection 12 mois et stress testing (scénarios baissier / neutre / haussier)

---

## 🗂️ Structure du projet

```
portfolio/
│
├── main.py                        # Point d'entrée – classe App avec run()
├── constants.py                   # Constantes globales (chemins, noms)
│
└── src/
    ├── __init__.py
    ├── repository.py              # Classe Repository – acquisition des données
    ├── model.py                   # Classe Model – calculs financiers
    ├── view.py                    # Classe View – graphiques et rapport PDF
    │
    ├── helpers/
    │   ├── __init__.py
    │   ├── helpers_logging.py     # Initialisation du logger depuis fichier YAML
    │   ├── helpers_serialize.py   # Lecture/écriture YAML, JSON, TOML
    │   └── helpers_portfolio.py   # Fonctions utilitaires pures (normalisation, poids)
    │
    └── input/
        ├── config.yaml            # Paramètres métier (dates, chemins, seuils)
        └── config_logging.yaml    # Configuration du logger
```

---

## ⚙️ Installation

### Prérequis

- Python 3.10+
- pip

### Dépendances

```bash
pip install yfinance fpdf2 matplotlib seaborn pandas numpy pyyaml toml
```

---

## 🚀 Lancement

```bash
python main.py
```

Le programme vous demandera :

```
--- Analyse de Portefeuille ---
Entrez les Tickers (ex: AMZN,JPM,META,PG,GOOGL) :
Entrez le Montant à investir (ex: 100000) :
Entrez le Taux sans risque (ex: 0.03) :
Entrez le nombre de Simulations Monte Carlo (ex: 1000) :
```

À la fin de l'exécution, le fichier **`Rapport_Client.pdf`** est généré dans le dossier courant.

---

## 📊 Exemple de résultat

| Métrique | Valeur (exemple) |
|---------|-----------------|
| Ratio de Sharpe optimal | 1.42 |
| Rendement annualisé | 18.3% |
| Volatilité annualisée | 14.7% |
| ROI historique (depuis 2018) | +312% |

---

## 📁 Fichiers générés

| Fichier | Description |
|--------|-------------|
| `Rapport_Client.pdf` | Rapport complet 9 sections |
| `1_prices.png` | Prix de clôture nominaux |
| `2_scaled.png` | Prix normalisés base 1 |
| `3_corr.png` | Matrice de corrélation |
| `4_sector.png` | Allocation sectorielle |
| `2_monetary.png` | Croissance historique monétaire |
| `5_frontier.png` | Frontière efficiente Monte Carlo |
| `portfolio.log` | Journal des logs d'exécution |

---

## 🔧 Configuration

Tous les paramètres sont centralisés dans `src/input/config.yaml` :

```yaml
date_debut: "2018-01-01"
sim_runs_default: 1000
seuil_volatilite_equilibre: 0.25
output_pdf_path: "Rapport_Client.pdf"
```

---

## 🏗️ Architecture – Pattern Sorbonne

Le projet suit le pattern **Repository / Model / View** enseigné en cours :

```
App (main.py)
 ├── Repository  →  récupère et stocke les données brutes
 ├── Model       →  calcule les métriques (reçoit le repo)
 └── View        →  affiche les résultats (reçoit le repo et le model)
```

---

## 📚 Sources et références

- Cours DataCamp : *Data Manipulation with pandas*
- Documentation officielle [yfinance](https://pypi.org/project/yfinance/)
- Documentation officielle [FPDF2](https://py-pdf.github.io/fpdf2/)
- Markowitz, H. (1952). *Portfolio Selection*. The Journal of Finance.
- Pattern architectural : [Paris 1 – UFR 02 Finance Python M1/M2](https://github.com/SorbonneParis1Ufr02FinancePythonM1-M2)
