from pathlib import Path
import json
import ast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="StudentIQ | Performance Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
METRICS_FILE = ARTIFACTS / "model_metrics.json"
PREDICTIONS_DIR = ARTIFACTS / "test_predictions_csv"

CLASS_LABELS = ["Pass", "Withdrawn", "Fail", "Distinction"]
CLASS_COLORS = {
    "Pass": "#38BDF8",
    "Withdrawn": "#FBBF24",
    "Fail": "#FB7185",
    "Distinction": "#A78BFA",
}

# ------------------------------------------------------------
# Premium dark theme
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #080B12;
        --panel: #101622;
        --panel-2: #141D2B;
        --line: rgba(148,163,184,.14);
        --muted: #8D9AAF;
        --text: #F1F5F9;
        --cyan: #38BDF8;
        --violet: #9B8AFB;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg);
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid="stHeader"] { background: rgba(8,11,18,.88); }
    [data-testid="stToolbar"] { right: 1rem; }
    [data-testid="stSidebar"] {
        background: #0D121D;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
    [data-testid="stMainBlockContainer"] {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }
    h1, h2, h3, h4 { font-family: 'Manrope', sans-serif !important; color: #F8FAFC !important; }
    p, label, span, div { }
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #141D2B, #101622);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 17px 19px;
        box-shadow: 0 10px 28px rgba(0,0,0,.14);
    }
    [data-testid="stMetricLabel"] { color: #9AA8BC !important; font-size: .82rem; }
    [data-testid="stMetricValue"] { color: #F8FAFC !important; font-family: 'Manrope',sans-serif; }
    [data-testid="stMetricDelta"] { font-size: .78rem; }
    .brand {
        display:flex; align-items:center; gap:11px;
        padding: 8px 4px 22px 4px;
    }
    .brand-icon {
        width:42px;height:42px;border-radius:13px;
        display:flex;align-items:center;justify-content:center;
        background:linear-gradient(135deg,#38BDF8,#7C3AED);
        color:white;font-size:21px;font-weight:800;
        box-shadow:0 8px 25px rgba(56,189,248,.22);
    }
    .brand-name {font:800 19px 'Manrope',sans-serif;color:#F8FAFC;letter-spacing:-.5px;}
    .brand-sub {font-size:10px;color:#8290A5;letter-spacing:1.7px;text-transform:uppercase;margin-top:1px;}
    .topline {
        display:flex;justify-content:space-between;align-items:center;
        border-bottom:1px solid var(--line);padding:0 0 17px 0;margin-bottom:25px;
    }
    .eyebrow {color:#38BDF8;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;}
    .page-title {font:800 28px 'Manrope',sans-serif;color:#F8FAFC;margin:3px 0 0 0;}
    .page-subtitle {color:#8D9AAF;font-size:13px;margin-top:5px;}
    .status-pill {
        display:inline-flex;align-items:center;gap:7px;padding:7px 11px;
        border:1px solid rgba(56,189,248,.22);border-radius:30px;
        color:#9BDCF8;background:rgba(56,189,248,.08);font-size:11px;font-weight:600;
    }
    .status-dot {width:7px;height:7px;border-radius:50%;background:#34D399;box-shadow:0 0 10px #34D399;}
    .section-head {font:700 16px 'Manrope',sans-serif;color:#E8EEF7;margin:18px 0 4px;}
    .section-hint {color:#8492A7;font-size:12px;margin-bottom:13px;}
    .panel {
        background:linear-gradient(145deg,#121A28,#0F1622);
        border:1px solid var(--line);border-radius:17px;padding:18px 20px;
    }
    .mini-label {color:#8D9AAF;font-size:11px;text-transform:uppercase;letter-spacing:1.2px;font-weight:700;}
    .big-number {font:800 27px 'Manrope',sans-serif;color:#F8FAFC;margin-top:5px;}
    .muted {color:#8D9AAF;font-size:12px;}
    .risk-card {
        border:1px solid rgba(251,113,133,.25);
        background:linear-gradient(135deg,rgba(251,113,133,.11),rgba(20,29,43,.8));
        border-radius:15px;padding:16px 18px;
    }
    .good-card {
        border:1px solid rgba(52,211,153,.22);
        background:linear-gradient(135deg,rgba(52,211,153,.09),rgba(20,29,43,.8));
        border-radius:15px;padding:16px 18px;
    }
    div[data-testid="stSelectbox"] > label, div[data-testid="stMultiSelect"] > label {
        color:#A9B6C9 !important;
    }
    .stButton button, .stDownloadButton button {
        border-radius:10px;border:1px solid rgba(56,189,248,.3);
        background:rgba(56,189,248,.10);color:#BDEBFF;font-weight:600;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        border-color:#38BDF8;color:white;background:rgba(56,189,248,.18);
    }
    [data-testid="stDataFrame"] {border:1px solid var(--line);border-radius:12px;overflow:hidden;}
    hr {border-color:var(--line);}
    footer {visibility:hidden;}
    #MainMenu {visibility:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Data loading
# ------------------------------------------------------------
@st.cache_data
def load_metrics():
    if not METRICS_FILE.exists():
        return {}
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_predictions():
    if not PREDICTIONS_DIR.exists():
        return pd.DataFrame()
    files = list(PREDICTIONS_DIR.glob("part-*.csv"))
    if not files:
        files = list(PREDICTIONS_DIR.glob("*.csv"))
    if not files:
        return pd.DataFrame()
    frames = [pd.read_csv(file) for file in files]
    df = pd.concat(frames, ignore_index=True)
    required = {"final_result", "prediction"}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    df["prediction"] = pd.to_numeric(df["prediction"], errors="coerce")
    df = df.dropna(subset=["prediction"]).copy()
    df["prediction"] = df["prediction"].astype(int)
    df["Actual"] = df["final_result"].astype(str)
    df["Predicted"] = df["prediction"].map(
        {i: label for i, label in enumerate(CLASS_LABELS)}
    )
    df = df.dropna(subset=["Predicted"])
    if "probability" in df.columns:
        def confidence(value):
            try:
                probs = json.loads(value) if isinstance(value, str) else value
                if isinstance(probs, str):
                    probs = ast.literal_eval(probs)
                return max(float(x) for x in probs)
            except (ValueError, TypeError, SyntaxError, json.JSONDecodeError):
                return None
        df["Confidence"] = df["probability"].apply(confidence)
    else:
        df["Confidence"] = None
    df["Confidence %"] = (pd.to_numeric(df["Confidence"], errors="coerce") * 100).round(1)
    df["Status"] = (df["Actual"] == df["Predicted"]).map(
        {True: "Correct", False: "Incorrect"}
    )
    return df


metrics = load_metrics()
predictions = load_predictions()

# ------------------------------------------------------------
# Sidebar navigation
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-icon">S</div>
          <div><div class="brand-name">StudentIQ</div>
          <div class="brand-sub">Performance intelligence</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="mini-label">WORKSPACE</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["Overview", "Predictions", "Model performance", "Individual assessment", "About project"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown('<div class="mini-label">PROJECT STATUS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="display:flex;align-items:center;gap:8px;margin-top:12px;color:#B7C3D4;font-size:12px;">'
        '<span class="status-dot"></span> Local model artifacts loaded</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="margin-top:18px;color:#64748B;font-size:11px;line-height:1.6;">'
        'OULAD · Big Data Analytics<br>Research decision-support prototype</div>',
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
page_meta = {
    "Overview": ("OVERVIEW", "Student performance at a glance"),
    "Predictions": ("PREDICTION EXPLORER", "Explore model predictions and outcomes"),
    "Model performance": ("MODEL ANALYTICS", "Compare machine-learning model performance"),
    "Individual assessment": ("STUDENT ASSESSMENT", "Manage individual student records, marks and support plans"),
    "About project": ("PROJECT INFORMATION", "Methodology, scope and responsible use"),
}
eyebrow, subtitle = page_meta[page]
st.markdown(
    f"""
    <div class="topline">
      <div>
        <div class="eyebrow">{eyebrow}</div>
        <div class="page-title">{page}</div>
        <div class="page-subtitle">{subtitle}</div>
      </div>
      <div class="status-pill"><span class="status-dot"></span> MODEL READY</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def get_model_rows(data):
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("models") or data.get("results") or data.get("metrics") or []
        if isinstance(rows, dict):
            rows = [{"Algorithm": k, **v} for k, v in rows.items() if isinstance(v, dict)]
    else:
        rows = []
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized.append({
            "Algorithm": row.get("Algorithm", row.get("model", row.get("name", "Model"))),
            "Weighted F1": row.get("weighted_f1", row.get("weightedF1", row.get("f1", None))),
            "Accuracy": row.get("accuracy", row.get("Accuracy", None)),
        })
    return pd.DataFrame(normalized)


def chart_layout(fig, height=320):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#AAB7CA", family="DM Sans"),
        margin=dict(l=8, r=8, t=28, b=8),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(gridcolor="rgba(148,163,184,.10)", zerolinecolor="rgba(148,163,184,.10)"),
        yaxis=dict(gridcolor="rgba(148,163,184,.10)", zerolinecolor="rgba(148,163,184,.10)"),
    )
    return fig


def section(title, hint=None):
    st.markdown(f'<div class="section-head">{title}</div>', unsafe_allow_html=True)
    if hint:
        st.markdown(f'<div class="section-hint">{hint}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------
# Overview page
# ------------------------------------------------------------
if page == "Overview":
    if predictions.empty:
        st.warning("Prediction data was not found. Check that artifacts/test_predictions_csv contains Spark part CSV files.")
    else:
        total = len(predictions)
        accuracy = (predictions["Status"] == "Correct").mean()
        avg_conf = predictions["Confidence %"].mean()
        risk_count = predictions["Predicted"].isin(["Fail", "Withdrawn"]).sum()
        pass_count = (predictions["Predicted"] == "Pass").sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TEST RECORDS", f"{total:,}", help="Number of rows in the saved test predictions.")
        m2.metric("TEST ACCURACY", f"{accuracy:.1%}", help="Share of test predictions matching the actual class.")
        m3.metric("AVERAGE MODEL SCORE", f"{avg_conf:.1f}%" if pd.notna(avg_conf) else "N/A",
                  help="Mean maximum class probability; not necessarily calibrated.")
        m4.metric("FAIL / WITHDRAWN FLAGS", f"{risk_count:,}",
                  help="Predictions labelled Fail or Withdrawn; not confirmed at-risk students.")

        st.markdown("")
        left, right = st.columns([1.35, 1])
        with left:
            section("Actual vs predicted outcomes", "Compare the distribution of true outcomes with the model's predicted outcomes.")
            actual = predictions["Actual"].value_counts().reindex(CLASS_LABELS, fill_value=0)
            predicted = predictions["Predicted"].value_counts().reindex(CLASS_LABELS, fill_value=0)
            dist = pd.DataFrame({"Outcome": CLASS_LABELS, "Actual": actual.values, "Predicted": predicted.values})
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Actual", x=dist["Outcome"], y=dist["Actual"], marker_color="#64748B"))
            fig.add_trace(go.Bar(name="Predicted", x=dist["Outcome"], y=dist["Predicted"],
                                 marker_color=[CLASS_COLORS[x] for x in CLASS_LABELS]))
            fig.update_layout(barmode="group", xaxis_title="", yaxis_title="Students")
            st.plotly_chart(chart_layout(fig, 350), use_container_width=True)
        with right:
            section("Prediction mix", "Share of model-assigned outcome categories.")
            counts = predictions["Predicted"].value_counts().reindex(CLASS_LABELS, fill_value=0)
            fig = px.pie(
                names=counts.index, values=counts.values, hole=.68,
                color=counts.index, color_discrete_map=CLASS_COLORS,
            )
            fig.update_traces(textposition="outside", textinfo="percent", marker=dict(line=dict(color="#101622", width=3)))
            fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-.12))
            st.plotly_chart(chart_layout(fig, 350), use_container_width=True)

        section("Prediction quality", "How often did the model's predicted class match the known test outcome?")
        c1, c2 = st.columns([1, 1])
        with c1:
            correct = int((predictions["Status"] == "Correct").sum())
            incorrect = total - correct
            fig = go.Figure(go.Pie(
                labels=["Correct", "Incorrect"], values=[correct, incorrect], hole=.76,
                marker=dict(colors=["#34D399", "#FB7185"], line=dict(color="#101622", width=3)),
                textinfo="none",
            ))
            fig.add_annotation(text=f"{accuracy:.1%}", x=.5, y=.53, showarrow=False,
                               font=dict(size=27, color="#F8FAFC", family="Manrope"))
            fig.add_annotation(text="accuracy", x=.5, y=.40, showarrow=False,
                               font=dict(size=11, color="#8D9AAF"))
            st.plotly_chart(chart_layout(fig, 270), use_container_width=True)
        with c2:
            st.markdown(
                f"""
                <div class="{'risk-card' if risk_count else 'good-card'}" style="margin-top:14px;">
                  <div class="mini-label">MODEL-IDENTIFIED FAIL / WITHDRAWN</div>
                  <div class="big-number">{risk_count:,}</div>
                  <div class="muted">of {total:,} test records ({risk_count/total:.1%})</div>
                  <p class="muted" style="margin-top:12px;">These are model predictions for research review, not verified student outcomes or automatic intervention decisions.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        section("Recent prediction sample", "A small preview of the saved test-set predictions.")
        display_cols = ["Actual", "Predicted", "Confidence %", "Status"]
        st.dataframe(predictions[display_cols].head(8), use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# Predictions page
# ------------------------------------------------------------
elif page == "Predictions":
    if predictions.empty:
        st.warning("No prediction CSV data found. Check artifacts/test_predictions_csv.")
    else:
        section("Filter prediction records", "Narrow the test-set records by predicted outcome and correctness.")
        f1, f2, f3 = st.columns([1, 1, 1])
        with f1:
            selected_results = st.multiselect("Predicted outcome", CLASS_LABELS, default=CLASS_LABELS)
        with f2:
            selected_status = st.multiselect("Prediction status", ["Correct", "Incorrect"], default=["Correct", "Incorrect"])
        with f3:
            min_conf = st.slider("Minimum score (%)", 0, 100, 0, 5)

        filtered = predictions[
            predictions["Predicted"].isin(selected_results)
            & predictions["Status"].isin(selected_status)
            & (predictions["Confidence %"].fillna(0) >= min_conf)
        ].copy()

        a, b, c = st.columns(3)
        a.metric("MATCHING RECORDS", f"{len(filtered):,}")
        b.metric("CORRECT IN FILTER", f"{(filtered['Status'] == 'Correct').sum():,}")
        bval = (filtered["Status"] == "Correct").mean() if len(filtered) else 0
        c.metric("FILTER ACCURACY", f"{bval:.1%}" if len(filtered) else "N/A")

        section("Prediction records", f"Showing {len(filtered):,} matching rows. The exported data contains no student identifier.")
        display = filtered[["Actual", "Predicted", "Confidence %", "Status"]].copy()
        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Confidence %": st.column_config.ProgressColumn("Model score", min_value=0, max_value=100, format="%.1f%%"),
            },
        )
        st.download_button(
            "↓  Download filtered predictions (CSV)",
            data=display.to_csv(index=False).encode("utf-8"),
            file_name="student_performance_predictions.csv",
            mime="text/csv",
        )

# ------------------------------------------------------------
# Model performance page
# ------------------------------------------------------------
elif page == "Model performance":
    model_table = get_model_rows(metrics)
    if model_table.empty:
        st.warning("Could not read model comparison rows from artifacts/model_metrics.json.")
        st.caption("Open model_metrics.json to confirm its structure.")
        st.json(metrics)
    else:
        for col in ["Weighted F1", "Accuracy"]:
            model_table[col] = pd.to_numeric(model_table[col], errors="coerce")
        section("Algorithm comparison", "Metrics reported by the training pipeline.")
        st.dataframe(
            model_table.style.format({"Weighted F1": "{:.2%}", "Accuracy": "{:.2%}"}),
            use_container_width=True,
            hide_index=True,
        )
        chart_data = model_table.melt(
            id_vars="Algorithm", value_vars=["Weighted F1", "Accuracy"],
            var_name="Metric", value_name="Score",
        )
        fig = px.bar(
            chart_data, x="Algorithm", y="Score", color="Metric", barmode="group",
            text=chart_data["Score"].map(lambda x: f"{x:.1%}" if pd.notna(x) else ""),
            color_discrete_map={"Weighted F1": "#38BDF8", "Accuracy": "#A78BFA"},
        )
        fig.update_traces(textposition="outside")
        fig.update_yaxes(range=[0, 1], tickformat=".0%")
        st.plotly_chart(chart_layout(fig, 390), use_container_width=True)

        best_f1 = model_table.loc[model_table["Weighted F1"].idxmax()] if model_table["Weighted F1"].notna().any() else None
        best_acc = model_table.loc[model_table["Accuracy"].idxmax()] if model_table["Accuracy"].notna().any() else None
        x1, x2 = st.columns(2)
        if best_f1 is not None:
            x1.metric("BEST WEIGHTED F1", str(best_f1["Algorithm"]), f"{best_f1['Weighted F1']:.2%}")
        if best_acc is not None:
            x2.metric("BEST ACCURACY", str(best_acc["Algorithm"]), f"{best_acc['Accuracy']:.2%}")
        st.info("Weighted F1 balances precision and recall across classes. Accuracy is the overall share of correct predictions. Compare both, especially when class sizes differ.")

# ------------------------------------------------------------
# About page
# ------------------------------------------------------------
elif page == "About project":
    section("Project overview", "An academic prototype for analysing student performance using the Open University Learning Analytics Dataset.")
    st.markdown(
        """
        <div class="panel">
          <div class="eyebrow">RESEARCH PROJECT</div>
          <h3 style="margin-top:8px;">Intelligent Student Performance Prediction and Early Warning System</h3>
          <p style="color:#AAB7CA;line-height:1.8;">The system uses historical student, assessment, registration and virtual learning environment activity data to build machine-learning models that predict the final course outcome.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        section("Data and target")
        st.markdown("""
        - **Dataset:** Open University Learning Analytics Dataset (OULAD)
        - **Prediction target:** Pass, Withdrawn, Fail or Distinction
        - **Pipeline:** Feature engineering, model training and test-set evaluation
        - **Algorithms:** Logistic Regression, Decision Tree and Random Forest
        """)
    with c2:
        section("Responsible interpretation")
        st.markdown("""
        - Predictions are indicators for research and review, not facts about a student's future.
        - Model probability scores may not be calibrated confidence values.
        - Human review and additional context are essential before any support decision.
        - Avoid using the system as the sole basis for high-impact academic decisions.
        """)
    st.warning("This dashboard is a research decision-support prototype. It should not be used to label, penalize or make consequential decisions about individual students.")
    st.caption("Built with Python, PySpark, Streamlit, pandas and Plotly.")


# ------------------------------------------------------------
# Individual student assessment module
# ------------------------------------------------------------
else:
    from assessment.ui import render_assessment
    render_assessment()
