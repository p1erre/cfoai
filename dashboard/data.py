import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


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


def metricas_comparativas(df: pd.DataFrame) -> dict:
    """Compara el mes más reciente con el anterior para calcular deltas MoM."""
    if df.empty:
        return {}

    meses = sorted(df["Mes_periodo"].unique())
    if len(meses) < 2:
        return {}

    mes_act = meses[-1]
    mes_ant = meses[-2]

    df_act = df[df["Mes_periodo"] == mes_act]
    df_ant = df[df["Mes_periodo"] == mes_ant]

    def pct(a, b):
        return round((a - b) / b * 100, 1) if b else None

    v_act = df_act["Venta"].sum()
    v_ant = df_ant["Venta"].sum()
    cl_act = df_act["Nombre tercero"].nunique()
    cl_ant = df_ant["Nombre tercero"].nunique()
    tk_act = df_act.groupby("Comprobante")["Venta"].sum().mean() if not df_act.empty else 0
    tk_ant = df_ant.groupby("Comprobante")["Venta"].sum().mean() if not df_ant.empty else 0
    fc_act = df_act["Comprobante"].nunique()
    fc_ant = df_ant["Comprobante"].nunique()

    return {
        "mes_actual_label": pd.Timestamp(mes_act).strftime("%b %Y"),
        "mes_anterior_label": pd.Timestamp(mes_ant).strftime("%b %Y"),
        "delta_venta": pct(v_act, v_ant),
        "delta_clientes": pct(cl_act, cl_ant),
        "delta_ticket": pct(tk_act, tk_ant),
        "delta_facturas": pct(fc_act, fc_ant),
    }


def calcular_concentracion(df: pd.DataFrame) -> dict:
    """Métricas de concentración de riesgo en clientes y productos."""
    if df.empty:
        return {}

    total = df["Venta"].sum()
    v_cl = df.groupby("Nombre tercero")["Venta"].sum().sort_values(ascending=False)
    v_prod = df.groupby("Descripción")["Venta"].sum().sort_values(ascending=False)

    top1_cl_pct = v_cl.iloc[0] / total * 100 if len(v_cl) > 0 else 0
    top3_cl_pct = v_cl.head(3).sum() / total * 100 if len(v_cl) >= 3 else v_cl.sum() / total * 100
    top1_prod_pct = v_prod.iloc[0] / total * 100 if len(v_prod) > 0 else 0

    cum = v_prod.cumsum() / total * 100
    n80 = int((cum <= 80).sum()) + 1

    return {
        "top1_cliente_pct": round(top1_cl_pct, 1),
        "top3_clientes_pct": round(top3_cl_pct, 1),
        "top1_producto_pct": round(top1_prod_pct, 1),
        "n80_productos": n80,
        "n_clientes": len(v_cl),
        "n_productos": len(v_prod),
    }


def clientes_en_riesgo(df: pd.DataFrame, dias: int = 60) -> pd.DataFrame:
    """Clientes cuya última compra supera `dias` días desde el máximo del dataset."""
    if df.empty:
        return pd.DataFrame()

    fecha_ref = df["Fecha"].max()
    ultima = (
        df.groupby("Nombre tercero")
        .agg(
            Ultima_Compra=("Fecha", "max"),
            Venta_Total=("Venta", "sum"),
            N_Facturas=("Comprobante", "nunique"),
        )
        .reset_index()
    )
    ultima["Dias_Sin_Compra"] = (fecha_ref - ultima["Ultima_Compra"]).dt.days
    return (
        ultima[ultima["Dias_Sin_Compra"] > dias]
        .sort_values("Venta_Total", ascending=False)
        .reset_index(drop=True)
    )


def nuevos_vs_recurrentes_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """Por mes, clasifica cada cliente como Nuevo (primera compra) o Recurrente."""
    if df.empty:
        return pd.DataFrame()

    primera = df.groupby("Nombre tercero")["Mes_periodo"].min().rename("Primer_Mes")
    mes_cl = df.groupby(["Mes_periodo", "Nombre tercero"])["Venta"].sum().reset_index()
    mes_cl = mes_cl.merge(primera, on="Nombre tercero")
    mes_cl["Tipo"] = mes_cl.apply(
        lambda r: "Nuevo" if r["Mes_periodo"] == r["Primer_Mes"] else "Recurrente",
        axis=1,
    )
    result = (
        mes_cl.groupby(["Mes_periodo", "Tipo"])["Nombre tercero"]
        .nunique()
        .reset_index()
        .rename(columns={"Nombre tercero": "Clientes"})
    )
    return result


def forecast_lineal(df: pd.DataFrame, meses_ahead: int = 3) -> pd.DataFrame:
    """Proyección lineal de ventas para los próximos N meses."""
    mensual = df.groupby("Mes_periodo")["Venta"].sum().reset_index().sort_values("Mes_periodo")
    if len(mensual) < 3:
        return pd.DataFrame()

    x = np.arange(len(mensual))
    y = mensual["Venta"].values
    coef = np.polyfit(x, y, 1)

    ultimo_mes = mensual["Mes_periodo"].max()
    futuros = [ultimo_mes + pd.DateOffset(months=i + 1) for i in range(meses_ahead)]
    x_fut = np.arange(len(mensual), len(mensual) + meses_ahead)
    y_fut = np.polyval(coef, x_fut).clip(min=0)

    return pd.DataFrame({"Mes_periodo": futuros, "Venta": y_fut})


def concentracion_marcas(df: pd.DataFrame) -> dict:
    """Métricas de concentración por marca."""
    if df.empty or "Marca" not in df.columns:
        return {}
    total = df["Venta"].sum()
    v_marca = df.groupby("Marca")["Venta"].sum().sort_values(ascending=False)
    top1 = v_marca.iloc[0] / total * 100 if len(v_marca) > 0 else 0
    top3 = v_marca.head(3).sum() / total * 100 if len(v_marca) >= 3 else v_marca.sum() / total * 100
    return {
        "top1_marca": v_marca.index[0] if len(v_marca) > 0 else "",
        "top1_marca_pct": round(top1, 1),
        "top3_marcas_pct": round(top3, 1),
        "n_marcas": len(v_marca),
    }


def generar_insights(df: pd.DataFrame, conc: dict, deltas: dict) -> list:
    """Genera lista de insights automáticos basados en los datos."""
    insights = []
    if df.empty:
        return insights

    # Tendencia de ventas
    if deltas:
        vd = deltas.get("delta_venta")
        if vd is not None:
            mes = deltas.get("mes_actual_label", "")
            if vd >= 10:
                insights.append(("success", f"Ventas de {mes} crecieron **{vd:+.1f}%** vs mes anterior — momentum positivo."))
            elif vd >= 0:
                insights.append(("info", f"Ventas de {mes} estables: **{vd:+.1f}%** vs mes anterior."))
            elif vd >= -10:
                insights.append(("warning", f"Ventas de {mes} bajaron **{vd:.1f}%** vs mes anterior — monitorear."))
            else:
                insights.append(("error", f"Caída significativa en ventas de {mes}: **{vd:.1f}%** vs mes anterior."))

    if conc:
        # Concentración de clientes
        t3 = conc["top3_clientes_pct"]
        if t3 > 60:
            insights.append(("error", f"Riesgo alto: top 3 clientes concentran **{t3:.0f}%** del ingreso. Diversificar cartera es prioritario."))
        elif t3 > 40:
            insights.append(("warning", f"Concentración moderada: top 3 clientes representan **{t3:.0f}%** del ingreso."))
        else:
            insights.append(("success", f"Cartera de clientes saludable: top 3 clientes representan solo **{t3:.0f}%** del ingreso."))

        # Concentración de productos
        n80 = conc["n80_productos"]
        n_total = conc["n_productos"]
        pct_sku = round(n80 / n_total * 100) if n_total > 0 else 0
        if pct_sku < 20:
            insights.append(("success", f"Eficiencia de portafolio: {n80} SKUs ({pct_sku}% del catálogo) generan el 80% del ingreso."))
        else:
            insights.append(("info", f"Pareto de productos: {n80} de {n_total} SKUs ({pct_sku}%) generan el 80% del ingreso."))

        # Ticket promedio
        if deltas and deltas.get("delta_ticket") is not None:
            td = deltas["delta_ticket"]
            if td > 5:
                insights.append(("success", f"Ticket promedio subió **{td:+.1f}%** — señal positiva de mix o precios."))
            elif td < -5:
                insights.append(("warning", f"Ticket promedio bajó **{td:.1f}%** — revisar mezcla de ventas y política de descuentos."))

    return insights
