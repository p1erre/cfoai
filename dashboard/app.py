import streamlit as st
import pandas as pd

from data import (
    load_ventas,
    load_costos,
    filtrar,
    metricas_comparativas,
    calcular_concentracion,
    concentracion_marcas,
    clientes_en_riesgo,
    nuevos_vs_recurrentes_mensual,
    forecast_lineal,
    generar_insights,
    margen_mensual,
    margen_por_producto,
    margen_por_marca,
    margen_mensual_por_marca,
)
from charts import (
    ventas_mensuales,
    ventas_por_trimestre,
    top_productos,
    pareto_productos,
    top_clientes,
    heatmap_cliente_mes,
    gauge_concentracion,
    nuevos_vs_recurrentes_chart,
    forecast_chart,
    marca_donut,
    top_marcas,
    marca_tendencia_mensual,
    margen_mensual_chart,
    margen_por_marca_chart,
    margen_por_producto_chart,
    tendencia_margen_marcas_chart,
)

st.set_page_config(
    page_title="CFO Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
h1, h2, h3, h4 { color: #1a1a2e !important; }

/* Sidebar branding */
[data-testid="stSidebar"] { background-color: #f8f9fb; }

/* Insight cards */
.insight-success { background:#d5f5e3; border-left:4px solid #27ae60;
    padding:10px 14px; border-radius:4px; margin-bottom:8px; color:#1a1a2e; }
.insight-info    { background:#d6eaf8; border-left:4px solid #2e86ab;
    padding:10px 14px; border-radius:4px; margin-bottom:8px; color:#1a1a2e; }
.insight-warning { background:#fef9e7; border-left:4px solid #f39c12;
    padding:10px 14px; border-radius:4px; margin-bottom:8px; color:#1a1a2e; }
.insight-error   { background:#fdf2f2; border-left:4px solid #e74c3c;
    padding:10px 14px; border-radius:4px; margin-bottom:8px; color:#1a1a2e; }
</style>
""", unsafe_allow_html=True)

# ── Datos ─────────────────────────────────────────────────────────────────────
ventas = load_ventas()
costos = load_costos()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 CFO Dashboard")
    st.caption("Inteligencia financiera para tu negocio")
    st.divider()

    st.markdown("**Filtros**")
    fecha_min = ventas["Fecha"].min().date()
    fecha_max = ventas["Fecha"].max().date()
    fecha_inicio, fecha_fin = st.date_input(
        "Período",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

    categorias_disp = sorted(ventas["Categoría"].dropna().unique())
    categorias_sel = st.multiselect("Categoría", categorias_disp, default=categorias_disp)

    st.divider()
    pagina = st.radio(
        "Vista",
        ["Resumen Ejecutivo", "Rentabilidad", "Salud Financiera", "Marcas", "Productos", "Clientes"],
        index=0,
    )
    st.divider()
    st.caption(f"Datos: {fecha_min.strftime('%d %b %Y')} → {fecha_max.strftime('%d %b %Y')}")

df = filtrar(ventas, fecha_inicio, fecha_fin, categorias_sel)

# Filtrar costos por fecha
mask_costos = (costos["Fecha"] >= pd.Timestamp(fecha_inicio)) & (costos["Fecha"] <= pd.Timestamp(fecha_fin))
df_costos = costos[mask_costos]

# Métricas calculadas sobre datos filtrados
deltas     = metricas_comparativas(df)
conc       = calcular_concentracion(df)
conc_marca = concentracion_marcas(df)
insights   = generar_insights(df, conc, deltas)


def fmt_delta(val):
    if val is None:
        return None
    return f"{val:+.1f}%"

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Resumen Ejecutivo
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "Resumen Ejecutivo":
    st.title("Resumen Ejecutivo")

    if deltas.get("mes_actual_label"):
        st.caption(f"Último mes con datos: **{deltas['mes_actual_label']}** · comparado con {deltas.get('mes_anterior_label', '—')}")

    total_venta = df["Venta"].sum()
    n_facturas  = df["Comprobante"].nunique()
    n_clientes  = df["Nombre tercero"].nunique()
    ticket_prom = df.groupby("Comprobante")["Venta"].sum().mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venta Total",       f"${total_venta:,.0f}", delta=fmt_delta(deltas.get("delta_venta")))
    c2.metric("Facturas",          f"{n_facturas:,}",      delta=fmt_delta(deltas.get("delta_facturas")))
    c3.metric("Clientes Activos",  f"{n_clientes:,}",      delta=fmt_delta(deltas.get("delta_clientes")))
    c4.metric("Ticket Promedio",   f"${ticket_prom:,.0f}", delta=fmt_delta(deltas.get("delta_ticket")))

    # ── Insights automáticos ─────────────────────────────────────────────────
    if insights:
        st.divider()
        with st.expander("💡 Insights del período", expanded=True):
            for tipo, texto in insights:
                st.markdown(
                    f'<div class="insight-{tipo}">{texto}</div>',
                    unsafe_allow_html=True,
                )

    st.divider()

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("Ventas Mensuales")
        st.plotly_chart(ventas_mensuales(df), width="stretch")
    with col_r:
        st.subheader("Ventas por Trimestre")
        st.plotly_chart(ventas_por_trimestre(df), width="stretch")

    col_prod, col_marca = st.columns([3, 2])
    with col_prod:
        st.subheader("Top 10 Productos por Ingreso")
        st.plotly_chart(top_productos(df, 10), width="stretch")
    with col_marca:
        st.subheader("Participación por Marca")
        st.plotly_chart(marca_donut(df), width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — Rentabilidad
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Rentabilidad":
    st.title("Rentabilidad")
    st.caption("Ganancia bruta porcentual por mes, producto y marca.")

    # Cálculos de margen
    df_margen_mes = margen_mensual(df, df_costos)
    df_margen_prod = margen_por_producto(df, df_costos)
    df_margen_marca = margen_por_marca(df, df_costos)

    # KPIs
    total_venta_r = df_margen_mes["Venta"].sum()
    total_costo_r = df_margen_mes["Costo"].sum()
    ganancia_bruta = total_venta_r - total_costo_r
    margen_global = (ganancia_bruta / total_venta_r * 100) if total_venta_r > 0 else 0

    # Marca más/menos rentable (solo marcas con venta > 1% del total)
    marcas_sig = df_margen_marca[df_margen_marca["Venta"] > total_venta_r * 0.01]
    marca_mas = marcas_sig.loc[marcas_sig["Margen_Pct"].idxmax()] if not marcas_sig.empty else None
    marca_menos = marcas_sig.loc[marcas_sig["Margen_Pct"].idxmin()] if not marcas_sig.empty else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Margen Bruto %", f"{margen_global:.1f}%")
    c2.metric("Ganancia Bruta", f"${ganancia_bruta:,.0f}")
    c3.metric(
        "Marca Más Rentable",
        f"{marca_mas['Marca']}" if marca_mas is not None else "—",
        delta=f"{marca_mas['Margen_Pct']:.1f}%" if marca_mas is not None else None,
    )
    c4.metric(
        "Marca Menos Rentable",
        f"{marca_menos['Marca']}" if marca_menos is not None else "—",
        delta=f"{marca_menos['Margen_Pct']:.1f}%" if marca_menos is not None else None,
        delta_color="inverse",
    )

    # Margen mensual
    st.divider()
    st.subheader("Margen Bruto Mensual")
    st.plotly_chart(margen_mensual_chart(df_margen_mes), width="stretch")

    # Marcas: margen + tendencia
    st.divider()
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("Top 15 Marcas por Margen %")
        st.plotly_chart(margen_por_marca_chart(df_margen_marca, 15), width="stretch")
    with col_r:
        st.subheader("Tendencia Margen % — Top 5 Marcas")
        df_tend = margen_mensual_por_marca(df, df_costos, top_n=5)
        st.plotly_chart(tendencia_margen_marcas_chart(df_tend), width="stretch")

    # Productos por margen
    st.divider()
    st.subheader("Top 20 Productos por Margen %")
    st.plotly_chart(margen_por_producto_chart(df_margen_prod, 20), width="stretch")

    # Tablas detalladas
    st.divider()
    with st.expander("📋 Detalle por Marca", expanded=False):
        tabla_m = df_margen_marca.copy()
        tabla_m["Venta"] = tabla_m["Venta"].map("${:,.0f}".format)
        tabla_m["Costo"] = tabla_m["Costo"].map("${:,.0f}".format)
        tabla_m["Ganancia_Bruta"] = tabla_m["Ganancia_Bruta"].map("${:,.0f}".format)
        tabla_m["Margen_Pct"] = tabla_m["Margen_Pct"].map("{:.1f}%".format)
        st.dataframe(tabla_m, width="stretch", height=400)

    with st.expander("📋 Detalle por Producto", expanded=False):
        tabla_p = df_margen_prod.copy()
        tabla_p["Venta"] = tabla_p["Venta"].map("${:,.0f}".format)
        tabla_p["Costo"] = tabla_p["Costo"].map("${:,.0f}".format)
        tabla_p["Ganancia_Bruta"] = tabla_p["Ganancia_Bruta"].map("${:,.0f}".format)
        tabla_p["Margen_Pct"] = tabla_p["Margen_Pct"].map("{:.1f}%".format)
        st.dataframe(
            tabla_p[["Código producto", "Nombre producto", "Marca", "Venta", "Costo", "Ganancia_Bruta", "Margen_Pct"]],
            width="stretch", height=400,
        )

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Salud Financiera
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Salud Financiera":
    st.title("Salud Financiera")
    st.caption("Concentración de riesgo, retención de clientes y proyección de ingresos.")

    # ── Concentración de riesgo ───────────────────────────────────────────────
    st.subheader("Concentración de Riesgo")
    st.markdown(
        "Un negocio saludable no depende de pocos clientes ni de pocos productos. "
        "Valores por encima del 60% representan riesgo operativo significativo."
    )

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(
            gauge_concentracion(conc.get("top1_cliente_pct", 0), "Top 1 Cliente"),
            width="stretch",
        )
    with g2:
        st.plotly_chart(
            gauge_concentracion(conc.get("top3_clientes_pct", 0), "Top 3 Clientes"),
            width="stretch",
        )
    with g3:
        st.plotly_chart(
            gauge_concentracion(conc.get("top1_producto_pct", 0), "Top 1 Producto"),
            width="stretch",
        )
    with g4:
        st.plotly_chart(
            gauge_concentracion(conc_marca.get("top3_marcas_pct", 0), "Top 3 Marcas"),
            width="stretch",
        )

    # ── Retención de clientes ─────────────────────────────────────────────────
    st.divider()
    st.subheader("Retención de Clientes")
    col_ret, col_riesgo = st.columns([3, 2])

    with col_ret:
        ret_df = nuevos_vs_recurrentes_mensual(df)
        st.caption("Nuevos: primera compra en ese mes · Recurrentes: clientes que ya habían comprado antes")
        st.plotly_chart(nuevos_vs_recurrentes_chart(ret_df), width="stretch")

    with col_riesgo:
        st.markdown("**Clientes en riesgo de fuga**")
        st.caption("Sin compras en los últimos 60 días")
        riesgo_df = clientes_en_riesgo(df, dias=60)
        if riesgo_df.empty:
            st.success("Sin clientes en riesgo en el período seleccionado.")
        else:
            riesgo_df["Ultima_Compra"] = riesgo_df["Ultima_Compra"].dt.strftime("%d %b %Y")
            riesgo_df["Venta_Total"]   = riesgo_df["Venta_Total"].map("${:,.0f}".format)
            st.dataframe(
                riesgo_df[["Nombre tercero", "Ultima_Compra", "Dias_Sin_Compra", "Venta_Total", "N_Facturas"]],
                width="stretch",
                height=350,
            )

    # ── Proyección de ingresos ────────────────────────────────────────────────
    st.divider()
    st.subheader("Proyección de Ingresos (3 meses)")
    st.caption("Proyección basada en la tendencia lineal del período seleccionado. Referencial — no considera estacionalidad.")

    fc_df = forecast_lineal(df, meses_ahead=3)
    st.plotly_chart(forecast_chart(df, fc_df), width="stretch")

    if not fc_df.empty:
        total_proyectado = fc_df["Venta"].sum()
        fp1, fp2, fp3 = st.columns(3)
        for col, row in zip([fp1, fp2, fp3], fc_df.itertuples()):
            col.metric(
                pd.Timestamp(row.Mes_periodo).strftime("%b %Y"),
                f"${row.Venta:,.0f}",
            )

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Marcas
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Marcas":
    st.title("Análisis por Marca")

    n_marcas = conc_marca.get("n_marcas", 0)
    top1_marca = conc_marca.get("top1_marca", "—")
    top1_marca_pct = conc_marca.get("top1_marca_pct", 0)
    top3_marcas_pct = conc_marca.get("top3_marcas_pct", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Marcas Activas", f"{n_marcas:,}")
    c2.metric("Marca #1", top1_marca)
    c3.metric("% Ingreso Top 1", f"{top1_marca_pct:.1f}%")
    c4.metric("% Ingreso Top 3", f"{top3_marcas_pct:.1f}%")

    if top3_marcas_pct > 60:
        st.warning(
            f"Las top 3 marcas concentran el **{top3_marcas_pct:.0f}%** del ingreso. "
            "Alta dependencia de proveedores — evaluar alternativas y poder de negociación.",
            icon="⚠️",
        )

    st.divider()

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("Top 15 Marcas por Ingreso")
        st.plotly_chart(top_marcas(df, 15), width="stretch")
    with col_r:
        st.subheader("Participación de Marcas")
        st.plotly_chart(marca_donut(df), width="stretch")

    st.divider()
    st.subheader("Tendencia Mensual — Top 5 Marcas")
    st.caption("Evolución de las 5 marcas con mayor ingreso en el período.")
    st.plotly_chart(marca_tendencia_mensual(df, 5), width="stretch")

    st.divider()
    st.subheader("Detalle por Marca")
    tabla_marca = (
        df.groupby("Marca")
        .agg(
            Productos=("Código producto", "nunique"),
            Cantidad=("Cantidad", "sum"),
            Venta=("Venta", "sum"),
            Facturas=("Comprobante", "nunique"),
            Clientes=("Nombre tercero", "nunique"),
        )
        .sort_values("Venta", ascending=False)
        .reset_index()
    )
    tabla_marca["% Ingreso"] = (tabla_marca["Venta"] / tabla_marca["Venta"].sum() * 100).round(1)
    tabla_marca["Venta"] = tabla_marca["Venta"].map("${:,.0f}".format)
    st.dataframe(tabla_marca, width="stretch", height=400)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — Productos
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Productos":
    st.title("Análisis de Productos")

    n_prods   = df["Código producto"].nunique()
    top1_prod = df.groupby("Descripción")["Venta"].sum().idxmax()
    top1_pct  = df.groupby("Descripción")["Venta"].sum().max() / df["Venta"].sum() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("SKUs Vendidos",   f"{n_prods:,}")
    c2.metric("Producto #1",     top1_prod[:40])
    c3.metric("% Ingreso Top 1", f"{top1_pct:.1f}%")

    if conc:
        st.info(
            f"**{conc['n80_productos']} de {conc['n_productos']} SKUs** "
            f"({round(conc['n80_productos']/conc['n_productos']*100)}% del catálogo) "
            f"generan el **80% del ingreso**.",
            icon="📦",
        )

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
        df.groupby(["Código producto", "Descripción", "Marca"])
        .agg(Cantidad=("Cantidad", "sum"), Venta=("Venta", "sum"), Facturas=("Comprobante", "nunique"))
        .sort_values("Venta", ascending=False)
        .reset_index()
    )
    tabla["Venta"] = tabla["Venta"].map("${:,.0f}".format)
    st.dataframe(tabla, width="stretch", height=400)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — Clientes
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "Clientes":
    st.title("Análisis de Clientes")

    n_cl        = df["Nombre tercero"].nunique()
    top1_cl     = df.groupby("Nombre tercero")["Venta"].sum().idxmax()
    top1_cl_pct = df.groupby("Nombre tercero")["Venta"].sum().max() / df["Venta"].sum() * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes Activos", f"{n_cl:,}", delta=fmt_delta(deltas.get("delta_clientes")) if deltas else None)
    c2.metric("Cliente #1",       top1_cl[:40])
    c3.metric("% Ingreso Top 1",  f"{top1_cl_pct:.1f}%")

    if conc and conc["top3_clientes_pct"] > 50:
        st.warning(
            f"Top 3 clientes representan el **{conc['top3_clientes_pct']:.0f}%** del ingreso. "
            "Considera estrategias de diversificación. Ver análisis completo en **Salud Financiera**.",
            icon="⚠️",
        )

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
