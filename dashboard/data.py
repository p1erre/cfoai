import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data01"


@st.cache_data
def load_ventas() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "ventas.csv", parse_dates=["Fecha"])
    df["Mes_periodo"] = df["Fecha"].dt.to_period("M").dt.to_timestamp()
    return df


@st.cache_data
def load_productos() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "productos.csv")


def filtrar(df: pd.DataFrame, fecha_inicio, fecha_fin, categorias) -> pd.DataFrame:
    mask = (df["Fecha"] >= pd.Timestamp(fecha_inicio)) & (df["Fecha"] <= pd.Timestamp(fecha_fin))
    if categorias:
        mask &= df["Categoría"].isin(categorias)
    return df[mask]
