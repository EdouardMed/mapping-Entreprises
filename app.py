import streamlit as st
import pandas as pd
import os
import traceback

# ============================================
# Configuration de la page
# ============================================
st.set_page_config(
    page_title="Mapping Entreprise Medipim",
    layout="wide"
)

# ============================================
# CSS personnalisé pour fixer le footer et ajouter une marge en bas
# ============================================
st.markdown("""
<style>
/* Exemple: changer la couleur de fond de la page */
body {
    background-color: #ff0000 !important;  /* un gris foncé */
    color: #ffffff !important;            /* texte en blanc */
}

/* Changer la couleur de la barre latérale (sidebar) */
.sidebar .sidebar-content {
    background-color: #2E2E2E !important;
}

/* Ajuster la couleur des titres */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

/* Footer personnalisé déjà présent */
#custom-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #0E1117;
    text-align: center;
    padding: 0.5rem;
    z-index: 9999;
}

#custom-footer-text {
    color: #999999;
    font-size: 12px;
    margin: 0;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# Disposition en colonnes pour le logo et le titre
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(SCRIPT_DIR, "assets", "logoMdpm_detoured.png")

col_logo, col_titre = st.columns([0.2, 0.8])  # le logo prend plus de place

with col_logo:
    if os.path.exists(logo_path):
        # Agrandit le logo
        st.image(logo_path, width=250)
        st.write("")  # espace vertical

    else:
        st.warning("Logo introuvable dans le dossier assets/")

with col_titre:
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    st.title("Interface de Mapping - LABOS et PRODUITS")

# ============================================
# Instructions
# ============================================
with st.expander("Instructions générales"):
    st.markdown("""
    **1.** Chargez le fichier **LABOS_LINK** (ID labo, nom labo, ID entreprise).  
    **2.** Chargez le fichier **PRODUITS** (ID produit, entreprise, ID labo).  
    **3.** Sélectionnez les colonnes et générez le fichier PRODUITS mis à jour.  
    """)

# ============================================
# Chargement des fichiers CSV
# ============================================
st.subheader("1. Charger les fichiers CSV")

# Deux colonnes pour les deux uploaders
col_labos, col_produits = st.columns(2)

with col_labos:
    st.markdown("#### Fichier LABOS_LINK")
    labos_file = st.file_uploader("Choisir un CSV pour LABOS_LINK", type=["csv"], key="labos")

with col_produits:
    st.markdown("#### Fichier PRODUITS")
    produits_file = st.file_uploader("Choisir un CSV pour PRODUITS", type=["csv"], key="produits")

labos_df = None
produits_df = None
WARNINGS = []
ERRORS = []

def read_csv_auto(file):
    return pd.read_csv(file, sep=None, engine='python')

if labos_file is not None:
    try:
        labos_df = read_csv_auto(labos_file)
        st.success("Fichier LABOS_LINK chargé avec succès!")
    except Exception as e:
        ERRORS.append(f"Erreur lors du chargement de LABOS_LINK: {e}")

if produits_file is not None:
    try:
        produits_df = read_csv_auto(produits_file)
        st.success("Fichier PRODUITS chargé avec succès!")
    except Exception as e:
        ERRORS.append(f"Erreur lors du chargement de PRODUITS: {e}")

# ============================================
# Sélection des colonnes
# ============================================
if labos_df is not None and produits_df is not None:
    st.subheader("2. Sélectionner les colonnes pour le mapping")
    col_sel1, col_sel2 = st.columns(2)

    with col_sel1:
        st.markdown("##### Colonnes du fichier LABOS_LINK")
        labo_id_col = st.selectbox("Colonne ID labo", labos_df.columns, key="labo_id")
        labo_name_col = st.selectbox("Colonne nom labo", labos_df.columns, key="labo_name")
        entreprise_id_col = st.selectbox("Colonne ID entreprise", labos_df.columns, key="entreprise_id")

    with col_sel2:
        st.markdown("##### Colonnes du fichier PRODUITS")
        produit_id_col = st.selectbox("Colonne ID produit", produits_df.columns, key="produit_id")
        produit_entreprise_col = st.selectbox("Colonne à remplir (entreprise)", produits_df.columns, key="produit_entreprise")
        produit_labos_col = st.selectbox("Colonne ID labo(s)", produits_df.columns, key="produit_labos")

    # ============================================
    # Logique de mapping
    # ============================================
    class LabosMappingBuilder:
        def __init__(self, dataframe, labo_id_col, labo_name_col, entreprise_id_col):
            self.dataframe = dataframe
            self.labo_id_col = labo_id_col
            self.labo_name_col = labo_name_col
            self.entreprise_id_col = entreprise_id_col

        def build_mapping(self):
            mapping = {}
            for idx, row in self.dataframe.iterrows():
                labo_id_raw = row[self.labo_id_col]
                entreprise_id_raw = row[self.entreprise_id_col]
                if pd.isna(labo_id_raw):
                    WARNINGS.append(f"Ligne {idx}: ID labo manquant. Ignorée.")
                    continue
                labo_id_str = str(labo_id_raw).strip()
                entreprise_id_str = str(entreprise_id_raw).strip() if not pd.isna(entreprise_id_raw) else ""
                if labo_id_str in mapping:
                    WARNINGS.append(f"Ligne {idx}: ID labo '{labo_id_str}' déjà présent. Valeur précédente conservée.")
                    continue
                mapping[labo_id_str] = entreprise_id_str
            st.info(f"Mapping construit avec {len(mapping)} entrées.")
            return mapping

    class ProductProcessor:
        def __init__(self, dataframe, product_id_col, entreprise_col, labo_id_col):
            self.dataframe = dataframe
            self.product_id_col = product_id_col
            self.entreprise_col = entreprise_col
            self.labo_id_col = labo_id_col

        def process(self, mapping):
            df = self.dataframe.copy()
            def map_entreprise(labo_value):
                if pd.isna(labo_value):
                    return None
                labo_id_str = str(labo_value).strip()
                if labo_id_str in mapping:
                    return mapping[labo_id_str]
                else:
                    ERRORS.append(f"Mapping non trouvé pour l'ID labo: '{labo_id_str}'")
                    return None
            df[self.entreprise_col] = df[self.labo_id_col].apply(map_entreprise)
            return df

    # ============================================
    # Génération du fichier PRODUITS mis à jour
    # ============================================
    st.subheader("3. Générer le fichier PRODUITS mis à jour")
    if st.button("Générer le fichier"):
        try:
            builder = LabosMappingBuilder(labos_df, labo_id_col, labo_name_col, entreprise_id_col)
            mapping = builder.build_mapping()

            processor = ProductProcessor(produits_df, produit_id_col, produit_entreprise_col, produit_labos_col)
            updated_df = processor.process(mapping)

            st.success("Fichier PRODUITS mis à jour généré avec succès !")
            st.dataframe(updated_df.head(20))

            csv_data = updated_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Télécharger le fichier mis à jour",
                data=csv_data,
                file_name="produits_mis_a_jour.csv",
                mime="text/csv"
            )
        except Exception as e:
            ERRORS.append(f"Erreur lors du traitement: {e}")
            ERRORS.append(traceback.format_exc())

# ============================================
# Affichage des avertissements / erreurs
# ============================================
if WARNINGS or ERRORS:
    with st.expander("Voir les messages d'avertissement / d'erreur"):
        for w in WARNINGS:
            st.warning(w)
        for e in ERRORS:
            st.error(e)

# ============================================
# Pied de page fixe
# ============================================
st.markdown("""
<div id="custom-footer">
    <p id="custom-footer-text">&copy; Edouard Georg - 2025. Tous droits réservés.</p>
</div>
""", unsafe_allow_html=True)
