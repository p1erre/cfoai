import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

PALETTE  = px.colors.qualitative.Set2
PRIMARY  = "#1f4e79"
ACCENT   = "#2e86ab"
TEXT     = "#1a1a2e"
SUBTEXT  = "#4a4a6a"
GREEN    = "#27ae60"
ORANGE   = "#f39c12"
RED      = "#e74c3c"


def _base_layout(**kwargs) -> dict:
    """Layout base con texto legible aplicado a todos los gráficos."""
    base = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=TEXT, family="Inter, Arial, sans-serif", size=12),
        xaxis=dict(
            tickfont=dict(color=TEXT),
            title_font=dict(color=TEXT),
            linecolor="#cccccc",
            gridcolor="#eeeeee",
        ),
        yaxis=dict(
            tickfont=dict(color=TEXT),
            title_font=dict(color=TEXT),
            linecolor="#cccccc",
            gridcolor="#eeeeee",
        ),
        legend=dict(font=dict(color=TEXT)),
        margin=dict(t=10, b=10),
    )
    for k, v in kwargs.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base


def kpi_card(label: str, value: str, delta: str = None):
    return {"label": label, "value": value, "delta": delta}


def ventas_mensuales(df: pd.DataFrame) -> go.Figure:
    """Barras mensuales con línea de tendencia."""
    import numpy as np

    mes = df.groupby("Mes_periodo")["Venta"].sum().reset_index()
    fig = go.Figure()
    fig.add_bar(
        x=mes["Mes_periodo"], y=mes["Venta"],
        name="Venta mensual", marker_color=ACCENT, opacity=0.85,
        hovertemplate="<b>%{x|%b %Y}</b><br>$%{y:,.0f}<extra></extra>",
    )
    if len(mes) >= 3:
        x = np.arange(len(mes))
        coef = np.polyfit(x, mes["Venta"].values, 1)
        trend = np.polyval(coef, x)
        fig.add_scatter(
            x=mes["Mes_periodo"], y=trend,
            name="Tendencia", mode="lines",
            line=dict(color=RED, width=2, dash="dot"),
            hovertemplate="%{x|%b %Y}<br>Tendencia: $%{y:,.0f}<extra></extra>",
        )
    fig.update_layout(**_base_layout(
        xaxis=dict(tickformat="%b %Y"),
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=30, b=10),
    ))
    return fig


def ventas_por_trimestre(df: pd.DataFrame) -> go.Figure:
    trim = df.groupby(["Año", "Trimestre"])["Venta"].sum().reset_index()
    trim["label"] = trim.apply(lambda r: f"Q{r['Trimestre']} {r['Año']}", axis=1)
    fig = px.bar(
        trim, x="label", y="Venta",
        labels={"label": "", "Venta": "Venta ($)"},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>")
    fig.update_layout(**_base_layout(
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
    ))
    return fig


def top_productos(df: pd.DataFrame, n: int = 20) -> go.Figure:
    top = (
        df.groupby(["Código producto", "Descripción"])["Venta"]
        .sum().reset_index()
        .sort_values("Venta", ascending=False)
        .head(n)
    )
    top["label"] = top["Descripción"].str[:45]
    fig = px.bar(
        top, x="Venta", y="label", orientation="h",
        labels={"Venta": "Venta ($)", "label": ""},
        color_discrete_sequence=[ACCENT],
    )
    fig.update_traces(hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>")
    fig.update_layout(**_base_layout(
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        yaxis=dict(autorange="reversed"),
        height=500,
    ))
    return fig


def pareto_productos(df: pd.DataFrame) -> go.Figure:
    vpp = (
        df.groupby("Código producto")["Venta"]
        .sum().sort_values(ascending=False).reset_index()
    )
    vpp["cum_pct"] = vpp["Venta"].cumsum() / vpp["Venta"].sum() * 100
    n80 = int((vpp["cum_pct"] <= 80).sum())

    fig = go.Figure()
    fig.add_bar(x=list(range(len(vpp))), y=vpp["Venta"], name="Venta", marker_color=ACCENT, opacity=0.7)
    fig.add_scatter(
        x=list(range(len(vpp))), y=vpp["cum_pct"],
        name="% acumulado", yaxis="y2",
        line=dict(color=RED, width=2),
    )
    fig.add_hline(y=80, yref="y2", line_dash="dash", line_color="gray", opacity=0.6)
    fig.add_annotation(
        x=n80, y=80, yref="y2",
        text=f"80% en {n80} productos",
        showarrow=True, arrowhead=2, arrowcolor=RED,
        font=dict(color=RED, size=11),
    )
    fig.update_layout(**_base_layout(
        xaxis=dict(title=dict(text="Productos (orden descendente de venta)", font=dict(color=TEXT))),
        yaxis=dict(title=dict(text="Venta ($)", font=dict(color=TEXT)), tickprefix="$", tickformat=",.0f"),
        yaxis2=dict(
            title=dict(text="% acumulado", font=dict(color=TEXT)),
            overlaying="y", side="right", range=[0, 105],
            tickfont=dict(color=TEXT),
        ),
        legend=dict(orientation="h", y=1.05, font=dict(color=TEXT)),
        margin=dict(t=30, b=10),
    ))
    return fig


def top_clientes(df: pd.DataFrame, n: int = 20) -> go.Figure:
    top = (
        df.groupby("Nombre tercero")["Venta"]
        .sum().reset_index()
        .sort_values("Venta", ascending=False)
        .head(n)
    )
    top["label"] = top["Nombre tercero"].str[:40]
    fig = px.bar(
        top, x="Venta", y="label", orientation="h",
        labels={"Venta": "Venta ($)", "label": ""},
        color_discrete_sequence=[GREEN],
    )
    fig.update_traces(hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>")
    fig.update_layout(**_base_layout(
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        yaxis=dict(autorange="reversed"),
        height=500,
    ))
    return fig


def heatmap_cliente_mes(df: pd.DataFrame, n_clientes: int = 15) -> go.Figure:
    top_cl = (
        df.groupby("Nombre tercero")["Venta"].sum()
        .nlargest(n_clientes).index.tolist()
    )
    sub = df[df["Nombre tercero"].isin(top_cl)].copy()
    pivot = (
        sub.groupby(["Nombre tercero", "Mes"])["Venta"].sum()
        .unstack(fill_value=0)
    )
    pivot = pivot[sorted(pivot.columns)]
    mes_labels = [pd.Timestamp(2025, m, 1).strftime("%b") for m in sorted(pivot.columns)]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=mes_labels,
        y=[n[:35] for n in pivot.index],
        colorscale="Blues",
        hovertemplate="<b>%{y}</b><br>%{x}<br>$%{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        xaxis=dict(title=""),
        yaxis=dict(autorange="reversed"),
        height=max(350, n_clientes * 30),
    ))
    return fig


# ── Nuevos gráficos para Salud Financiera ─────────────────────────────────────

def gauge_concentracion(valor: float, titulo: str) -> go.Figure:
    """Gauge de concentración de riesgo. Verde <30%, Amarillo 30-60%, Rojo >60%."""
    if valor < 30:
        color, nivel = GREEN, "Riesgo bajo"
    elif valor < 60:
        color, nivel = ORANGE, "Riesgo moderado"
    else:
        color, nivel = RED, "Riesgo alto"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number=dict(suffix="%", font=dict(color=TEXT, size=28)),
        title=dict(
            text=f"{titulo}<br><span style='font-size:0.85em;color:{color}'>{nivel}</span>",
            font=dict(color=TEXT, size=13),
        ),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(color=SUBTEXT), tickcolor=SUBTEXT),
            bar=dict(color=color),
            steps=[
                dict(range=[0, 30], color="#d5f5e3"),
                dict(range=[30, 60], color="#fef9e7"),
                dict(range=[60, 100], color="#fdf2f2"),
            ],
            threshold=dict(line=dict(color=RED, width=2), thickness=0.75, value=60),
        ),
    ))
    fig.update_layout(**_base_layout(height=230, margin=dict(t=40, b=10, l=20, r=20)))
    return fig


def nuevos_vs_recurrentes_chart(ret_df: pd.DataFrame) -> go.Figure:
    """Barras apiladas: clientes nuevos vs recurrentes por mes."""
    if ret_df.empty:
        return go.Figure()

    colores = {"Nuevo": GREEN, "Recurrente": ACCENT}
    fig = go.Figure()
    for tipo in ["Recurrente", "Nuevo"]:
        sub = ret_df[ret_df["Tipo"] == tipo]
        if sub.empty:
            continue
        fig.add_bar(
            x=sub["Mes_periodo"], y=sub["Clientes"],
            name=tipo, marker_color=colores.get(tipo, ACCENT),
            hovertemplate=f"<b>%{{x|%b %Y}}</b><br>{tipo}: %{{y}} clientes<extra></extra>",
        )
    fig.update_layout(**_base_layout(
        barmode="stack",
        xaxis=dict(tickformat="%b %Y"),
        yaxis=dict(title="Clientes"),
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=30, b=10),
    ))
    return fig


def forecast_chart(df: pd.DataFrame, forecast_df: pd.DataFrame) -> go.Figure:
    """Ventas históricas (últimos 6 meses) + proyección lineal."""
    mensual = (
        df.groupby("Mes_periodo")["Venta"].sum()
        .reset_index().sort_values("Mes_periodo")
        .tail(9)
    )
    fig = go.Figure()
    fig.add_bar(
        x=mensual["Mes_periodo"], y=mensual["Venta"],
        name="Histórico", marker_color=ACCENT, opacity=0.85,
        hovertemplate="<b>%{x|%b %Y}</b><br>$%{y:,.0f}<extra></extra>",
    )
    if not forecast_df.empty:
        fig.add_bar(
            x=forecast_df["Mes_periodo"], y=forecast_df["Venta"],
            name="Proyección (tendencia lineal)", marker_color=ORANGE, opacity=0.75,
            hovertemplate="<b>%{x|%b %Y}</b><br>Proyección: $%{y:,.0f}<extra></extra>",
        )
    fig.update_layout(**_base_layout(
        xaxis=dict(tickformat="%b %Y"),
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
        legend=dict(orientation="h", y=1.08),
        margin=dict(t=30, b=10),
        barmode="group",
    ))
    return fig


def venta_por_categoria_donut(df: pd.DataFrame) -> go.Figure:
    """Donut de participación de ingresos por categoría."""
    cat = df.groupby("Categoría")["Venta"].sum().reset_index().sort_values("Venta", ascending=False)
    fig = go.Figure(go.Pie(
        labels=cat["Categoría"],
        values=cat["Venta"],
        hole=0.5,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
        marker=dict(colors=PALETTE),
    ))
    fig.update_layout(**_base_layout(
        showlegend=False,
        height=280,
        margin=dict(t=10, b=10, l=10, r=10),
    ))
    return fig
