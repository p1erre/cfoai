import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

PALETTE = px.colors.qualitative.Set2
PRIMARY = "#1f4e79"
ACCENT  = "#2e86ab"


def kpi_card(label: str, value: str, delta: str = None):
    return {"label": label, "value": value, "delta": delta}


def ventas_mensuales(df: pd.DataFrame) -> go.Figure:
    mes = df.groupby("Mes_periodo")["Venta"].sum().reset_index()
    fig = px.bar(
        mes, x="Mes_periodo", y="Venta",
        labels={"Mes_periodo": "", "Venta": "Venta ($)"},
        color_discrete_sequence=[ACCENT],
    )
    fig.update_traces(hovertemplate="<b>%{x|%b %Y}</b><br>$%{y:,.0f}<extra></extra>")
    fig.update_layout(
        xaxis=dict(tickformat="%b %Y"),
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10),
    )
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
    fig.update_layout(
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10),
    )
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
    fig.update_layout(
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10),
        height=500,
    )
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
        line=dict(color="#e74c3c", width=2),
    )
    fig.add_hline(y=80, yref="y2", line_dash="dash", line_color="gray", opacity=0.6)
    fig.add_annotation(
        x=n80, y=80, yref="y2",
        text=f"80% en {n80} productos",
        showarrow=True, arrowhead=2, arrowcolor="#e74c3c",
        font=dict(color="#e74c3c", size=11),
    )
    fig.update_layout(
        xaxis=dict(title="Productos (orden descendente de venta)"),
        yaxis=dict(title="Venta ($)", tickprefix="$", tickformat=",.0f"),
        yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 105]),
        legend=dict(orientation="h", y=1.05),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=30, b=10),
    )
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
        color_discrete_sequence=["#27ae60"],
    )
    fig.update_traces(hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>")
    fig.update_layout(
        xaxis=dict(tickprefix="$", tickformat=",.0f"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10),
        height=500,
    )
    return fig


def heatmap_cliente_mes(df: pd.DataFrame, n_clientes: int = 15) -> go.Figure:
    top_cl = (
        df.groupby("Nombre tercero")["Venta"].sum()
        .nlargest(n_clientes).index.tolist()
    )
    sub = df[df["Nombre tercero"].isin(top_cl)].copy()
    sub["Mes_label"] = sub["Fecha"].dt.strftime("%b")
    pivot = (
        sub.groupby(["Nombre tercero", "Mes"])["Venta"].sum()
        .unstack(fill_value=0)
    )
    # Ordenar meses
    pivot = pivot[sorted(pivot.columns)]
    mes_labels = [pd.Timestamp(2025, m, 1).strftime("%b") for m in sorted(pivot.columns)]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=mes_labels,
        y=[n[:35] for n in pivot.index],
        colorscale="Blues",
        hovertemplate="<b>%{y}</b><br>%{x}<br>$%{z:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=10, b=10),
        height=max(350, n_clientes * 30),
    )
    return fig
