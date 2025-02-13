# mapping.py
import pandas as pd
import streamlit as st

class LabosMappingBuilder:
    """
    Construit un dictionnaire de mapping {labo_id -> entreprise_id} à partir d'un DataFrame.
    """
    def __init__(self, dataframe: pd.DataFrame, labo_id_col: str, labo_name_col: str, entreprise_id_col: str):
        self.dataframe = dataframe
        self.labo_id_col = labo_id_col
        self.labo_name_col = labo_name_col
        self.entreprise_id_col = entreprise_id_col

    def build_mapping(self) -> dict:
        mapping = {}
        for idx, row in self.dataframe.iterrows():
            labo_id_raw = row[self.labo_id_col]
            entreprise_id_raw = row[self.entreprise_id_col]
            if pd.isna(labo_id_raw):
                st.warning(f"Ligne {idx}: ID labo manquant. Ignorée.")
                continue
            labo_id_str = str(labo_id_raw).strip()
            entreprise_id_str = str(entreprise_id_raw).strip() if not pd.isna(entreprise_id_raw) else ""
            if labo_id_str in mapping:
                st.warning(f"Ligne {idx}: ID labo '{labo_id_str}' déjà présent. Valeur précédente conservée.")
                continue
            mapping[labo_id_str] = entreprise_id_str
        st.info(f"Mapping construit avec {len(mapping)} entrées.")
        return mapping

class ProductProcessor:
    """
    Applique le mapping labo->entreprise à un DataFrame de produits.
    """
    def __init__(self, dataframe: pd.DataFrame, product_id_col: str, entreprise_col: str, labo_id_col: str):
        self.dataframe = dataframe
        self.product_id_col = product_id_col
        self.entreprise_col = entreprise_col
        self.labo_id_col = labo_id_col

    def process(self, mapping: dict) -> pd.DataFrame:
        df = self.dataframe.copy()
        def map_entreprise(labo_value):
            if pd.isna(labo_value):
                return None
            labo_id_str = str(labo_value).strip()
            if labo_id_str in mapping:
                return mapping[labo_id_str]
            else:
                st.error(f"Mapping non trouvé pour l'ID labo: '{labo_id_str}'")
                return None
        df[self.entreprise_col] = df[self.labo_id_col].apply(map_entreprise)
        return df
