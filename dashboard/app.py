import streamlit as st
import pandas as pd

from data import load_ventas, filtrar
from charts import (
    ventas_mensuales,
    ventas_por_trimestre,
    top_productos,
    pareto_productos,
    top_clientes,
    heatmap_cliente_mes,
)

st.set_page_config(
    page_title="Dashboard CFO",
    page_icon="📊",
    layout="wide",
)

# ── Datos ─────────────────────────────────────────────────────────────────────
ventas = load_ventas()

# ── Sidebar — filtros globales ─────────────────────────────────────────────────
with st.sidebar:
    st.title("Filtros")

    fecha_min = ventas["Fecha"].min().date()
    fecha_max = ventas["Fecha"].max().date()
    fecha_inicio, fecha_fin = st.date_input(
        "Período",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

    categorias_disp = sorted(ventas["Categoría"].dropna().unique())
    categorias_sel = st.multiselect(
        "Categoría", categorias_disp, default=categorias_disp
    )

df = filtrar(ventas, fecha_inicio, fecha_fin, categorias_sel)

# ── Navegación ─────────────────────────────────────────────────────────────────
pagina = st.sidebar.radio(
    "Vista",
    ["Resumen Ejecutivo", "Productos", "Clientes"],
    index=0,
)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Resumen Ejecutivo
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "Resumen Ejecutivo":
    st.title("Resumen Ejecutivo")

    total_venta    = df["Venta"].sum()
    n_facturas     = df["Comprobante"].nunique()
    n_clientes     = df["Nombre tercero"].nunique()
    ticket_prom    = df.groupby("Comprobante")["Venta"].sum().mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venta Total",        f"${total_venta:,.0f}")
    c2.metric("Facturas",           f"{n_facturas:,}")
    c3.metric("Clientes Activos",   f"{n_clientes:,}")
    c4.metric("Ticket Promedio",    f"${ticket_prom:,.0f}")

    st.divider()

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("Ventas Mensuales")
        st.plotly_chart(ventas_mensuales(df), width="stretch")
    with col_r:
        st.subheader("Ventas por Trimestre")
        st.plotly_chart(ventas_por_trimestre(df), width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — Productos
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Productos":
    st.title("Análisis de Productos")

    n_prods   = df["Código producto"].nunique()
    top1_prod = df.groupby("Descripción")["Venta"].sum().idxmax()
    top1_pct  = df.groupby("Descripción")["Venta"].sum().max() / df["Venta"].sum() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Productos Vendidos", f"{n_prods:,}")
    c2.metric("Producto #1",        top1_prod[:40])
    c3.metric("% Ingreso Top 1",    f"{top1_pct:.1f}%")

    st.divider()

    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("Top 20 Productos por Ingreso")
        st.plotly_chart(top_productos(df, 20), width="stretch")
    with col_r:
        st.subheader("Concentración de Ventas (Pareto)")
        st.plotly_chart(pareto_productos(df), width="stretch")

    st.divider()
    st.subheader("Detalle por Producto")
    tabla = (
        df.groupby(["Código producto", "Descripción", "Categoría"])
        .agg(Cantidad=("Cantidad", "sum"), Venta=("Venta", "sum"), Facturas=("Comprobante", "nunique"))
        .sort_values("Venta", ascending=False)
        .reset_index()
    )
    tabla["Venta"] = tabla["Venta"].map("${:,.0f}".format)
    st.dataframe(tabla, width="stretch", height=400)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Clientes
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Clientes":
    st.title("Análisis de Clientes")

    n_cl    = df["Nombre tercero"].nunique()
    top1_cl = df.groupby("Nombre tercero")["Venta"].sum().idxmax()
    top1_cl_pct = df.groupby("Nombre tercero")["Venta"].sum().max() / df["Venta"].sum() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes Activos",  f"{n_cl:,}")
    c2.metric("Cliente #1",        top1_cl[:40])
    c3.metric("% Ingreso Top 1",   f"{top1_cl_pct:.1f}%")

    st.divider()

    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("Top 20 Clientes por Ingreso")
        st.plotly_chart(top_clientes(df, 20), width="stretch")
    with col_r:
        st.subheader("Estacionalidad por Cliente (Top 15)")
        st.plotly_chart(heatmap_cliente_mes(df, 15), width="stretch")

    st.divider()
    st.subheader("Detalle por Cliente")
    tabla_cl = (
        df.groupby(["Identificación", "Nombre tercero"])
        .agg(Facturas=("Comprobante", "nunique"), Venta=("Venta", "sum"))
        .sort_values("Venta", ascending=False)
        .reset_index()
    )
    tabla_cl["Venta"] = tabla_cl["Venta"].map("${:,.0f}".format)
    st.dataframe(tabla_cl, width="stretch", height=400)
