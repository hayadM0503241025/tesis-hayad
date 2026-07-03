import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import html
import networkx as nx
from community import community_louvain
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px

# =========================================================
# 1. KONFIGURASI TEMA & UI DDP (WHITE SIDEBAR STANDARD)
# =========================================================
LOGO_PATH = os.path.join("assets", "logo-banner2.png")
DEFAULT_DATA_PATH = "data-hayad.xlsx"
HEADER_PATH = next(
    (
        p
        for p in [
            os.path.join("assets", "header.png"),
            os.path.join("assets", "header.jpg"),
            os.path.join("assets", "header.jpeg"),
        ]
        if os.path.exists(p)
    ),
    None,
)
FRAME_PATH = os.path.join("assets", "frame.png") if os.path.exists(os.path.join("assets", "frame.png")) else None

# Jika file logo ada di assets, pakai itu. Jika tidak, pakai icon default sementara.
if os.path.exists(LOGO_PATH):
    page_icon = LOGO_PATH
else:
    page_icon = "SNA"


def get_image_data_uri(path):
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg" if ext in {".jpg", ".jpeg"} else "application/octet-stream"
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def get_logo_data_uri(path):
    if not os.path.exists(path):
        return None
    return get_image_data_uri(path)

st.set_page_config(
    page_title="DDP Dashboard SNA",
    page_icon=page_icon,
    layout="wide"
)

DDP_BLUE = "#111827"
DDP_RED = "#B91C1C"
LIGHT_BG = "#EEF2F7"

# Skala warna kontras tinggi yang tetap layak untuk publikasi.
SATELLITE_COLORS = [[0, "#B91C1C"], [0.5, "#F59E0B"], [1, "#2563EB"]]
CONTRAST_COLORS = [
    "#1F77B4", "#D62728", "#2CA02C", "#9467BD", "#8C564B",
    "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF", "#FF7F0E",
    "#4C78A8", "#F58518", "#54A24B", "#B279A2", "#72B7B2",
    "#9D755D", "#EECA3B", "#E45756"
]
PLOTLY_DRAW_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToAdd": ["drawrect", "drawline", "drawopenpath", "drawclosedpath", "drawcircle", "eraseshape"],
}
BINARY_COLOR_MAP = {"YA": "#2563EB", "TIDAK": DDP_RED}
BANSOS_TARGETING_COLORS = {
    "Rendah - Penerima": "#0f766e",
    "Rendah - Belum Menerima": "#b91c1c",
    "Sedang - Penerima": "#14b8a6",
    "Sedang - Belum Menerima": "#f59e0b",
    "Tinggi - Penerima": "#2563eb",
    "Tinggi - Belum Menerima": "#64748b",
    "Sangat Tinggi - Penerima": "#7c3aed",
    "Sangat Tinggi - Belum Menerima": "#94a3b8",
    "Tidak Valid": "#cbd5e1",
}
BPS_CATEGORY_COLORS = {
    "Rendah": "#b91c1c",
    "Sedang": "#d97706",
    "Tinggi": "#0f766e",
    "Sangat Tinggi": "#2563eb",
}
BPS_CATEGORY_ORDER = ("Sangat Tinggi", "Tinggi", "Sedang", "Rendah")
BPS_FALLBACK_COLOR = "#94a3b8"
PLOT_TEXT_COLOR = "#111827"
PLOT_GRID_COLOR = "#E2E8F0"
PUBLICATION_TEMPLATE = "ddp_clarity"
PUBLICATION_FONT = '"Source Sans Pro", "Segoe UI", Arial, sans-serif'
PUBLICATION_CONTINUOUS_SCALE = [[0.0, "#B91C1C"], [0.5, "#F59E0B"], [1.0, "#0F766E"]]
NETWORK_EDGE_NEUTRAL = "rgba(71, 85, 105, 0.24)"
NETWORK_EDGE_FAINT = "rgba(148, 163, 184, 0.28)"
NETWORK_NODE_LINE = "#111827"
HEADER_DATA_URI = get_image_data_uri(HEADER_PATH)
FRAME_DATA_URI = get_image_data_uri(FRAME_PATH)
KPI_FRAME_STYLE = (
    f"""
        border: none;
        border-radius: 0;
        padding: 18px 12px 14px 12px;
        background-image: url('{FRAME_DATA_URI}');
        background-size: 100% 100%;
        background-repeat: no-repeat;
        background-position: center;
    """
    if FRAME_DATA_URI
    else """
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 18px;
        padding: 18px 14px;
    """
)


def render_global_header():
    if not HEADER_DATA_URI:
        return
    st.markdown(
        f"""
        <div class="global-header-wrap">
            <img src="{HEADER_DATA_URI}" class="global-header-img" alt="Dashboard Header"/>
        </div>
        """,
        unsafe_allow_html=True,
    )


def subbab_dropdown(title, expanded=False):
    return st.expander(title, expanded=expanded)


pio.templates["ddp_clarity"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=PLOT_TEXT_COLOR, size=13, family=PUBLICATION_FONT),
        title=dict(font=dict(color=PLOT_TEXT_COLOR, size=18, family=PUBLICATION_FONT), x=0.02, xanchor="left"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(color=PLOT_TEXT_COLOR),
        ),
        xaxis=dict(
            color=PLOT_TEXT_COLOR,
            gridcolor=PLOT_GRID_COLOR,
            zerolinecolor="#94a3b8",
            linecolor="#334155",
            ticks="outside",
        ),
        yaxis=dict(
            color=PLOT_TEXT_COLOR,
            gridcolor=PLOT_GRID_COLOR,
            zerolinecolor="#94a3b8",
            linecolor="#334155",
            ticks="outside",
        ),
        coloraxis=dict(
            colorbar=dict(
                tickfont=dict(color=PLOT_TEXT_COLOR),
                title=dict(font=dict(color=PLOT_TEXT_COLOR)),
            )
        ),
    )
)
pio.templates.default = PUBLICATION_TEMPLATE
pio.templates["plotly_white"] = pio.templates[PUBLICATION_TEMPLATE]


def style_publication_figure(
    fig,
    title=None,
    height=None,
    xaxis_title=None,
    yaxis_title=None,
    showlegend=None,
    legend_title=None,
    margin=None,
):
    layout_kwargs = {
        "template": PUBLICATION_TEMPLATE,
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#FFFFFF",
        "font": dict(color=PLOT_TEXT_COLOR, family=PUBLICATION_FONT, size=13),
        "hoverlabel": dict(bgcolor="#FFFFFF", font_size=12, font_family=PUBLICATION_FONT),
        "margin": margin or dict(l=48, r=24, t=72, b=48),
    }
    if title is not None:
        layout_kwargs["title"] = dict(text=title, x=0.02, xanchor="left")
    if height is not None:
        layout_kwargs["height"] = height
    if showlegend is not None:
        layout_kwargs["showlegend"] = showlegend
    if legend_title is not None:
        layout_kwargs["legend_title_text"] = legend_title
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(
        title_text=xaxis_title,
        showline=True,
        linewidth=1,
        linecolor="#CBD5E1",
        gridcolor=PLOT_GRID_COLOR,
        zerolinecolor="#CBD5E1",
        ticks="outside",
    )
    fig.update_yaxes(
        title_text=yaxis_title,
        showline=True,
        linewidth=1,
        linecolor="#CBD5E1",
        gridcolor=PLOT_GRID_COLOR,
        zerolinecolor="#CBD5E1",
        ticks="outside",
    )
    return fig


def style_network_figure(fig, title, height=540, showlegend=False):
    style_publication_figure(
        fig,
        title=title,
        height=height,
        showlegend=showlegend,
        margin=dict(l=16, r=16, t=72, b=16),
    )
    fig.update_xaxes(visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(visible=False, showgrid=False, zeroline=False)
    return fig


def ordered_existing_categories(values, preferred_order, invalid_label="Tidak Valid"):
    observed = pd.Series(values).dropna().astype(str).str.strip()
    observed = observed[(observed != "") & (observed != invalid_label)]
    present = set(observed.tolist())
    ordered = [cat for cat in preferred_order if cat in present]
    extras = sorted(present.difference(ordered))
    return ordered + extras

st.markdown(f"""
    <style>
    :root {{
        --surface: rgba(255, 255, 255, 0.88);
        --surface-strong: rgba(255, 255, 255, 0.96);
        --stroke: rgba(15, 23, 42, 0.12);
        --shadow: 0 18px 45px rgba(15, 23, 42, 0.10);
        --text-main: {DDP_BLUE};
        --accent: #2563EB;
    }}
    .stApp {{
        font-family: "SF Pro Display", "SF Pro Text", "Helvetica Neue", "Segoe UI", sans-serif;
        background:
            radial-gradient(1200px 460px at 5% -10%, rgba(37, 99, 235, 0.13) 0%, rgba(37, 99, 235, 0) 62%),
            radial-gradient(900px 420px at 98% 0%, rgba(15, 23, 42, 0.08) 0%, rgba(15, 23, 42, 0) 65%),
            linear-gradient(180deg, {LIGHT_BG} 0%, #F8FAFC 60%, #FFFFFF 100%);
    }}
    .main .block-container {{
        max-width: 1400px;
        padding-top: 1.1rem;
        padding-bottom: 1.6rem;
    }}
    .global-header-wrap {{
        width: 100%;
        border-radius: 0;
        overflow: hidden;
        margin: 0.1rem 0 1.0rem 0;
        border: 1px solid rgba(15, 23, 42, 0.10);
        box-shadow: 0 16px 40px rgba(15, 23, 42, 0.16);
        background: rgba(255,255,255,0.82);
    }}
    .global-header-img {{
        width: 100%;
        display: block;
        object-fit: cover;
    }}
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0F172A 0%, #111827 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.10);
    }}
    section[data-testid="stSidebar"] * {{
        color: #E5E7EB !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div,
    section[data-testid="stSidebar"] .stSlider {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
    }}
    .sidebar-logo-shell {{
        width: 62px;
        height: 62px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.42);
        background: linear-gradient(145deg, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0.06) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.24), 0 8px 20px rgba(2,6,23,0.34);
    }}
    .sidebar-logo-disc {{
        width: 48px;
        height: 48px;
        border-radius: 999px;
        background: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #E5E7EB;
        overflow: hidden;
    }}
    .sidebar-logo-img {{
        width: 36px;
        height: 36px;
        object-fit: contain;
        display: block;
    }}
    .sidebar-logo-fallback {{
        color: #111827 !important;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }}
    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] {{
        margin-top: 0.15rem;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background: rgba(148,163,184,0.14) !important;
        border: 1px solid rgba(255,255,255,0.28) !important;
        border-radius: 14px !important;
        padding: 0.75rem 0.7rem !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {{
        background: rgba(148,163,184,0.20) !important;
        border-color: rgba(255,255,255,0.42) !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small {{
        color: #E5E7EB !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] {{
        color: #F8FAFC !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
        background: rgba(255,255,255,0.10) !important;
        color: #F8FAFC !important;
        border: 1px solid rgba(255,255,255,0.26) !important;
        border-radius: 10px !important;
    }}
    .kpi-card {{
        {KPI_FRAME_STYLE}
        min-height: 132px;
        border-radius: 0;
        color: #F8FAFC;
        text-align: center;
        box-shadow: var(--shadow);
        margin-bottom: 14px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .kpi-card h3 {{
        margin: 0 0 6px 0;
        font-size: 1.7rem;
        line-height: 1.05;
        letter-spacing: 0.3px;
        font-weight: 700;
    }}
    .kpi-card p {{
        margin: 0;
        font-size: 0.82rem;
        letter-spacing: 0.4px;
        opacity: 0.96;
    }}
    .bg-ddp-blue {{
        background-color: #1E293B;
    }}
    .bg-ddp-red {{
        background-color: #991B1B;
    }}
    .main-header {{
        color: var(--text-main);
        font-family: "SF Pro Display", "Helvetica Neue", sans-serif;
        font-weight: 700;
        letter-spacing: 0.2px;
        border-bottom: 1px solid rgba(15, 23, 42, 0.16);
        padding-bottom: 10px;
        margin-bottom: 14px;
    }}
    .soft-card {{
        background: var(--surface);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--stroke);
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: var(--shadow);
    }}
    .premium-hero {{
        background:
            linear-gradient(130deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.92) 70%),
            radial-gradient(circle at 85% 20%, rgba(37, 99, 235, 0.35) 0%, rgba(37, 99, 235, 0) 52%);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 20px;
        color: #F8FAFC;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 16px 40px rgba(2, 6, 23, 0.30);
    }}
    .premium-hero b {{
        color: #FFFFFF;
    }}
    @media (max-width: 768px) {{
        .kpi-card {{ min-height: 116px; border-radius: 0; }}
        .main-header {{ font-size: 1.2rem; }}
        .stats-container {{ font-size: 12px; }}
    }}
    .stats-container {{
        background: var(--surface-strong);
        padding: 22px;
        border-radius: 14px;
        border: 1px solid var(--stroke);
        font-family: "SF Mono", "JetBrains Mono", "Consolas", monospace;
        color: #1F2937;
        line-height: 1.5;
        font-size: 14px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }}
    .explanation-pillar {{
        padding: 20px;
        border-radius: 14px;
        border: 1px solid var(--stroke);
        background: var(--surface-strong);
        min-height: 180px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        margin-bottom: 15px;
    }}
    div[data-testid="stPlotlyChart"] {{
        background: var(--surface-strong);
        border: 1px solid var(--stroke);
        border-radius: 16px;
        padding: 8px 10px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06) !important;
    }}
    .streamlit-expanderHeader {{
        background: var(--surface-strong);
        border-radius: 14px;
        border: 1px solid var(--stroke);
        padding: 0.2rem 0.4rem;
        font-weight: 700;
        color: var(--text-main);
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(15, 23, 42, 0.12);
        padding: 7px 14px;
    }}
    .stTabs [aria-selected="true"] {{
        background: #0F172A !important;
        color: #F8FAFC !important;
        border-color: #0F172A !important;
    }}
    div[data-testid="stMetric"] {{
        background: var(--surface);
        border: 1px solid var(--stroke);
        border-radius: 14px;
        padding: 10px 12px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

BUILDER_GRAPH_COLS = ("ipm_mikro", "dusun", "organisasi_num")
EDGE_REKAP_COLS = (
    "f_a_dari_rekap_kk",
    "f_b_dari_rekap_kk",
    "f_c_dari_rekap_kk",
    "f_d_dari_rekap_kk",
    "f_e_dari_rekap_kk",
)
IKD_DIMENSION_DISPLAY = {
    "f_a_dari_rekap_kk": "Sandang, Pangan, dan Papan",
    "f_b_dari_rekap_kk": "Pendidikan",
    "f_c_dari_rekap_kk": "Sosial, Hukum, dan HAM",
    "f_d_dari_rekap_kk": "Kesehatan dan Pekerjaan",
    "f_e_dari_rekap_kk": "Lingkungan dan Infrastruktur",
}
IKD_DIMENSION_MAP = (
    ("Sandang, Pangan, dan Papan", "f_a_dari_rekap_kk"),
    ("Pendidikan", "f_b_dari_rekap_kk"),
    ("Sosial, Hukum, dan HAM", "f_c_dari_rekap_kk"),
    ("Kesehatan dan Pekerjaan", "f_d_dari_rekap_kk"),
    ("Lingkungan dan Infrastruktur", "f_e_dari_rekap_kk"),
)
IKD_OVERALL_METRIC = ("IKD Agregat (Indeks Kesejahteraan Desa)", "f_ikr_dari_rekap_kk")
IKD_OVERALL_LABEL = "IKD Agregat"
PSEUDO_DIMENSION_COLS = tuple(IKD_DIMENSION_DISPLAY.values())


def format_dimension_source_label(col_name):
    if col_name == IKD_OVERALL_METRIC[1]:
        return "Skor IKD agregat"
    if col_name in IKD_DIMENSION_DISPLAY:
        return f"Skor dimensi {IKD_DIMENSION_DISPLAY[col_name]}"
    return str(col_name)


DRILLDOWN_DIMENSIONS = {
    "A": {
        "label": "Sandang, Pangan, dan Papan",
        "aggregate_col": "f_a_dari_rekap_kk",
        "variables": [
            {
                "code": "A1",
                "label": "Sandang",
                "description": "Seberapa sering keluarga membeli pakaian baru (indikator gaya hidup).",
                "candidates": ["a1_sandang", "a1", "f_a1", "f_a_1", "sandang"],
            },
            {
                "code": "A2",
                "label": "Pangan",
                "description": "Frekuensi makan dan gizi menu harian (indikator ketahanan pangan mikro).",
                "candidates": ["a2_pangan", "a2", "f_a2", "f_a_2", "pangan"],
            },
            {
                "code": "A3",
                "label": "Papan",
                "description": "Kualitas lantai, dinding, atap, dan sanitasi rumah (indikator aset fisik).",
                "candidates": ["a3_papan", "a3", "f_a3", "f_a_3", "papan"],
            },
        ],
    },
    "B": {
        "label": "Pendidikan",
        "aggregate_col": "f_b_dari_rekap_kk",
        "variables": [
            {
                "code": "B1",
                "label": "Lama Sekolah",
                "description": "Capaian ijazah KK (indikator modal intelektual).",
                "candidates": ["b1_lama_sekolah", "b1", "f_b1", "f_b_1", "lama_sekolah"],
            },
            {
                "code": "B2",
                "label": "Partisipasi Sekolah",
                "description": "Status sekolah anggota keluarga (indikator keberlanjutan pendidikan).",
                "candidates": ["b2_partisipasi", "b2", "f_b2", "f_b_2", "partisipasi_sekolah"],
            },
        ],
    },
    "C": {
        "label": "Sosial, Hukum, dan HAM",
        "aggregate_col": "f_c_dari_rekap_kk",
        "variables": [
            {
                "code": "C1",
                "label": "Kehidupan Sosial",
                "description": "Akses bansos dan partisipasi organisasi (indikator inklusi kebijakan).",
                "candidates": ["c1_kehidupan_sosial", "c1", "f_c1", "f_c_1", "kehidupan_sosial"],
            },
            {
                "code": "C2",
                "label": "Hukum dan HAM",
                "description": "Pengalaman kriminalitas dan bantuan hukum (indikator keamanan).",
                "candidates": ["c2_hukum_ham", "c2", "f_c2", "f_c_2", "hukum_ham"],
            },
        ],
    },
    "D": {
        "label": "Kesehatan dan Pekerjaan",
        "aggregate_col": "f_d_dari_rekap_kk",
        "variables": [
            {
                "code": "D1",
                "label": "Kesehatan",
                "description": "Riwayat penyakit berat dan disabilitas (indikator kerentanan fisik).",
                "candidates": ["d1_kesehatan", "d1", "f_d1", "f_d_1", "kesehatan"],
            },
            {
                "code": "D2",
                "label": "Pekerjaan",
                "description": "Status bekerja dan keterampilan (indikator produktivitas ekonomi).",
                "candidates": ["d2_pekerjaan", "d2", "f_d2", "f_d_2", "pekerjaan"],
            },
            {
                "code": "D3",
                "label": "Jaminan Sosial",
                "description": "Kepesertaan BPJS/JKN (indikator jaring pengaman).",
                "candidates": ["d3_jaminan_sosial", "d3", "f_d3", "f_d_3", "jaminan_sosial", "bpjs"],
            },
        ],
    },
    "E": {
        "label": "Lingkungan dan Infrastruktur",
        "aggregate_col": "f_e_dari_rekap_kk",
        "variables": [
            {
                "code": "E1",
                "label": "Lingkungan",
                "description": "Sumber air bersih dan pengelolaan sampah (indikator sanitasi lingkungan).",
                "candidates": ["e1_lingkungan", "e1", "f_e1", "f_e_1", "lingkungan"],
            },
            {
                "code": "E2",
                "label": "Infrastruktur",
                "description": "Akses listrik, ponsel, dan transportasi (indikator konektivitas digital).",
                "candidates": ["e2_infrastruktur", "e2", "f_e2", "f_e_2", "infrastruktur"],
            },
        ],
    },
}
def _normalize_text(val):
    return str(val).strip().lower() if pd.notnull(val) else ""


def to_binary_presence(val):
    v = _normalize_text(val)
    if v in {"0", "0.0", "tidak", "tidak ada", "none", "nan", ""}:
        return 0
    return 1


def to_binary_phone(val):
    v = _normalize_text(val)
    if v in {"ya", "yes", "1", "1.0", "true"}:
        return 1
    if v in {"tidak", "no", "0", "0.0", "false", "tidak ada", "none", "nan", ""}:
        return 0
    return 0


def _safe_float_metric(val, default=0.0):
    try:
        fval = float(val)
        return fval if np.isfinite(fval) else float(default)
    except Exception:
        return float(default)


def rgba_from_hex(color, alpha=0.28):
    color_text = str(color or "").strip()
    if color_text.startswith("rgba") or color_text.startswith("rgb"):
        return color_text
    if color_text.startswith("#") and len(color_text) in {4, 7}:
        if len(color_text) == 4:
            r = int(color_text[1] * 2, 16)
            g = int(color_text[2] * 2, 16)
            b = int(color_text[3] * 2, 16)
        else:
            r = int(color_text[1:3], 16)
            g = int(color_text[3:5], 16)
            b = int(color_text[5:7], 16)
        return f"rgba({r},{g},{b},{float(alpha):.3f})"
    return color_text or f"rgba(71,85,105,{float(alpha):.3f})"


def normalize_layout_positions(pos_dict, outer_quantile=0.88, clip_radius=1.35):
    if not pos_dict:
        return {}
    keys = list(pos_dict.keys())
    arr = np.array([pos_dict[k] for k in keys], dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        return {k: np.array([0.0, 0.0]) for k in keys}
    center = np.nanmedian(arr, axis=0)
    arr = np.nan_to_num(arr - center, nan=0.0, posinf=0.0, neginf=0.0)
    radii = np.sqrt((arr ** 2).sum(axis=1))
    valid_radii = radii[np.isfinite(radii) & (radii > 1e-9)]
    scale_ref = float(np.quantile(valid_radii, outer_quantile)) if len(valid_radii) else 1.0
    scale_ref = max(scale_ref, 1e-9)
    arr = arr / scale_ref
    radii = np.sqrt((arr ** 2).sum(axis=1))
    too_far = radii > clip_radius
    if np.any(too_far):
        arr[too_far] = arr[too_far] / radii[too_far, None] * clip_radius
    return {k: arr[idx] for idx, k in enumerate(keys)}


def build_clustered_network_layout(graph_obj, partition=None, layout_spread=2.0, seed=42):
    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        return {}
    nodes = list(graph_obj.nodes())
    if partition is None:
        partition = {n: graph_obj.nodes[n].get("cluster", 0) for n in nodes}
    cluster_nodes = {}
    for n in nodes:
        try:
            cid = int(partition.get(n, graph_obj.nodes[n].get("cluster", 0)))
        except (TypeError, ValueError):
            cid = 0
        cluster_nodes.setdefault(cid, []).append(n)

    cluster_ids = sorted(cluster_nodes)
    max_cluster_size = max(len(v) for v in cluster_nodes.values())
    spread = float(np.clip(layout_spread, 1.0, 3.4))

    cluster_graph = nx.Graph()
    for cid, c_nodes in cluster_nodes.items():
        cluster_graph.add_node(cid, size=len(c_nodes))
    for u, v, d in graph_obj.edges(data=True):
        cu = int(partition.get(u, graph_obj.nodes[u].get("cluster", 0)))
        cv = int(partition.get(v, graph_obj.nodes[v].get("cluster", 0)))
        if cu == cv:
            continue
        weight = _safe_float_metric(d.get("weight"), default=0.0)
        if cluster_graph.has_edge(cu, cv):
            cluster_graph[cu][cv]["weight"] += weight
        else:
            cluster_graph.add_edge(cu, cv, weight=weight)

    if len(cluster_ids) == 1:
        cluster_centers = {cluster_ids[0]: np.array([0.0, 0.0])}
    elif len(cluster_ids) == 2:
        cluster_centers = {
            cluster_ids[0]: np.array([-1.0, 0.0]),
            cluster_ids[1]: np.array([1.0, 0.0]),
        }
    else:
        cluster_centers = nx.circular_layout(cluster_graph, scale=1.0)

    pos_final = {}
    center_radius = 2.45 + (1.05 * spread)
    for idx, cid in enumerate(cluster_ids):
        c_nodes = cluster_nodes[cid]
        sub_g = graph_obj.subgraph(c_nodes).copy()
        if len(c_nodes) == 1:
            local_pos = {c_nodes[0]: np.array([0.0, 0.0])}
        elif len(c_nodes) <= 12:
            local_pos = nx.circular_layout(sub_g, scale=1.0)
        else:
            local_k = float(np.clip(5.0 / np.sqrt(len(c_nodes)), 0.38, 1.15))
            local_pos = nx.spring_layout(
                sub_g,
                seed=int(seed) + idx + 13,
                weight="weight",
                k=local_k,
                iterations=360,
                scale=1.0,
            )
        local_pos = normalize_layout_positions(local_pos, outer_quantile=0.86, clip_radius=1.42)
        size_ratio = np.sqrt(len(c_nodes) / max(max_cluster_size, 1))
        local_radius = (0.75 + (1.35 * size_ratio)) * (0.92 + (0.08 * spread))
        center = np.array(cluster_centers[cid], dtype=float) * center_radius
        for n in c_nodes:
            pos_final[n] = center + (np.array(local_pos.get(n, [0.0, 0.0]), dtype=float) * local_radius)

    return pos_final


def select_representative_edges(graph_obj, max_edges=900, per_node=1):
    if graph_obj is None or graph_obj.number_of_edges() == 0:
        return []
    all_edges = [
        (u, v, d, _safe_float_metric(d.get("weight"), default=0.0))
        for u, v, d in graph_obj.edges(data=True)
    ]
    limit = int(max(0, min(max_edges, len(all_edges))))
    if len(all_edges) <= limit:
        return [(u, v, d) for u, v, d, _ in sorted(all_edges, key=lambda x: x[3], reverse=True)]

    edge_lookup = {frozenset((u, v)): (u, v, d, w) for u, v, d, w in all_edges}
    selected_keys = set()
    if per_node > 0:
        for n in graph_obj.nodes():
            incident = [
                (frozenset((u, v)), w)
                for u, v, _, w in all_edges
                if u == n or v == n
            ]
            incident = sorted(incident, key=lambda x: x[1], reverse=True)[:per_node]
            for key, _ in incident:
                selected_keys.add(key)

    strongest = sorted(all_edges, key=lambda x: x[3], reverse=True)
    for u, v, _, _ in strongest:
        if len(selected_keys) >= limit:
            break
        selected_keys.add(frozenset((u, v)))

    selected = [edge_lookup[key] for key in selected_keys if key in edge_lookup]
    selected = sorted(selected, key=lambda x: x[3], reverse=True)[:limit]
    return [(u, v, d) for u, v, d, _ in selected]


def network_marker_size(n_nodes, base=8.0):
    n_nodes = int(max(n_nodes, 1))
    if n_nodes >= 700:
        return max(5.2, base - 3.0)
    if n_nodes >= 450:
        return max(5.8, base - 2.2)
    if n_nodes >= 250:
        return max(6.5, base - 1.3)
    return base


def centrality_marker_sizes(values, n_nodes):
    val_arr = np.asarray(values, dtype=float)
    if val_arr.size == 0:
        return []
    valid = val_arr[np.isfinite(val_arr)]
    if valid.size == 0:
        return [7.0 for _ in val_arr]
    lo = float(np.quantile(valid, 0.05))
    hi = float(np.quantile(valid, 0.95))
    if hi <= lo:
        lo = float(np.nanmin(valid))
        hi = float(np.nanmax(valid))
    denom = max(hi - lo, 1e-9)
    norm = np.clip((val_arr - lo) / denom, 0.0, 1.0)
    min_size = network_marker_size(n_nodes, base=7.2)
    max_size = min_size + (8.5 if n_nodes >= 350 else 12.0)
    return (min_size + ((max_size - min_size) * np.sqrt(norm))).tolist()


def add_network_edge_traces(
    fig,
    edge_items,
    pos,
    edge_min,
    edge_span,
    color_fn=None,
    base_width=0.32,
    width_scale=0.95,
    hover=False,
):
    for u, v, d in edge_items:
        if u not in pos or v not in pos:
            continue
        w = _safe_float_metric(d.get("weight"), default=0.0)
        w_norm = float(np.clip((w - edge_min) / max(edge_span, 1e-9), 0.0, 1.0))
        if color_fn:
            try:
                edge_color = color_fn(u, v, d, w_norm)
            except TypeError:
                edge_color = color_fn(u, v)
        else:
            edge_color = NETWORK_EDGE_NEUTRAL
        edge_width = base_width + (width_scale * w_norm)
        fig.add_trace(
            go.Scatter(
                x=[pos[u][0], pos[v][0], None],
                y=[pos[u][1], pos[v][1], None],
                mode="lines",
                line=dict(width=edge_width, color=edge_color),
                hovertemplate=f"Interaksi: {w:.4f}<extra></extra>" if hover else None,
                hoverinfo="text" if hover else "none",
                showlegend=False,
            )
        )


def resolve_basis_column(df_in, preferred_col):
    if preferred_col in df_in.columns:
        return preferred_col
    numeric_candidates = []
    for c in df_in.columns:
        if c in {"family_id", "cluster", "bansos_num", "digital_num", "organisasi_num"}:
            continue
        s = pd.to_numeric(df_in[c], errors="coerce")
        if s.notna().sum() >= max(3, int(0.2 * len(df_in))):
            numeric_candidates.append(c)
    priority = ["f_ikr_dari_rekap_kk", "ipm_mikro", "indeks_pengeluaran", "indeks_kesehatan", "indeks_pendidikan"]
    for p in priority:
        if p in numeric_candidates:
            return p
    return numeric_candidates[0] if numeric_candidates else None


def build_onehot_feature_matrix(df_builder, feature_cols, rounding_decimals=2):
    if not feature_cols:
        return pd.DataFrame(np.zeros((len(df_builder), 1)), columns=["__no_feature_cols__"], index=df_builder.index)
    rounding_decimals = int(rounding_decimals) if pd.notnull(rounding_decimals) else 2
    rounding_decimals = 2 if rounding_decimals not in {0, 1, 2} else rounding_decimals
    feat_df = df_builder[list(feature_cols)].copy()
    for col in feature_cols:
        # Jika numerik, bulatkan dulu sesuai opsi desimal agar kategori one-hot lebih stabil.
        raw_col = feat_df[col].replace(["", "nan", "None", "none"], np.nan)
        num_col = pd.to_numeric(raw_col, errors="coerce")
        if num_col.notna().any():
            fmt_num = num_col.round(rounding_decimals).map(
                lambda x: f"{x:.{rounding_decimals}f}" if pd.notnull(x) else "__MISSING__"
            )
            fmt_raw = raw_col.astype("string").fillna("__MISSING__")
            feat_df[col] = np.where(num_col.notna(), fmt_num, fmt_raw)
        else:
            feat_df[col] = raw_col.astype("string").fillna("__MISSING__")
    dummies = pd.get_dummies(
        feat_df,
        columns=list(feature_cols),
        prefix=list(feature_cols),
        prefix_sep="=",
        dummy_na=False,
        dtype=float,
    )
    if dummies.empty:
        return pd.DataFrame(np.zeros((len(df_builder), 1)), columns=["__all_missing__"], index=df_builder.index)
    return dummies

def compute_cosine_similarity(vec_i, vec_j):
    denom = float(np.linalg.norm(vec_i) * np.linalg.norm(vec_j))
    if denom <= 1e-12:
        return 0.0
    return float(np.clip(np.dot(vec_i, vec_j) / denom, 0.0, 1.0))


def compute_jaccard_similarity(vec_i, vec_j):
    b_i = vec_i > 0
    b_j = vec_j > 0
    union = int(np.logical_or(b_i, b_j).sum())
    if union == 0:
        return 0.0
    inter = int(np.logical_and(b_i, b_j).sum())
    return float(inter / union)


def compute_pearson_similarity(vec_i, vec_j):
    std_i = float(np.std(vec_i))
    std_j = float(np.std(vec_j))
    if std_i <= 1e-12 or std_j <= 1e-12:
        return 0.0
    corr = float(np.corrcoef(vec_i, vec_j)[0, 1])
    if not np.isfinite(corr):
        return 0.0
    return float(corr)


def compute_auto_threshold_from_distribution(sim_values, threshold_grid=None):
    if threshold_grid is None:
        threshold_grid = [round(x, 1) for x in np.arange(0.1, 1.0, 0.1)]
    sim_series = pd.Series(sim_values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    if sim_series.empty:
        n_candidates = max(len(threshold_grid), 1)
        table = [
            {
                "threshold": float(t),
                "edge_count": 0,
                "total_edge_kumulatif": 0,
                "rata2_edge_umum_total_bagi_kandidat": 0.0,
                "jumlah_kandidat_threshold": int(n_candidates),
            }
            for t in threshold_grid
        ]
        return 0.4, table
    counts = []
    for t in threshold_grid:
        counts.append(int((sim_series >= float(t)).sum()))
    n_candidates = max(len(threshold_grid), 1)
    total_edge_kumulatif = int(np.sum(counts))
    target_count = float(total_edge_kumulatif / n_candidates)
    best_idx = min(range(len(threshold_grid)), key=lambda i: (abs(counts[i] - target_count), abs(threshold_grid[i] - 0.5)))
    table = [
        {
            "threshold": float(threshold_grid[i]),
            "edge_count": int(counts[i]),
            "jarak_ke_rata2_edge": float(abs(counts[i] - target_count)),
            "total_edge_kumulatif": int(total_edge_kumulatif),
            "rata2_edge_umum_total_bagi_kandidat": float(target_count),
            "jumlah_kandidat_threshold": int(n_candidates),
        }
        for i in range(len(threshold_grid))
    ]
    return float(threshold_grid[best_idx]), table


def compute_threshold_sensitivity_analysis(
    node_ids,
    candidate_edges,
    threshold_grid=None,
    lcc_only=True,
    force_louvain_lcc=False,
):
    if threshold_grid is None:
        threshold_grid = [round(x, 1) for x in np.arange(0.1, 1.0, 0.1)]
    nodes = list(node_ids or [])
    pair_total = int(len(candidate_edges or []))
    rows = []

    for threshold in threshold_grid:
        threshold_float = float(threshold)
        graph_raw = nx.Graph()
        graph_raw.add_nodes_from(nodes)
        for u, v, sim_weight in candidate_edges:
            if float(sim_weight) >= threshold_float:
                graph_raw.add_edge(u, v, weight=float(sim_weight))

        if graph_raw.number_of_nodes() > 0:
            lcc_nodes = max(nx.connected_components(graph_raw), key=len)
            graph_lcc = graph_raw.subgraph(lcc_nodes).copy()
        else:
            graph_lcc = nx.Graph()

        graph_target = graph_lcc if lcc_only else graph_raw
        partition_graph = graph_lcc if force_louvain_lcc else graph_target
        modularity_q = 0.0
        cluster_count = 0

        if partition_graph.number_of_nodes() > 0:
            if partition_graph.number_of_edges() > 0:
                try:
                    partition_tmp = community_louvain.best_partition(partition_graph, weight="weight", random_state=42)
                    cluster_count = int(len(set(partition_tmp.values())))
                    modularity_q = _safe_float_metric(
                        community_louvain.modularity(partition_tmp, partition_graph, weight="weight"),
                        default=0.0,
                    )
                except Exception:
                    cluster_count = int(nx.number_connected_components(partition_graph))
                    modularity_q = 0.0
            else:
                cluster_count = int(partition_graph.number_of_nodes())

        edge_count = int(graph_raw.number_of_edges())
        rows.append(
            {
                "threshold": threshold_float,
                "edge_count": edge_count,
                "edge_ratio_pct": float((edge_count / pair_total) * 100.0) if pair_total else 0.0,
                "density_raw": float(nx.density(graph_raw)) if graph_raw.number_of_nodes() > 1 else 0.0,
                "komponen_raw": int(nx.number_connected_components(graph_raw)) if graph_raw.number_of_nodes() else 0,
                "node_lcc": int(graph_lcc.number_of_nodes()),
                "edge_lcc": int(graph_lcc.number_of_edges()),
                "density_analisis": float(nx.density(graph_target)) if graph_target.number_of_nodes() > 1 else 0.0,
                "jumlah_cluster": int(cluster_count),
                "modularity": float(modularity_q),
            }
        )

    return rows


def merge_threshold_distribution_with_sensitivity(distribution_rows, sensitivity_rows):
    distribution_lookup = {
        round(float(row.get("threshold", 0.0)), 6): dict(row)
        for row in (distribution_rows or [])
    }
    merged_rows = []
    for sensitivity_row in sensitivity_rows or []:
        key = round(float(sensitivity_row.get("threshold", 0.0)), 6)
        merged_row = dict(sensitivity_row)
        for col, val in distribution_lookup.get(key, {}).items():
            if col not in merged_row:
                merged_row[col] = val
        merged_rows.append(merged_row)
    return merged_rows


def get_threshold_sensitivity_dataframe(meta):
    rows = meta.get("threshold_sensitivity") or meta.get("threshold_distribution") or []
    df_sens = pd.DataFrame(rows)
    if df_sens.empty or "threshold" not in df_sens.columns:
        return pd.DataFrame()
    df_sens = df_sens.copy()
    df_sens["threshold"] = pd.to_numeric(df_sens["threshold"], errors="coerce")
    df_sens = df_sens.dropna(subset=["threshold"]).sort_values("threshold").reset_index(drop=True)
    threshold_selected = round(float(meta.get("threshold_selected", 0.0)), 6)
    df_sens["threshold_terpilih"] = df_sens["threshold"].round(6).eq(threshold_selected)
    return df_sens


def render_threshold_sensitivity_heatmap(df_sens):
    heatmap_cols = [
        ("edge_count", "Edge"),
        ("density_analisis", "Density"),
        ("modularity", "Modularity Q"),
        ("jumlah_cluster", "Jumlah Klaster"),
        ("komponen_raw", "Komponen Raw"),
    ]
    available_cols = [(col, label) for col, label in heatmap_cols if col in df_sens.columns]
    if not available_cols:
        return

    heat_display = pd.DataFrame(
        {
            label: pd.to_numeric(df_sens[col], errors="coerce").fillna(0.0).to_numpy()
            for col, label in available_cols
        },
        index=df_sens["threshold"].map(lambda x: f"{float(x):.1f}"),
    ).T

    heat_norm = heat_display.copy()
    for idx in heat_norm.index:
        row = pd.to_numeric(heat_norm.loc[idx], errors="coerce").fillna(0.0)
        span = float(row.max() - row.min())
        heat_norm.loc[idx] = 0.5 if span <= 1e-12 else (row - row.min()) / span

    text_values = heat_display.astype(object)
    for idx in text_values.index:
        if idx in {"Edge", "Jumlah Klaster", "Komponen Raw"}:
            text_values.loc[idx] = heat_display.loc[idx].map(lambda x: f"{float(x):.0f}")
        else:
            text_values.loc[idx] = heat_display.loc[idx].map(lambda x: f"{float(x):.4f}")

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=heat_norm.astype(float).values,
            x=list(heat_norm.columns),
            y=list(heat_norm.index),
            text=text_values.values,
            texttemplate="%{text}",
            colorscale="RdYlGn",
            colorbar=dict(title="Skala relatif"),
            hovertemplate="Threshold %{x}<br>%{y}: %{text}<extra></extra>",
        )
    )
    fig_heat.update_layout(
        title="Heatmap Sensitivitas Seluruh Kandidat Threshold",
        xaxis_title="Threshold",
        yaxis_title="Metrik",
        template="plotly_white",
        height=max(330, 70 * len(heat_norm.index)),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def render_auto_threshold_summary(
    meta,
    graph_obj,
    partition,
    selected_desa=None,
    basis_col=None,
    method_label="-",
    kernel_info="-",
    rounding_label="-",
    compact=False,
):
    threshold_used = float(meta.get("threshold_selected", 0.0))
    df_sens = get_threshold_sensitivity_dataframe(meta)
    if df_sens.empty:
        st.info("Data kandidat threshold belum tersedia untuk dirangkum.")
        return

    selected_rows = df_sens[df_sens["threshold_terpilih"]]
    selected_row = selected_rows.iloc[0].to_dict() if not selected_rows.empty else {}
    total_pair = int(len(meta.get("pairwise_similarity_values", [])))
    total_edge_kumulatif = int(df_sens["edge_count"].sum()) if "edge_count" in df_sens.columns else 0
    jumlah_kandidat = int(len(df_sens))
    rata2_edge_umum = float(total_edge_kumulatif / max(jumlah_kandidat, 1))
    jarak_terpilih = float(selected_row.get("jarak_ke_rata2_edge", abs(float(selected_row.get("edge_count", 0.0)) - rata2_edge_umum)))
    density_default = float(nx.density(graph_obj)) if graph_obj.number_of_nodes() > 1 else 0.0
    modularity_default = 0.0
    if graph_obj.number_of_edges() > 0 and partition:
        try:
            modularity_default = _safe_float_metric(community_louvain.modularity(partition, graph_obj, weight="weight"), default=0.0)
        except Exception:
            modularity_default = 0.0
    cluster_default = int(len(set(partition.values()))) if partition else 0

    if not compact:
        st.markdown(
            f"<div class='premium-hero'><b>Rangkuman Sensitivity Analysis Threshold Otomatis</b><br>"
            f"Desa: <b>{selected_desa or '-'}</b> | Basis: <b>{basis_col or '-'}</b> | "
            f"Metode: <b>{method_label}</b> ({kernel_info}) | One-Hot Rounding: <b>{rounding_label}</b><br>"
            f"Threshold otomatis dipilih dari {jumlah_kandidat} kandidat dengan membandingkan jumlah edge yang terbentuk "
            f"pada tiap nilai ambang.</div>",
            unsafe_allow_html=True,
        )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Threshold Terpilih", f"{threshold_used:.2f}")
    c2.metric("Edge Terpilih", f"{int(selected_row.get('edge_count', graph_obj.number_of_edges())):,}")
    c3.metric("Density Analisis", f"{float(selected_row.get('density_analisis', density_default)):.4f}")
    c4.metric("Modularity Q", f"{float(selected_row.get('modularity', modularity_default)):.4f}")
    c5.metric("Jumlah Klaster", f"{int(selected_row.get('jumlah_cluster', cluster_default))}")

    st.markdown(
        f"<div class='soft-card'><b>Justifikasi threshold otomatis.</b><br>"
        f"Ambang <b>{threshold_used:.2f}</b> dipilih karena jumlah edge pada kandidat ini paling dekat dengan "
        f"rata-rata edge kumulatif seluruh kandidat ({rata2_edge_umum:.2f}). "
        f"Jarak kandidat terpilih terhadap rata-rata tersebut adalah <b>{jarak_terpilih:.2f} edge</b>. "
        f"Tabel dan heatmap di bawah memperlihatkan bagaimana density, modularity, dan jumlah klaster berubah "
        f"di semua kandidat, sehingga hasil graf tidak hanya bergantung pada satu angka yang tampak subjektif.</div>",
        unsafe_allow_html=True,
    )

    chart_cols = st.columns([1.0, 1.0])
    with chart_cols[0]:
        fig_edges = px.line(
            df_sens,
            x="threshold",
            y="edge_count",
            markers=True,
            title="Threshold vs Jumlah Edge",
            labels={"threshold": "Threshold", "edge_count": "Jumlah Edge"},
        )
        fig_edges.add_hline(
            y=rata2_edge_umum,
            line_dash="dash",
            line_color=DDP_RED,
            annotation_text=f"Rata-rata edge = {rata2_edge_umum:.2f}",
        )
        fig_edges.add_vline(
            x=threshold_used,
            line_dash="dash",
            line_color="#111827",
            annotation_text=f"Terpilih {threshold_used:.2f}",
        )
        fig_edges.update_layout(template="plotly_white")
        st.plotly_chart(fig_edges, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    with chart_cols[1]:
        trend_cols = [
            ("density_analisis", "Density"),
            ("modularity", "Modularity Q"),
            ("jumlah_cluster", "Jumlah Klaster"),
        ]
        trend_df = df_sens[["threshold"] + [col for col, _ in trend_cols if col in df_sens.columns]].copy()
        trend_long_rows = []
        for col, label in trend_cols:
            if col not in trend_df.columns:
                continue
            vals = pd.to_numeric(trend_df[col], errors="coerce").fillna(0.0)
            span = float(vals.max() - vals.min())
            norm_vals = pd.Series(0.5, index=vals.index) if span <= 1e-12 else (vals - vals.min()) / span
            for idx, val in norm_vals.items():
                trend_long_rows.append({"threshold": float(trend_df.loc[idx, "threshold"]), "Metrik": label, "Nilai Relatif": float(val)})
        trend_long = pd.DataFrame(trend_long_rows)
        if not trend_long.empty:
            fig_trend = px.line(
                trend_long,
                x="threshold",
                y="Nilai Relatif",
                color="Metrik",
                markers=True,
                title="Tren Relatif Density, Modularity, dan Klaster",
            )
            fig_trend.add_vline(x=threshold_used, line_dash="dash", line_color="#111827")
            fig_trend.update_layout(template="plotly_white", yaxis_title="Nilai relatif 0-1")
            st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    render_threshold_sensitivity_heatmap(df_sens)

    table_cols = [
        ("threshold", "Threshold"),
        ("edge_count", "Jumlah Edge Raw"),
        ("edge_ratio_pct", "Rasio Edge (%)"),
        ("density_raw", "Density Raw"),
        ("komponen_raw", "Komponen Raw"),
        ("node_lcc", "Node LCC"),
        ("edge_lcc", "Edge LCC"),
        ("density_analisis", "Density Analisis"),
        ("modularity", "Modularity Q"),
        ("jumlah_cluster", "Jumlah Klaster"),
        ("jarak_ke_rata2_edge", "Jarak ke Rata-rata Edge"),
        ("threshold_terpilih", "Terpilih"),
    ]
    display_cols = [col for col, _ in table_cols if col in df_sens.columns]
    df_display = df_sens[display_cols].copy()
    rename_map = {col: label for col, label in table_cols if col in df_display.columns}
    df_display = df_display.rename(columns=rename_map)
    if "Terpilih" in df_display.columns:
        df_display["Terpilih"] = df_display["Terpilih"].map(lambda x: "Ya" if bool(x) else "")

    def _highlight_selected_threshold(row):
        if str(row.get("Terpilih", "")).lower() == "ya":
            return ["background-color: #DCFCE7; color: #14532D; font-weight: 700;"] * len(row)
        return [""] * len(row)

    format_cols = {
        "Threshold": "{:.2f}",
        "Rasio Edge (%)": "{:.2f}",
        "Density Raw": "{:.4f}",
        "Density Analisis": "{:.4f}",
        "Modularity Q": "{:.4f}",
        "Jarak ke Rata-rata Edge": "{:.2f}",
    }
    st.dataframe(
        df_display.style.format({k: v for k, v in format_cols.items() if k in df_display.columns}).apply(_highlight_selected_threshold, axis=1),
        use_container_width=True,
    )


def safe_numeric_assortativity(graph_obj, attr_name, default=0.0):
    if graph_obj is None or graph_obj.number_of_nodes() < 2 or graph_obj.number_of_edges() == 0:
        return float(default)
    raw_series = pd.Series({n: graph_obj.nodes[n].get(attr_name) for n in graph_obj.nodes()})
    num_series = pd.to_numeric(raw_series, errors="coerce")
    valid_nodes = [n for n in graph_obj.nodes() if pd.notnull(num_series.get(n))]
    if len(valid_nodes) < 2:
        return float(default)
    g_sub = graph_obj.subgraph(valid_nodes).copy()
    if g_sub.number_of_edges() == 0:
        return float(default)
    for n in g_sub.nodes():
        g_sub.nodes[n][attr_name] = float(num_series.get(n))
    vals = pd.Series([g_sub.nodes[n].get(attr_name) for n in g_sub.nodes()], dtype=float)
    if vals.nunique() <= 1:
        return float(default)
    try:
        return _safe_float_metric(nx.numeric_assortativity_coefficient(g_sub, attr_name), default=default)
    except Exception:
        return float(default)


def interpret_assortativity_value(r_val):
    r = _safe_float_metric(r_val, default=0.0)
    abs_r = abs(r)
    if abs_r < 0.10:
        level = "Sangat lemah"
    elif abs_r < 0.30:
        level = "Lemah"
    elif abs_r < 0.50:
        level = "Sedang"
    else:
        level = "Kuat"
    direction = "Asortatif" if r > 0 else "Disasortatif" if r < 0 else "Campuran/Acak"
    return direction, level


def safe_attribute_assortativity(graph_obj, attr_name, default=0.0):
    if graph_obj is None or graph_obj.number_of_nodes() < 2 or graph_obj.number_of_edges() == 0:
        return float(default)
    valid_nodes = [n for n in graph_obj.nodes() if pd.notnull(graph_obj.nodes[n].get(attr_name))]
    if len(valid_nodes) < 2:
        return float(default)
    g_sub = graph_obj.subgraph(valid_nodes).copy()
    if g_sub.number_of_edges() == 0:
        return float(default)
    vals = pd.Series([g_sub.nodes[n].get(attr_name) for n in g_sub.nodes()])
    if vals.nunique() <= 1:
        return float(default)
    try:
        return _safe_float_metric(nx.attribute_assortativity_coefficient(g_sub, attr_name), default=default)
    except Exception:
        return float(default)


def steinley_segregation_label(r_val):
    r_abs = abs(_safe_float_metric(r_val, default=0.0))
    if r_abs < 0.10:
        return "Low Segregation"
    if r_abs < 0.30:
        return "Moderate Segregation"
    return "High Segregation"


def interpret_q_strength(q_val):
    q = _safe_float_metric(q_val, default=0.0)
    a = abs(q)
    if a < 0.10:
        return "lemah"
    if a < 0.30:
        return "cukup"
    if a < 0.50:
        return "sedang"
    return "kuat"


def build_audit_auto_narrative(df_audit):
    if df_audit is None or df_audit.empty:
        return "Narasi audit belum dapat dibuat karena tabel audit kosong."
    lines = []
    for _, row in df_audit.iterrows():
        metric = row.get("Metrik", "-")
        r_val = _safe_float_metric(row.get("r"), default=0.0)
        qw_val = _safe_float_metric(row.get("Qw*"), default=0.0)
        qb_val = _safe_float_metric(row.get("Qb*"), default=0.0)
        dir_r, lvl_r = interpret_assortativity_value(r_val)
        if qw_val >= 0.10:
            intra_note = f"intra-klaster {interpret_q_strength(qw_val)} homogen"
        elif qw_val <= -0.10:
            intra_note = "intra-klaster cenderung lintas kategori"
        else:
            intra_note = "intra-klaster campuran/netral"
        if qb_val >= 0.10:
            inter_note = f"antar-klaster {interpret_q_strength(qb_val)} homogen"
        elif qb_val <= -0.10:
            inter_note = "antar-klaster cenderung berbeda kategori"
        else:
            inter_note = "antar-klaster campuran/netral"
        lines.append(
            f"- <b>{metric}</b>: r=<b>{r_val:.3f}</b> ({dir_r}, {lvl_r}); Qw*=<b>{qw_val:.3f}</b> ({intra_note}); Qb*=<b>{qb_val:.3f}</b> ({inter_note})."
        )
    return "<br>".join(lines)


def resolve_first_existing_column(df_columns, candidates):
    lookup = {str(c).lower().strip(): c for c in df_columns}
    for cand in candidates:
        key = str(cand).lower().strip()
        if key in lookup:
            return lookup[key]
    return None


def compute_assortativity_for_column(graph_obj, col_name):
    node_vals = [graph_obj.nodes[n].get(col_name) for n in graph_obj.nodes()]
    num_series = pd.to_numeric(pd.Series(node_vals), errors="coerce")
    if num_series.notna().sum() >= 3 and num_series.nunique(dropna=True) > 1:
        return safe_numeric_assortativity(graph_obj, col_name, default=0.0), "numeric"
    return safe_attribute_assortativity(graph_obj, col_name, default=0.0), "attribute"


def centrality_help_text(metric_key):
    mapping = {
        "degree": "Degree: seberapa banyak dan seberapa kuat koneksi langsung node.",
        "betweenness": "Betweenness: seberapa sering node menjadi jembatan jalur terpendek antar-node.",
        "closeness": "Closeness: seberapa dekat node ke node lain (rata-rata jarak paling pendek).",
        "eigenvector": "Eigenvector: node penting jika terhubung ke node penting lainnya.",
    }
    return mapping.get(metric_key, "-")


def compute_centrality_on_similarity_graph(graph_obj, metric_key):
    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        return {}
    metric_key = str(metric_key).strip().lower()
    if metric_key == "degree":
        return {n: float(graph_obj.degree(n, weight="weight")) for n in graph_obj.nodes()}

    # Untuk metrik shortest-path, similarity diubah jadi jarak: distance = 1 / similarity.
    graph_dist = graph_obj.copy()
    for u, v, d in graph_dist.edges(data=True):
        w = _safe_float_metric(d.get("weight"), default=0.0)
        d["distance"] = 1.0 / max(w, 1e-9)

    if metric_key == "betweenness":
        return nx.betweenness_centrality(graph_dist, weight="distance", normalized=True)
    if metric_key == "closeness":
        return nx.closeness_centrality(graph_dist, distance="distance")
    if metric_key == "eigenvector":
        try:
            return nx.eigenvector_centrality_numpy(graph_obj, weight="weight")
        except Exception:
            return nx.eigenvector_centrality(graph_obj, weight="weight", max_iter=2000, tol=1e-6)
    return {}


CENTRALITY_METRIC_SPECS = [
    ("Degree Centrality", "degree"),
    ("Betweenness Centrality", "betweenness"),
    ("Closeness Centrality", "closeness"),
    ("Eigenvector Centrality", "eigenvector"),
]
CENTRALITY_METRIC_COLUMNS = [label for label, _ in CENTRALITY_METRIC_SPECS]
CENTRALITY_METRIC_SHORT_LABELS = {
    "Degree Centrality": "Degree tinggi",
    "Betweenness Centrality": "Betweenness tinggi",
    "Closeness Centrality": "Closeness tinggi",
    "Eigenvector Centrality": "Eigenvector tinggi",
}
CENTRALITY_METRIC_FLAG_COLUMNS = {
    "Degree Centrality": "_degree_high",
    "Betweenness Centrality": "_betweenness_high",
    "Closeness Centrality": "_closeness_high",
    "Eigenvector Centrality": "_eigenvector_high",
}
CENTRALITY_METRIC_Q75_COLUMNS = {
    "Degree Centrality": "_degree_q75",
    "Betweenness Centrality": "_betweenness_q75",
    "Closeness Centrality": "_closeness_q75",
    "Eigenvector Centrality": "_eigenvector_q75",
}

CENTRALITY_ROLE_COLORS = {
    "Aktor strategis multiperan": "#7C3AED",
    "Aktor sentral berpengaruh": "#2563EB",
    "Broker antar-kelompok": "#F59E0B",
    "Penyebar cepat": "#059669",
    "Hub lokal aktif": "#0EA5E9",
    "Aktor dekat inti jaringan": "#DB2777",
    "Node umum": "#94A3B8",
}

CENTRALITY_ROLE_ORDER = [
    "Aktor strategis multiperan",
    "Aktor sentral berpengaruh",
    "Broker antar-kelompok",
    "Penyebar cepat",
    "Hub lokal aktif",
    "Aktor dekat inti jaringan",
    "Node umum",
]

CENTRALITY_ROLE_METRIC_BASIS = {
    "Aktor strategis multiperan": ">=3 metrik centrality Q75",
    "Aktor sentral berpengaruh": "Degree + Eigenvector Q75",
    "Broker antar-kelompok": "Betweenness Q75",
    "Penyebar cepat": "Closeness Q75",
    "Hub lokal aktif": "Degree Q75",
    "Aktor dekat inti jaringan": "Eigenvector Q75",
    "Node umum": "semua metrik < Q75",
}
CENTRALITY_ROLE_DISPLAY_LABELS = {
    role: f"{role} ({CENTRALITY_ROLE_METRIC_BASIS.get(role, '-')})"
    for role in CENTRALITY_ROLE_ORDER
}
CENTRALITY_ROLE_DISPLAY_ORDER = [
    CENTRALITY_ROLE_DISPLAY_LABELS[role]
    for role in CENTRALITY_ROLE_ORDER
]
CENTRALITY_ROLE_DISPLAY_COLORS = {
    CENTRALITY_ROLE_DISPLAY_LABELS[role]: CENTRALITY_ROLE_COLORS[role]
    for role in CENTRALITY_ROLE_ORDER
}


def centrality_role_metric_basis(role):
    return CENTRALITY_ROLE_METRIC_BASIS.get(str(role), "-")


def centrality_role_display_label(role):
    role_text = str(role)
    return CENTRALITY_ROLE_DISPLAY_LABELS.get(
        role_text,
        f"{role_text} ({centrality_role_metric_basis(role_text)})",
    )


def make_anonymized_node_mapping(node_ids):
    stable_ids = sorted({str(n) for n in (node_ids or [])})
    return {node_id: f"N-{idx + 1:03d}" for idx, node_id in enumerate(stable_ids)}


def apply_privacy_view(df, id_col="family_id", name_col="Nama", publish_mode=True):
    if df is None:
        return pd.DataFrame()
    result = df.copy()
    if "Kode Node" not in result.columns:
        if id_col in result.columns:
            anon_map = make_anonymized_node_mapping(result[id_col].dropna().astype(str).tolist())
            result["Kode Node"] = result[id_col].astype(str).map(anon_map).fillna("N-000")
        else:
            result["Kode Node"] = [f"N-{idx + 1:03d}" for idx in range(len(result))]

    if "Dusun/Kode Dusun" not in result.columns and "Dusun" in result.columns:
        if publish_mode:
            dusun_vals = sorted(result["Dusun"].fillna("Tidak tersedia").astype(str).unique().tolist())
            dusun_map = {val: f"Dusun-{idx + 1}" for idx, val in enumerate(dusun_vals)}
            result["Dusun/Kode Dusun"] = result["Dusun"].fillna("Tidak tersedia").astype(str).map(dusun_map)
        else:
            result["Dusun/Kode Dusun"] = result["Dusun"].fillna("Tidak tersedia").astype(str)

    if publish_mode:
        drop_cols = [col for col in [id_col, name_col, "Dusun"] if col in result.columns]
        if drop_cols:
            result = result.drop(columns=drop_cols)
    return result


def safe_hover_text(row, publish_mode=True):
    def pick(*cols, default="-"):
        for col in cols:
            if col in row and pd.notnull(row.get(col)):
                value = row.get(col)
                if str(value).strip() != "":
                    return value
        return default

    parts = []
    if publish_mode:
        parts.append(f"Kode Node: {pick('Kode Node')}")
    else:
        parts.append(f"Nama: {pick('Nama')}")
        parts.append(f"family_id: {pick('family_id')}")
        parts.append(f"Kode Node: {pick('Kode Node')}")
    parts.extend(
        [
            f"Klaster Louvain: {pick('Klaster Louvain')}",
            f"Dusun/Kode Dusun: {pick('Dusun/Kode Dusun', 'Dusun')}",
        ]
    )
    if "Sinyal Centrality" in row:
        parts.extend(
            [
                f"Peran Aktor: {pick('Peran Aktor', 'Peran Struktural')}",
                f"Basis Metrik: {pick('Basis Metrik Peran')}",
                f"Sinyal Centrality: {pick('Sinyal Centrality')}",
                f"Jumlah Metrik Tinggi: {pick('Jumlah Metrik Tinggi')}",
            ]
        )
    else:
        parts.extend(
            [
                f"IKD Agregat: {_safe_float_metric(pick('IKD Agregat', default=np.nan), default=np.nan):.3f}",
                f"Status BPS: {pick('Status BPS')}",
                f"Status Bansos: {pick('Status Bansos')}",
                f"Akses Informasi: {pick('Akses Informasi')}",
                f"Peran Struktural: {pick('Peran Struktural')}",
            ]
        )
    for col in ["Degree Centrality", "Betweenness Centrality", "Closeness Centrality", "Eigenvector Centrality"]:
        if col in row:
            parts.append(f"{col}: {_safe_float_metric(row.get(col), default=0.0):.6f}")
    if "Sinyal Centrality" in row:
        parts.append("Catatan: peran aktor dihitung hanya dari degree, betweenness, closeness, dan eigenvector.")
    else:
        parts.append("Catatan: indikasi awal, perlu pendalaman lapangan, bukan bukti tunggal.")
    return "<br>".join(parts)


def centrality_level_from_quantile(value, q25, q75):
    val = _safe_float_metric(value, default=np.nan)
    if not np.isfinite(val):
        return "Tidak tersedia"
    q25_val = _safe_float_metric(q25, default=val)
    q75_val = _safe_float_metric(q75, default=val)
    if abs(q75_val - q25_val) <= 1e-12:
        return "Sedang"
    if val >= q75_val:
        return "Tinggi"
    if val <= q25_val:
        return "Rendah"
    return "Sedang"


def ikr_level_from_value(ikr_value, status_bps=None):
    status_text = str(status_bps or "").strip().lower()
    ikr = _safe_float_metric(ikr_value, default=np.nan)
    if status_text == "rendah" or (np.isfinite(ikr) and ikr < 60):
        return "Rendah"
    if status_text == "sedang" or (np.isfinite(ikr) and 60 <= ikr < 70):
        return "Sedang"
    if status_text in {"tinggi", "sangat tinggi"} or (np.isfinite(ikr) and ikr >= 70):
        return "Tinggi"
    return "Tidak tersedia"


def access_info_label(row):
    internet_available = "internet_num" in row and pd.notnull(row.get("internet_num"))
    ponsel_available = "ponsel_num" in row and pd.notnull(row.get("ponsel_num"))
    internet_val = _safe_float_metric(row.get("internet_num"), default=0.0)
    ponsel_val = _safe_float_metric(row.get("ponsel_num"), default=0.0)
    if not internet_available and not ponsel_available:
        return "Tidak tersedia"
    if internet_val >= 1 or ponsel_val >= 1:
        return "Tersedia"
    return "Tidak tersedia pada data"


def centrality_role_implication(role):
    mapping = {
        "Aktor strategis multiperan": "Menonjol pada sedikitnya tiga metrik centrality; aktor ini kuat sebagai pusat koneksi, penghubung, dan/atau titik jangkau jaringan.",
        "Aktor sentral berpengaruh": "Degree dan eigenvector tinggi; aktor ini memiliki banyak koneksi langsung sekaligus terhubung dengan aktor-aktor yang juga penting.",
        "Broker antar-kelompok": "Betweenness tinggi; aktor ini sering berada pada jalur penghubung antarbagian jaringan.",
        "Penyebar cepat": "Closeness tinggi; aktor ini relatif dekat ke banyak node lain sehingga berpotensi cepat menjangkau jaringan.",
        "Hub lokal aktif": "Degree tinggi; aktor ini memiliki banyak koneksi langsung, meskipun belum tentu berada pada inti pengaruh jaringan.",
        "Aktor dekat inti jaringan": "Eigenvector tinggi; aktor ini terhubung dengan node-node yang juga memiliki posisi penting.",
        "Node umum": "Tidak berada pada kuartil atas empat metrik centrality; tetap bagian jaringan, tetapi tidak ditandai sebagai aktor strategis utama.",
    }
    return mapping.get(role, mapping["Node umum"])


def centrality_role_ethics_note(role=None):
    return "Interpretasi ini hanya membaca posisi jaringan dari degree, betweenness, closeness, dan eigenvector; bukan label sosial atau penilaian kesejahteraan."


def classify_centrality_policy_role(row, centrality_col, betweenness_col=None):
    degree_high = bool(row.get("_degree_high", False))
    betweenness_high = bool(row.get("_betweenness_high", False))
    closeness_high = bool(row.get("_closeness_high", False))
    eigenvector_high = bool(row.get("_eigenvector_high", False))
    high_count = int(_safe_float_metric(row.get("Jumlah Metrik Tinggi"), default=0.0))

    if high_count >= 3:
        return "Aktor strategis multiperan"
    if degree_high and eigenvector_high:
        return "Aktor sentral berpengaruh"
    if betweenness_high:
        return "Broker antar-kelompok"
    if closeness_high:
        return "Penyebar cepat"
    if degree_high:
        return "Hub lokal aktif"
    if eigenvector_high:
        return "Aktor dekat inti jaringan"
    return "Node umum"


def add_centrality_role_features(df_role):
    if df_role is None or df_role.empty:
        return pd.DataFrame()
    result = df_role.copy()
    high_flag_cols = []
    for metric_label, _ in CENTRALITY_METRIC_SPECS:
        if metric_label not in result.columns:
            continue
        series = pd.to_numeric(result[metric_label], errors="coerce").fillna(0.0)
        q75 = float(series.quantile(0.75)) if not series.empty else 0.0
        has_spread = bool((float(series.max()) - float(series.min())) > 1e-12) if not series.empty else False
        flag_col = CENTRALITY_METRIC_FLAG_COLUMNS[metric_label]
        q75_col = CENTRALITY_METRIC_Q75_COLUMNS[metric_label]
        result[q75_col] = q75
        result[flag_col] = series.ge(q75) if has_spread else False
        high_flag_cols.append(flag_col)

    if high_flag_cols:
        result["Jumlah Metrik Tinggi"] = result[high_flag_cols].astype(int).sum(axis=1)
    else:
        result["Jumlah Metrik Tinggi"] = 0

    def format_signal(row):
        signals = [
            CENTRALITY_METRIC_SHORT_LABELS[metric_label]
            for metric_label, _ in CENTRALITY_METRIC_SPECS
            if bool(row.get(CENTRALITY_METRIC_FLAG_COLUMNS[metric_label], False))
        ]
        return ", ".join(signals) if signals else "Tidak ada metrik pada kuartil atas"

    result["Sinyal Centrality"] = result.apply(format_signal, axis=1)
    result["Peran Struktural"] = result.apply(
        lambda r: classify_centrality_policy_role(r, centrality_col="Degree Centrality", betweenness_col="Betweenness Centrality"),
        axis=1,
    )
    result["Basis Metrik Peran"] = result["Peran Struktural"].map(centrality_role_metric_basis)
    result["Peran Aktor"] = result["Peran Struktural"].map(centrality_role_display_label)
    result["Implikasi Program"] = result["Peran Struktural"].map(centrality_role_implication)
    result["Catatan Etika"] = result["Peran Struktural"].map(centrality_role_ethics_note)
    return result


def build_centrality_policy_narrative(df_role, centrality_name):
    if df_role is None or df_role.empty:
        return "Analisis centrality belum memiliki node yang cukup untuk ditafsirkan."
    role_counts = df_role["Peran Struktural"].value_counts()
    strategic_mask = df_role["Peran Struktural"].ne("Node umum")
    n_strategic = int(strategic_mask.sum())
    n_multi = int(role_counts.get("Aktor strategis multiperan", 0))
    n_core = int(role_counts.get("Aktor sentral berpengaruh", 0))
    n_broker = int(role_counts.get("Broker antar-kelompok", 0))
    n_fast = int(role_counts.get("Penyebar cepat", 0))
    n_degree_eigen = int((df_role.get("_degree_high", False) & df_role.get("_eigenvector_high", False)).sum()) if {"_degree_high", "_eigenvector_high"}.issubset(df_role.columns) else 0
    return (
        "Analisis aktor strategis ini hanya memakai empat metrik centrality: degree, betweenness, closeness, dan eigenvector. "
        f"Pada filter aktif terdapat {n_strategic} node yang masuk peran strategis jaringan. "
        f"Sebanyak {n_multi} node menonjol pada sedikitnya tiga metrik, {n_core} node menjadi aktor sentral berpengaruh, "
        f"{n_broker} node berperan sebagai broker antar-kelompok, dan {n_fast} node menonjol sebagai penyebar cepat. "
        f"Kombinasi Degree tinggi dan Eigenvector tinggi muncul pada {n_degree_eigen} node; tanda ini dibaca sebagai banyak koneksi langsung sekaligus dekat dengan inti pengaruh jaringan."
    )


def build_role_composition_summary(df_view, group_col):
    if df_view is None or df_view.empty or group_col not in df_view.columns or "Peran Struktural" not in df_view.columns:
        return pd.DataFrame()
    summary = (
        df_view.groupby([group_col, "Peran Struktural"], as_index=False)
        .size()
        .rename(columns={"size": "Jumlah Node"})
    )
    summary["Basis Metrik Peran"] = summary["Peran Struktural"].map(centrality_role_metric_basis)
    summary["Peran Aktor"] = summary["Peran Struktural"].map(centrality_role_display_label)
    summary["Total Grup"] = summary.groupby(group_col)["Jumlah Node"].transform("sum")
    summary["Persentase Dalam Grup (%)"] = np.where(
        summary["Total Grup"] > 0,
        (summary["Jumlah Node"] / summary["Total Grup"]) * 100.0,
        0.0,
    )
    summary["Label Segmen"] = summary.apply(
        lambda row: f"n={int(row['Jumlah Node'])}<br>{float(row['Persentase Dalam Grup (%)']):.1f}%",
        axis=1,
    )
    return summary


def build_role_composition_bar(summary_df, x_col, title, xaxis_title, group_label, height=500):
    fig = px.bar(
        summary_df,
        x=x_col,
        y="Jumlah Node",
        color="Peran Aktor",
        text="Label Segmen",
        barmode="stack",
        title=title,
        color_discrete_map=CENTRALITY_ROLE_DISPLAY_COLORS,
        category_orders={"Peran Aktor": CENTRALITY_ROLE_DISPLAY_ORDER},
        custom_data=[
            x_col,
            "Peran Struktural",
            "Basis Metrik Peran",
            "Jumlah Node",
            "Persentase Dalam Grup (%)",
            "Total Grup",
        ],
    )
    fig.update_traces(
        texttemplate="%{text}",
        textposition="inside",
        insidetextanchor="middle",
        cliponaxis=False,
        hovertemplate=(
            f"{xaxis_title}: %{{customdata[0]}}<br>"
            "Peran: %{customdata[1]}<br>"
            "Basis metrik: %{customdata[2]}<br>"
            "Jumlah node: %{customdata[3]}<br>"
            "Persentase dalam grup: %{customdata[4]:.1f}%<br>"
            "Total grup: %{customdata[5]}<extra></extra>"
        ),
    )
    style_publication_figure(
        fig,
        title=title,
        height=height,
        xaxis_title=xaxis_title,
        yaxis_title="Jumlah node",
        legend_title="Peran Aktor (basis metrik)",
        margin=dict(l=54, r=28, t=126, b=62),
    )
    total_nodes = int(summary_df["Jumlah Node"].sum()) if "Jumlah Node" in summary_df.columns else 0
    fig.add_annotation(
        x=0,
        y=1.14,
        xref="paper",
        yref="paper",
        text=f"Total node terfilter: {total_nodes}. Label segmen menunjukkan n dan % dalam {group_label}.",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        align="left",
        font=dict(size=11, color="#475569"),
    )
    totals = summary_df.groupby(x_col, sort=False)["Jumlah Node"].sum()
    max_total = float(totals.max()) if not totals.empty else 0.0
    for x_val, total_val in totals.items():
        fig.add_annotation(
            x=x_val,
            y=float(total_val),
            text=f"Total n={int(total_val)}",
            showarrow=False,
            yshift=10,
            font=dict(size=11, color="#0F172A"),
        )
    if max_total > 0:
        fig.update_yaxes(range=[0, max_total * 1.22])
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode="hide",
        legend=dict(font=dict(size=10), tracegroupgap=4),
    )
    return fig


CENTRALITY_QUARTILE_ORDER = [
    "Q4 tinggi (>=Q75)",
    "Q2-Q3 sedang",
    "Q1 rendah (<=Q25)",
    "Tidak ada variasi",
]
CENTRALITY_QUARTILE_COLORS = {
    "Q4 tinggi (>=Q75)": "#DC2626",
    "Q2-Q3 sedang": "#F59E0B",
    "Q1 rendah (<=Q25)": "#2563EB",
    "Tidak ada variasi": "#94A3B8",
}


def format_quartile_threshold(value):
    val = _safe_float_metric(value, default=np.nan)
    if not np.isfinite(val):
        return "-"
    return f"{val:.6f}"


def build_centrality_quartile_breakdown(df_view):
    if df_view is None or df_view.empty:
        return pd.DataFrame()
    rows = []
    for metric_label, _ in CENTRALITY_METRIC_SPECS:
        if metric_label not in df_view.columns:
            continue
        series = pd.to_numeric(df_view[metric_label], errors="coerce").dropna()
        if series.empty:
            continue
        q25 = float(series.quantile(0.25))
        q50 = float(series.quantile(0.50))
        q75 = float(series.quantile(0.75))
        has_spread = bool((float(series.max()) - float(series.min())) > 1e-12)

        def classify_quartile(value):
            if not has_spread:
                return "Tidak ada variasi"
            if float(value) >= q75:
                return "Q4 tinggi (>=Q75)"
            if float(value) <= q25:
                return "Q1 rendah (<=Q25)"
            return "Q2-Q3 sedang"

        category_counts = series.map(classify_quartile).value_counts()
        total_nodes = max(int(series.shape[0]), 1)
        for category in CENTRALITY_QUARTILE_ORDER:
            count_val = int(category_counts.get(category, 0))
            if count_val <= 0:
                continue
            pct_val = float((count_val / total_nodes) * 100.0)
            rows.append(
                {
                    "Metrik": metric_label.replace(" Centrality", ""),
                    "Metrik Lengkap": metric_label,
                    "Kelompok Kuartil": category,
                    "Jumlah Node": count_val,
                    "Persentase Node (%)": pct_val,
                    "Label Segmen": f"n={count_val}<br>{pct_val:.1f}%",
                    "Q25": q25,
                    "Q50": q50,
                    "Q75": q75,
                    "Threshold Kuartil": (
                        f"Q25={format_quartile_threshold(q25)} | "
                        f"Q50={format_quartile_threshold(q50)} | "
                        f"Q75={format_quartile_threshold(q75)}"
                    ),
                    "Total Node": total_nodes,
                }
            )
    return pd.DataFrame(rows)


def render_centrality_quartile_visual(df_view):
    quartile_df = build_centrality_quartile_breakdown(df_view)
    if quartile_df.empty:
        st.info("Visual kuartil centrality belum dapat ditampilkan karena data centrality belum lengkap.")
        return
    st.markdown("#### Visual Pembagian Kuartil Centrality")
    metric_order = [
        label.replace(" Centrality", "")
        for label, _ in CENTRALITY_METRIC_SPECS
        if label in set(quartile_df["Metrik Lengkap"])
    ]
    fig_quartile = px.bar(
        quartile_df,
        x="Jumlah Node",
        y="Metrik",
        color="Kelompok Kuartil",
        orientation="h",
        text="Label Segmen",
        barmode="stack",
        title="Pembagian Kuartil Centrality untuk Penentuan Peran Aktor",
        color_discrete_map=CENTRALITY_QUARTILE_COLORS,
        category_orders={
            "Metrik": list(reversed(metric_order)),
            "Kelompok Kuartil": CENTRALITY_QUARTILE_ORDER,
        },
        custom_data=[
            "Metrik Lengkap",
            "Kelompok Kuartil",
            "Jumlah Node",
            "Persentase Node (%)",
            "Threshold Kuartil",
            "Total Node",
        ],
    )
    fig_quartile.update_traces(
        texttemplate="%{text}",
        textposition="inside",
        insidetextanchor="middle",
        cliponaxis=False,
        hovertemplate=(
            "Metrik: %{customdata[0]}<br>"
            "Kelompok: %{customdata[1]}<br>"
            "Jumlah node: %{customdata[2]}<br>"
            "Persentase: %{customdata[3]:.1f}%<br>"
            "%{customdata[4]}<br>"
            "Total node: %{customdata[5]}<extra></extra>"
        ),
    )
    style_publication_figure(
        fig_quartile,
        title="Pembagian Kuartil Centrality untuk Penentuan Peran Aktor",
        height=max(430, 240 + (70 * len(metric_order))),
        xaxis_title="Jumlah node",
        yaxis_title="Metrik centrality",
        legend_title="Kelompok kuartil",
        margin=dict(l=72, r=260, t=132, b=56),
    )
    fig_quartile.add_annotation(
        x=0,
        y=1.14,
        xref="paper",
        yref="paper",
        text="Q4 (nilai >= Q75) menjadi sinyal centrality tinggi; kombinasi sinyal inilah yang membentuk peran aktor.",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        align="left",
        font=dict(size=11, color="#475569"),
    )
    threshold_df = quartile_df.drop_duplicates("Metrik")[["Metrik", "Threshold Kuartil", "Total Node"]]
    max_total = float(threshold_df["Total Node"].max()) if not threshold_df.empty else 0.0
    for _, row in threshold_df.iterrows():
        fig_quartile.add_annotation(
            x=max_total * 1.04,
            y=row["Metrik"],
            text=row["Threshold Kuartil"],
            showarrow=False,
            xanchor="left",
            align="left",
            font=dict(size=10, color="#334155"),
        )
    if max_total > 0:
        fig_quartile.update_xaxes(range=[0, max_total * 1.72])
    fig_quartile.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")
    st.plotly_chart(fig_quartile, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def build_centrality_role_legend_df():
    return pd.DataFrame(
        [
            {
                "Peran Aktor": role,
                "Basis Metrik": centrality_role_metric_basis(role),
                "Keterangan": centrality_role_implication(role),
            }
            for role in CENTRALITY_ROLE_ORDER
        ]
    )


def render_centrality_role_legend_table():
    with st.expander("Keterangan Peran Aktor", expanded=False):
        st.dataframe(build_centrality_role_legend_df(), use_container_width=True, hide_index=True)


def render_role_composition_charts(df_view, publish_mode=True, include_legend=True):
    role_cluster_df = build_role_composition_summary(df_view, "Klaster Louvain")
    role_dusun_col = "Dusun/Kode Dusun" if publish_mode else "Dusun"
    role_dusun_df = build_role_composition_summary(df_view, role_dusun_col)
    rc1, rc2 = st.columns(2)
    with rc1:
        if not role_cluster_df.empty:
            fig_role_cluster = build_role_composition_bar(
                role_cluster_df,
                x_col="Klaster Louvain",
                title="Komposisi Aktor Strategis per Klaster",
                xaxis_title="Klaster Louvain",
                group_label="klaster",
                height=500,
            )
            st.plotly_chart(fig_role_cluster, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    with rc2:
        if not role_dusun_df.empty:
            fig_role_dusun = build_role_composition_bar(
                role_dusun_df,
                x_col=role_dusun_col,
                title="Komposisi Aktor Strategis per Dusun",
                xaxis_title="Dusun/Kode Dusun" if publish_mode else "Dusun",
                group_label="dusun",
                height=max(500, min(820, 340 + (18 * role_dusun_df[role_dusun_col].nunique()))),
            )
            st.plotly_chart(fig_role_dusun, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    render_centrality_quartile_visual(df_view)
    if include_legend:
        render_centrality_role_legend_table()


def render_strategic_actor_centrality_map(df_view):
    required_cols = [
        "Degree Centrality",
        "Betweenness Centrality",
        "Closeness Centrality",
        "Eigenvector Centrality",
        "Peran Struktural",
        "Hover Aman",
    ]
    if df_view is None or df_view.empty or any(col not in df_view.columns for col in required_cols):
        st.info("Peta aktor strategis belum dapat ditampilkan karena empat metrik centrality belum lengkap.")
        return

    plot_df = df_view.dropna(subset=["Degree Centrality", "Eigenvector Centrality"]).copy()
    if plot_df.empty:
        st.info("Peta aktor strategis belum dapat ditampilkan karena nilai Degree atau Eigenvector belum tersedia.")
        return
    if "Peran Aktor" not in plot_df.columns:
        plot_df["Peran Aktor"] = plot_df["Peran Struktural"].map(centrality_role_display_label)

    betweenness_size = pd.to_numeric(plot_df["Betweenness Centrality"], errors="coerce").fillna(0.0)
    if float(betweenness_size.max()) <= 0:
        betweenness_size = pd.to_numeric(plot_df["Degree Centrality"], errors="coerce").fillna(0.0)
    plot_df["Ukuran Betweenness"] = betweenness_size + max(float(betweenness_size.max()) * 0.08, 1e-6)
    closeness_signal = (
        plot_df["_closeness_high"].fillna(False).astype(bool)
        if "_closeness_high" in plot_df.columns
        else pd.Series(False, index=plot_df.index)
    )
    plot_df["Sinyal Closeness"] = np.where(closeness_signal, "Closeness tinggi", "Closeness lainnya")

    degree_q75 = (
        float(pd.to_numeric(plot_df["_degree_q75"], errors="coerce").dropna().iloc[0])
        if "_degree_q75" in plot_df.columns and pd.to_numeric(plot_df["_degree_q75"], errors="coerce").dropna().size
        else float(pd.to_numeric(plot_df["Degree Centrality"], errors="coerce").quantile(0.75))
    )
    eigen_q75 = (
        float(pd.to_numeric(plot_df["_eigenvector_q75"], errors="coerce").dropna().iloc[0])
        if "_eigenvector_q75" in plot_df.columns and pd.to_numeric(plot_df["_eigenvector_q75"], errors="coerce").dropna().size
        else float(pd.to_numeric(plot_df["Eigenvector Centrality"], errors="coerce").quantile(0.75))
    )

    fig_actor = px.scatter(
        plot_df,
        x="Degree Centrality",
        y="Eigenvector Centrality",
        color="Peran Aktor",
        size="Ukuran Betweenness",
        symbol="Sinyal Closeness",
        hover_name="Kode Node" if "Kode Node" in plot_df.columns else None,
        custom_data=["Hover Aman"],
        color_discrete_map=CENTRALITY_ROLE_DISPLAY_COLORS,
        category_orders={
            "Peran Aktor": CENTRALITY_ROLE_DISPLAY_ORDER,
            "Sinyal Closeness": ["Closeness tinggi", "Closeness lainnya"],
        },
        size_max=28,
        title="Peta Aktor Strategis Berdasarkan Empat Centrality",
    )
    fig_actor.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        marker=dict(line=dict(color="#111827", width=0.55)),
    )
    if np.isfinite(degree_q75):
        fig_actor.add_vline(x=degree_q75, line_dash="dash", line_color="#0F172A", annotation_text="Q75 Degree")
    if np.isfinite(eigen_q75):
        fig_actor.add_hline(y=eigen_q75, line_dash="dash", line_color="#2563EB", annotation_text="Q75 Eigenvector")
    fig_actor.add_annotation(
        x=0.75,
        y=0.88,
        xref="paper",
        yref="paper",
        text="Degree + Eigenvector tinggi: aktor sentral berpengaruh",
        showarrow=False,
        font=dict(size=12, color="#1D4ED8"),
        align="left",
    )
    fig_actor.add_annotation(
        x=0.72,
        y=0.12,
        xref="paper",
        yref="paper",
        text="Degree tinggi: hub lokal aktif",
        showarrow=False,
        font=dict(size=12, color="#0369A1"),
        align="left",
    )
    fig_actor.add_annotation(
        x=0.22,
        y=0.88,
        xref="paper",
        yref="paper",
        text="Eigenvector tinggi: dekat inti jaringan",
        showarrow=False,
        font=dict(size=12, color="#BE185D"),
        align="left",
    )
    style_publication_figure(
        fig_actor,
        title="Peta Aktor Strategis Berdasarkan Empat Centrality",
        height=580,
        xaxis_title="Degree Centrality",
        yaxis_title="Eigenvector Centrality",
        legend_title="Peran Aktor (basis metrik) / Closeness",
    )
    st.plotly_chart(fig_actor, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def render_degree_eigenvector_role_matrix(df_view):
    if df_view is None or df_view.empty or not {"_degree_high", "_eigenvector_high"}.issubset(df_view.columns):
        st.info("Matriks Degree-Eigenvector belum dapat ditampilkan.")
        return

    matrix_df = df_view.copy()
    matrix_df["Kelompok Degree"] = np.where(matrix_df["_degree_high"], "Degree tinggi", "Degree lainnya")
    matrix_df["Kelompok Eigenvector"] = np.where(matrix_df["_eigenvector_high"], "Eigenvector tinggi", "Eigenvector lainnya")
    x_order = ["Degree lainnya", "Degree tinggi"]
    y_order = ["Eigenvector lainnya", "Eigenvector tinggi"]
    meanings = {
        ("Eigenvector tinggi", "Degree tinggi"): "Aktor sentral berpengaruh",
        ("Eigenvector lainnya", "Degree tinggi"): "Hub lokal aktif",
        ("Eigenvector tinggi", "Degree lainnya"): "Aktor dekat inti jaringan",
        ("Eigenvector lainnya", "Degree lainnya"): "Node umum / cek betweenness dan closeness",
    }
    total_n = max(int(len(matrix_df)), 1)
    z_vals, text_vals, table_rows = [], [], []
    for y_label in y_order:
        z_row, text_row = [], []
        for x_label in x_order:
            count_val = int(((matrix_df["Kelompok Eigenvector"] == y_label) & (matrix_df["Kelompok Degree"] == x_label)).sum())
            pct_val = float((count_val / total_n) * 100.0)
            meaning = meanings[(y_label, x_label)]
            z_row.append(count_val)
            text_row.append(f"{count_val} node<br>{pct_val:.1f}%<br>{meaning}")
            table_rows.append(
                {
                    "Kelompok Degree": x_label,
                    "Kelompok Eigenvector": y_label,
                    "Jumlah Node": count_val,
                    "Persentase Node (%)": pct_val,
                    "Makna Aktor": meaning,
                }
            )
        z_vals.append(z_row)
        text_vals.append(text_row)

    fig_matrix = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=x_order,
            y=y_order,
            text=text_vals,
            texttemplate="%{text}",
            colorscale="YlGnBu",
            colorbar=dict(title="Jumlah node"),
            hovertemplate="%{y}<br>%{x}<br>%{text}<extra></extra>",
        )
    )
    style_publication_figure(
        fig_matrix,
        title="Matriks Degree dan Eigenvector untuk Aktor Strategis",
        height=420,
        xaxis_title="Degree Centrality",
        yaxis_title="Eigenvector Centrality",
    )
    st.plotly_chart(fig_matrix, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    st.dataframe(pd.DataFrame(table_rows).style.format({"Persentase Node (%)": "{:.2f}"}), use_container_width=True)


def unique_existing_columns(df, columns):
    return [col for col in dict.fromkeys(columns) if col in df.columns]


def prepare_centrality_policy_dataframe(graph_obj, partition, selected_centrality_key, dusun_attr, publish_mode=True):
    centrality_name = {
        "degree": "Degree Centrality",
        "betweenness": "Betweenness Centrality",
        "closeness": "Closeness Centrality",
        "eigenvector": "Eigenvector Centrality",
    }.get(selected_centrality_key, "Degree Centrality")
    all_centrality_specs = CENTRALITY_METRIC_SPECS
    centrality_metric_values = {
        metric_label: compute_centrality_on_similarity_graph(graph_obj, metric_key)
        for metric_label, metric_key in all_centrality_specs
    }
    node_ids_local = list(graph_obj.nodes())
    anon_node_map = make_anonymized_node_mapping(node_ids_local)
    dusun_values = sorted(
        {
            str(graph_obj.nodes[n].get(dusun_attr, "Tidak tersedia"))
            for n in node_ids_local
        }
    )
    dusun_code_map = {val: f"Dusun-{idx + 1}" for idx, val in enumerate(dusun_values)}
    rows = []
    for n in node_ids_local:
        n_attr = graph_obj.nodes[n]
        profesi_raw = n_attr.get(
            "profesi pekerjaan",
            n_attr.get("profesi_pekerjaan", n_attr.get("pekerjaan", n_attr.get("profesi", "Tidak diketahui"))),
        )
        bansos_status = "Penerima" if int(_safe_float_metric(n_attr.get("bansos_num"), default=0.0) > 0) == 1 else "Tidak Menerima"
        row = {
            "family_id": n,
            "Nama": n_attr.get("nama", "-"),
            "Kode Node": anon_node_map.get(str(n), "N-000"),
            "Klaster Louvain": int(partition.get(n, -1)),
            "Dusun": n_attr.get(dusun_attr, "-"),
            "Dusun/Kode Dusun": (
                dusun_code_map.get(str(n_attr.get(dusun_attr, "Tidak tersedia")), "Dusun-0")
                if publish_mode
                else str(n_attr.get(dusun_attr, "-"))
            ),
            "Profesi/Pekerjaan": str(profesi_raw).strip() if pd.notnull(profesi_raw) else "Tidak diketahui",
            "Status Bansos": bansos_status,
            "IKD Agregat": _safe_float_metric(n_attr.get("f_ikr_dari_rekap_kk"), default=np.nan),
            "internet_num": n_attr.get("internet_num", n_attr.get("digital_num", np.nan)),
            "ponsel_num": n_attr.get("ponsel_num", np.nan),
        }
        for metric_label, _ in all_centrality_specs:
            row[metric_label] = float(centrality_metric_values.get(metric_label, {}).get(n, 0.0))
        row["Status BPS"] = n_attr.get("kategori_ikr", categorize_ikr_bps(row["IKD Agregat"])[0])
        for dim_label, dim_col in IKD_DIMENSION_MAP:
            row[dim_label] = _safe_float_metric(n_attr.get(dim_col), default=np.nan)
        rows.append(row)

    df_role = pd.DataFrame(rows)
    if df_role.empty:
        return df_role, centrality_name, all_centrality_specs

    c_series = pd.to_numeric(df_role[centrality_name], errors="coerce").fillna(0.0)
    c_q25 = float(c_series.quantile(0.25)) if not c_series.empty else 0.0
    c_q75 = float(c_series.quantile(0.75)) if not c_series.empty else 0.0
    df_role["_centrality_q25"] = c_q25
    df_role["_centrality_q75"] = c_q75
    df_role["Level Centrality"] = df_role[centrality_name].map(lambda v: centrality_level_from_quantile(v, c_q25, c_q75))
    df_role["Level IKD"] = df_role.apply(lambda r: ikr_level_from_value(r.get("IKD Agregat"), r.get("Status BPS")), axis=1)
    df_role["Akses Informasi"] = df_role.apply(access_info_label, axis=1)
    df_role = add_centrality_role_features(df_role)
    df_role["Centrality terpilih"] = df_role[centrality_name]
    df_role["Hover Aman"] = df_role.apply(lambda r: safe_hover_text(r, publish_mode=publish_mode), axis=1)
    return df_role.sort_values(centrality_name, ascending=False).reset_index(drop=True), centrality_name, all_centrality_specs


def render_centrality_analysis_page(
    graph_obj,
    partition,
    df_v,
    selected_desa,
    selected_centrality_key,
    col_spasial,
    layout_spread=2.2,
):
    st.markdown(f"<h1 class='main-header'>Analisis Centrality: {selected_desa}</h1>", unsafe_allow_html=True)
    publish_mode = st.toggle("Mode publikasi / anonimisasi", value=True, key=f"centrality_page_publish_{selected_centrality_key}")
    highlight_roles = st.toggle("Highlight Aktor Strategis", value=True, key=f"centrality_page_highlight_{selected_centrality_key}")
    dusun_attr = "dusun" if "dusun" in df_v.columns else col_spasial
    df_role, centrality_name, all_centrality_specs = prepare_centrality_policy_dataframe(
        graph_obj,
        partition,
        selected_centrality_key,
        dusun_attr,
        publish_mode=publish_mode,
    )
    if df_role.empty:
        st.info("Nilai centrality belum bisa dihitung untuk graf saat ini.")
        return

    cluster_opts = sorted(df_role["Klaster Louvain"].dropna().unique().tolist())
    dusun_filter_col = "Dusun/Kode Dusun" if publish_mode else "Dusun"
    dusun_opts = sorted(df_role[dusun_filter_col].fillna("Tidak tersedia").astype(str).unique().tolist())
    f1, f2 = st.columns(2)
    with f1:
        selected_clusters = st.multiselect("Pilih Klaster", options=cluster_opts, default=cluster_opts, key=f"cent_page_cluster_{selected_centrality_key}")
    with f2:
        selected_dusun = st.multiselect("Pilih Dusun/Kode Dusun", options=dusun_opts, default=dusun_opts, key=f"cent_page_dusun_{selected_centrality_key}")
    df_view = df_role[
        df_role["Klaster Louvain"].isin(selected_clusters)
        & df_role[dusun_filter_col].astype(str).isin([str(x) for x in selected_dusun])
    ].copy()
    if df_view.empty:
        st.warning("Filter klaster/dusun tidak memiliki node. Silakan ubah filter.")
        return

    selected_node_set = set(df_view["family_id"].tolist())
    graph_view = graph_obj.subgraph(selected_node_set).copy()
    df_view, centrality_name, all_centrality_specs = prepare_centrality_policy_dataframe(
        graph_view,
        {n: partition.get(n, -1) for n in graph_view.nodes()},
        selected_centrality_key,
        dusun_attr,
        publish_mode=publish_mode,
    )
    df_view = df_view.sort_values(centrality_name, ascending=False).reset_index(drop=True)
    node_ids_view = list(graph_view.nodes())
    pos = build_clustered_network_layout(graph_view, partition=partition, layout_spread=layout_spread, seed=42)
    edge_weights = [_safe_float_metric(d.get("weight"), default=0.0) for _, _, d in graph_view.edges(data=True)]
    edge_min = float(min(edge_weights)) if edge_weights else 0.0
    edge_max = float(max(edge_weights)) if edge_weights else 1.0
    edge_span = max(edge_max - edge_min, 1e-9)
    visible_edges = select_representative_edges(graph_view, max_edges=int(np.clip(graph_view.number_of_nodes() * 1.25, 120, 650)), per_node=1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Node Terpilih", f"{len(df_view):,}")
    c2.metric("Edge Terpilih", f"{graph_view.number_of_edges():,}")
    c3.metric("Nilai Tertinggi", f"{float(df_view[centrality_name].max()):.6f}")
    c4.metric("Node Strategis", f"{int(df_view['Peran Struktural'].ne('Node umum').sum()):,}")

    st.markdown(f"#### Visual Jaringan Centrality ({centrality_name})")
    fig_cent = go.Figure()
    add_network_edge_traces(
        fig_cent,
        visible_edges,
        pos,
        edge_min,
        edge_span,
        color_fn=lambda *_args, **_kwargs: "rgba(148, 163, 184, 0.24)",
        base_width=0.26,
        width_scale=0.72,
        hover=False,
    )
    lookup = df_view.set_index("family_id")
    node_order = [n for n in node_ids_view if n in lookup.index and n in pos]
    node_vals = np.array([float(lookup.loc[n, centrality_name]) for n in node_order], dtype=float)
    size_vals = centrality_marker_sizes(node_vals, len(node_order))
    if highlight_roles:
        for role in [r for r in CENTRALITY_ROLE_ORDER if r in set(df_view["Peran Struktural"].astype(str))]:
            role_nodes = [n for n in node_order if str(lookup.loc[n, "Peran Struktural"]) == role]
            if not role_nodes:
                continue
            fig_cent.add_trace(
                go.Scatter(
                    x=[pos[n][0] for n in role_nodes],
                    y=[pos[n][1] for n in role_nodes],
                    mode="markers",
                    marker=dict(
                        size=[size_vals[node_order.index(n)] for n in role_nodes],
                        color=CENTRALITY_ROLE_COLORS.get(role, "#94A3B8"),
                        opacity=0.32 if role == "Node umum" else 0.9,
                        line=dict(color=NETWORK_NODE_LINE, width=0.7),
                    ),
                    text=[safe_hover_text(lookup.loc[n], publish_mode=publish_mode) for n in role_nodes],
                    hoverinfo="text",
                    name=centrality_role_display_label(role),
                )
            )
    else:
        cmin = float(np.nanmin(node_vals)) if len(node_vals) else 0.0
        cmax = float(np.nanmax(node_vals)) if len(node_vals) else 1.0
        fig_cent.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in node_order],
                y=[pos[n][1] for n in node_order],
                mode="markers",
                marker=dict(
                    size=size_vals,
                    color=node_vals.tolist(),
                    colorscale="Viridis",
                    showscale=True,
                    cmin=cmin,
                    cmax=cmax if cmax > cmin else cmin + 1e-6,
                    colorbar=dict(title=centrality_name),
                    opacity=0.84,
                    line=dict(color=NETWORK_NODE_LINE, width=0.5),
                ),
                text=[safe_hover_text(lookup.loc[n], publish_mode=publish_mode) for n in node_order],
                hoverinfo="text",
                showlegend=False,
            )
        )
    top5_nodes = df_view.head(5)["family_id"].tolist()
    top5_nodes = [n for n in top5_nodes if n in pos]
    if top5_nodes:
        size_lookup = {n: size_vals[idx] for idx, n in enumerate(node_order)}
        fig_cent.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in top5_nodes],
                y=[pos[n][1] for n in top5_nodes],
                mode="markers",
                marker=dict(size=[size_lookup.get(n, 12.0) + 5.0 for n in top5_nodes], color="rgba(255,255,255,0)", line=dict(color="#111827", width=1.8)),
                hoverinfo="skip",
                name="Top 5 centrality",
                showlegend=True,
            )
        )
    style_network_figure(fig_cent, title=f"Jaringan Louvain Menurut {centrality_name}", height=690, showlegend=highlight_roles)
    st.plotly_chart(fig_cent, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    st.markdown("#### Peta Aktor Strategis Empat Centrality")
    render_strategic_actor_centrality_map(df_view)

    st.markdown("#### Matriks Degree-Eigenvector Aktor Strategis")
    render_degree_eigenvector_role_matrix(df_view)

    st.markdown("#### Profil Aktor Strategis")
    top_n = st.slider("Jumlah node pada tabel profil", min_value=5, max_value=30, value=15, step=5, key=f"centrality_page_profile_topn_{selected_centrality_key}")
    role_rank = {role: idx for idx, role in enumerate(CENTRALITY_ROLE_ORDER)}
    df_profile = df_view.copy()
    df_profile["_role_rank"] = df_profile["Peran Struktural"].map(role_rank).fillna(len(role_rank))
    df_profile = df_profile.sort_values(["_role_rank", centrality_name], ascending=[True, False]).head(top_n).copy()
    profile_cols = unique_existing_columns(
        df_profile,
        [
            "Kode Node",
            "Klaster Louvain",
            "Dusun/Kode Dusun",
            "Centrality terpilih",
            "Degree Centrality",
            "Betweenness Centrality",
            "Closeness Centrality",
            "Eigenvector Centrality",
            "Sinyal Centrality",
            "Jumlah Metrik Tinggi",
            "Peran Struktural",
            "Basis Metrik Peran",
            "Peran Aktor",
            "Implikasi Program",
            "Catatan Etika",
        ],
    )
    st.dataframe(
        df_profile[profile_cols].style.format(
            {
                "Centrality terpilih": "{:.6f}",
                "Degree Centrality": "{:.6f}",
                "Betweenness Centrality": "{:.6f}",
                "Closeness Centrality": "{:.6f}",
                "Eigenvector Centrality": "{:.6f}",
            }
        ),
        use_container_width=True,
    )
    st.download_button(
        "Unduh Tabel Anonim",
        data=df_profile[profile_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"profil_node_strategis_anonim_{selected_centrality_key}.csv",
        mime="text/csv",
        key=f"centrality_page_download_{selected_centrality_key}",
    )

    st.markdown("#### Komposisi Aktor Strategis per Klaster dan Dusun")
    render_role_composition_charts(df_view, publish_mode=publish_mode)

    st.markdown("#### Top 5 Centrality per Pilar")
    top_dusun_col = "Dusun/Kode Dusun" if publish_mode else "Dusun"
    tabs = st.tabs([label.replace(" Centrality", "") for label, _ in all_centrality_specs])
    for tab, (metric_label, _) in zip(tabs, all_centrality_specs):
        with tab:
            top_cols = unique_existing_columns(
                df_view,
                [
                    "Kode Node",
                    top_dusun_col,
                    metric_label,
                    "Sinyal Centrality",
                    "Jumlah Metrik Tinggi",
                    "Peran Aktor",
                    "Basis Metrik Peran",
                ],
            )
            st.dataframe(
                df_view[top_cols].sort_values(metric_label, ascending=False).head(5).style.format({metric_label: "{:.6f}"}),
                use_container_width=True,
            )

    st.info(build_centrality_policy_narrative(df_view, centrality_name))
    with subbab_dropdown("Catatan Etika dan Batasan Interpretasi", expanded=publish_mode):
        st.markdown(
            """
            - Data mikro rumah tangga adalah data sensitif.
            - Identitas individu/KK perlu disamarkan dalam visualisasi publik.
            - Peran aktor hanya membaca posisi jaringan dari degree, betweenness, closeness, dan eigenvector.
            - Centrality tidak boleh dimaknai sebagai status sosial, tingkat kesejahteraan, atau kelayakan bantuan.
            - Degree, betweenness, closeness, dan eigenvector memiliki tafsir berbeda sehingga perlu dibaca bersama konteks lapangan.
            - Hasil ini mendukung pemetaan aktor strategis, bukan dasar tunggal penetapan tokoh atau sasaran program.
            - Hindari penyebutan nama orang, alamat spesifik, atau koordinat presisi pada materi presentasi/publikasi.
            """
        )


def build_centrality_top_table_figure(df_table, title, score_col):
    if df_table is None or df_table.empty:
        return None
    table_df = df_table.copy()
    zebra_fill = ["#F8FAFC" if idx % 2 == 0 else "#EEF2F7" for idx in range(len(table_df))]
    for col in ["Nama", "Dusun", "Peran", "Sinyal"]:
        table_df[col] = table_df[col].fillna("-").astype(str)
    table_df[score_col] = pd.to_numeric(table_df[score_col], errors="coerce").map(
        lambda x: f"{x:.6f}" if pd.notnull(x) else "-"
    )

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[1.25, 1.1, 2.85, 2.0, 1.2],
                header=dict(
                    values=["Node", "Dusun/Kode", "Peran (Basis Metrik)", "Sinyal Centrality", "Skor Centrality"],
                    fill_color="#0F172A",
                    font=dict(color="#F8FAFC", size=13),
                    align="left",
                    line_color="rgba(255,255,255,0.08)",
                    height=34,
                ),
                cells=dict(
                    values=[
                        table_df["Nama"],
                        table_df["Dusun"],
                        table_df["Peran"],
                        table_df["Sinyal"],
                        table_df[score_col],
                    ],
                    fill_color=[
                        zebra_fill,
                        zebra_fill,
                        zebra_fill,
                        zebra_fill,
                        zebra_fill,
                    ],
                    font=dict(color="#0F172A", size=12),
                    align="left",
                    line_color="#E2E8F0",
                    height=32,
                ),
            )
        ]
    )
    fig.update_layout(
        title=title,
        height=280,
        margin=dict(l=12, r=12, t=52, b=12),
        paper_bgcolor="rgba(255,255,255,0.0)",
    )
    return fig


def detect_lat_lon_columns(columns):
    lower_map = {str(c).lower().strip(): c for c in columns}
    lat_candidates = ["lat", "latitude", "lintang", "y", "coord_lat"]
    lon_candidates = ["lon", "lng", "long", "longitude", "bujur", "x", "coord_lon"]
    lat_col = next((lower_map[k] for k in lat_candidates if k in lower_map), None)
    lon_col = next((lower_map[k] for k in lon_candidates if k in lower_map), None)
    return lat_col, lon_col


def build_spatial_node_figure(
    graph_obj,
    node_ids,
    node_color_vals,
    node_hover_text,
    title,
    spatial_mode="Spasial OSM",
    marker_size=11,
    colorscale="Viridis",
    colorbar=None,
    cmin=None,
    cmax=None,
    line_color=NETWORK_NODE_LINE,
    line_width=0.6,
):
    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        return None
    sample_cols = set()
    for n in graph_obj.nodes():
        sample_cols.update(graph_obj.nodes[n].keys())
        break
    lat_col, lon_col = detect_lat_lon_columns(sample_cols)
    if not lat_col or not lon_col:
        return None

    lats, lons, colors, hovers = [], [], [], []
    for idx, n in enumerate(node_ids):
        if n not in graph_obj.nodes():
            continue
        lat_v = _safe_float_metric(graph_obj.nodes[n].get(lat_col), default=np.nan)
        lon_v = _safe_float_metric(graph_obj.nodes[n].get(lon_col), default=np.nan)
        if not (np.isfinite(lat_v) and np.isfinite(lon_v)):
            continue
        lats.append(float(lat_v))
        lons.append(float(lon_v))
        colors.append(node_color_vals[idx] if idx < len(node_color_vals) else 0.0)
        hovers.append(node_hover_text[idx] if idx < len(node_hover_text) else f"Node: {n}")
    if len(lats) == 0:
        return None

    marker_cfg = dict(
        size=marker_size,
        color=colors,
        colorscale=colorscale,
        showscale=True,
    )
    if colorbar is not None:
        marker_cfg["colorbar"] = colorbar
    if cmin is not None:
        marker_cfg["cmin"] = cmin
    if cmax is not None:
        marker_cfg["cmax"] = cmax

    fig = go.Figure(
        go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode="markers",
            marker=marker_cfg,
            text=hovers,
            hoverinfo="text",
            showlegend=False,
        )
    )
    center_lat = float(np.mean(lats))
    center_lon = float(np.mean(lons))
    mapbox_cfg = dict(
        zoom=12,
        center=dict(lat=center_lat, lon=center_lon),
    )
    if spatial_mode == "Spasial ArcGIS":
        mapbox_cfg["style"] = "white-bg"
        mapbox_cfg["layers"] = [
            {
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
                "below": "traces",
            }
        ]
    else:
        mapbox_cfg["style"] = "open-street-map"
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left"),
        height=560,
        template=PUBLICATION_TEMPLATE,
        margin=dict(l=20, r=20, t=60, b=20),
        mapbox=mapbox_cfg,
    )
    return fig


def categorize_ikr_bps(score):
    s = _safe_float_metric(score, default=np.nan)
    if not np.isfinite(s):
        return ("Tidak Valid", 0)
    # Referensi BPS (2014): kategori capaian skor (skala 0-100).
    if s >= 80.0:
        return ("Sangat Tinggi", 4)
    if s >= 70.0:
        return ("Tinggi", 3)
    if s >= 60.0:
        return ("Sedang", 2)
    return ("Rendah", 1)


def add_bps_ikr_category(df_in, ikr_col="f_ikr_dari_rekap_kk"):
    if ikr_col not in df_in.columns:
        return df_in.copy()
    df_out = df_in.copy()
    mapped = df_out[ikr_col].apply(categorize_ikr_bps)
    df_out["kategori_ikr"] = mapped.apply(lambda x: x[0])
    df_out["kategori_ikr_code"] = mapped.apply(lambda x: int(x[1]))
    return df_out


def compute_montes_within_between_assortativity(
    graph_obj,
    category_attr="kategori_ikr_code",
    group_attr="cluster",
    invalid_category_values=None,
):
    # Referensi Montes et al. (2018): dekomposisi within-between berbasis delta kategorikal.
    if graph_obj is None or graph_obj.number_of_nodes() < 2 or graph_obj.number_of_edges() == 0:
        return {
            "q_w_star": 0.0,
            "q_b_star": 0.0,
            "m_w": 0.0,
            "m_b": 0.0,
            "n_nodes": int(graph_obj.number_of_nodes() if graph_obj is not None else 0),
            "n_edges": int(graph_obj.number_of_edges() if graph_obj is not None else 0),
        }

    nodes = list(graph_obj.nodes())
    k = {n: _safe_float_metric(graph_obj.degree(n, weight="weight"), default=0.0) for n in nodes}
    two_m = float(sum(k.values()))
    if two_m <= 1e-12:
        return {
            "q_w_star": 0.0,
            "q_b_star": 0.0,
            "m_w": 0.0,
            "m_b": 0.0,
            "n_nodes": int(graph_obj.number_of_nodes()),
            "n_edges": int(graph_obj.number_of_edges()),
        }

    m_w = 0.0
    m_b = 0.0
    k_w = {n: 0.0 for n in nodes}
    k_b = {n: 0.0 for n in nodes}
    for u, v, d in graph_obj.edges(data=True):
        w = _safe_float_metric(d.get("weight"), default=0.0)
        if graph_obj.nodes[u].get(group_attr) == graph_obj.nodes[v].get(group_attr):
            m_w += w
            k_w[u] += w
            k_w[v] += w
        else:
            m_b += w
            k_b[u] += w
            k_b[v] += w

    two_m_w = 2.0 * m_w
    two_m_b = 2.0 * m_b
    sum_w = 0.0
    sum_b = 0.0
    exp_w_masked = 0.0
    exp_b_masked = 0.0
    invalid_set = set() if invalid_category_values is None else set(invalid_category_values)
    for i in nodes:
        xi = graph_obj.nodes[i].get(category_attr, 0)
        hi = graph_obj.nodes[i].get(group_attr, None)
        for j in nodes:
            xj = graph_obj.nodes[j].get(category_attr, 0)
            hj = graph_obj.nodes[j].get(group_attr, None)
            xi_valid = pd.notnull(xi) and xi not in invalid_set
            xj_valid = pd.notnull(xj) and xj not in invalid_set
            delta_x = 1.0 if xi_valid and xj_valid and xi == xj else 0.0
            delta_h = 1.0 if hi == hj else 0.0
            a_ij = _safe_float_metric(graph_obj[i][j].get("weight"), default=0.0) if graph_obj.has_edge(i, j) else 0.0
            expected_w = (k_w[i] * k_w[j] / two_m_w) if two_m_w > 1e-12 else 0.0
            expected_b = (k_b[i] * k_b[j] / two_m_b) if two_m_b > 1e-12 else 0.0
            mask_w = delta_x * delta_h
            mask_b = delta_x * (1.0 - delta_h)
            sum_w += (a_ij - expected_w) * mask_w
            sum_b += (a_ij - expected_b) * mask_b
            exp_w_masked += expected_w * mask_w
            exp_b_masked += expected_b * mask_b

    # Qw dan Qb raw sesuai pembagi 2m_w / 2m_b.
    q_w_raw = (sum_w / two_m_w) if two_m_w > 1e-12 else 0.0
    q_b_raw = (sum_b / two_m_b) if two_m_b > 1e-12 else 0.0

    # Normalisasi Montes (Pers. 6-7): Q* = Q / Qmax.
    # Qmax numerik dihitung dari: (2m - sum(expected_term_masked)).
    q_w_max_num = (two_m_w - exp_w_masked) if two_m_w > 1e-12 else 0.0
    q_b_max_num = (two_m_b - exp_b_masked) if two_m_b > 1e-12 else 0.0
    q_w_max = (q_w_max_num / two_m_w) if two_m_w > 1e-12 else 0.0
    q_b_max = (q_b_max_num / two_m_b) if two_m_b > 1e-12 else 0.0
    q_w_star = (q_w_raw / q_w_max) if abs(q_w_max) > 1e-12 else 0.0
    q_b_star = (q_b_raw / q_b_max) if abs(q_b_max) > 1e-12 else 0.0
    q_w_star = float(np.clip(q_w_star, -1.0, 1.0))
    q_b_star = float(np.clip(q_b_star, -1.0, 1.0))
    return {
        "q_w_star": float(q_w_star),
        "q_b_star": float(q_b_star),
        "q_w_raw": float(q_w_raw),
        "q_b_raw": float(q_b_raw),
        "q_w_max": float(q_w_max),
        "q_b_max": float(q_b_max),
        "m_w": float(m_w),
        "m_b": float(m_b),
        "n_nodes": int(graph_obj.number_of_nodes()),
        "n_edges": int(graph_obj.number_of_edges()),
    }


def build_category_connection_breakdown(
    graph_obj,
    category_attr="kategori_ikr",
    group_attr="cluster",
    category_order=None,
    invalid_label="Tidak Valid",
):
    if graph_obj is None or graph_obj.number_of_edges() == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    category_order = list(category_order or [])
    order_map = {str(cat): idx for idx, cat in enumerate(category_order)}

    def normalize_cat(val):
        if pd.isna(val):
            return invalid_label
        txt = str(val).strip()
        return txt if txt else invalid_label

    def sort_pair(cat_a, cat_b):
        idx_a = order_map.get(cat_a, len(order_map))
        idx_b = order_map.get(cat_b, len(order_map))
        return (cat_a, cat_b) if (idx_a, cat_a) <= (idx_b, cat_b) else (cat_b, cat_a)

    rows = []
    for u, v, d in graph_obj.edges(data=True):
        cat_u = normalize_cat(graph_obj.nodes[u].get(category_attr, invalid_label))
        cat_v = normalize_cat(graph_obj.nodes[v].get(category_attr, invalid_label))
        cat_a, cat_b = sort_pair(cat_u, cat_v)
        scope = "Within" if graph_obj.nodes[u].get(group_attr) == graph_obj.nodes[v].get(group_attr) else "Between"
        weight = _safe_float_metric(d.get("weight"), default=0.0)
        rows.append(
            {
                "Ruang": scope,
                "Kategori 1": cat_a,
                "Kategori 2": cat_b,
                "Pasangan": f"{cat_a} - {cat_b}",
                "Jenis Pasangan": "Sama" if cat_a == cat_b else "Beda",
                "Bobot Edge": weight,
                "Jumlah Edge": 1,
            }
        )

    if not rows:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_pairs = pd.DataFrame(rows)
    df_summary = (
        df_pairs.groupby(["Ruang", "Kategori 1", "Kategori 2", "Pasangan", "Jenis Pasangan"], as_index=False)
        .agg({"Bobot Edge": "sum", "Jumlah Edge": "sum"})
    )
    scope_weight = df_summary.groupby("Ruang")["Bobot Edge"].transform("sum")
    scope_edge = df_summary.groupby("Ruang")["Jumlah Edge"].transform("sum")
    df_summary["Persentase Bobot (%)"] = np.where(scope_weight > 0, (df_summary["Bobot Edge"] / scope_weight) * 100.0, 0.0)
    df_summary["Persentase Edge (%)"] = np.where(scope_edge > 0, (df_summary["Jumlah Edge"] / scope_edge) * 100.0, 0.0)
    df_summary["Urut 1"] = df_summary["Kategori 1"].map(lambda x: order_map.get(str(x), len(order_map)))
    df_summary["Urut 2"] = df_summary["Kategori 2"].map(lambda x: order_map.get(str(x), len(order_map)))
    df_summary = df_summary.sort_values(["Ruang", "Urut 1", "Urut 2", "Pasangan"]).reset_index(drop=True)

    matrix_rows = []
    for _, row in df_summary.iterrows():
        matrix_rows.append(
            {
                "Ruang": row["Ruang"],
                "Kategori Baris": row["Kategori 1"],
                "Kategori Kolom": row["Kategori 2"],
                "Persentase Bobot (%)": float(row["Persentase Bobot (%)"]),
            }
        )
        if row["Kategori 1"] != row["Kategori 2"]:
            matrix_rows.append(
                {
                    "Ruang": row["Ruang"],
                    "Kategori Baris": row["Kategori 2"],
                    "Kategori Kolom": row["Kategori 1"],
                    "Persentase Bobot (%)": float(row["Persentase Bobot (%)"]),
                }
            )
    df_matrix_long = pd.DataFrame(matrix_rows)
    return df_pairs, df_summary, df_matrix_long


def build_spatial_category_figure(
    df_map,
    lat_col,
    lon_col,
    category_col,
    hover_col,
    title,
    spatial_mode="Spasial ArcGIS",
    category_order=None,
    category_colors=None,
    marker_size=12,
):
    if df_map is None or df_map.empty or lat_col not in df_map.columns or lon_col not in df_map.columns:
        return None

    plot_df = df_map.copy()
    plot_df[category_col] = plot_df[category_col].fillna("Tidak Valid").astype(str)
    plot_df[lat_col] = pd.to_numeric(plot_df[lat_col], errors="coerce")
    plot_df[lon_col] = pd.to_numeric(plot_df[lon_col], errors="coerce")
    plot_df = plot_df[plot_df[lat_col].notna() & plot_df[lon_col].notna()].copy()
    if plot_df.empty:
        return None

    uniq = plot_df[category_col].unique().tolist()
    category_order = list(category_order or [])
    ordered_categories = [cat for cat in category_order if cat in uniq]
    ordered_categories += sorted([cat for cat in uniq if cat not in ordered_categories])
    category_colors = category_colors or {}

    fig = go.Figure()
    for idx, category in enumerate(ordered_categories):
        sub = plot_df[plot_df[category_col] == category]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scattermapbox(
                lat=sub[lat_col],
                lon=sub[lon_col],
                mode="markers",
                marker=dict(
                    size=marker_size,
                    color=category_colors.get(category, CONTRAST_COLORS[idx % len(CONTRAST_COLORS)]),
                    opacity=0.90,
                ),
                name=category,
                text=sub[hover_col],
                hoverinfo="text",
            )
        )

    mapbox_cfg = dict(
        zoom=12,
        center=dict(
            lat=float(plot_df[lat_col].mean()),
            lon=float(plot_df[lon_col].mean()),
        ),
    )
    if spatial_mode == "Spasial ArcGIS":
        mapbox_cfg["style"] = "white-bg"
        mapbox_cfg["layers"] = [
            {
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
                "below": "traces",
            }
        ]
    else:
        mapbox_cfg["style"] = "open-street-map"

    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left"),
        height=620,
        template=PUBLICATION_TEMPLATE,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            title=dict(text=category_col),
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.85)",
        ),
        mapbox=mapbox_cfg,
    )
    return fig


def build_spatial_numeric_figure(
    df_map,
    lat_col,
    lon_col,
    value_col,
    hover_col,
    title,
    spatial_mode="Spasial ArcGIS",
    marker_size_col=None,
    colorscale="RdYlGn",
    colorbar_title="Nilai",
):
    if df_map is None or df_map.empty or lat_col not in df_map.columns or lon_col not in df_map.columns:
        return None

    plot_df = df_map.copy()
    plot_df[lat_col] = pd.to_numeric(plot_df[lat_col], errors="coerce")
    plot_df[lon_col] = pd.to_numeric(plot_df[lon_col], errors="coerce")
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")
    plot_df = plot_df[plot_df[lat_col].notna() & plot_df[lon_col].notna()].copy()
    if plot_df.empty:
        return None

    marker_size = 12
    if marker_size_col and marker_size_col in plot_df.columns:
        size_vals = pd.to_numeric(plot_df[marker_size_col], errors="coerce").fillna(0)
        marker_size = (size_vals.clip(lower=0) * 3) + 10

    fig = go.Figure(
        go.Scattermapbox(
            lat=plot_df[lat_col],
            lon=plot_df[lon_col],
            mode="markers",
            marker=dict(
                size=marker_size,
                color=plot_df[value_col],
                colorscale=colorscale,
                showscale=True,
                colorbar=dict(title=colorbar_title),
                cmin=float(plot_df[value_col].min()) if plot_df[value_col].notna().any() else 0.0,
                cmax=float(plot_df[value_col].max()) if plot_df[value_col].notna().any() else 100.0,
                opacity=0.92,
            ),
            text=plot_df[hover_col],
            hoverinfo="text",
            showlegend=False,
        )
    )

    mapbox_cfg = dict(
        zoom=12,
        center=dict(
            lat=float(plot_df[lat_col].mean()),
            lon=float(plot_df[lon_col].mean()),
        ),
    )
    if spatial_mode == "Spasial ArcGIS":
        mapbox_cfg["style"] = "white-bg"
        mapbox_cfg["layers"] = [
            {
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
                "below": "traces",
            }
        ]
    else:
        mapbox_cfg["style"] = "open-street-map"

    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left"),
        height=620,
        template=PUBLICATION_TEMPLATE,
        margin=dict(l=20, r=20, t=60, b=20),
        mapbox=mapbox_cfg,
    )
    return fig


def render_bansos_spatial_analysis_page(
    df_v,
    graph_obj,
    partition,
    spatial_mode="Spasial ArcGIS",
    selected_dimension_col="f_a_dari_rekap_kk",
    map_color_mode="IKD Agregat",
    filter_mode="Semua KK",
    dim_thresholds=None,
):
    st.markdown("<h1 class='main-header'>Analisis Bansos Spasial</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='premium-hero'><b>Fokus Halaman:</b> memetakan penerima bansos berdasarkan "
        "dimensi IKD yang dipilih. Warna node selalu mengikuti <b>IKD agregat</b> sebagai tingkat "
        "kesejahteraan ekonomi, sedangkan detail hover menampilkan skor dimensi dan jenis bansos yang diterima.</div>",
        unsafe_allow_html=True,
    )

    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        st.warning("Graf analisis belum tersedia.")
        return

    dim_thresholds = dim_thresholds or {}
    node_ids = list(graph_obj.nodes())
    df_nodes = (
        df_v[df_v["family_id"].isin(node_ids)]
        .drop_duplicates("family_id")
        .copy()
    )
    if df_nodes.empty:
        st.warning("Tidak ada node graf yang cocok dengan data desa terpilih.")
        return

    lat_col, lon_col = detect_lat_lon_columns(df_nodes.columns)
    raw_bansos_col = resolve_first_existing_column(df_nodes.columns, ["bansos", "keikutsertaan program bantuan", "program bantuan", "bantuan sosial", "bansos bantuan"])
    df_nodes["cluster"] = df_nodes["family_id"].map(lambda fid: int(partition.get(fid, -1)))
    df_nodes["Cluster Louvain"] = df_nodes["cluster"].map(lambda x: f"Klaster {x}" if x >= 0 else "Tidak Terklaster")
    df_nodes["Status Bansos"] = df_nodes["bansos_num"].apply(lambda x: "Penerima" if int(_safe_float_metric(x, default=0.0) > 0) == 1 else "Non-Penerima")
    df_nodes["F_IKD"] = pd.to_numeric(df_nodes.get("f_ikr_dari_rekap_kk"), errors="coerce")
    df_nodes["Jenis Bansos"] = (
        df_nodes[raw_bansos_col].astype(str).replace({"nan": "-", "None": "-", "none": "-", "": "-"}).fillna("-")
        if raw_bansos_col
        else "-"
    )

    dim_lookup = {col: label for label, col in IKD_DIMENSION_MAP}
    selected_dimension_label = dim_lookup.get(selected_dimension_col, selected_dimension_col)
    df_nodes["Skor Dimensi Pilihan"] = pd.to_numeric(df_nodes.get(selected_dimension_col), errors="coerce")
    selected_threshold = float(dim_thresholds.get(selected_dimension_col, 60.0))
    df_nodes["Status Dimensi Pilihan"] = np.where(
        df_nodes["Skor Dimensi Pilihan"].le(selected_threshold).fillna(False),
        f"Rentan {selected_dimension_label}",
        f"Tidak Rentan {selected_dimension_label}",
    )

    weak_dim_labels = []
    weak_dim_count = np.zeros(len(df_nodes), dtype=int)
    for dim_label, col_name in IKD_DIMENSION_MAP:
        thr = float(dim_thresholds.get(col_name, 60.0))
        dim_vals = pd.to_numeric(df_nodes.get(col_name), errors="coerce")
        weak_flag = (dim_vals <= thr).fillna(False)
        weak_dim_count += weak_flag.astype(int).to_numpy()
        weak_dim_labels.append(
            weak_flag.map(lambda x, lbl=dim_label: lbl if bool(x) else None)
        )
    weak_dim_df = pd.concat(weak_dim_labels, axis=1) if weak_dim_labels else pd.DataFrame(index=df_nodes.index)
    df_nodes["Jumlah Dimensi Rentan"] = weak_dim_count.astype(int)
    df_nodes["Dimensi Rentan"] = weak_dim_df.apply(
        lambda row: ", ".join([str(v) for v in row.tolist() if pd.notnull(v)]) if len(row) else "-",
        axis=1,
    )
    def classify_bps_bansos(row):
        kategori = str(row.get("kategori_ikr", "Tidak Valid"))
        status = str(row.get("Status Bansos", "Non-Penerima"))
        if kategori not in {"Rendah", "Sedang", "Tinggi", "Sangat Tinggi"}:
            return "Tidak Valid"
        return f"{kategori} - {'Penerima' if status == 'Penerima' else 'Belum Menerima'}"

    df_nodes["Status BPS-Bansos"] = df_nodes.apply(classify_bps_bansos, axis=1)
    df_nodes["Label Dimensi Rentan"] = df_nodes["Jumlah Dimensi Rentan"].map(lambda x: f"{int(x)} dimensi rentan")

    nx.set_node_attributes(
        graph_obj,
        df_nodes.set_index("family_id")[["kategori_ikr", "kategori_ikr_code"]].to_dict("index"),
    )
    montes_res = compute_montes_within_between_assortativity(
        graph_obj,
        category_attr="kategori_ikr_code",
        group_attr="cluster",
        invalid_category_values={0},
    )
    q_w_star = float(montes_res["q_w_star"])
    q_b_star = float(montes_res["q_b_star"])

    total_nodes = int(len(df_nodes))
    total_receiver = int((df_nodes["Status Bansos"] == "Penerima").sum())
    total_selected_dim_vulnerable = int(df_nodes["Status Dimensi Pilihan"].eq(f"Rentan {selected_dimension_label}").sum())
    total_rendah_terima = int((df_nodes["Status BPS-Bansos"] == "Rendah - Penerima").sum())
    total_rendah_belum = int((df_nodes["Status BPS-Bansos"] == "Rendah - Belum Menerima").sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Node Tersedia", total_nodes)
    k2.metric("Penerima Bansos", total_receiver)
    k3.metric(f"Rentan {selected_dimension_label}", total_selected_dim_vulnerable)
    k4.metric("Rendah - Penerima", total_rendah_terima)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Qw*", f"{q_w_star:.4f}")
    m2.metric("Qb*", f"{q_b_star:.4f}")
    m3.metric("Rendah - Belum Menerima", total_rendah_belum)
    m4.metric("Rata-rata Dimensi Rentan", f"{float(df_nodes['Jumlah Dimensi Rentan'].mean()):.2f}")

    st.markdown(
        f"<div class='soft-card'><b>Interpretasi Cepat:</b><br>"
        f"Qw* = <b>{q_w_star:.3f}</b> menunjukkan kekompakan kategori BPS di dalam klaster, "
        f"sedangkan Qb* = <b>{q_b_star:.3f}</b> membaca kemiripan strata BPS antar-klaster. "
        f"Pada page ini, <b>warna node memakai IKD agregat</b> sebagai base kesejahteraan ekonomi, "
        f"sedangkan analisis bansos dibaca dari dimensi terpilih <b>{selected_dimension_label}</b> "
        f"dengan ambang <b>{selected_threshold:.1f}</b>.</div>",
        unsafe_allow_html=True,
    )

    map_df = df_nodes.copy()
    if filter_mode == "Penerima Bansos":
        map_df = map_df[map_df["Status Bansos"] == "Penerima"].copy()
    elif filter_mode == "Rendah - Penerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Rendah - Penerima"].copy()
    elif filter_mode == "Rendah - Belum Menerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Rendah - Belum Menerima"].copy()
    elif filter_mode == "Sedang - Penerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Sedang - Penerima"].copy()
    elif filter_mode == "Sedang - Belum Menerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Sedang - Belum Menerima"].copy()
    elif filter_mode == "Tinggi - Penerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Tinggi - Penerima"].copy()
    elif filter_mode == "Tinggi - Belum Menerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Tinggi - Belum Menerima"].copy()
    elif filter_mode == "Sangat Tinggi - Penerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Sangat Tinggi - Penerima"].copy()
    elif filter_mode == "Sangat Tinggi - Belum Menerima":
        map_df = map_df[map_df["Status BPS-Bansos"] == "Sangat Tinggi - Belum Menerima"].copy()
    elif filter_mode == "Rentan Dimensi Terpilih":
        map_df = map_df[map_df["Status Dimensi Pilihan"] == f"Rentan {selected_dimension_label}"].copy()
    elif filter_mode == "Penerima pada Dimensi Terpilih":
        map_df = map_df[
            (map_df["Status Bansos"] == "Penerima")
            & (map_df["Status Dimensi Pilihan"] == f"Rentan {selected_dimension_label}")
        ].copy()

    df_nodes["nama"] = df_nodes.get("nama", df_nodes["family_id"]).astype(str)
    hover_text = []
    for _, row in map_df.iterrows():
        dim_lines = []
        for dim_label, col_name in IKD_DIMENSION_MAP:
            dim_lines.append(f"{dim_label}: {_safe_float_metric(row.get(col_name), default=np.nan):.2f}")
        hover_text.append(
            f"Nama: {row.get('nama', row.get('family_id', '-'))}"
            f"<br>Family ID: {row.get('family_id', '-')}"
            f"<br>Status Bansos: {row.get('Status Bansos', '-')}"
            f"<br>Jenis Bansos: {row.get('Jenis Bansos', '-')}"
            f"<br>Status BPS-Bansos: {row.get('Status BPS-Bansos', '-')}"
            f"<br>Kategori BPS: {row.get('kategori_ikr', '-')}"
            f"<br>IKD Agregat: {_safe_float_metric(row.get('F_IKD'), default=np.nan):.2f}"
            f"<br>{selected_dimension_label}: {_safe_float_metric(row.get('Skor Dimensi Pilihan'), default=np.nan):.2f}"
            f"<br>Status Dimensi: {row.get('Status Dimensi Pilihan', '-')}"
            f"<br>Cluster: {row.get('Cluster Louvain', '-')}"
            f"<br>Dimensi Rentan: {row.get('Dimensi Rentan', '-')}"
            f"<br>{'<br>'.join(dim_lines)}"
        )
    map_df["__hover_text__"] = hover_text

    c_map, c_table = st.columns([1.6, 1.0], gap="large")
    with c_map:
        st.markdown("### Peta Spasial Bansos")
        if not lat_col or not lon_col:
            st.warning("Kolom lat/lon belum ditemukan sehingga peta spasial belum bisa ditampilkan.")
        elif map_df.empty:
            st.info("Tidak ada node yang cocok dengan filter peta saat ini.")
        else:
            if map_color_mode == "Status Bansos (YA/TIDAK)":
                fig_map = build_spatial_category_figure(
                    map_df,
                    lat_col=lat_col,
                    lon_col=lon_col,
                    category_col="Status Bansos",
                    hover_col="__hover_text__",
                    title=f"Peta Persebaran Bansos berdasarkan {selected_dimension_label} ({filter_mode})",
                    spatial_mode=spatial_mode,
                    category_order=["Penerima", "Non-Penerima"],
                    category_colors={"Penerima": "#0f766e", "Non-Penerima": "#b91c1c"},
                    marker_size=12,
                )
            elif map_color_mode == "Status BPS-Bansos":
                fig_map = build_spatial_category_figure(
                    map_df,
                    lat_col=lat_col,
                    lon_col=lon_col,
                    category_col="Status BPS-Bansos",
                    hover_col="__hover_text__",
                    title=f"Peta Persebaran Bansos berdasarkan {selected_dimension_label} ({filter_mode})",
                    spatial_mode=spatial_mode,
                    category_order=list(BANSOS_TARGETING_COLORS.keys()),
                    category_colors=BANSOS_TARGETING_COLORS,
                    marker_size=12,
                )
            else:
                fig_map = build_spatial_numeric_figure(
                    map_df,
                    lat_col=lat_col,
                    lon_col=lon_col,
                    value_col="F_IKD",
                    hover_col="__hover_text__",
                    title=f"Peta Persebaran Bansos berdasarkan {selected_dimension_label} ({filter_mode})",
                    spatial_mode=spatial_mode,
                    marker_size_col="bansos_num",
                    colorscale="RdYlGn",
                    colorbar_title="IKD Agregat",
                )
            if fig_map is not None:
                st.plotly_chart(fig_map, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            else:
                st.warning("Koordinat belum valid untuk divisualisasikan di peta.")

    with c_table:
        st.markdown(f"### Ringkasan {selected_dimension_label}")
        summary_cols = [
            "Status Dimensi Pilihan",
            "Status BPS-Bansos",
            "Status Bansos",
            "kategori_ikr",
            "Jenis Bansos",
        ]
        df_summary = (
            df_nodes.groupby(summary_cols, dropna=False)
            .size()
            .reset_index(name="Jumlah KK")
            .sort_values(["Jumlah KK", "Status Dimensi Pilihan"], ascending=[False, True])
        )
        st.dataframe(df_summary, use_container_width=True)

        jenis_summary = (
            df_nodes[df_nodes["Status Bansos"] == "Penerima"]
            .groupby(["Status Dimensi Pilihan", "Jenis Bansos"], dropna=False)
            .size()
            .reset_index(name="Jumlah KK")
            .sort_values(["Status Dimensi Pilihan", "Jumlah KK"], ascending=[True, False])
        )
        st.markdown("#### Jenis Bansos pada Dimensi Terpilih")
        st.dataframe(jenis_summary, use_container_width=True)

    dim_priority_cols = [col for _, col in IKD_DIMENSION_MAP if col in df_nodes.columns]
    if dim_priority_cols:
        dim_long = (
            df_nodes.melt(
                id_vars=["Status Bansos"],
                value_vars=dim_priority_cols,
                var_name="Dimensi",
                value_name="Skor",
            )
        )
        dim_label_map = {col: label for label, col in IKD_DIMENSION_MAP}
        dim_long["Dimensi"] = dim_long["Dimensi"].map(lambda c: dim_label_map.get(c, c))
        dim_long["Skor"] = pd.to_numeric(dim_long["Skor"], errors="coerce")
        dim_long = dim_long.dropna(subset=["Skor"])
        if not dim_long.empty:
            fig_dim = px.box(
                dim_long,
                x="Dimensi",
                y="Skor",
                color="Status Bansos",
                color_discrete_map={"Penerima": "#0f766e", "Non-Penerima": "#b91c1c"},
                title="Sebaran Skor Tiap Dimensi menurut Status Penerimaan Bansos",
            )
            fig_dim.update_layout(template="plotly_white", height=460, xaxis_title="", yaxis_title="Skor")
            st.plotly_chart(fig_dim, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    bansos_dim_focus = df_nodes[["family_id", "nama", "Status Bansos", "Jenis Bansos", "kategori_ikr", "F_IKD", "Skor Dimensi Pilihan", "Status Dimensi Pilihan", "Cluster Louvain"]].copy()
    fig_focus = px.scatter(
        bansos_dim_focus,
        x="Skor Dimensi Pilihan",
        y="F_IKD",
        color="Status Bansos",
        symbol="kategori_ikr",
        hover_data=["nama", "family_id", "Jenis Bansos", "Cluster Louvain"],
        color_discrete_map={"Penerima": "#0f766e", "Non-Penerima": "#b91c1c"},
        labels={"F_IKD": "IKD Agregat", "Skor Dimensi Pilihan": selected_dimension_label},
        title=f"Relasi {selected_dimension_label} terhadap IKD Agregat dan Penerimaan Bansos",
    )
    fig_focus.add_vline(x=selected_threshold, line_dash="dash", line_color="#475569")
    fig_focus.update_layout(template="plotly_white", height=460, xaxis_title=selected_dimension_label, yaxis_title="IKD Agregat")
    st.plotly_chart(fig_focus, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    detail_cols = [
        "family_id",
        "nama",
        "Status Bansos",
        "Jenis Bansos",
        "Status Dimensi Pilihan",
        "Skor Dimensi Pilihan",
        "Status BPS-Bansos",
        "kategori_ikr",
        "F_IKD",
        "Cluster Louvain",
        "Jumlah Dimensi Rentan",
        "Dimensi Rentan",
    ] + [col for _, col in IKD_DIMENSION_MAP if col in df_nodes.columns]
    if lat_col and lon_col:
        detail_cols += [lat_col, lon_col]
    detail_cols = [col for col in detail_cols if col in df_nodes.columns]
    st.markdown("### Detail Rumah Tangga")
    detail_display_df = df_nodes[detail_cols].sort_values(
        ["Status Dimensi Pilihan", "Status Bansos", "F_IKD"],
        ascending=[True, True, True],
    )
    detail_display_df = detail_display_df.rename(
        columns={
            **{col: label for label, col in IKD_DIMENSION_MAP},
            "F_IKD": "IKD Agregat",
            "kategori_ikr": "Kategori IKD",
        }
    )
    st.dataframe(
        detail_display_df,
        use_container_width=True,
    )


def build_labeled_attribute_connection_breakdown(
    graph_obj,
    attr_name,
    value_map=None,
    group_attr="cluster",
    category_order=None,
    invalid_label="Tidak Valid",
):
    if graph_obj is None or graph_obj.number_of_edges() == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    value_map = value_map or {}

    def map_value(val):
        if pd.isna(val):
            return invalid_label
        key = val
        if isinstance(val, str):
            key = val.strip()
        mapped = value_map.get(key, value_map.get(str(key), key))
        mapped_txt = str(mapped).strip()
        return mapped_txt if mapped_txt else invalid_label

    graph_tmp = graph_obj.copy()
    for n in graph_tmp.nodes():
        graph_tmp.nodes[n]["__mapped_attr__"] = map_value(graph_tmp.nodes[n].get(attr_name, invalid_label))
    return build_category_connection_breakdown(
        graph_tmp,
        category_attr="__mapped_attr__",
        group_attr=group_attr,
        category_order=category_order,
        invalid_label=invalid_label,
    )


def build_spatial_indicator_profile(
    graph_obj,
    dusun_attr,
    indicator_specs,
):
    if graph_obj is None or graph_obj.number_of_nodes() == 0 or not dusun_attr:
        return pd.DataFrame()

    rows = []
    dusun_vals = pd.Series([graph_obj.nodes[n].get(dusun_attr) for n in graph_obj.nodes()]).fillna("Tidak Valid").astype(str)
    dusun_order = sorted(dusun_vals.unique().tolist())
    for dusun_name in dusun_order:
        dusun_nodes = [n for n in graph_obj.nodes() if str(graph_obj.nodes[n].get(dusun_attr, "Tidak Valid")) == dusun_name]
        if not dusun_nodes:
            continue
        sub_g = graph_obj.subgraph(dusun_nodes).copy()
        row = {
            "Dusun": dusun_name,
            "Jumlah KK": int(len(dusun_nodes)),
            "Jumlah Edge Internal": int(sub_g.number_of_edges()),
            "Total Bobot Edge Internal": float(sum(_safe_float_metric(d.get("weight"), default=0.0) for _, _, d in sub_g.edges(data=True))),
        }
        for spec in indicator_specs:
            label = spec["label"]
            col = spec["col"]
            bin_vals = [int(_safe_float_metric(graph_obj.nodes[n].get(col), default=0.0) > 0) for n in dusun_nodes]
            yes_count = int(sum(bin_vals))
            row[f"{label} - Jumlah YA"] = yes_count
            row[f"{label} - Persentase YA (%)"] = float((yes_count / len(dusun_nodes)) * 100.0) if dusun_nodes else 0.0

            yy_weight = 0.0
            yn_weight = 0.0
            nn_weight = 0.0
            yy_edges = 0
            yn_edges = 0
            nn_edges = 0
            total_weight = 0.0
            total_edges = 0
            for u, v, d in sub_g.edges(data=True):
                u_yes = int(_safe_float_metric(sub_g.nodes[u].get(col), default=0.0) > 0)
                v_yes = int(_safe_float_metric(sub_g.nodes[v].get(col), default=0.0) > 0)
                weight = _safe_float_metric(d.get("weight"), default=0.0)
                total_weight += weight
                total_edges += 1
                if u_yes == 1 and v_yes == 1:
                    yy_weight += weight
                    yy_edges += 1
                elif u_yes == 0 and v_yes == 0:
                    nn_weight += weight
                    nn_edges += 1
                else:
                    yn_weight += weight
                    yn_edges += 1

            row[f"{label} - YA-YA Bobot (%)"] = float((yy_weight / total_weight) * 100.0) if total_weight > 0 else 0.0
            row[f"{label} - YA-TIDAK Bobot (%)"] = float((yn_weight / total_weight) * 100.0) if total_weight > 0 else 0.0
            row[f"{label} - TIDAK-TIDAK Bobot (%)"] = float((nn_weight / total_weight) * 100.0) if total_weight > 0 else 0.0
            row[f"{label} - YA-YA Edge (%)"] = float((yy_edges / total_edges) * 100.0) if total_edges > 0 else 0.0
            row[f"{label} - YA-TIDAK Edge (%)"] = float((yn_edges / total_edges) * 100.0) if total_edges > 0 else 0.0
            row[f"{label} - TIDAK-TIDAK Edge (%)"] = float((nn_edges / total_edges) * 100.0) if total_edges > 0 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def build_dusun_cluster_composition(graph_obj, dusun_attr, partition=None):
    if graph_obj is None or graph_obj.number_of_nodes() == 0 or not dusun_attr:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    rows = []
    for n in graph_obj.nodes():
        node_attr = graph_obj.nodes[n]
        dusun_raw = node_attr.get(dusun_attr, "Tidak Valid")
        dusun_name = str(dusun_raw).strip() if pd.notnull(dusun_raw) and str(dusun_raw).strip() else "Tidak Valid"
        raw_cluster = partition.get(n, node_attr.get("cluster", -1)) if partition else node_attr.get("cluster", -1)
        try:
            cluster_id = int(raw_cluster)
        except (TypeError, ValueError):
            cluster_id = -1
        rows.append(
            {
                "family_id": n,
                "Dusun": dusun_name,
                "ID Klaster Internal": cluster_id,
            }
        )

    if not rows:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_nodes = pd.DataFrame(rows)
    cluster_order = sorted(df_nodes["ID Klaster Internal"].dropna().unique().tolist())
    valid_cluster_order = [cid for cid in cluster_order if cid >= 0]
    cluster_label_map = {cid: f"Klaster {idx + 1}" for idx, cid in enumerate(valid_cluster_order)}
    for cid in cluster_order:
        if cid < 0:
            cluster_label_map[cid] = "Tidak Terklaster"
    df_nodes["Klaster Louvain"] = df_nodes["ID Klaster Internal"].map(cluster_label_map)
    cluster_label_order = [cluster_label_map[cid] for cid in cluster_order]

    df_long = (
        df_nodes.groupby(["Dusun", "ID Klaster Internal", "Klaster Louvain"], as_index=False)
        .size()
        .rename(columns={"size": "Jumlah KK"})
    )
    dusun_totals = (
        df_nodes.groupby("Dusun", as_index=False)
        .size()
        .rename(columns={"size": "Total KK Dusun"})
    )
    cluster_totals = (
        df_nodes.groupby("Klaster Louvain", as_index=False)
        .size()
        .rename(columns={"size": "Total KK Klaster"})
    )
    total_kk = int(df_nodes.shape[0])
    df_long = df_long.merge(dusun_totals, on="Dusun", how="left").merge(cluster_totals, on="Klaster Louvain", how="left")
    df_long["Persentase dalam Dusun (%)"] = np.where(
        df_long["Total KK Dusun"] > 0,
        (df_long["Jumlah KK"] / df_long["Total KK Dusun"]) * 100.0,
        0.0,
    )
    df_long["Persentase dari Total Graf (%)"] = (df_long["Jumlah KK"] / max(total_kk, 1)) * 100.0
    df_long["Persentase dari Klaster (%)"] = np.where(
        df_long["Total KK Klaster"] > 0,
        (df_long["Jumlah KK"] / df_long["Total KK Klaster"]) * 100.0,
        0.0,
    )
    df_long["Label Persen"] = df_long["Persentase dalam Dusun (%)"].map(lambda v: f"{v:.1f}%" if v >= 5 else "")
    df_long = df_long.sort_values(["Dusun", "ID Klaster Internal"]).reset_index(drop=True)

    count_pivot = (
        df_long.pivot_table(index="Dusun", columns="Klaster Louvain", values="Jumlah KK", aggfunc="sum", fill_value=0)
        .reindex(columns=cluster_label_order, fill_value=0)
        .astype(int)
    )
    pct_pivot = (
        df_long.pivot_table(index="Dusun", columns="Klaster Louvain", values="Persentase dalam Dusun (%)", aggfunc="sum", fill_value=0.0)
        .reindex(columns=cluster_label_order, fill_value=0.0)
    )
    wide_rows = dusun_totals.set_index("Dusun").sort_index().copy()
    for cluster_label in cluster_label_order:
        wide_rows[f"{cluster_label} - Jumlah KK"] = count_pivot.get(cluster_label, pd.Series(0, index=wide_rows.index)).reindex(wide_rows.index, fill_value=0).astype(int)
        wide_rows[f"{cluster_label} - Persentase (%)"] = pct_pivot.get(cluster_label, pd.Series(0.0, index=wide_rows.index)).reindex(wide_rows.index, fill_value=0.0)
    df_wide = wide_rows.reset_index()

    df_overall = (
        df_nodes.groupby(["ID Klaster Internal", "Klaster Louvain"], as_index=False)
        .size()
        .rename(columns={"size": "Jumlah KK"})
        .sort_values("ID Klaster Internal")
        .reset_index(drop=True)
    )
    df_overall["Persentase KK (%)"] = (df_overall["Jumlah KK"] / max(total_kk, 1)) * 100.0
    df_overall["Label Batang"] = df_overall.apply(
        lambda r: f"{int(r['Jumlah KK'])} KK ({float(r['Persentase KK (%)']):.1f}%)",
        axis=1,
    )
    return df_long, df_wide, df_overall


LOUVAIN_CLUSTER_PROFILE_COLUMNS = [
    "Klaster Louvain",
    "Jumlah Node",
    "Persentase Node (%)",
    "Jumlah Edge Internal",
    "Density Internal",
    "Rerata Weighted Degree",
    "Rerata Degree Centrality",
    "Rerata Betweenness Centrality",
    "Rerata Closeness Centrality",
    "Rerata Eigenvector Centrality",
    "Rerata IKD Agregat",
    "Kategori IKD Dominan",
    "Persentase IKD Rendah (%)",
    "Persentase IKD Sedang (%)",
    "Persentase IKD Tinggi (%)",
    "Persentase IKD Sangat Tinggi (%)",
    "Rerata Sandang, Pangan, dan Papan",
    "Rerata Pendidikan",
    "Rerata Sosial, Hukum, dan HAM",
    "Rerata Kesehatan dan Pekerjaan",
    "Rerata Lingkungan dan Infrastruktur",
    "Dimensi Terlemah",
    "Nilai Dimensi Terlemah",
    "Dimensi Terkuat",
    "Nilai Dimensi Terkuat",
    "Persentase Penerima Bansos (%)",
    "Persentase Belum Menerima Bansos (%)",
    "Persentase Akses Internet/Informasi (%)",
    "Persentase Kepemilikan Ponsel (%)",
    "Dusun Dominan / Kode Dusun Dominan",
    "Persentase Dusun Dominan (%)",
    "Top Profesi/Pekerjaan",
    "Label Karakter Klaster",
    "Implikasi Program",
    "Catatan Etika",
]


def _is_missing_profile_value(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "null"}


def _profile_text(value, default="Tidak tersedia"):
    if _is_missing_profile_value(value):
        return default
    text = str(value).strip()
    return text if text else default


def _clean_profile_category(value, default="Tidak tersedia"):
    text = _profile_text(value, default=default)
    if text.lower() in {"0", "0.0", "-", "tidak valid", "tidak diketahui"}:
        return default
    return text


def _profile_mean(values, default=0.0):
    series = pd.to_numeric(pd.Series(list(values)), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if series.empty:
        return float(default)
    return float(series.mean())


def _profile_binary_percent(values):
    vals = list(values)
    if not vals:
        return 0.0
    series = pd.to_numeric(pd.Series(vals), errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return float((series.gt(0).sum() / max(len(series), 1)) * 100.0)


def _profile_top_values(values, top_n=3, default="Tidak tersedia"):
    cleaned = [
        _clean_profile_category(v, default="")
        for v in list(values)
    ]
    cleaned = [v for v in cleaned if v and v.lower() not in {"tidak tersedia", "tidak diketahui"}]
    if not cleaned:
        return default
    counts = pd.Series(cleaned).value_counts().head(top_n)
    return ", ".join([f"{idx} ({int(val)})" for idx, val in counts.items()])


def _profile_value_from_sources(node_id, node_attr, df_lookup, candidates, default=np.nan):
    for candidate in [c for c in candidates if c]:
        if candidate in node_attr and not _is_missing_profile_value(node_attr.get(candidate)):
            return node_attr.get(candidate)
        if df_lookup is not None and candidate in df_lookup.columns:
            try:
                if node_id in df_lookup.index:
                    value = df_lookup.at[node_id, candidate]
                elif str(node_id) in df_lookup.index:
                    value = df_lookup.at[str(node_id), candidate]
                else:
                    continue
                if not _is_missing_profile_value(value):
                    return value
            except Exception:
                continue
    return default


def _cluster_id_for_node(node_id, node_attr, partition):
    partition = partition or {}
    partition_str = {str(k): v for k, v in partition.items()} if partition else {}
    raw_cluster = partition.get(node_id, partition_str.get(str(node_id), node_attr.get("cluster", -1)))
    try:
        return int(raw_cluster)
    except (TypeError, ValueError):
        return -1


def compute_louvain_profile_centrality_maps(graph_obj):
    node_ids = list(graph_obj.nodes()) if graph_obj is not None else []
    empty_maps = {
        "Weighted Degree": {n: 0.0 for n in node_ids},
        "Degree Centrality": {n: 0.0 for n in node_ids},
        "Betweenness Centrality": {n: 0.0 for n in node_ids},
        "Closeness Centrality": {n: 0.0 for n in node_ids},
        "Eigenvector Centrality": {n: 0.0 for n in node_ids},
    }
    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        return empty_maps
    try:
        empty_maps["Weighted Degree"] = {
            n: _safe_float_metric(v, default=0.0)
            for n, v in compute_centrality_on_similarity_graph(graph_obj, "degree").items()
        }
    except Exception:
        empty_maps["Weighted Degree"] = {n: float(graph_obj.degree(n, weight="weight")) for n in node_ids}
    try:
        empty_maps["Degree Centrality"] = {
            n: _safe_float_metric(v, default=0.0)
            for n, v in nx.degree_centrality(graph_obj).items()
        }
    except Exception:
        denom = max(graph_obj.number_of_nodes() - 1, 1)
        empty_maps["Degree Centrality"] = {n: float(graph_obj.degree(n) / denom) for n in node_ids}
    for label, metric_key in [
        ("Betweenness Centrality", "betweenness"),
        ("Closeness Centrality", "closeness"),
        ("Eigenvector Centrality", "eigenvector"),
    ]:
        try:
            metric_map = compute_centrality_on_similarity_graph(graph_obj, metric_key)
            empty_maps[label] = {n: _safe_float_metric(metric_map.get(n), default=0.0) for n in node_ids}
        except Exception:
            empty_maps[label] = {n: 0.0 for n in node_ids}
    return empty_maps


def build_louvain_cluster_node_profile_dataframe(graph_obj, partition, df_v=None, col_spasial=None, publish_mode=True):
    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        return pd.DataFrame()

    df_lookup = None
    if isinstance(df_v, pd.DataFrame) and not df_v.empty and "family_id" in df_v.columns:
        df_lookup = df_v.copy()
        df_lookup["family_id"] = df_lookup["family_id"].astype(str)
        df_lookup = df_lookup.drop_duplicates("family_id")
        df_lookup = df_lookup.set_index("family_id", drop=False)

    node_ids = list(graph_obj.nodes())
    anon_map = make_anonymized_node_mapping(node_ids)
    centrality_maps = compute_louvain_profile_centrality_maps(graph_obj)
    spatial_candidates = [col_spasial, "dusun", "rt", "rw", "desa", "deskel"]
    name_candidates = ["nama", "Nama", "nama kk", "nama_kk", "nama kepala keluarga", "nama_kepala_keluarga", "kepala keluarga"]
    profession_candidates = ["profesi pekerjaan", "profesi_pekerjaan", "pekerjaan", "profesi", "jenis pekerjaan"]

    raw_spatial_values = []
    for n in node_ids:
        raw_spatial_values.append(
            _profile_text(
                _profile_value_from_sources(n, graph_obj.nodes[n], df_lookup, spatial_candidates, default="Tidak tersedia"),
                default="Tidak tersedia",
            )
        )
    spatial_code_map = {
        val: f"Dusun-{idx + 1}"
        for idx, val in enumerate(sorted({v for v in raw_spatial_values if v.lower() not in {"tidak tersedia", "tidak valid"}}))
    }

    rows = []
    for idx, n in enumerate(node_ids):
        n_attr = graph_obj.nodes[n]
        ikr_val = _safe_float_metric(
            _profile_value_from_sources(n, n_attr, df_lookup, ["f_ikr_dari_rekap_kk"], default=np.nan),
            default=np.nan,
        )
        category_raw = _profile_value_from_sources(n, n_attr, df_lookup, ["kategori_ikr"], default=None)
        category_text = _profile_text(category_raw, default="")
        if category_text not in {"Rendah", "Sedang", "Tinggi", "Sangat Tinggi"}:
            category_text = categorize_ikr_bps(ikr_val)[0]
        bansos_num = _safe_float_metric(
            _profile_value_from_sources(n, n_attr, df_lookup, ["bansos_num", "bansos"], default=0.0),
            default=0.0,
        )
        internet_num = _safe_float_metric(
            _profile_value_from_sources(n, n_attr, df_lookup, ["internet_num", "digital_num", "media informasi"], default=0.0),
            default=0.0,
        )
        ponsel_num = _safe_float_metric(
            _profile_value_from_sources(n, n_attr, df_lookup, ["ponsel_num", "kepemilikan ponsel", "ponsel"], default=0.0),
            default=0.0,
        )
        raw_spatial = raw_spatial_values[idx]
        row = {
            "family_id": n,
            "Nama": _profile_text(
                _profile_value_from_sources(n, n_attr, df_lookup, name_candidates, default="Tidak tersedia"),
                default="Tidak tersedia",
            ),
            "Kode Node": anon_map.get(str(n), f"N-{idx + 1:03d}"),
            "Klaster Louvain": _cluster_id_for_node(n, n_attr, partition),
            "Dusun": raw_spatial,
            "Dusun/Kode Dusun": spatial_code_map.get(raw_spatial, raw_spatial) if publish_mode else raw_spatial,
            "Profesi/Pekerjaan": _clean_profile_category(
                _profile_value_from_sources(n, n_attr, df_lookup, profession_candidates, default="Tidak tersedia"),
                default="Tidak tersedia",
            ),
            "IKD Agregat": ikr_val,
            "Kategori IKD": category_text,
            "Status BPS": category_text,
            "bansos_num": bansos_num,
            "internet_num": internet_num,
            "ponsel_num": ponsel_num,
            "Status Bansos": "Penerima" if bansos_num > 0 else "Belum Menerima",
        }
        for label, col_name in IKD_DIMENSION_MAP:
            row[label] = _safe_float_metric(
                _profile_value_from_sources(n, n_attr, df_lookup, [col_name], default=np.nan),
                default=np.nan,
            )
        for metric_label, metric_map in centrality_maps.items():
            row[metric_label] = _safe_float_metric(metric_map.get(n), default=0.0)
        rows.append(row)

    df_nodes = pd.DataFrame(rows)
    if df_nodes.empty:
        return df_nodes
    df_nodes["Akses Informasi"] = df_nodes.apply(access_info_label, axis=1)
    df_nodes["Hover Aman"] = df_nodes.apply(lambda r: safe_hover_text(r, publish_mode=publish_mode), axis=1)
    return df_nodes


def _cluster_centrality_flags(row):
    centrality_val = _safe_float_metric(row.get("Rerata Weighted Degree", row.get("Rerata Degree Centrality")), default=0.0)
    q25 = _safe_float_metric(row.get("_centrality_q25"), default=centrality_val)
    q75 = _safe_float_metric(row.get("_centrality_q75"), default=centrality_val)
    has_spread = abs(q75 - q25) > 1e-12
    if not has_spread:
        return False, False
    return centrality_val >= q75, centrality_val <= q25


def classify_louvain_cluster_character(row):
    ikr = _safe_float_metric(row.get("Rerata IKD Agregat"), default=np.nan)
    weak_dim_value = _safe_float_metric(row.get("Nilai Dimensi Terlemah"), default=np.nan)
    internet_pct = _safe_float_metric(row.get("Persentase Akses Internet/Informasi (%)"), default=0.0)
    phone_pct = _safe_float_metric(row.get("Persentase Kepemilikan Ponsel (%)"), default=0.0)
    spatial_pct = _safe_float_metric(row.get("Persentase Dusun Dominan (%)"), default=0.0)
    centrality_high, centrality_low = _cluster_centrality_flags(row)
    access_high = max(internet_pct, phone_pct) >= 70.0 or ((internet_pct + phone_pct) / 2.0) >= 60.0

    if np.isfinite(ikr) and ikr < 60.0 and centrality_low:
        label = "Klaster rentan dan relatif terisolasi"
    elif np.isfinite(ikr) and ikr < 60.0 and centrality_high:
        label = "Klaster prioritas verifikasi berbasis data"
    elif np.isfinite(ikr) and 60.0 <= ikr < 70.0 and np.isfinite(weak_dim_value) and weak_dim_value < 55.0:
        label = "Klaster rentan pada dimensi spesifik"
    elif np.isfinite(ikr) and ikr >= 60.0 and access_high and centrality_high:
        label = "Klaster penghubung informasi potensial"
    elif np.isfinite(ikr) and ikr >= 60.0 and np.isfinite(weak_dim_value) and weak_dim_value < 60.0:
        label = "Klaster rentan pada dimensi spesifik"
    elif spatial_pct <= 40.0:
        label = "Klaster lintas wilayah"
    elif np.isfinite(ikr) and ikr >= 70.0 and (not np.isfinite(weak_dim_value) or weak_dim_value >= 60.0):
        label = "Klaster relatif stabil"
    else:
        label = "Klaster menengah dengan kapasitas campuran"

    if spatial_pct > 60.0 and "spasial" not in label.lower():
        if label == "Klaster menengah dengan kapasitas campuran":
            return "Klaster berbasis konsentrasi spasial"
        return f"{label} - berbasis konsentrasi spasial"
    return label


def recommend_cluster_program(row):
    weak_dim = str(row.get("Dimensi Terlemah", "") or "").strip()
    ikr = _safe_float_metric(row.get("Rerata IKD Agregat"), default=np.nan)
    centrality_high, centrality_low = _cluster_centrality_flags(row)
    recommendation_map = {
        "Pendidikan": "Pendampingan pendidikan, validasi partisipasi sekolah, dan penguatan akses belajar.",
        "Lingkungan dan Infrastruktur": "Prioritas perbaikan akses infrastruktur dasar, sanitasi, air, listrik, atau konektivitas.",
        "Kesehatan dan Pekerjaan": "Pendampingan layanan kesehatan, jaminan sosial, dan penguatan kapasitas ekonomi rumah tangga.",
        "Sandang, Pangan, dan Papan": "Verifikasi kebutuhan dasar rumah tangga, ketahanan pangan, dan kondisi hunian.",
        "Sosial, Hukum, dan HAM": "Pendampingan akses perlindungan sosial, keamanan, dan partisipasi sosial.",
    }
    recommendations = []
    for key, text in recommendation_map.items():
        if key.lower() in weak_dim.lower():
            recommendations.append(text)
            break
    if not recommendations:
        recommendations.append("Pendalaman profil klaster melalui musyawarah data, verifikasi lapangan, dan triangulasi indikator kesejahteraan.")
    if centrality_high:
        recommendations.append(
            "Klaster ini juga dapat menjadi kanal komunikasi program, dengan tetap memperhatikan persetujuan dan konteks sosial lokal."
        )
    if centrality_low and np.isfinite(ikr) and ikr < 60.0:
        recommendations.append("Perlu pendekatan langsung karena posisi jaringan relatif tidak menonjol.")
    return " ".join(recommendations)


def generate_louvain_cluster_story(row):
    def fmt_num(value, decimals=2, default="Tidak tersedia"):
        num = _safe_float_metric(value, default=np.nan)
        if not np.isfinite(num):
            return default
        return f"{num:.{decimals}f}"

    cluster_id = row.get("Klaster Louvain", "-")
    jumlah_node = int(_safe_float_metric(row.get("Jumlah Node"), default=0.0))
    pct_node = fmt_num(row.get("Persentase Node (%)"), decimals=1)
    ikr_avg = fmt_num(row.get("Rerata IKD Agregat"), decimals=2)
    category = _profile_text(row.get("Kategori IKD Dominan"), default="Tidak tersedia")
    weak_dim = _profile_text(row.get("Dimensi Terlemah"), default="Tidak tersedia")
    weak_val = fmt_num(row.get("Nilai Dimensi Terlemah"), decimals=2)
    dominant_spatial = _profile_text(row.get("Dusun Dominan / Kode Dusun Dominan"), default="Tidak tersedia")
    dominant_spatial_pct = fmt_num(row.get("Persentase Dusun Dominan (%)"), decimals=1)
    bansos_pct = fmt_num(row.get("Persentase Penerima Bansos (%)"), decimals=1)
    internet_pct = fmt_num(row.get("Persentase Akses Internet/Informasi (%)"), decimals=1)
    phone_pct = fmt_num(row.get("Persentase Kepemilikan Ponsel (%)"), decimals=1)
    label = _profile_text(row.get("Label Karakter Klaster"), default="Klaster menengah dengan kapasitas campuran")
    implication = _profile_text(row.get("Implikasi Program"), default="-")
    return (
        f"Klaster {cluster_id} berisi {jumlah_node} node atau {pct_node}% dari total node. "
        f"Rerata IKD agregat klaster ini adalah {ikr_avg} dan masuk kategori dominan {category}. "
        f"Dimensi yang paling lemah adalah {weak_dim} dengan nilai rata-rata {weak_val}. "
        f"Secara spasial, klaster ini dominan berada di {dominant_spatial} sebesar {dominant_spatial_pct}%. "
        f"Proporsi penerima bansos sebesar {bansos_pct}%, sementara akses informasi sebesar {internet_pct}% dan kepemilikan ponsel sebesar {phone_pct}%. "
        f"Berdasarkan kombinasi kondisi kesejahteraan, posisi jaringan, dan konsentrasi spasial, klaster ini dapat dibaca sebagai {label}. "
        f"Implikasi program yang disarankan adalah {implication} "
        "Hasil ini merupakan indikasi awal, tidak menunjuk individu sebagai sasaran pasti, dan tetap memerlukan verifikasi lapangan."
    )


def build_louvain_cluster_characteristics(graph_obj, partition, df_v, col_spasial=None, publish_mode=True):
    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        return pd.DataFrame(columns=LOUVAIN_CLUSTER_PROFILE_COLUMNS)

    df_nodes = build_louvain_cluster_node_profile_dataframe(
        graph_obj=graph_obj,
        partition=partition,
        df_v=df_v,
        col_spasial=col_spasial,
        publish_mode=publish_mode,
    )
    if df_nodes.empty:
        return pd.DataFrame(columns=LOUVAIN_CLUSTER_PROFILE_COLUMNS)

    total_nodes = max(int(df_nodes.shape[0]), 1)
    spatial_display_col = "Dusun/Kode Dusun" if publish_mode else "Dusun"
    rows = []
    for cluster_id, df_cluster in df_nodes.groupby("Klaster Louvain", dropna=False):
        cluster_nodes = df_cluster["family_id"].tolist()
        g_cluster = graph_obj.subgraph(cluster_nodes).copy()
        category_counts = df_cluster["Kategori IKD"].fillna("Tidak Valid").astype(str).value_counts()
        valid_category_counts = category_counts[[c for c in category_counts.index if c in {"Rendah", "Sedang", "Tinggi", "Sangat Tinggi"}]]
        dominant_category = valid_category_counts.idxmax() if not valid_category_counts.empty else "Tidak Valid"
        dim_means = {
            label: _profile_mean(df_cluster[label], default=np.nan)
            for label, _ in IKD_DIMENSION_MAP
            if label in df_cluster.columns
        }
        valid_dim_means = {label: val for label, val in dim_means.items() if np.isfinite(val)}
        if valid_dim_means:
            weakest_dim, weakest_val = min(valid_dim_means.items(), key=lambda item: item[1])
            strongest_dim, strongest_val = max(valid_dim_means.items(), key=lambda item: item[1])
        else:
            weakest_dim, weakest_val = "Tidak tersedia", 0.0
            strongest_dim, strongest_val = "Tidak tersedia", 0.0
        spatial_values = df_cluster[spatial_display_col].fillna("Tidak tersedia").astype(str)
        spatial_values_valid = spatial_values[
            ~spatial_values.str.lower().isin({"tidak tersedia", "tidak valid", "nan", "none", ""})
        ]
        spatial_counts = spatial_values_valid.value_counts()
        dominant_spatial = spatial_counts.idxmax() if not spatial_counts.empty else "Tidak tersedia"
        dominant_spatial_pct = float((spatial_counts.max() / max(len(df_cluster), 1)) * 100.0) if not spatial_counts.empty else 0.0
        n_cluster = int(len(df_cluster))
        row = {
            "Klaster Louvain": int(cluster_id) if pd.notnull(cluster_id) else -1,
            "Jumlah Node": n_cluster,
            "Persentase Node (%)": float((n_cluster / total_nodes) * 100.0),
            "Jumlah Edge Internal": int(g_cluster.number_of_edges()),
            "Density Internal": float(nx.density(g_cluster)) if g_cluster.number_of_nodes() > 1 else 0.0,
            "Rerata Weighted Degree": _profile_mean(df_cluster["Weighted Degree"], default=0.0),
            "Rerata Degree Centrality": _profile_mean(df_cluster["Degree Centrality"], default=0.0),
            "Rerata Betweenness Centrality": _profile_mean(df_cluster["Betweenness Centrality"], default=0.0),
            "Rerata Closeness Centrality": _profile_mean(df_cluster["Closeness Centrality"], default=0.0),
            "Rerata Eigenvector Centrality": _profile_mean(df_cluster["Eigenvector Centrality"], default=0.0),
            "Rerata IKD Agregat": _profile_mean(df_cluster["IKD Agregat"], default=0.0),
            "Kategori IKD Dominan": dominant_category,
            "Persentase IKD Rendah (%)": float((category_counts.get("Rendah", 0) / max(n_cluster, 1)) * 100.0),
            "Persentase IKD Sedang (%)": float((category_counts.get("Sedang", 0) / max(n_cluster, 1)) * 100.0),
            "Persentase IKD Tinggi (%)": float((category_counts.get("Tinggi", 0) / max(n_cluster, 1)) * 100.0),
            "Persentase IKD Sangat Tinggi (%)": float((category_counts.get("Sangat Tinggi", 0) / max(n_cluster, 1)) * 100.0),
            "Rerata Sandang, Pangan, dan Papan": _safe_float_metric(dim_means.get("Sandang, Pangan, dan Papan"), default=0.0),
            "Rerata Pendidikan": _safe_float_metric(dim_means.get("Pendidikan"), default=0.0),
            "Rerata Sosial, Hukum, dan HAM": _safe_float_metric(dim_means.get("Sosial, Hukum, dan HAM"), default=0.0),
            "Rerata Kesehatan dan Pekerjaan": _safe_float_metric(dim_means.get("Kesehatan dan Pekerjaan"), default=0.0),
            "Rerata Lingkungan dan Infrastruktur": _safe_float_metric(dim_means.get("Lingkungan dan Infrastruktur"), default=0.0),
            "Dimensi Terlemah": weakest_dim,
            "Nilai Dimensi Terlemah": _safe_float_metric(weakest_val, default=0.0),
            "Dimensi Terkuat": strongest_dim,
            "Nilai Dimensi Terkuat": _safe_float_metric(strongest_val, default=0.0),
            "Persentase Penerima Bansos (%)": _profile_binary_percent(df_cluster["bansos_num"]),
            "Persentase Belum Menerima Bansos (%)": 100.0 - _profile_binary_percent(df_cluster["bansos_num"]),
            "Persentase Akses Internet/Informasi (%)": _profile_binary_percent(df_cluster["internet_num"]),
            "Persentase Kepemilikan Ponsel (%)": _profile_binary_percent(df_cluster["ponsel_num"]),
            "Dusun Dominan / Kode Dusun Dominan": dominant_spatial,
            "Persentase Dusun Dominan (%)": dominant_spatial_pct,
            "Top Profesi/Pekerjaan": _profile_top_values(df_cluster["Profesi/Pekerjaan"], top_n=3),
        }
        rows.append(row)

    profile_df = pd.DataFrame(rows).sort_values("Klaster Louvain").reset_index(drop=True)
    if profile_df.empty:
        return pd.DataFrame(columns=LOUVAIN_CLUSTER_PROFILE_COLUMNS)

    weighted_series = pd.to_numeric(profile_df["Rerata Weighted Degree"], errors="coerce").fillna(0.0)
    profile_df["_centrality_q25"] = float(weighted_series.quantile(0.25)) if not weighted_series.empty else 0.0
    profile_df["_centrality_q75"] = float(weighted_series.quantile(0.75)) if not weighted_series.empty else 0.0
    profile_df["Label Karakter Klaster"] = profile_df.apply(classify_louvain_cluster_character, axis=1)
    profile_df["Implikasi Program"] = profile_df.apply(recommend_cluster_program, axis=1)
    profile_df["Catatan Etika"] = (
        "Indikasi awal berbasis graf; bukan label sosial permanen, bukan dasar tunggal penetapan bantuan, dan perlu verifikasi lapangan."
    )

    for col in LOUVAIN_CLUSTER_PROFILE_COLUMNS:
        if col not in profile_df.columns:
            profile_df[col] = "Tidak tersedia" if col in {"Kategori IKD Dominan", "Dimensi Terlemah", "Dimensi Terkuat", "Dusun Dominan / Kode Dusun Dominan", "Top Profesi/Pekerjaan", "Label Karakter Klaster", "Implikasi Program", "Catatan Etika"} else 0.0
    return profile_df[LOUVAIN_CLUSTER_PROFILE_COLUMNS]


def _format_profile_cluster_label(value):
    cluster_num = _safe_float_metric(value, default=np.nan)
    if np.isfinite(cluster_num):
        return f"Klaster {int(cluster_num)}"
    return "Tidak Terklaster"


def _format_profile_viz_value(value, decimals=2, suffix=""):
    num = _safe_float_metric(value, default=np.nan)
    if not np.isfinite(num):
        return "-"
    decimals = int(max(decimals, 0))
    if decimals == 0:
        text = f"{num:,.0f}"
    else:
        text = f"{num:,.{decimals}f}"
    return f"{text}{suffix}"


def _truncate_profile_viz_text(value, max_chars=56):
    text = _profile_text(value, default="Tidak tersedia")
    text = " ".join(str(text).split())
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars - 3].rstrip()}..."


def _prepare_profile_viz_dataframe(profile_df):
    viz_df = profile_df.copy()
    viz_df["Klaster Label"] = viz_df["Klaster Louvain"].map(_format_profile_cluster_label)
    viz_df["_cluster_sort"] = pd.to_numeric(viz_df["Klaster Louvain"], errors="coerce").fillna(10**9)
    return viz_df.sort_values("_cluster_sort").reset_index(drop=True)


def _build_profile_metric_long(profile_df, metric_specs):
    records = []
    for col_name, label, decimals, suffix in metric_specs:
        if col_name not in profile_df.columns:
            continue
        for _, row in profile_df.iterrows():
            value = _safe_float_metric(row.get(col_name), default=np.nan)
            if not np.isfinite(value):
                continue
            records.append(
                {
                    "Klaster Label": row.get("Klaster Label", _format_profile_cluster_label(row.get("Klaster Louvain"))),
                    "Variabel": label,
                    "Nilai": value,
                    "Label Nilai": _format_profile_viz_value(value, decimals=decimals, suffix=suffix),
                }
            )
    return pd.DataFrame(records)


def _render_profile_metric_charts(profile_df, metric_specs, title, xaxis_title="Nilai", range_x=None):
    long_df = _build_profile_metric_long(profile_df, metric_specs)
    if long_df.empty:
        st.info("Data variabel numerik belum tersedia untuk divisualisasikan.")
        return

    cluster_order = profile_df["Klaster Label"].dropna().astype(str).tolist()
    metric_order = [label for _, label, _, _ in metric_specs if label in set(long_df["Variabel"])]
    if not metric_order:
        st.info("Data variabel numerik belum tersedia untuk divisualisasikan.")
        return

    st.markdown(f"##### {title}")
    chart_height = max(360, 160 + (36 * max(len(cluster_order), 1)))
    for metric_label in metric_order:
        metric_df = long_df[long_df["Variabel"] == metric_label].copy()
        if metric_df.empty:
            continue

        fig = px.bar(
            metric_df,
            x="Nilai",
            y="Klaster Label",
            color="Klaster Label",
            orientation="h",
            text="Label Nilai",
            color_discrete_sequence=CONTRAST_COLORS,
            category_orders={"Klaster Label": cluster_order},
            hover_data={"Label Nilai": True, "Nilai": ":.4f", "Variabel": False, "Klaster Label": False},
        )
        fig.update_traces(textposition="auto", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
        style_publication_figure(
            fig,
            title=metric_label,
            height=chart_height,
            xaxis_title=xaxis_title,
            yaxis_title="",
            showlegend=False,
            margin=dict(l=72, r=28, t=66, b=48),
        )
        fig.update_layout(bargap=0.2, uniformtext_minsize=10, uniformtext_mode="hide")
        fig.update_yaxes(categoryorder="array", categoryarray=cluster_order[::-1], automargin=True)
        fig.update_xaxes(rangemode="tozero")
        if range_x is not None:
            fig.update_xaxes(range=range_x)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_profile_category_distribution(profile_df, category_specs):
    records = []
    for col_name, label in category_specs:
        if col_name not in profile_df.columns:
            continue
        series = profile_df[col_name].map(lambda value: _profile_text(value, default="Tidak tersedia"))
        series = series.replace("", "Tidak tersedia")
        for category, count in series.value_counts().items():
            records.append(
                {
                    "Variabel": label,
                    "Kategori": _truncate_profile_viz_text(category, max_chars=46),
                    "Kategori Lengkap": category,
                    "Jumlah Klaster": int(count),
                }
            )
    cat_df = pd.DataFrame(records)
    if cat_df.empty:
        st.info("Data kategori belum tersedia untuk divisualisasikan.")
        return

    variable_order = [label for _, label in category_specs if label in set(cat_df["Variabel"])]
    st.markdown("##### Sebaran Kategori Dominan, Dimensi, dan Karakter Klaster")
    for variable_label in variable_order:
        variable_df = cat_df[cat_df["Variabel"] == variable_label].copy()
        if variable_df.empty:
            continue

        category_order = variable_df.sort_values(["Jumlah Klaster", "Kategori"], ascending=[False, True])["Kategori"].tolist()
        height = max(340, 150 + (40 * len(category_order)))
        fig = px.bar(
            variable_df,
            x="Jumlah Klaster",
            y="Kategori",
            color="Kategori",
            orientation="h",
            text="Jumlah Klaster",
            color_discrete_sequence=CONTRAST_COLORS,
            hover_data={"Kategori Lengkap": True, "Kategori": False, "Variabel": False},
        )
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
        style_publication_figure(
            fig,
            title=variable_label,
            height=height,
            xaxis_title="Jumlah klaster",
            yaxis_title="",
            showlegend=False,
            margin=dict(l=88, r=42, t=66, b=48),
        )
        fig.update_layout(bargap=0.22)
        fig.update_xaxes(rangemode="tozero")
        fig.update_yaxes(categoryorder="array", categoryarray=category_order[::-1], automargin=True)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_profile_category_matrix(profile_df):
    display_specs = [
        ("Klaster Label", "Klaster"),
        ("Kategori IKD Dominan", "Kategori IKD"),
        ("Dimensi Terlemah", "Dimensi Terlemah"),
        ("Dimensi Terkuat", "Dimensi Terkuat"),
        ("Dusun Dominan / Kode Dusun Dominan", "Dusun Dominan"),
        ("Top Profesi/Pekerjaan", "Top Profesi"),
        ("Label Karakter Klaster", "Karakter Klaster"),
    ]
    existing_specs = [(col_name, label) for col_name, label in display_specs if col_name in profile_df.columns]
    if not existing_specs:
        return

    matrix_df = profile_df[[col_name for col_name, _ in existing_specs]].copy()
    for col_name, _ in existing_specs:
        max_chars = 42 if col_name != "Top Profesi/Pekerjaan" else 64
        matrix_df[col_name] = matrix_df[col_name].map(lambda value: _truncate_profile_viz_text(value, max_chars=max_chars))

    row_count = max(len(matrix_df), 1)
    row_colors = ["#FFFFFF" if idx % 2 == 0 else "#F8FAFC" for idx in range(row_count)]
    fill_color = [["#EEF2FF"] * row_count] + [row_colors for _ in existing_specs[1:]]
    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[0.8, 1.0, 1.25, 1.25, 1.35, 2.05, 1.9][: len(existing_specs)],
                header=dict(
                    values=[label for _, label in existing_specs],
                    fill_color="#111827",
                    font=dict(color="#FFFFFF", size=12, family=PUBLICATION_FONT),
                    align="left",
                    height=34,
                ),
                cells=dict(
                    values=[matrix_df[col_name].tolist() for col_name, _ in existing_specs],
                    fill_color=fill_color,
                    font=dict(color=PLOT_TEXT_COLOR, size=11, family=PUBLICATION_FONT),
                    align="left",
                    height=32,
                ),
            )
        ]
    )
    fig.update_layout(
        template=PUBLICATION_TEMPLATE,
        title=dict(text="Matriks Kategori Penting per Klaster", x=0.02, xanchor="left"),
        height=max(360, 95 + (34 * row_count)),
        margin=dict(l=24, r=24, t=72, b=24),
        paper_bgcolor="#FFFFFF",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def render_louvain_profile_variable_visualizations(profile_df):
    viz_df = _prepare_profile_viz_dataframe(profile_df)
    st.markdown("#### Visualisasi Variabel Relevan dari Tabel Profil")
    tab_size, tab_centrality, tab_ikr, tab_access, tab_category = st.tabs(
        ["Ukuran & Struktur", "Centrality", "IKD & Dimensi", "Akses & Bansos", "Kategori"]
    )

    with tab_size:
        _render_profile_metric_charts(
            viz_df,
            [
                ("Jumlah Node", "Jumlah Node", 0, ""),
                ("Persentase Node (%)", "Persentase Node", 1, "%"),
                ("Jumlah Edge Internal", "Edge Internal", 0, ""),
                ("Density Internal", "Density Internal", 4, ""),
            ],
            title="Ukuran, Proporsi, Edge, dan Density Internal Klaster",
            xaxis_title="Nilai",
        )

    with tab_centrality:
        _render_profile_metric_charts(
            viz_df,
            [
                ("Rerata Weighted Degree", "Weighted Degree", 4, ""),
                ("Rerata Degree Centrality", "Degree Centrality", 5, ""),
                ("Rerata Betweenness Centrality", "Betweenness", 5, ""),
                ("Rerata Closeness Centrality", "Closeness", 5, ""),
                ("Rerata Eigenvector Centrality", "Eigenvector", 5, ""),
            ],
            title="Rerata Centrality per Klaster",
            xaxis_title="Nilai centrality",
        )

    with tab_ikr:
        _render_profile_metric_charts(
            viz_df,
            [
                ("Rerata IKD Agregat", "IKD Agregat", 1, ""),
                ("Rerata Sandang, Pangan, dan Papan", "Sandang/Pangan/Papan", 1, ""),
                ("Rerata Pendidikan", "Pendidikan", 1, ""),
                ("Rerata Sosial, Hukum, dan HAM", "Sosial/Hukum/HAM", 1, ""),
                ("Rerata Kesehatan dan Pekerjaan", "Kesehatan/Pekerjaan", 1, ""),
                ("Rerata Lingkungan dan Infrastruktur", "Lingkungan/Infrastruktur", 1, ""),
                ("Nilai Dimensi Terlemah", "Nilai Dimensi Terlemah", 1, ""),
                ("Nilai Dimensi Terkuat", "Nilai Dimensi Terkuat", 1, ""),
            ],
            title="Rerata IKD Agregat dan Dimensi per Klaster",
            xaxis_title="Skor",
            range_x=[0, 100],
        )
        _render_profile_metric_charts(
            viz_df,
            [
                ("Persentase IKD Rendah (%)", "IKD Rendah", 1, "%"),
                ("Persentase IKD Sedang (%)", "IKD Sedang", 1, "%"),
                ("Persentase IKD Tinggi (%)", "IKD Tinggi", 1, "%"),
                ("Persentase IKD Sangat Tinggi (%)", "IKD Sangat Tinggi", 1, "%"),
            ],
            title="Proporsi Kategori IKD per Klaster",
            xaxis_title="Persentase",
            range_x=[0, 100],
        )

    with tab_access:
        _render_profile_metric_charts(
            viz_df,
            [
                ("Persentase Penerima Bansos (%)", "Penerima Bansos", 1, "%"),
                ("Persentase Belum Menerima Bansos (%)", "Belum Menerima Bansos", 1, "%"),
                ("Persentase Akses Internet/Informasi (%)", "Akses Internet/Informasi", 1, "%"),
                ("Persentase Kepemilikan Ponsel (%)", "Kepemilikan Ponsel", 1, "%"),
                ("Persentase Dusun Dominan (%)", "Konsentrasi Dusun Dominan", 1, "%"),
            ],
            title="Akses, Bansos, dan Konsentrasi Spasial per Klaster",
            xaxis_title="Persentase",
            range_x=[0, 100],
        )

    with tab_category:
        _render_profile_category_distribution(
            viz_df,
            [
                ("Kategori IKD Dominan", "Kategori IKD Dominan"),
                ("Dimensi Terlemah", "Dimensi Terlemah"),
                ("Dimensi Terkuat", "Dimensi Terkuat"),
                ("Label Karakter Klaster", "Karakter Klaster"),
            ],
        )
        _render_profile_category_matrix(viz_df)


def _ikr_category_order_value(category):
    return {
        "Rendah": 1,
        "Sedang": 2,
        "Tinggi": 3,
        "Sangat Tinggi": 4,
    }.get(_profile_text(category, default="Tidak Valid"), 0)


def _build_louvain_category_anomaly_summary(df_node_profile):
    if df_node_profile is None or df_node_profile.empty:
        return pd.DataFrame()
    if "Klaster Louvain" not in df_node_profile.columns or "Kategori IKD" not in df_node_profile.columns:
        return pd.DataFrame()

    df = df_node_profile.copy()
    df["Klaster Louvain"] = pd.to_numeric(df["Klaster Louvain"], errors="coerce")
    df = df.dropna(subset=["Klaster Louvain"]).copy()
    if df.empty:
        return pd.DataFrame()
    df["Klaster Louvain"] = df["Klaster Louvain"].astype(int)
    df["Kategori IKD"] = df["Kategori IKD"].map(lambda value: _profile_text(value, default="Tidak Valid"))
    df = df[df["Kategori IKD"].isin(["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"])].copy()
    if df.empty:
        return pd.DataFrame()

    agg_kwargs = {
        "Jumlah Node": ("family_id", "count"),
        "Rerata IKD Agregat": ("IKD Agregat", lambda s: _profile_mean(s, default=np.nan)),
        "Penerima Bansos (%)": ("bansos_num", _profile_binary_percent),
        "Akses Internet/Informasi (%)": ("internet_num", _profile_binary_percent),
        "Kepemilikan Ponsel (%)": ("ponsel_num", _profile_binary_percent),
    }
    for dim_label, _ in IKD_DIMENSION_MAP:
        if dim_label in df.columns:
            agg_kwargs[f"Rerata {dim_label}"] = (dim_label, lambda s: _profile_mean(s, default=np.nan))
    for centrality_col in [
        "Weighted Degree",
        "Degree Centrality",
        "Betweenness Centrality",
        "Closeness Centrality",
        "Eigenvector Centrality",
    ]:
        if centrality_col in df.columns:
            agg_kwargs[f"Rerata {centrality_col}"] = (centrality_col, lambda s: _profile_mean(s, default=np.nan))

    summary = df.groupby(["Klaster Louvain", "Kategori IKD"], as_index=False).agg(**agg_kwargs)
    if summary.empty:
        return summary

    totals = summary.groupby("Klaster Louvain", as_index=False)["Jumlah Node"].sum().rename(columns={"Jumlah Node": "Total Node Klaster"})
    summary = summary.merge(totals, on="Klaster Louvain", how="left")
    summary["Persentase Dalam Klaster (%)"] = (summary["Jumlah Node"] / summary["Total Node Klaster"].clip(lower=1)) * 100.0
    summary["_category_order"] = summary["Kategori IKD"].map(_ikr_category_order_value)

    dominant_rows = (
        summary.sort_values(["Klaster Louvain", "Jumlah Node", "_category_order"], ascending=[True, False, True])
        .drop_duplicates("Klaster Louvain")
        [["Klaster Louvain", "Kategori IKD", "Persentase Dalam Klaster (%)", "_category_order"]]
        .rename(
            columns={
                "Kategori IKD": "Kategori Dominan Klaster",
                "Persentase Dalam Klaster (%)": "Persentase Dominan (%)",
                "_category_order": "_dominant_order",
            }
        )
    )
    summary = summary.merge(dominant_rows, on="Klaster Louvain", how="left")
    summary["Jarak dari Dominan"] = (summary["_category_order"] - summary["_dominant_order"]).abs()
    summary["Keterangan"] = np.where(
        summary["Kategori IKD"].eq(summary["Kategori Dominan Klaster"]),
        "Dominan",
        "Minoritas",
    )
    summary["Skor Anomali"] = np.where(
        summary["Keterangan"].eq("Minoritas"),
        summary["Jarak dari Dominan"] * (1.0 - (summary["Persentase Dalam Klaster (%)"] / 100.0)) * np.log1p(summary["Jumlah Node"]),
        0.0,
    )
    summary["Keterangan"] = np.where(
        summary["Skor Anomali"].gt(0),
        "Minoritas anomali",
        summary["Keterangan"],
    )

    for source_col, output_col in [
        ("Profesi/Pekerjaan", "Top Profesi/Pekerjaan"),
        ("Dusun/Kode Dusun", "Dusun/Kode Dominan"),
        ("Dusun", "Dusun/Kode Dominan"),
    ]:
        if source_col in df.columns and output_col not in summary.columns:
            top_values = (
                df.groupby(["Klaster Louvain", "Kategori IKD"])[source_col]
                .apply(lambda values: _profile_top_values(values, top_n=2))
                .reset_index(name=output_col)
            )
            summary = summary.merge(top_values, on=["Klaster Louvain", "Kategori IKD"], how="left")

    summary["Klaster Label"] = summary["Klaster Louvain"].map(_format_profile_cluster_label)
    summary["Subkelompok Label"] = summary.apply(
        lambda row: f"{row['Klaster Label']} | {row['Kategori IKD']} ({int(row['Jumlah Node'])})",
        axis=1,
    )
    return summary.sort_values(["Skor Anomali", "Klaster Louvain", "_category_order"], ascending=[False, True, True]).reset_index(drop=True)


def _build_louvain_cluster_anomaly_scores(summary_df):
    if summary_df is None or summary_df.empty:
        return pd.DataFrame()
    category_counts = (
        summary_df.groupby("Klaster Louvain", as_index=False)["Kategori IKD"]
        .nunique()
        .rename(columns={"Kategori IKD": "Jumlah Kategori IKD"})
    )
    max_scores = (
        summary_df.groupby("Klaster Louvain", as_index=False)["Skor Anomali"]
        .max()
        .rename(columns={"Skor Anomali": "Skor Anomali Maks"})
    )
    entropy_rows = []
    for cluster_id, group in summary_df.groupby("Klaster Louvain"):
        shares = pd.to_numeric(group["Persentase Dalam Klaster (%)"], errors="coerce").fillna(0.0) / 100.0
        entropy = float(-(shares[shares > 0] * np.log(shares[shares > 0])).sum())
        dominant_pct = float(pd.to_numeric(group["Persentase Dominan (%)"], errors="coerce").fillna(0.0).max())
        entropy_rows.append(
            {
                "Klaster Louvain": int(cluster_id),
                "Indeks Campuran": entropy,
                "Persentase Dominan (%)": dominant_pct,
            }
        )
    cluster_scores = max_scores.merge(category_counts, on="Klaster Louvain", how="left").merge(pd.DataFrame(entropy_rows), on="Klaster Louvain", how="left")
    cluster_scores["Klaster Label"] = cluster_scores["Klaster Louvain"].map(_format_profile_cluster_label)
    cluster_scores["Skor Prioritas Anomali"] = cluster_scores["Skor Anomali Maks"] + cluster_scores["Indeks Campuran"]
    return cluster_scores.sort_values("Skor Prioritas Anomali", ascending=False).reset_index(drop=True)


def _default_anomaly_clusters(cluster_scores, max_clusters=4):
    if cluster_scores is None or cluster_scores.empty:
        return []
    anomalous = cluster_scores[
        (pd.to_numeric(cluster_scores["Skor Anomali Maks"], errors="coerce").fillna(0.0) > 0)
        & (pd.to_numeric(cluster_scores["Jumlah Kategori IKD"], errors="coerce").fillna(0.0) > 1)
    ]
    if anomalous.empty:
        return []
    return anomalous.head(max_clusters)["Klaster Louvain"].astype(int).tolist()


def _render_louvain_anomaly_score_chart(cluster_scores):
    if cluster_scores is None or cluster_scores.empty:
        return
    plot_df = cluster_scores.head(12).copy()
    plot_df["Label Skor"] = plot_df["Skor Prioritas Anomali"].map(lambda value: _format_profile_viz_value(value, decimals=2))
    fig = px.bar(
        plot_df.sort_values("Skor Prioritas Anomali", ascending=True),
        x="Skor Prioritas Anomali",
        y="Klaster Label",
        color="Jumlah Kategori IKD",
        orientation="h",
        text="Label Skor",
        color_continuous_scale=PUBLICATION_CONTINUOUS_SCALE,
        hover_data={
            "Skor Anomali Maks": ":.3f",
            "Indeks Campuran": ":.3f",
            "Persentase Dominan (%)": ":.1f",
            "Jumlah Kategori IKD": True,
            "Skor Prioritas Anomali": ":.3f",
            "Klaster Label": False,
        },
        title="Peringkat Klaster dengan Subkelompok IKD Anomali",
    )
    fig.update_traces(textposition="outside", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
    style_publication_figure(fig, title="Peringkat Klaster dengan Subkelompok IKD Anomali", height=max(420, 130 + 36 * len(plot_df)), xaxis_title="Skor prioritas anomali", yaxis_title="")
    fig.update_layout(coloraxis_colorbar=dict(title="Jumlah kategori"))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_louvain_anomaly_dimension_heatmap(selected_summary):
    dim_cols = [f"Rerata {dim_label}" for dim_label, _ in IKD_DIMENSION_MAP if f"Rerata {dim_label}" in selected_summary.columns]
    metric_cols = ["Rerata IKD Agregat"] + dim_cols
    metric_cols = [col for col in metric_cols if col in selected_summary.columns]
    if not metric_cols:
        return

    metric_labels = [
        "IKD Agregat" if col == "Rerata IKD Agregat" else col.replace("Rerata ", "")
        for col in metric_cols
    ]
    heat_df = selected_summary.sort_values(["Klaster Louvain", "_category_order"]).copy()
    z_vals = heat_df[metric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    text_vals = np.vectorize(lambda value: f"{value:.1f}")(z_vals)
    fig = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=metric_labels,
            y=heat_df["Subkelompok Label"],
            text=text_vals,
            texttemplate="%{text}",
            colorscale=PUBLICATION_CONTINUOUS_SCALE,
            zmin=0,
            zmax=100,
            colorbar=dict(title="Rerata skor"),
        )
    )
    style_publication_figure(
        fig,
        title="Dimensi IKD dan Agregat pada Subkelompok Dominan vs Anomali",
        height=max(430, 180 + 38 * len(heat_df)),
        xaxis_title="Dimensi / agregat",
        yaxis_title="Subkelompok",
    )
    fig.update_xaxes(tickangle=-18)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_louvain_anomaly_supporting_bars(selected_summary):
    support_specs = [
        ("Penerima Bansos (%)", "Penerima Bansos", 1, "%"),
        ("Akses Internet/Informasi (%)", "Akses Internet/Informasi", 1, "%"),
        ("Kepemilikan Ponsel (%)", "Kepemilikan Ponsel", 1, "%"),
        ("Rerata Weighted Degree", "Weighted Degree", 3, ""),
        ("Rerata Betweenness Centrality", "Betweenness", 5, ""),
    ]
    records = []
    for col_name, label, decimals, suffix in support_specs:
        if col_name not in selected_summary.columns:
            continue
        for _, row in selected_summary.iterrows():
            value = _safe_float_metric(row.get(col_name), default=np.nan)
            if not np.isfinite(value):
                continue
            records.append(
                {
                    "Subkelompok Label": row["Subkelompok Label"],
                    "Kategori IKD": row["Kategori IKD"],
                    "Indikator": label,
                    "Nilai": value,
                    "Label Nilai": _format_profile_viz_value(value, decimals=decimals, suffix=suffix),
                }
            )
    support_df = pd.DataFrame(records)
    if support_df.empty:
        return

    facet_rows = int(np.ceil(support_df["Indikator"].nunique() / 2))
    fig = px.bar(
        support_df,
        x="Nilai",
        y="Subkelompok Label",
        color="Kategori IKD",
        facet_col="Indikator",
        facet_col_wrap=2,
        orientation="h",
        text="Label Nilai",
        color_discrete_map=BPS_CATEGORY_COLORS,
        category_orders={"Kategori IKD": ["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"]},
        hover_data={"Label Nilai": True, "Nilai": ":.5f", "Indikator": False, "Subkelompok Label": False},
    )
    fig.update_traces(textposition="auto", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
    style_publication_figure(
        fig,
        title="Indikator Pendukung pada Subkelompok Dominan vs Anomali",
        height=max(460, 250 * facet_rows + max(0, selected_summary.shape[0] - 6) * 20),
        xaxis_title="Nilai",
        yaxis_title="Subkelompok",
        showlegend=True,
        legend_title="Kategori IKD",
    )
    fig.update_xaxes(matches=None, showticklabels=True)
    fig.update_yaxes(matches=None, automargin=True)
    fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_louvain_anomaly_node_distribution(df_node_profile, selected_clusters):
    if df_node_profile is None or df_node_profile.empty:
        return
    node_df = df_node_profile.copy()
    node_df["Klaster Louvain"] = pd.to_numeric(node_df["Klaster Louvain"], errors="coerce")
    node_df = node_df[node_df["Klaster Louvain"].isin(selected_clusters)].copy()
    node_df = node_df.dropna(subset=["IKD Agregat"])
    if node_df.empty:
        return
    node_df["Klaster Louvain"] = node_df["Klaster Louvain"].astype(int)
    node_df["Klaster Label"] = node_df["Klaster Louvain"].map(_format_profile_cluster_label)
    node_df["Subkelompok Label"] = node_df["Klaster Label"] + " | " + node_df["Kategori IKD"].astype(str)
    if "Hover Aman" not in node_df.columns:
        node_df["Hover Aman"] = node_df["Kode Node"] if "Kode Node" in node_df.columns else node_df["Subkelompok Label"]

    fig = px.box(
        node_df,
        x="Subkelompok Label",
        y="IKD Agregat",
        color="Kategori IKD",
        points="all",
        color_discrete_map=BPS_CATEGORY_COLORS,
        category_orders={"Kategori IKD": ["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"]},
        hover_name="Kode Node" if "Kode Node" in node_df.columns else None,
        custom_data=["Hover Aman"],
        title="Sebaran Node IKD Agregat pada Subkelompok Anomali",
    )
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>", marker=dict(size=7, opacity=0.72, line=dict(color="#111827", width=0.35)))
    for cutoff, label, color in [(60, "Batas Sedang", "#B91C1C"), (70, "Batas Tinggi", "#D97706"), (80, "Batas Sangat Tinggi", "#2563EB")]:
        fig.add_hline(y=cutoff, line_dash="dash", line_color=color, annotation_text=label, annotation_position="top left")
    style_publication_figure(fig, title="Sebaran Node IKD Agregat pada Subkelompok Anomali", height=520, xaxis_title="Subkelompok", yaxis_title="IKD Agregat", legend_title="Kategori IKD")
    fig.update_xaxes(tickangle=-22, automargin=True)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _build_louvain_anomaly_node_detail(df_node_profile, selected_summary):
    if df_node_profile is None or df_node_profile.empty or selected_summary is None or selected_summary.empty:
        return pd.DataFrame()
    anomaly_groups = selected_summary[selected_summary["Keterangan"].eq("Minoritas anomali")].copy()
    if anomaly_groups.empty:
        return pd.DataFrame()

    keys = anomaly_groups[["Klaster Louvain", "Kategori IKD", "Kategori Dominan Klaster", "Skor Anomali", "Jarak dari Dominan"]].copy()
    keys["Klaster Louvain"] = pd.to_numeric(keys["Klaster Louvain"], errors="coerce").astype("Int64")
    detail_df = df_node_profile.copy()
    detail_df["Klaster Louvain"] = pd.to_numeric(detail_df["Klaster Louvain"], errors="coerce").astype("Int64")
    detail_df["Kategori IKD"] = detail_df["Kategori IKD"].map(lambda value: _profile_text(value, default="Tidak Valid"))
    detail_df = detail_df.merge(keys, on=["Klaster Louvain", "Kategori IKD"], how="inner")
    if detail_df.empty:
        return detail_df
    detail_df["Klaster Label"] = detail_df["Klaster Louvain"].astype(int).map(_format_profile_cluster_label)
    detail_df["Selisih Orde Kategori"] = pd.to_numeric(detail_df["Jarak dari Dominan"], errors="coerce").fillna(0).astype(int)
    return detail_df.sort_values(["Skor Anomali", "Klaster Louvain", "Kategori IKD", "IKD Agregat"], ascending=[False, True, True, True]).reset_index(drop=True)


def _render_louvain_anomaly_node_detail(df_node_profile, selected_summary, publish_mode=True):
    detail_df = _build_louvain_anomaly_node_detail(df_node_profile, selected_summary)
    st.markdown("##### Detail KK pada Subkelompok Anomali")
    if detail_df.empty:
        st.info("Tidak ada KK detail pada subkelompok anomali untuk klaster terpilih.")
        return

    name_available = "Nama" in detail_df.columns and detail_df["Nama"].map(lambda value: _profile_text(value, default="")).astype(str).str.strip().ne("").any()
    show_names = False
    if name_available:
        show_names = st.checkbox(
            "Tampilkan nama KK pada detail anomali",
            value=not publish_mode,
            key="louvain_profile_anomaly_show_names",
            help="Gunakan untuk verifikasi internal. Jika tidak dicentang, tabel memakai Kode Node anonim.",
        )

    identity_cols = ["Kode Node"]
    if show_names and name_available:
        identity_cols = ["Nama", "family_id", "Kode Node"]
    spatial_col = "Dusun/Kode Dusun" if publish_mode and "Dusun/Kode Dusun" in detail_df.columns else "Dusun"
    dimension_cols = [dim_label for dim_label, _ in IKD_DIMENSION_MAP if dim_label in detail_df.columns]
    metric_cols = [
        "IKD Agregat",
        *dimension_cols,
        "Weighted Degree",
        "Betweenness Centrality",
        "Closeness Centrality",
        "Eigenvector Centrality",
    ]
    display_cols = [
        *identity_cols,
        "Klaster Label",
        "Kategori Dominan Klaster",
        "Kategori IKD",
        "Status Bansos",
        spatial_col,
        "Profesi/Pekerjaan",
        *metric_cols,
        "Skor Anomali",
        "Selisih Orde Kategori",
    ]
    display_cols = [col for col in display_cols if col in detail_df.columns]

    format_map = {
        "IKD Agregat": "{:.2f}",
        "Weighted Degree": "{:.4f}",
        "Betweenness Centrality": "{:.6f}",
        "Closeness Centrality": "{:.6f}",
        "Eigenvector Centrality": "{:.6f}",
        "Skor Anomali": "{:.3f}",
        **{dim_label: "{:.2f}" for dim_label in dimension_cols},
    }
    st.dataframe(
        detail_df[display_cols].style.format(format_map),
        use_container_width=True,
    )

    heat_identity_col = "Nama" if show_names and name_available else "Kode Node"
    heat_metrics = ["IKD Agregat", *dimension_cols]
    heat_df = detail_df[[heat_identity_col, "Klaster Label", "Kategori IKD", *heat_metrics]].copy()
    heat_df["Label KK"] = heat_df.apply(
        lambda row: f"{row['Klaster Label']} | {row['Kategori IKD']} | {row[heat_identity_col]}",
        axis=1,
    )
    heat_df = heat_df.dropna(subset=heat_metrics, how="all")
    if not heat_df.empty:
        max_heat_rows = min(80, int(heat_df.shape[0]))
        if heat_df.shape[0] > max_heat_rows:
            st.caption(f"Heatmap menampilkan {max_heat_rows} KK anomali pertama; tabel di atas tetap memuat seluruh KK anomali.")
        heat_plot = heat_df.head(max_heat_rows)
        z_vals = heat_plot[heat_metrics].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
        text_vals = np.vectorize(lambda value: f"{value:.1f}")(z_vals)
        metric_labels = ["IKD Agregat" if col == "IKD Agregat" else col for col in heat_metrics]
        fig_detail_heat = go.Figure(
            go.Heatmap(
                z=z_vals,
                x=metric_labels,
                y=heat_plot["Label KK"],
                text=text_vals,
                texttemplate="%{text}",
                colorscale=PUBLICATION_CONTINUOUS_SCALE,
                zmin=0,
                zmax=100,
                colorbar=dict(title="Skor KK"),
            )
        )
        style_publication_figure(
            fig_detail_heat,
            title="Heatmap Nilai Dimensi KK pada Subkelompok Anomali",
            height=max(430, 180 + 28 * len(heat_plot)),
            xaxis_title="Agregat dan dimensi",
            yaxis_title="KK anomali",
        )
        fig_detail_heat.update_xaxes(tickangle=-18)
        st.plotly_chart(fig_detail_heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    safe_name = "detail_kk_anomali_klaster.csv"
    st.download_button(
        "Unduh Detail KK Anomali",
        data=detail_df[display_cols].to_csv(index=False).encode("utf-8"),
        file_name=safe_name,
        mime="text/csv",
        key="download_louvain_anomaly_kk_detail",
    )


def render_louvain_category_anomaly_analysis(df_node_profile, publish_mode=True):
    summary_df = _build_louvain_category_anomaly_summary(df_node_profile)
    if summary_df.empty:
        st.info("Data node belum cukup untuk mendeteksi subkelompok IKD anomali di dalam klaster.")
        return

    cluster_scores = _build_louvain_cluster_anomaly_scores(summary_df)
    default_clusters = _default_anomaly_clusters(cluster_scores)
    st.markdown("#### Analisis Subkelompok IKD Anomali dalam Klaster")
    _render_louvain_anomaly_score_chart(cluster_scores)

    cluster_options = cluster_scores["Klaster Louvain"].astype(int).tolist()
    selected_clusters = st.multiselect(
        "Pilih klaster untuk analisis anomali",
        options=cluster_options,
        default=default_clusters,
        format_func=lambda value: _format_profile_cluster_label(value),
        key="louvain_profile_anomaly_clusters",
        help="Default dipilih otomatis dari skor anomali tertinggi, bukan klaster tertentu.",
    )
    if not selected_clusters:
        st.info("Tidak ada klaster dengan subkelompok kategori IKD yang cukup berbeda dari kategori dominannya.")
        return

    selected_summary = summary_df[summary_df["Klaster Louvain"].isin(selected_clusters)].copy()
    if selected_summary.empty:
        st.info("Klaster terpilih belum memiliki subkelompok kategori IKD yang bisa dibandingkan.")
        return

    dist_df = selected_summary.sort_values(["Klaster Louvain", "_category_order"]).copy()
    dist_df["Label Jumlah"] = dist_df.apply(
        lambda row: f"{int(row['Jumlah Node'])} node",
        axis=1,
    )
    fig_dist = px.bar(
        dist_df,
        x="Klaster Label",
        y="Persentase Dalam Klaster (%)",
        color="Kategori IKD",
        text="Label Jumlah",
        barmode="stack",
        color_discrete_map=BPS_CATEGORY_COLORS,
        category_orders={"Kategori IKD": ["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"]},
        hover_data={
            "Keterangan": True,
            "Skor Anomali": ":.3f",
            "Kategori Dominan Klaster": True,
            "Jarak dari Dominan": True,
            "Persentase Dalam Klaster (%)": ":.1f",
            "Klaster Label": False,
        },
        title="Komposisi Subkelompok Dominan dan Anomali pada Klaster Terpilih",
    )
    fig_dist.update_traces(textposition="inside", marker_line_color="#FFFFFF", marker_line_width=0.6)
    style_publication_figure(fig_dist, title="Komposisi Subkelompok Dominan dan Anomali pada Klaster Terpilih", height=450, xaxis_title="", yaxis_title="Persentase (%)", legend_title="Kategori IKD")
    fig_dist.update_yaxes(range=[0, 100], ticksuffix="%")
    st.plotly_chart(fig_dist, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    _render_louvain_anomaly_dimension_heatmap(selected_summary)
    _render_louvain_anomaly_supporting_bars(selected_summary)
    _render_louvain_anomaly_node_distribution(df_node_profile, selected_clusters)
    _render_louvain_anomaly_node_detail(df_node_profile, selected_summary, publish_mode=publish_mode)

    display_cols = [
        "Klaster Label",
        "Kategori IKD",
        "Keterangan",
        "Jumlah Node",
        "Persentase Dalam Klaster (%)",
        "Kategori Dominan Klaster",
        "Jarak dari Dominan",
        "Skor Anomali",
        "Rerata IKD Agregat",
        "Penerima Bansos (%)",
        "Akses Internet/Informasi (%)",
        "Kepemilikan Ponsel (%)",
        "Top Profesi/Pekerjaan",
        "Dusun/Kode Dominan",
    ]
    display_cols = [col for col in display_cols if col in selected_summary.columns]
    st.dataframe(
        selected_summary[display_cols]
        .sort_values(["Skor Anomali", "Klaster Label"], ascending=[False, True])
        .style.format(
            {
                "Persentase Dalam Klaster (%)": "{:.2f}",
                "Skor Anomali": "{:.3f}",
                "Rerata IKD Agregat": "{:.2f}",
                "Penerima Bansos (%)": "{:.2f}",
                "Akses Internet/Informasi (%)": "{:.2f}",
                "Kepemilikan Ponsel (%)": "{:.2f}",
            }
        ),
        use_container_width=True,
    )


def _build_louvain_bansos_dimension_summary(df_node_profile):
    if df_node_profile is None or df_node_profile.empty:
        return pd.DataFrame()
    required_cols = {"Klaster Louvain", "Status Bansos", "IKD Agregat"}
    if not required_cols.issubset(df_node_profile.columns):
        return pd.DataFrame()

    df = df_node_profile.copy()
    df["Klaster Louvain"] = pd.to_numeric(df["Klaster Louvain"], errors="coerce")
    df = df.dropna(subset=["Klaster Louvain"]).copy()
    if df.empty:
        return pd.DataFrame()
    df["Klaster Louvain"] = df["Klaster Louvain"].astype(int)
    df["Status Bansos"] = df["Status Bansos"].map(lambda value: _profile_text(value, default="Belum Menerima"))
    df["Status Bansos"] = np.where(df["Status Bansos"].eq("Penerima"), "Penerima", "Belum Menerima")

    agg_kwargs = {
        "Jumlah Node": ("family_id", "count"),
        "Rerata IKD Agregat": ("IKD Agregat", lambda s: _profile_mean(s, default=np.nan)),
    }
    for dim_label, _ in IKD_DIMENSION_MAP:
        if dim_label in df.columns:
            agg_kwargs[f"Rerata {dim_label}"] = (dim_label, lambda s: _profile_mean(s, default=np.nan))
    support_specs = [
        ("Weighted Degree", "Rerata Weighted Degree", "mean"),
        ("Betweenness Centrality", "Rerata Betweenness Centrality", "mean"),
        ("internet_num", "Akses Internet/Informasi (%)", "percent"),
        ("ponsel_num", "Kepemilikan Ponsel (%)", "percent"),
    ]
    for support_col, output_col, mode in support_specs:
        if support_col in df.columns:
            if mode == "percent":
                agg_kwargs[output_col] = (support_col, _profile_binary_percent)
            else:
                agg_kwargs[output_col] = (support_col, lambda s: _profile_mean(s, default=np.nan))

    summary = df.groupby(["Klaster Louvain", "Status Bansos"], as_index=False).agg(**agg_kwargs)
    if summary.empty:
        return summary
    totals = summary.groupby("Klaster Louvain", as_index=False)["Jumlah Node"].sum().rename(columns={"Jumlah Node": "Total Node Klaster"})
    summary = summary.merge(totals, on="Klaster Louvain", how="left")
    summary["Persentase Dalam Klaster (%)"] = (summary["Jumlah Node"] / summary["Total Node Klaster"].clip(lower=1)) * 100.0
    summary["Klaster Label"] = summary["Klaster Louvain"].map(_format_profile_cluster_label)
    summary["Subkelompok Bansos"] = summary["Klaster Label"] + " | " + summary["Status Bansos"]
    return summary.sort_values(["Klaster Louvain", "Status Bansos"]).reset_index(drop=True)


def _bansos_metric_columns(summary_df):
    metric_cols = ["Rerata IKD Agregat"]
    metric_cols.extend([f"Rerata {dim_label}" for dim_label, _ in IKD_DIMENSION_MAP])
    return [col for col in metric_cols if col in summary_df.columns]


def _render_louvain_bansos_dimension_heatmap(summary_df):
    metric_cols = _bansos_metric_columns(summary_df)
    if not metric_cols:
        return
    heat_df = summary_df.copy()
    metric_labels = ["IKD Agregat" if col == "Rerata IKD Agregat" else col.replace("Rerata ", "") for col in metric_cols]
    z_vals = heat_df[metric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    text_vals = np.vectorize(lambda value: f"{value:.1f}")(z_vals)
    fig = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=metric_labels,
            y=heat_df["Subkelompok Bansos"],
            text=text_vals,
            texttemplate="%{text}",
            colorscale=PUBLICATION_CONTINUOUS_SCALE,
            zmin=0,
            zmax=100,
            colorbar=dict(title="Rerata skor"),
        )
    )
    style_publication_figure(
        fig,
        title="Heatmap Dimensi IKD dan Agregat menurut Status Bansos per Klaster",
        height=max(460, 180 + 34 * len(heat_df)),
        xaxis_title="Dimensi / agregat",
        yaxis_title="Klaster dan status bansos",
    )
    fig.update_xaxes(tickangle=-18)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _build_louvain_bansos_gap_dataframe(summary_df):
    metric_cols = _bansos_metric_columns(summary_df)
    rows = []
    for cluster_id, group in summary_df.groupby("Klaster Louvain"):
        receiver = group[group["Status Bansos"].eq("Penerima")]
        non_receiver = group[group["Status Bansos"].eq("Belum Menerima")]
        if receiver.empty or non_receiver.empty:
            continue
        row = {
            "Klaster Louvain": int(cluster_id),
            "Klaster Label": _format_profile_cluster_label(cluster_id),
            "Jumlah Penerima": int(receiver.iloc[0].get("Jumlah Node", 0)),
            "Jumlah Belum Menerima": int(non_receiver.iloc[0].get("Jumlah Node", 0)),
            "Persentase Penerima (%)": _safe_float_metric(receiver.iloc[0].get("Persentase Dalam Klaster (%)"), default=0.0),
        }
        for col in metric_cols:
            recv_val = _safe_float_metric(receiver.iloc[0].get(col), default=np.nan)
            non_val = _safe_float_metric(non_receiver.iloc[0].get(col), default=np.nan)
            row[col.replace("Rerata ", "Gap ")] = recv_val - non_val if np.isfinite(recv_val) and np.isfinite(non_val) else np.nan
            row[col] = recv_val
            row[f"{col} Belum Menerima"] = non_val
        rows.append(row)
    return pd.DataFrame(rows)


def _render_louvain_bansos_gap_heatmap(summary_df):
    gap_df = _build_louvain_bansos_gap_dataframe(summary_df)
    if gap_df.empty:
        st.info("Sebagian klaster hanya memiliki satu status bansos, sehingga selisih penerima vs belum menerima belum dapat dihitung.")
        return gap_df

    gap_cols = [col for col in gap_df.columns if col.startswith("Gap ")]
    if not gap_cols:
        return gap_df
    z_vals = gap_df[gap_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    max_abs = float(np.nanmax(np.abs(z_vals))) if z_vals.size else 1.0
    max_abs = max(max_abs, 1.0)
    metric_labels = [
        "IKD Agregat" if col == "Gap IKD Agregat" else col.replace("Gap ", "")
        for col in gap_cols
    ]
    text_vals = np.vectorize(lambda value: f"{value:+.1f}")(z_vals)
    fig = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=metric_labels,
            y=gap_df["Klaster Label"],
            text=text_vals,
            texttemplate="%{text}",
            colorscale=[[0.0, "#0F766E"], [0.5, "#FFFFFF"], [1.0, "#B91C1C"]],
            zmin=-max_abs,
            zmax=max_abs,
            zmid=0,
            colorbar=dict(title="Penerima - belum"),
        )
    )
    style_publication_figure(
        fig,
        title="Selisih Rerata Skor Penerima Bansos dibanding Belum Menerima",
        height=max(420, 190 + 34 * len(gap_df)),
        xaxis_title="Dimensi / agregat",
        yaxis_title="Klaster",
    )
    fig.update_xaxes(tickangle=-18)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    return gap_df


def _render_louvain_bansos_supporting_indicators(summary_df):
    support_specs = [
        ("Akses Internet/Informasi (%)", "Akses Internet/Informasi", 1, "%"),
        ("Kepemilikan Ponsel (%)", "Kepemilikan Ponsel", 1, "%"),
        ("Rerata Weighted Degree", "Weighted Degree", 3, ""),
        ("Rerata Betweenness Centrality", "Betweenness", 5, ""),
    ]
    records = []
    for col_name, label, decimals, suffix in support_specs:
        if col_name not in summary_df.columns:
            continue
        for _, row in summary_df.iterrows():
            value = _safe_float_metric(row.get(col_name), default=np.nan)
            if not np.isfinite(value):
                continue
            records.append(
                {
                    "Subkelompok Bansos": row["Subkelompok Bansos"],
                    "Status Bansos": row["Status Bansos"],
                    "Indikator": label,
                    "Nilai": value,
                    "Label Nilai": _format_profile_viz_value(value, decimals=decimals, suffix=suffix),
                }
            )
    support_df = pd.DataFrame(records)
    if support_df.empty:
        return

    facet_rows = int(np.ceil(support_df["Indikator"].nunique() / 2))
    fig = px.bar(
        support_df,
        x="Nilai",
        y="Subkelompok Bansos",
        color="Status Bansos",
        facet_col="Indikator",
        facet_col_wrap=2,
        orientation="h",
        text="Label Nilai",
        color_discrete_map={"Penerima": "#2563EB", "Belum Menerima": "#B91C1C"},
        category_orders={"Status Bansos": ["Penerima", "Belum Menerima"]},
        hover_data={"Label Nilai": True, "Nilai": ":.5f", "Indikator": False, "Subkelompok Bansos": False},
    )
    fig.update_traces(textposition="auto", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
    style_publication_figure(
        fig,
        title="Indikator Pendukung Status Bansos per Klaster",
        height=max(460, 250 * facet_rows + max(0, summary_df.shape[0] - 8) * 14),
        xaxis_title="Nilai",
        yaxis_title="Klaster dan status bansos",
        legend_title="Status bansos",
    )
    fig.update_xaxes(matches=None, showticklabels=True)
    fig.update_yaxes(matches=None, automargin=True)
    fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _classify_bansos_targeting_group(row):
    category = _profile_text(row.get("Kategori IKD"), default="Tidak Valid")
    status = _profile_text(row.get("Status Bansos"), default="Belum Menerima")
    vulnerable = category in {"Rendah", "Sedang"}
    strong = category in {"Tinggi", "Sangat Tinggi"}
    if vulnerable and status == "Penerima":
        return "Rentan - Penerima"
    if vulnerable and status != "Penerima":
        return "Rentan - Belum Menerima"
    if strong and status == "Penerima":
        return "Relatif kuat - Penerima"
    if strong and status != "Penerima":
        return "Relatif kuat - Belum Menerima"
    return "Tidak Valid"


def _render_louvain_bansos_targeting_mix(df_node_profile):
    if df_node_profile is None or df_node_profile.empty:
        return pd.DataFrame()
    required_cols = {"Klaster Louvain", "Status Bansos", "Kategori IKD"}
    if not required_cols.issubset(df_node_profile.columns):
        return pd.DataFrame()

    df = df_node_profile.copy()
    df["Klaster Louvain"] = pd.to_numeric(df["Klaster Louvain"], errors="coerce")
    df = df.dropna(subset=["Klaster Louvain"]).copy()
    if df.empty:
        return pd.DataFrame()
    df["Klaster Louvain"] = df["Klaster Louvain"].astype(int)
    df["Kelompok Verifikasi Bansos"] = df.apply(_classify_bansos_targeting_group, axis=1)
    mix_df = (
        df.groupby(["Klaster Louvain", "Kelompok Verifikasi Bansos"], as_index=False)
        .size()
        .rename(columns={"size": "Jumlah Node"})
    )
    totals = mix_df.groupby("Klaster Louvain", as_index=False)["Jumlah Node"].sum().rename(columns={"Jumlah Node": "Total Node Klaster"})
    mix_df = mix_df.merge(totals, on="Klaster Louvain", how="left")
    mix_df["Persentase (%)"] = (mix_df["Jumlah Node"] / mix_df["Total Node Klaster"].clip(lower=1)) * 100.0
    mix_df["Klaster Label"] = mix_df["Klaster Louvain"].map(_format_profile_cluster_label)
    mix_df["Label Jumlah"] = mix_df["Jumlah Node"].map(lambda value: f"{int(value)}")
    order = [
        "Rentan - Penerima",
        "Rentan - Belum Menerima",
        "Relatif kuat - Penerima",
        "Relatif kuat - Belum Menerima",
        "Tidak Valid",
    ]
    color_map = {
        "Rentan - Penerima": "#2563EB",
        "Rentan - Belum Menerima": "#B91C1C",
        "Relatif kuat - Penerima": "#D97706",
        "Relatif kuat - Belum Menerima": "#64748B",
        "Tidak Valid": "#CBD5E1",
    }
    fig = px.bar(
        mix_df,
        x="Klaster Label",
        y="Persentase (%)",
        color="Kelompok Verifikasi Bansos",
        text="Label Jumlah",
        barmode="stack",
        color_discrete_map=color_map,
        category_orders={"Kelompok Verifikasi Bansos": order},
        hover_data={"Jumlah Node": True, "Persentase (%)": ":.1f", "Klaster Label": False},
        title="Komposisi Verifikasi Bansos berdasarkan Kategori IKD per Klaster",
    )
    fig.update_traces(textposition="inside", marker_line_color="#FFFFFF", marker_line_width=0.6)
    style_publication_figure(
        fig,
        title="Komposisi Verifikasi Bansos berdasarkan Kategori IKD per Klaster",
        height=470,
        xaxis_title="",
        yaxis_title="Persentase (%)",
        legend_title="Kelompok verifikasi",
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    return mix_df


def _render_louvain_bansos_distribution(df_node_profile):
    if df_node_profile is None or df_node_profile.empty or "IKD Agregat" not in df_node_profile.columns:
        return
    df = df_node_profile.copy()
    df["Klaster Louvain"] = pd.to_numeric(df["Klaster Louvain"], errors="coerce")
    df = df.dropna(subset=["Klaster Louvain", "IKD Agregat"]).copy()
    if df.empty:
        return
    df["Klaster Louvain"] = df["Klaster Louvain"].astype(int)
    df["Klaster Label"] = df["Klaster Louvain"].map(_format_profile_cluster_label)
    if "Hover Aman" not in df.columns:
        df["Hover Aman"] = df["Kode Node"] if "Kode Node" in df.columns else df["Klaster Label"]
    fig = px.box(
        df,
        x="Klaster Label",
        y="IKD Agregat",
        color="Status Bansos",
        points="all",
        color_discrete_map={"Penerima": "#2563EB", "Belum Menerima": "#B91C1C"},
        category_orders={"Status Bansos": ["Penerima", "Belum Menerima"]},
        custom_data=["Hover Aman"],
        title="Sebaran IKD Agregat menurut Status Bansos per Klaster",
    )
    fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>", marker=dict(size=6, opacity=0.64, line=dict(color="#111827", width=0.3)))
    for cutoff, label, color in [(60, "Batas Sedang", "#B91C1C"), (70, "Batas Tinggi", "#D97706"), (80, "Batas Sangat Tinggi", "#2563EB")]:
        fig.add_hline(y=cutoff, line_dash="dash", line_color=color, annotation_text=label, annotation_position="top left")
    style_publication_figure(
        fig,
        title="Sebaran IKD Agregat menurut Status Bansos per Klaster",
        height=530,
        xaxis_title="Klaster",
        yaxis_title="IKD Agregat",
        legend_title="Status bansos",
    )
    fig.update_xaxes(tickangle=-18)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def render_louvain_bansos_dimension_analysis(df_node_profile):
    summary_df = _build_louvain_bansos_dimension_summary(df_node_profile)
    if summary_df.empty:
        st.info("Data status bansos dan dimensi IKD belum cukup untuk dianalisis per klaster.")
        return

    st.markdown("#### Analisis Penerima Bansos berdasarkan Dimensi IKD per Klaster")
    _render_louvain_bansos_dimension_heatmap(summary_df)
    gap_df = _render_louvain_bansos_gap_heatmap(summary_df)
    _render_louvain_bansos_supporting_indicators(summary_df)
    _render_louvain_bansos_targeting_mix(df_node_profile)
    _render_louvain_bansos_distribution(df_node_profile)

    display_cols = [
        "Klaster Label",
        "Status Bansos",
        "Jumlah Node",
        "Persentase Dalam Klaster (%)",
        "Rerata IKD Agregat",
        *[f"Rerata {dim_label}" for dim_label, _ in IKD_DIMENSION_MAP],
        "Akses Internet/Informasi (%)",
        "Kepemilikan Ponsel (%)",
        "Rerata Weighted Degree",
        "Rerata Betweenness Centrality",
    ]
    display_cols = [col for col in display_cols if col in summary_df.columns]
    st.dataframe(
        summary_df[display_cols].style.format(
            {
                "Persentase Dalam Klaster (%)": "{:.2f}",
                "Rerata IKD Agregat": "{:.2f}",
                "Akses Internet/Informasi (%)": "{:.2f}",
                "Kepemilikan Ponsel (%)": "{:.2f}",
                "Rerata Weighted Degree": "{:.4f}",
                "Rerata Betweenness Centrality": "{:.6f}",
                **{f"Rerata {dim_label}": "{:.2f}" for dim_label, _ in IKD_DIMENSION_MAP if f"Rerata {dim_label}" in summary_df.columns},
            }
        ),
        use_container_width=True,
    )

    if not gap_df.empty:
        gap_display_cols = [
            "Klaster Label",
            "Jumlah Penerima",
            "Jumlah Belum Menerima",
            "Persentase Penerima (%)",
            "Gap IKD Agregat",
            *[f"Gap {dim_label}" for dim_label, _ in IKD_DIMENSION_MAP],
        ]
        gap_display_cols = [col for col in gap_display_cols if col in gap_df.columns]
        st.dataframe(
            gap_df[gap_display_cols].style.format(
                {
                    "Persentase Penerima (%)": "{:.2f}",
                    "Gap IKD Agregat": "{:+.2f}",
                    **{f"Gap {dim_label}": "{:+.2f}" for dim_label, _ in IKD_DIMENSION_MAP if f"Gap {dim_label}" in gap_df.columns},
                }
            ),
            use_container_width=True,
        )


def _resolve_graph_node_id(graph_obj, node_id):
    if graph_obj is None:
        return node_id
    if node_id in graph_obj:
        return node_id
    node_text = str(node_id)
    for candidate in graph_obj.nodes():
        if str(candidate) == node_text:
            return candidate
    return node_id


def _node_profile_lookup(df_node_profile):
    if df_node_profile is None or df_node_profile.empty or "family_id" not in df_node_profile.columns:
        return {}
    return {str(row.get("family_id")): row for _, row in df_node_profile.iterrows()}


def _node_display_name(row, show_name=False):
    if row is None:
        return "Node tidak tersedia"
    if show_name:
        name = _profile_text(row.get("Nama"), default="")
        if name:
            return name
    code = _profile_text(row.get("Kode Node"), default="")
    if code:
        return code
    return _profile_text(row.get("family_id"), default="Node")


def _node_select_label(row, show_name=False):
    name = _node_display_name(row, show_name=show_name)
    cluster = _profile_text(row.get("Klaster Louvain"), default="-")
    category = _profile_text(row.get("Kategori IKD"), default="-")
    ikr = _format_profile_viz_value(row.get("IKD Agregat"), decimals=1)
    return f"{name} | Klaster {cluster} | {category} | IKD {ikr}"


def _dimension_similarity_text(base_row, other_row, top_n=3):
    if base_row is None or other_row is None:
        return "Tidak tersedia"
    diffs = []
    for dim_label, _ in IKD_DIMENSION_MAP:
        if dim_label not in base_row or dim_label not in other_row:
            continue
        base_val = _safe_float_metric(base_row.get(dim_label), default=np.nan)
        other_val = _safe_float_metric(other_row.get(dim_label), default=np.nan)
        if np.isfinite(base_val) and np.isfinite(other_val):
            diffs.append((dim_label, abs(base_val - other_val)))
    if not diffs:
        return "Tidak tersedia"
    diffs = sorted(diffs, key=lambda item: item[1])[:top_n]
    return ", ".join([f"{label} (selisih {diff:.1f})" for label, diff in diffs])


def _get_edge_weight(graph_obj, source, target):
    edge_data = graph_obj.get_edge_data(source, target, default={}) if graph_obj is not None else {}
    return _safe_float_metric(edge_data.get("weight", edge_data.get("similarity", 1.0)), default=1.0)


def _build_node_neighbor_profile(graph_obj, selected_node, df_node_profile, partition=None, show_names=False):
    if graph_obj is None or selected_node not in graph_obj:
        return pd.DataFrame()
    lookup = _node_profile_lookup(df_node_profile)
    selected_row = lookup.get(str(selected_node))
    rows = []
    for neighbor in graph_obj.neighbors(selected_node):
        neighbor_row = lookup.get(str(neighbor))
        neighbor_cluster = (
            neighbor_row.get("Klaster Louvain")
            if neighbor_row is not None and "Klaster Louvain" in neighbor_row
            else (partition or {}).get(neighbor, graph_obj.nodes[neighbor].get("cluster", -1))
        )
        rows.append(
            {
                "neighbor_id": neighbor,
                "Tetangga Terdekat": _node_display_name(neighbor_row, show_name=show_names),
                "Klaster Tetangga": int(_safe_float_metric(neighbor_cluster, default=-1)),
                "Bobot Similarity": _get_edge_weight(graph_obj, selected_node, neighbor),
                "Kategori IKD": _profile_text(neighbor_row.get("Kategori IKD") if neighbor_row is not None else None, default="Tidak tersedia"),
                "IKD Agregat": _safe_float_metric(neighbor_row.get("IKD Agregat") if neighbor_row is not None else np.nan, default=np.nan),
                "Dimensi Paling Mirip": _dimension_similarity_text(selected_row, neighbor_row),
            }
        )
    return pd.DataFrame(rows).sort_values("Bobot Similarity", ascending=False).reset_index(drop=True)


def _build_node_cluster_similarity(neighbor_df):
    if neighbor_df is None or neighbor_df.empty:
        return pd.DataFrame()
    stats = (
        neighbor_df.groupby("Klaster Tetangga", as_index=False)
        .agg(
            Jumlah_Tetangga=("neighbor_id", "count"),
            Total_Bobot=("Bobot Similarity", "sum"),
            Rata_Rata_Bobot=("Bobot Similarity", "mean"),
            Bobot_Maks=("Bobot Similarity", "max"),
        )
        .sort_values("Total_Bobot", ascending=False)
    )
    stats["Klaster Label"] = stats["Klaster Tetangga"].map(_format_profile_cluster_label)
    return stats.reset_index(drop=True)


def _render_node_neighbor_table(neighbor_df, top_n):
    if neighbor_df is None or neighbor_df.empty:
        st.info("Node terpilih belum memiliki tetangga pada graf aktif.")
        return
    display_cols = [
        "Tetangga Terdekat",
        "Klaster Tetangga",
        "Bobot Similarity",
        "Kategori IKD",
        "IKD Agregat",
        "Dimensi Paling Mirip",
    ]
    st.dataframe(
        neighbor_df.head(int(top_n))[display_cols].style.format(
            {
                "Bobot Similarity": "{:.4f}",
                "IKD Agregat": "{:.2f}",
            }
        ),
        use_container_width=True,
    )


def _render_node_cluster_similarity_bars(cluster_stats):
    if cluster_stats is None or cluster_stats.empty:
        return
    plot_df = cluster_stats.melt(
        id_vars=["Klaster Tetangga", "Klaster Label", "Jumlah_Tetangga"],
        value_vars=["Rata_Rata_Bobot", "Total_Bobot"],
        var_name="Metrik Similarity",
        value_name="Nilai",
    )
    plot_df["Metrik Similarity"] = plot_df["Metrik Similarity"].map(
        {
            "Rata_Rata_Bobot": "Rata-rata bobot",
            "Total_Bobot": "Total bobot",
        }
    )
    plot_df["Label Nilai"] = plot_df["Nilai"].map(lambda value: _format_profile_viz_value(value, decimals=3))
    fig = px.bar(
        plot_df,
        x="Klaster Label",
        y="Nilai",
        color="Klaster Label",
        facet_col="Metrik Similarity",
        text="Label Nilai",
        color_discrete_sequence=CONTRAST_COLORS,
        hover_data={"Jumlah_Tetangga": True, "Nilai": ":.5f", "Klaster Label": False},
        title="Bobot Similarity Node Terpilih ke Tiap Klaster",
    )
    fig.update_traces(textposition="outside", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
    style_publication_figure(
        fig,
        title="Bobot Similarity Node Terpilih ke Tiap Klaster",
        height=430,
        xaxis_title="Klaster tetangga",
        yaxis_title="Bobot similarity",
        showlegend=False,
    )
    fig.update_xaxes(matches=None, tickangle=-18)
    fig.update_yaxes(matches=None, rangemode="tozero")
    fig.for_each_annotation(lambda annotation: annotation.update(text=annotation.text.split("=")[-1]))
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_node_ego_network(graph_obj, selected_node, neighbor_df, selected_row, top_n=20, show_names=False):
    if graph_obj is None or selected_node not in graph_obj or neighbor_df is None or neighbor_df.empty:
        return
    ego_neighbors = neighbor_df.head(int(top_n)).copy()
    if ego_neighbors.empty:
        return

    angle_values = np.linspace(0, 2 * np.pi, len(ego_neighbors), endpoint=False)
    positions = {selected_node: (0.0, 0.0)}
    for angle, neighbor in zip(angle_values, ego_neighbors["neighbor_id"].tolist()):
        positions[neighbor] = (float(np.cos(angle)), float(np.sin(angle)))

    max_weight = max(float(ego_neighbors["Bobot Similarity"].max()), 1e-9)
    cluster_ids = sorted(ego_neighbors["Klaster Tetangga"].dropna().astype(int).unique().tolist())
    color_map = {cid: CONTRAST_COLORS[idx % len(CONTRAST_COLORS)] for idx, cid in enumerate(cluster_ids)}

    fig = go.Figure()
    for _, row in ego_neighbors.iterrows():
        neighbor = row["neighbor_id"]
        x0, y0 = positions[selected_node]
        x1, y1 = positions[neighbor]
        width = 1.0 + 5.0 * (_safe_float_metric(row.get("Bobot Similarity"), default=0.0) / max_weight)
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=width, color="rgba(71,85,105,0.38)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    neighbor_x = []
    neighbor_y = []
    neighbor_labels = []
    neighbor_colors = []
    neighbor_hover = []
    for _, row in ego_neighbors.iterrows():
        neighbor = row["neighbor_id"]
        x, y = positions[neighbor]
        neighbor_x.append(x)
        neighbor_y.append(y)
        neighbor_labels.append(row["Tetangga Terdekat"])
        neighbor_colors.append(color_map.get(int(row["Klaster Tetangga"]), "#64748B"))
        neighbor_hover.append(
            f"{html.escape(str(row['Tetangga Terdekat']))}<br>"
            f"Klaster: {int(row['Klaster Tetangga'])}<br>"
            f"Bobot similarity: {_safe_float_metric(row['Bobot Similarity'], default=0.0):.4f}<br>"
            f"Kategori IKD: {html.escape(str(row['Kategori IKD']))}<br>"
            f"IKD Agregat: {_safe_float_metric(row['IKD Agregat'], default=np.nan):.2f}<br>"
            f"Dimensi mirip: {html.escape(str(row['Dimensi Paling Mirip']))}"
        )

    fig.add_trace(
        go.Scatter(
            x=neighbor_x,
            y=neighbor_y,
            mode="markers+text",
            text=neighbor_labels,
            textposition="top center",
            hovertext=neighbor_hover,
            hoverinfo="text",
            marker=dict(size=15, color=neighbor_colors, line=dict(color="#111827", width=0.8)),
            name="Tetangga",
            showlegend=False,
        )
    )
    selected_label = _node_display_name(selected_row, show_name=show_names)
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers+text",
            text=[selected_label],
            textposition="bottom center",
            hovertext=[_node_select_label(selected_row, show_name=show_names)],
            hoverinfo="text",
            marker=dict(size=25, color="#111827", symbol="star", line=dict(color="#F59E0B", width=2)),
            name="Node terpilih",
            showlegend=False,
        )
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    style_publication_figure(
        fig,
        title="Ego Network Node Terpilih berdasarkan Top Neighbor",
        height=560,
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=24, r=24, t=72, b=24),
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def _render_node_centroid_comparison(df_node_profile, selected_node, selected_row, cluster_stats):
    metric_cols = ["IKD Agregat"] + [dim_label for dim_label, _ in IKD_DIMENSION_MAP if dim_label in df_node_profile.columns]
    metric_cols = [col for col in metric_cols if col in selected_row.index and col in df_node_profile.columns]
    if not metric_cols:
        return

    selected_cluster = int(_safe_float_metric(selected_row.get("Klaster Louvain"), default=-1))
    available_clusters = sorted(pd.to_numeric(df_node_profile["Klaster Louvain"], errors="coerce").dropna().astype(int).unique().tolist())
    similarity_defaults = []
    if cluster_stats is not None and not cluster_stats.empty:
        similarity_defaults = cluster_stats.sort_values("Total_Bobot", ascending=False)["Klaster Tetangga"].astype(int).head(3).tolist()
    default_clusters = list(dict.fromkeys([selected_cluster, *similarity_defaults]))
    default_clusters = [cluster for cluster in default_clusters if cluster in available_clusters]
    comparison_clusters = st.multiselect(
        "Pilih centroid klaster pembanding",
        options=available_clusters,
        default=default_clusters or available_clusters[: min(3, len(available_clusters))],
        format_func=lambda value: _format_profile_cluster_label(value),
        key="louvain_node_centroid_comparison_clusters",
    )
    if not comparison_clusters:
        st.info("Pilih minimal satu klaster pembanding untuk melihat centroid.")
        return

    rows = [
        {
            "Profil": "Node terpilih",
            **{col: _safe_float_metric(selected_row.get(col), default=np.nan) for col in metric_cols},
        }
    ]
    for cluster_id in comparison_clusters:
        cluster_df = df_node_profile[pd.to_numeric(df_node_profile["Klaster Louvain"], errors="coerce").eq(cluster_id)]
        rows.append(
            {
                "Profil": f"Rerata {_format_profile_cluster_label(cluster_id)}",
                **{col: _profile_mean(cluster_df[col], default=np.nan) for col in metric_cols},
            }
        )
    comparison_df = pd.DataFrame(rows)
    z_vals = comparison_df[metric_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    text_vals = np.vectorize(lambda value: f"{value:.1f}")(z_vals)
    fig = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=metric_cols,
            y=comparison_df["Profil"],
            text=text_vals,
            texttemplate="%{text}",
            colorscale=PUBLICATION_CONTINUOUS_SCALE,
            zmin=0,
            zmax=100,
            colorbar=dict(title="Skor"),
        )
    )
    style_publication_figure(
        fig,
        title="Perbandingan Profil Node dengan Centroid Klaster",
        height=max(420, 190 + 44 * len(comparison_df)),
        xaxis_title="Agregat dan dimensi",
        yaxis_title="Profil pembanding",
    )
    fig.update_xaxes(tickangle=-18)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    own_cluster_df = df_node_profile[pd.to_numeric(df_node_profile["Klaster Louvain"], errors="coerce").eq(selected_cluster)]
    if own_cluster_df.empty:
        return
    deviation_rows = []
    for col in metric_cols:
        node_val = _safe_float_metric(selected_row.get(col), default=np.nan)
        cluster_val = _profile_mean(own_cluster_df[col], default=np.nan)
        if np.isfinite(node_val) and np.isfinite(cluster_val):
            deviation_rows.append(
                {
                    "Indikator": col,
                    "Selisih Node - Rerata Klaster": node_val - cluster_val,
                    "Label Selisih": _format_profile_viz_value(node_val - cluster_val, decimals=1),
                }
            )
    deviation_df = pd.DataFrame(deviation_rows)
    if deviation_df.empty:
        return
    fig_dev = px.bar(
        deviation_df,
        x="Selisih Node - Rerata Klaster",
        y="Indikator",
        orientation="h",
        color="Selisih Node - Rerata Klaster",
        color_continuous_scale=[[0.0, "#B91C1C"], [0.5, "#FFFFFF"], [1.0, "#0F766E"]],
        text="Label Selisih",
        title="Deviasi Node terhadap Rerata Klaster Asalnya",
    )
    fig_dev.add_vline(x=0, line_dash="dash", line_color="#111827")
    fig_dev.update_traces(textposition="outside", cliponaxis=False, marker_line_color="#111827", marker_line_width=0.35)
    style_publication_figure(
        fig_dev,
        title=f"Deviasi Node terhadap Rerata {_format_profile_cluster_label(selected_cluster)}",
        height=430,
        xaxis_title="Selisih skor",
        yaxis_title="Indikator",
        showlegend=False,
    )
    fig_dev.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_dev, use_container_width=True, config=PLOTLY_DRAW_CONFIG)


def render_louvain_node_membership_diagnostic(graph_obj, partition, df_node_profile, publish_mode=True):
    if graph_obj is None or graph_obj.number_of_nodes() == 0 or df_node_profile is None or df_node_profile.empty:
        st.info("Data node/graf belum cukup untuk uji posisi node dalam klaster.")
        return

    st.markdown("#### Uji Dinamis Posisi Node dalam Klaster Louvain")
    show_names = st.checkbox(
        "Gunakan nama KK pada pilihan node",
        value=not publish_mode,
        key="louvain_node_diagnostic_show_names",
        help="Untuk publikasi sebaiknya tetap memakai Kode Node anonim.",
    )

    node_df = df_node_profile.copy()
    node_df["_select_label"] = node_df.apply(lambda row: _node_select_label(row, show_name=show_names), axis=1)
    anomaly_summary = _build_louvain_category_anomaly_summary(df_node_profile)
    anomaly_detail = _build_louvain_anomaly_node_detail(df_node_profile, anomaly_summary) if not anomaly_summary.empty else pd.DataFrame()
    default_node = None
    if not anomaly_detail.empty:
        default_node = anomaly_detail.iloc[0].get("family_id")
    if default_node is None or str(default_node) not in set(node_df["family_id"].astype(str)):
        default_node = node_df.sort_values("IKD Agregat", ascending=False).iloc[0].get("family_id")
    node_options = node_df.sort_values("_select_label")["family_id"].tolist()
    default_idx = next((idx for idx, node_id in enumerate(node_options) if str(node_id) == str(default_node)), 0)
    label_lookup = dict(zip(node_df["family_id"], node_df["_select_label"]))

    selected_raw = st.selectbox(
        "Pilih KK/node yang ingin diuji",
        options=node_options,
        index=default_idx,
        format_func=lambda value: label_lookup.get(value, str(value)),
        key="louvain_node_membership_selected_node",
    )
    selected_node = _resolve_graph_node_id(graph_obj, selected_raw)
    lookup = _node_profile_lookup(df_node_profile)
    selected_row = lookup.get(str(selected_node), lookup.get(str(selected_raw)))
    if selected_node not in graph_obj or selected_row is None:
        st.info("Node terpilih tidak ditemukan pada graf aktif.")
        return

    neighbor_df = _build_node_neighbor_profile(graph_obj, selected_node, df_node_profile, partition=partition, show_names=show_names)
    cluster_stats = _build_node_cluster_similarity(neighbor_df)
    selected_cluster = int(_safe_float_metric(selected_row.get("Klaster Louvain"), default=-1))
    selected_name = _node_display_name(selected_row, show_name=show_names)

    if not cluster_stats.empty:
        strongest_total = cluster_stats.sort_values("Total_Bobot", ascending=False).iloc[0]
        strongest_mean = cluster_stats.sort_values("Rata_Rata_Bobot", ascending=False).iloc[0]
        own_stats = cluster_stats[cluster_stats["Klaster Tetangga"].eq(selected_cluster)]
        own_text = "tidak memiliki edge langsung ke klaster asal"
        if not own_stats.empty:
            own_text = (
                f"memiliki {int(own_stats.iloc[0]['Jumlah_Tetangga'])} tetangga langsung "
                f"dengan total bobot {own_stats.iloc[0]['Total_Bobot']:.3f} di klaster asal"
            )
        st.markdown(
            f"<div class='soft-card'><b>{html.escape(str(selected_name))}</b> berada di "
            f"<b>{html.escape(_format_profile_cluster_label(selected_cluster))}</b>. "
            f"Bobot similarity total terbesar mengarah ke <b>{html.escape(str(strongest_total['Klaster Label']))}</b> "
            f"({strongest_total['Total_Bobot']:.3f}), sedangkan rata-rata bobot tertinggi mengarah ke "
            f"<b>{html.escape(str(strongest_mean['Klaster Label']))}</b> ({strongest_mean['Rata_Rata_Bobot']:.3f}). "
            f"Node ini {own_text}. Jika bobot dan tetangga terkuat lebih terkonsentrasi pada klaster asal, "
            f"maka posisi Louvain-nya konsisten dengan struktur edge, meskipun kategori IKD-nya berbeda.</div>",
            unsafe_allow_html=True,
        )

    neighbor_count = int(neighbor_df.shape[0]) if neighbor_df is not None and not neighbor_df.empty else 0
    top_n = st.slider(
        "Jumlah top neighbor yang ditampilkan",
        min_value=1,
        max_value=40,
        value=15,
        step=1,
        key="louvain_node_diagnostic_top_neighbors",
        help="Range kontrol tetap 1-40. Jika neighbor aktual lebih sedikit dari angka pilihan, hanya neighbor yang tersedia yang ditampilkan.",
    )
    if neighbor_count <= 0:
        st.caption("Node ini belum memiliki neighbor langsung pada graf aktif.")
    elif neighbor_count < top_n:
        st.caption(f"Node ini hanya memiliki {neighbor_count} neighbor langsung; tampilan mengikuti jumlah neighbor yang tersedia.")

    col_left, col_right = st.columns([1.05, 0.95])
    with col_left:
        st.markdown("##### Top Neighbor dan Bobot Similarity")
        _render_node_neighbor_table(neighbor_df, top_n)
    with col_right:
        st.markdown("##### Ringkasan Similarity ke Klaster")
        if cluster_stats.empty:
            st.info("Belum ada edge tetangga untuk dihitung.")
        else:
            st.dataframe(
                cluster_stats.style.format(
                    {
                        "Total_Bobot": "{:.4f}",
                        "Rata_Rata_Bobot": "{:.4f}",
                        "Bobot_Maks": "{:.4f}",
                    }
                ),
                use_container_width=True,
            )

    _render_node_cluster_similarity_bars(cluster_stats)
    _render_node_ego_network(graph_obj, selected_node, neighbor_df, selected_row, top_n=top_n, show_names=show_names)
    _render_node_centroid_comparison(df_node_profile, selected_node, selected_row, cluster_stats)


def render_louvain_cluster_profile_page(graph_obj, partition, df_v, selected_desa, col_spasial=None, layout_spread=2.2):
    st.markdown(f"<h1 class='main-header'>Profil Karakteristik Klaster Louvain: {html.escape(str(selected_desa))}</h1>", unsafe_allow_html=True)
    publish_mode = st.toggle("Mode publikasi / anonimisasi", value=True, key="louvain_cluster_profile_publish")
    st.markdown(
        "<div class='premium-hero'><b>Profil Karakteristik Klaster Louvain</b><br>"
        "Klaster Louvain menunjukkan kelompok node yang lebih rapat dan lebih mirip berdasarkan struktur graf. "
        "Klaster bukan batas administratif, melainkan pola komunitas berbasis kemiripan dan keterhubungan.</div>",
        unsafe_allow_html=True,
    )

    if graph_obj is None or graph_obj.number_of_nodes() == 0:
        st.info("Graf Louvain belum tersedia untuk desa dan konfigurasi saat ini.")
        return

    profile_df = build_louvain_cluster_characteristics(
        graph_obj=graph_obj,
        partition=partition,
        df_v=df_v,
        col_spasial=col_spasial,
        publish_mode=publish_mode,
    )
    if profile_df.empty:
        st.info("Profil klaster belum dapat dihitung karena data graf atau atribut node belum cukup.")
        return

    partition_complete = {
        n: _cluster_id_for_node(n, graph_obj.nodes[n], partition)
        for n in graph_obj.nodes()
    }
    try:
        modularity_q = _safe_float_metric(community_louvain.modularity(partition_complete, graph_obj, weight="weight"), default=0.0)
    except Exception:
        modularity_q = 0.0
    largest_row = profile_df.sort_values("Jumlah Node", ascending=False).iloc[0]
    graph_ikr_values = [
        _safe_float_metric(graph_obj.nodes[n].get("f_ikr_dari_rekap_kk"), default=np.nan)
        for n in graph_obj.nodes()
    ]
    graph_ikr_avg = _profile_mean(graph_ikr_values, default=0.0)

    kpi_cols = st.columns(6)
    kpi_cols[0].metric("Jumlah Klaster", f"{int(profile_df['Klaster Louvain'].nunique()):,}")
    kpi_cols[1].metric("Jumlah Node", f"{int(graph_obj.number_of_nodes()):,}")
    kpi_cols[2].metric("Jumlah Edge", f"{int(graph_obj.number_of_edges()):,}")
    kpi_cols[3].metric("Modularity Q", f"{modularity_q:.4f}")
    kpi_cols[4].metric("Klaster Terbesar", f"Klaster {int(largest_row['Klaster Louvain'])}", f"{int(largest_row['Jumlah Node'])} node")
    kpi_cols[5].metric("Rerata IKD Graf", f"{graph_ikr_avg:.2f}")

    st.markdown("#### Tabel Profil Karakteristik Klaster")
    percent_cols = [c for c in profile_df.columns if "Persentase" in c]
    centrality_cols = [c for c in profile_df.columns if "Centrality" in c]
    formatters = {
        **{c: "{:.2f}" for c in percent_cols},
        **{c: "{:.6f}" for c in centrality_cols},
        "Density Internal": "{:.4f}",
        "Rerata Weighted Degree": "{:.4f}",
        "Rerata IKD Agregat": "{:.2f}",
        "Rerata Sandang, Pangan, dan Papan": "{:.2f}",
        "Rerata Pendidikan": "{:.2f}",
        "Rerata Sosial, Hukum, dan HAM": "{:.2f}",
        "Rerata Kesehatan dan Pekerjaan": "{:.2f}",
        "Rerata Lingkungan dan Infrastruktur": "{:.2f}",
        "Nilai Dimensi Terlemah": "{:.2f}",
        "Nilai Dimensi Terkuat": "{:.2f}",
    }
    st.dataframe(profile_df.style.format(formatters), use_container_width=True)
    safe_desa = "".join(ch if str(ch).isalnum() or ch in {"_", "-"} else "_" for ch in str(selected_desa).strip()) or "desa"
    st.download_button(
        "Unduh Profil Klaster Louvain",
        data=profile_df.to_csv(index=False).encode("utf-8"),
        file_name=f"profil_klaster_louvain_{safe_desa}.csv",
        mime="text/csv",
        key="download_louvain_cluster_profile",
    )
    render_louvain_profile_variable_visualizations(profile_df)

    dim_average_cols = [
        "Rerata Sandang, Pangan, dan Papan",
        "Rerata Pendidikan",
        "Rerata Sosial, Hukum, dan HAM",
        "Rerata Kesehatan dan Pekerjaan",
        "Rerata Lingkungan dan Infrastruktur",
        "Rerata IKD Agregat",
    ]
    dim_short_labels = [
        "Sandang/Pangan/Papan",
        "Pendidikan",
        "Sosial/Hukum/HAM",
        "Kesehatan/Pekerjaan",
        "Lingkungan/Infrastruktur",
        "IKD Agregat",
    ]
    heat_df = profile_df[["Klaster Louvain"] + dim_average_cols].copy()
    heat_df["Klaster Label"] = heat_df["Klaster Louvain"].map(lambda v: f"Klaster {int(v)}")
    z_vals = heat_df[dim_average_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    text_vals = np.vectorize(lambda x: f"{x:.1f}")(z_vals)
    fig_heat = go.Figure(
        go.Heatmap(
            z=z_vals,
            x=dim_short_labels,
            y=heat_df["Klaster Label"],
            text=text_vals,
            texttemplate="%{text}",
            colorscale=PUBLICATION_CONTINUOUS_SCALE,
            zmin=0,
            zmax=100,
            colorbar=dict(title="Rerata skor"),
        )
    )
    style_publication_figure(fig_heat, title="Heatmap Profil Dimensi IKD per Klaster", height=max(420, 210 + (34 * len(heat_df))), xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    st.markdown("#### Radar Chart Dimensi IKD per Klaster")
    cluster_options = profile_df["Klaster Louvain"].tolist()
    default_clusters = profile_df.sort_values("Jumlah Node", ascending=False).head(min(5, len(profile_df)))["Klaster Louvain"].tolist()
    selected_clusters = st.multiselect(
        "Pilih klaster untuk radar",
        options=cluster_options,
        default=default_clusters,
        key="louvain_profile_radar_clusters",
    )
    radar_dims = dim_average_cols[:-1]
    radar_labels = dim_short_labels[:-1]
    if selected_clusters:
        fig_radar = go.Figure()
        for idx, cluster_id in enumerate(selected_clusters):
            row = profile_df[profile_df["Klaster Louvain"] == cluster_id]
            if row.empty:
                continue
            vals = [float(_safe_float_metric(row.iloc[0].get(col), default=0.0)) for col in radar_dims]
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=radar_labels + [radar_labels[0]],
                    fill="toself",
                    name=f"Klaster {int(cluster_id)}",
                    line=dict(color=CONTRAST_COLORS[idx % len(CONTRAST_COLORS)]),
                    opacity=0.72,
                )
            )
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template=PUBLICATION_TEMPLATE,
            height=520,
            margin=dict(l=48, r=48, t=72, b=48),
            title=dict(text="Radar Lima Dimensi IKD per Klaster", x=0.02, xanchor="left"),
            font=dict(color=PLOT_TEXT_COLOR, family=PUBLICATION_FONT, size=13),
        )
        st.plotly_chart(fig_radar, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    else:
        st.info("Pilih minimal satu klaster untuk menampilkan radar chart.")

    bar_col_1, bar_col_2 = st.columns(2)
    with bar_col_1:
        ikr_comp = profile_df[
            [
                "Klaster Louvain",
                "Persentase IKD Rendah (%)",
                "Persentase IKD Sedang (%)",
                "Persentase IKD Tinggi (%)",
                "Persentase IKD Sangat Tinggi (%)",
            ]
        ].melt(id_vars="Klaster Louvain", var_name="Kategori IKD", value_name="Persentase")
        ikr_comp["Kategori IKD"] = (
            ikr_comp["Kategori IKD"]
            .str.replace("Persentase IKD ", "", regex=False)
            .str.replace(" (%)", "", regex=False)
        )
        ikr_comp["Klaster Label"] = ikr_comp["Klaster Louvain"].map(lambda v: f"Klaster {int(v)}")
        fig_ikr_stack = px.bar(
            ikr_comp,
            x="Klaster Label",
            y="Persentase",
            color="Kategori IKD",
            barmode="stack",
            color_discrete_map=BPS_CATEGORY_COLORS,
            category_orders={"Kategori IKD": ["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"]},
            title="Komposisi Kategori IKD per Klaster",
        )
        style_publication_figure(fig_ikr_stack, title="Komposisi Kategori IKD per Klaster", height=440, xaxis_title="", yaxis_title="Persentase (%)", legend_title="Kategori IKD")
        fig_ikr_stack.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig_ikr_stack, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    with bar_col_2:
        bansos_comp = profile_df[
            [
                "Klaster Louvain",
                "Persentase Penerima Bansos (%)",
                "Persentase Belum Menerima Bansos (%)",
            ]
        ].melt(id_vars="Klaster Louvain", var_name="Status Bansos", value_name="Persentase")
        bansos_comp["Status Bansos"] = (
            bansos_comp["Status Bansos"]
            .str.replace("Persentase ", "", regex=False)
            .str.replace(" Bansos (%)", "", regex=False)
        )
        bansos_comp["Klaster Label"] = bansos_comp["Klaster Louvain"].map(lambda v: f"Klaster {int(v)}")
        fig_bansos_stack = px.bar(
            bansos_comp,
            x="Klaster Label",
            y="Persentase",
            color="Status Bansos",
            barmode="stack",
            color_discrete_map={"Penerima": "#2563EB", "Belum Menerima": "#B91C1C"},
            title="Komposisi Status Bansos per Klaster",
        )
        style_publication_figure(fig_bansos_stack, title="Komposisi Status Bansos per Klaster", height=440, xaxis_title="", yaxis_title="Persentase (%)", legend_title="Status Bansos")
        fig_bansos_stack.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig_bansos_stack, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    df_node_profile = build_louvain_cluster_node_profile_dataframe(
        graph_obj=graph_obj,
        partition=partition,
        df_v=df_v,
        col_spasial=col_spasial,
        publish_mode=publish_mode,
    )
    render_louvain_bansos_dimension_analysis(df_node_profile)
    render_louvain_category_anomaly_analysis(df_node_profile, publish_mode=publish_mode)
    render_louvain_node_membership_diagnostic(graph_obj, partition, df_node_profile, publish_mode=publish_mode)

    st.markdown("#### Komposisi Dusun per Klaster")
    dusun_attr_profile = col_spasial if col_spasial else ("dusun" if isinstance(df_v, pd.DataFrame) and "dusun" in df_v.columns else None)
    df_dusun_cluster, _, _ = build_dusun_cluster_composition(graph_obj, dusun_attr= dusun_attr_profile, partition=partition)
    if df_dusun_cluster.empty:
        st.info("Komposisi dusun belum tersedia untuk graf aktif.")
    else:
        dusun_plot = df_dusun_cluster.copy()
        dusun_plot["Klaster Profil"] = dusun_plot["ID Klaster Internal"].map(lambda v: f"Klaster {int(v)}" if int(v) >= 0 else "Tidak Terklaster")
        if publish_mode:
            dusun_codes = {val: f"Dusun-{idx + 1}" for idx, val in enumerate(sorted(dusun_plot["Dusun"].astype(str).unique()))}
            dusun_plot["Dusun Visual"] = dusun_plot["Dusun"].astype(str).map(dusun_codes)
        else:
            dusun_plot["Dusun Visual"] = dusun_plot["Dusun"].astype(str)
        dusun_pivot = dusun_plot.pivot_table(
            index="Klaster Profil",
            columns="Dusun Visual",
            values="Persentase dari Klaster (%)",
            aggfunc="sum",
            fill_value=0.0,
        )
        if not dusun_pivot.empty:
            z_dusun = dusun_pivot.to_numpy(dtype=float)
            text_dusun = np.vectorize(lambda x: f"{x:.1f}%")(z_dusun)
            fig_dusun_heat = go.Figure(
                go.Heatmap(
                    z=z_dusun,
                    x=dusun_pivot.columns.tolist(),
                    y=dusun_pivot.index.tolist(),
                    text=text_dusun,
                    texttemplate="%{text}",
                    colorscale="YlGnBu",
                    zmin=0,
                    zmax=100,
                    colorbar=dict(title="% dari klaster"),
                )
            )
            style_publication_figure(
                fig_dusun_heat,
                title="Heatmap Konsentrasi Dusun dalam Setiap Klaster",
                height=max(420, 210 + (34 * len(dusun_pivot))),
                xaxis_title="Dusun/Kode dusun",
                yaxis_title="Klaster Louvain",
            )
            st.plotly_chart(fig_dusun_heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    st.markdown("#### Scatter Centrality vs IKD")
    x_metric_options = [
        ("Weighted Degree", "Weighted Degree"),
        ("Degree Centrality", "Degree Centrality"),
        ("Betweenness Centrality", "Betweenness Centrality"),
        ("Closeness Centrality", "Closeness Centrality"),
        ("Eigenvector Centrality", "Eigenvector Centrality"),
    ]
    selected_x_metric = st.selectbox(
        "Metrik centrality pada sumbu X",
        options=x_metric_options,
        format_func=lambda x: x[0],
        key="louvain_profile_scatter_metric",
    )[1]
    if not df_node_profile.empty and selected_x_metric in df_node_profile.columns:
        scatter_df = df_node_profile.dropna(subset=["IKD Agregat"]).copy()
        scatter_df[selected_x_metric] = pd.to_numeric(scatter_df[selected_x_metric], errors="coerce").fillna(0.0)
        scatter_df["Klaster Label"] = scatter_df["Klaster Louvain"].map(lambda v: f"Klaster {int(v)}")
        size_source = "Betweenness Centrality" if "Betweenness Centrality" in scatter_df.columns else "Weighted Degree"
        scatter_df["Ukuran Visual"] = pd.to_numeric(scatter_df[size_source], errors="coerce").fillna(0.0)
        if float(scatter_df["Ukuran Visual"].max()) <= 0 and "Weighted Degree" in scatter_df.columns:
            scatter_df["Ukuran Visual"] = pd.to_numeric(scatter_df["Weighted Degree"], errors="coerce").fillna(0.0)
        scatter_df["Ukuran Visual"] = scatter_df["Ukuran Visual"] + max(float(scatter_df["Ukuran Visual"].max()) * 0.05, 1e-6)
        fig_scatter = px.scatter(
            scatter_df,
            x=selected_x_metric,
            y="IKD Agregat",
            color="Klaster Label",
            symbol="Status Bansos",
            size="Ukuran Visual",
            hover_name="Kode Node",
            custom_data=["Hover Aman"],
            title="IKD Agregat vs Centrality pada Node Klaster Louvain",
            color_discrete_sequence=CONTRAST_COLORS,
        )
        fig_scatter.update_traces(hovertemplate="%{customdata[0]}<extra></extra>", marker=dict(line=dict(color="#111827", width=0.45)))
        median_centrality = float(pd.to_numeric(scatter_df[selected_x_metric], errors="coerce").fillna(0.0).median())
        fig_scatter.add_hline(y=60.0, line_dash="dash", line_color="#B91C1C", annotation_text="Batas IKD 60")
        fig_scatter.add_vline(x=median_centrality, line_dash="dash", line_color="#111827", annotation_text="Median centrality")
        fig_scatter.add_annotation(x=0.76, y=0.20, xref="paper", yref="paper", text="Prioritas verifikasi, mudah dijangkau jaringan", showarrow=False, font=dict(size=11, color="#92400E"))
        fig_scatter.add_annotation(x=0.22, y=0.20, xref="paper", yref="paper", text="Rentan dan relatif terisolasi", showarrow=False, font=dict(size=11, color="#B91C1C"))
        fig_scatter.add_annotation(x=0.76, y=0.84, xref="paper", yref="paper", text="Penghubung informasi potensial", showarrow=False, font=dict(size=11, color="#1D4ED8"))
        fig_scatter.add_annotation(x=0.24, y=0.84, xref="paper", yref="paper", text="Relatif stabil, bukan prioritas jaringan", showarrow=False, font=dict(size=11, color="#475569"))
        style_publication_figure(fig_scatter, title="IKD Agregat vs Centrality pada Node Klaster Louvain", height=570, xaxis_title=selected_x_metric, yaxis_title="IKD Agregat", legend_title="")
        st.plotly_chart(fig_scatter, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
    else:
        st.info("Data node untuk scatter centrality vs IKD belum tersedia.")

    st.markdown("#### Kartu Narasi Otomatis per Klaster")
    for _, row in profile_df.iterrows():
        label = _profile_text(row.get("Label Karakter Klaster"), default="-")
        story = generate_louvain_cluster_story(row)
        implication = _profile_text(row.get("Implikasi Program"), default="-")
        note = _profile_text(row.get("Catatan Etika"), default="-")
        st.markdown(
            f"<div class='soft-card'><b>Klaster {int(row['Klaster Louvain'])}: {html.escape(label)}</b><br>"
            f"{html.escape(story)}<br><br>"
            f"<b>Implikasi Program:</b> {html.escape(implication)}<br>"
            f"<b>Catatan Etika:</b> {html.escape(note)}</div>",
            unsafe_allow_html=True,
        )

    with subbab_dropdown("Catatan Etika dan Batasan Interpretasi", expanded=True):
        st.markdown(
            """
            - Klaster Louvain adalah hasil pengelompokan berbasis struktur graf, bukan label sosial permanen.
            - Hasil ini tidak boleh digunakan sebagai dasar tunggal penetapan bantuan.
            - Hasil ini bersifat indikatif untuk mendukung verifikasi, diskusi kebijakan, dan perencanaan program.
            - Data mikro rumah tangga harus dianonimkan dalam publikasi.
            - Hindari penyebutan nama individu, alamat spesifik, atau identitas sensitif.
            - Verifikasi lapangan tetap diperlukan.
            """
        )


def build_ikr_assortativity_table(graph_obj, dimension_map=None):
    dimension_map = dimension_map or IKD_DIMENSION_MAP
    rows = []
    overall_label, overall_col = IKD_OVERALL_METRIC
    r_overall = safe_numeric_assortativity(graph_obj, overall_col, default=0.0)
    dir_overall, lvl_overall = interpret_assortativity_value(r_overall)
    rows.append(
        {
            "Dimensi IKD": overall_label,
            "Sumber Skor": format_dimension_source_label(overall_col),
            "Kolom Internal": overall_col,
            "Assortativity r": float(r_overall),
            "Arah": dir_overall,
            "Kekuatan": lvl_overall,
            "Jenis": "Agregat",
        }
    )
    for dim_label, col_name in dimension_map:
        r_val = safe_numeric_assortativity(graph_obj, col_name, default=0.0)
        direction, strength = interpret_assortativity_value(r_val)
        rows.append(
            {
                "Dimensi IKD": dim_label,
                "Sumber Skor": format_dimension_source_label(col_name),
                "Kolom Internal": col_name,
                "Assortativity r": float(r_val),
                "Arah": direction,
                "Kekuatan": strength,
                "Jenis": "Dimensi",
            }
        )
    return pd.DataFrame(rows)


def compute_base_five_dimension_summary(df_assort):
    if df_assort is None or df_assort.empty:
        return None
    filter_col = "Kolom Internal" if "Kolom Internal" in df_assort.columns else "Kolom Database"
    df_dims = df_assort[df_assort[filter_col].isin(EDGE_REKAP_COLS)].copy()
    if df_dims.empty:
        return None
    r_mean = float(df_dims["Assortativity r"].mean())
    direction, strength = interpret_assortativity_value(r_mean)
    return {
        "Dimensi IKD": "Ringkasan Lima Dimensi Kesejahteraan",
        "Sumber Skor": "Rata-rata koefisien lima dimensi penyusun",
        "Kolom Internal": "ringkasan_lima_dimensi",
        "Assortativity r": r_mean,
        "Arah": direction,
        "Kekuatan": strength,
        "Jenis": "Ringkasan",
    }

# =========================================================
# 2. CORE ANALYTICS ENGINE
# =========================================================

@st.cache_data
def load_and_clean_ddp(file):
    try:
        file_name = getattr(file, "name", str(file))
        if file_name.lower().endswith('.csv'):
            df = pd.read_csv(file)
        else:
            xls = pd.ExcelFile(file)
            sheet_name = next(
                (s for s in xls.sheet_names if str(s).lower() == "database"),
                next((s for s in xls.sheet_names if str(s).lower() == "dataset"), xls.sheet_names[0])
            )
            df = xls.parse(sheet_name)
        df.columns = [
            str(c).lower().strip().replace("\u00a0", " ").replace("\n", " ")
            for c in df.columns
        ]
        df.columns = [c.replace("  ", " ").strip() for c in df.columns]

        def pick_col(candidates):
            for cand in candidates:
                if cand in df.columns:
                    return cand
            return None

        subjek_col = pick_col(["subjek", "subyek", "subject"])
        if subjek_col is None:
            subjek_candidates = [c for c in df.columns if "subjek" in c]
            if subjek_candidates:
                subjek_col = subjek_candidates[0]
        if subjek_col is None:
            st.error("Kolom wajib `subjek` tidak ditemukan pada file upload.")
            return pd.DataFrame()

        family_src = pick_col([
            "family_id", "nomor kartu keluarga", "nomor_kartu_keluarga", "no_kk", "nokk", "kk"
        ])
        if family_src is None:
            st.warning("Kolom ID keluarga tidak ditemukan, `family_id` dibuat otomatis dari nomor baris.")
            df["family_id"] = [f"AUTO_FID_{i+1}" for i in range(len(df))]
        else:
            df["family_id"] = df[family_src].astype(str).str.strip()
            bad_fid = df["family_id"].isin(["", "nan", "none"])
            if bad_fid.any():
                df.loc[bad_fid, "family_id"] = [f"AUTO_FID_{i+1}" for i in range(int(bad_fid.sum()))]

        if "deskel" not in df.columns:
            nama_deskel_col = pick_col(["nama deskel", "desa", "nama desa"])
            if nama_deskel_col is not None:
                df["deskel"] = df[nama_deskel_col]
        if "desa" not in df.columns and "deskel" in df.columns:
            df["desa"] = df["deskel"]

        if "par_organisa" not in df.columns and "partisipasi organisasi" in df.columns:
            df["par_organisa"] = df["partisipasi organisasi"]
        if "bansos" not in df.columns and "keikutsertaan program bantuan" in df.columns:
            df["bansos"] = df["keikutsertaan program bantuan"]

        df['subjek_clean'] = df[subjek_col].astype(str).str.lower().str.strip()
        df_kk = df[df['subjek_clean'].str.contains('kepala keluarga', na=False)].drop_duplicates('family_id').copy()
        if df_kk.empty:
            st.error("Tidak ada baris dengan `subjek` berisi 'kepala keluarga'.")
            return pd.DataFrame()

        bansos_col = pick_col(["bansos", "keikutsertaan program bantuan", "program bantuan", "bantuan sosial", "bansos bantuan"])
        media_info_col = pick_col(["media informasi", "media_informasi", "akses informasi", "sumber informasi", "media info"])
        ponsel_col = pick_col(["kepemilikan ponsel", "kepemilikan_ponsel", "memiliki ponsel", "ponsel", "hp"])

        bansos_src = df_kk[bansos_col] if bansos_col in df_kk.columns else pd.Series(["0"] * len(df_kk), index=df_kk.index)
        df_kk['bansos_num'] = bansos_src.apply(to_binary_presence).astype(int)

        if media_info_col in df_kk.columns:
            df_kk['internet_num'] = df_kk[media_info_col].apply(to_binary_presence).astype(int)
        else:
            # Fallback: legacy digital indicator dari wifi/medsos bila kolom media informasi tidak tersedia.
            df_kk['internet_num'] = df_kk.apply(
                lambda r: 1 if (pd.notnull(r.get('wifi')) and _normalize_text(r.get('wifi')) not in {'tidak ada', '0', '0.0', 'nan', 'none', ''})
                or (pd.notnull(r.get('medsos')) and _normalize_text(r.get('medsos')) not in {'tidak ada', '0', '0.0', 'nan', 'none', ''})
                else 0,
                axis=1
            ).astype(int)

        if ponsel_col in df_kk.columns:
            df_kk['ponsel_num'] = df_kk[ponsel_col].apply(to_binary_phone).astype(int)
        else:
            df_kk['ponsel_num'] = 0

        # Backward compatibility untuk bagian dashboard lama yang masih memakai nama digital_num.
        df_kk['digital_num'] = df_kk['internet_num']
        df_kk['organisasi_num'] = df_kk.apply(lambda r: 1 if (pd.notnull(r.get('par_organisa')) or pd.notnull(r.get('par_organisasi'))) and 
                                           str(r.get('par_organisa') if pd.notnull(r.get('par_organisa')) else r.get('par_organisasi')).lower() not in ['0','tidak','tidak ada','nan',''] else 0, axis=1)
        return df_kk
    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
        return None

def build_sna_network(
    df_v,
    basis_col,
    threshold_val=None,
    auto_threshold=True,
    lcc_only=True,
    similarity_method="cosine",
    force_louvain_lcc=False,
    threshold_grid=None,
    edge_feature_cols=None,
    onehot_round_decimals=2,
):
    if len(df_v) < 5:
        return None
    method_norm = str(similarity_method or "cosine").lower().strip()
    if method_norm not in {"cosine", "jaccard", "pearson"}:
        method_norm = "cosine"
    if threshold_grid is None:
        threshold_grid = [round(x, 1) for x in np.arange(0.1, 1.0, 0.1)]

    G = nx.Graph()
    threshold_used = 0.4
    threshold_distribution = []
    threshold_sensitivity = []
    pairwise_similarity_values = []
    if not edge_feature_cols:
        st.error("Kolom fitur edge belum ditentukan.")
        return None
    col_lookup = {str(c).lower().strip(): c for c in df_v.columns}
    resolved_feature_cols = []
    missing_cols = []
    for c in edge_feature_cols:
        key = str(c).lower().strip()
        if key in col_lookup:
            resolved_feature_cols.append(col_lookup[key])
        else:
            missing_cols.append(c)
    feature_cols = tuple(resolved_feature_cols)
    required_cols = {"family_id", *feature_cols}
    missing_cols += [c for c in required_cols if c not in df_v.columns]
    if missing_cols:
        st.error(f"Kolom fitur edge belum lengkap: {', '.join(missing_cols)}")
        return None
    df_builder = df_v.copy()
    df_builder = df_builder[df_builder["family_id"].notna()].drop_duplicates("family_id").copy()
    if len(df_builder) < 5:
        return None
    node_data = df_builder.set_index("family_id").to_dict("index")
    for nid, attr in node_data.items():
        G.add_node(nid, **attr)
    ids = list(node_data.keys())
    feature_matrix = build_onehot_feature_matrix(
        df_builder,
        feature_cols,
        rounding_decimals=onehot_round_decimals,
    ).astype(float)
    feature_vectors = {
        fid: feature_matrix.iloc[idx].to_numpy(dtype=float)
        for idx, fid in enumerate(df_builder["family_id"].tolist())
    }
    candidate_edges = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            vec_i = feature_vectors[ids[i]]
            vec_j = feature_vectors[ids[j]]
            if method_norm == "cosine":
                sim_weight = compute_cosine_similarity(vec_i, vec_j)
            elif method_norm == "jaccard":
                sim_weight = compute_jaccard_similarity(vec_i, vec_j)
            else:
                sim_weight = compute_pearson_similarity(vec_i, vec_j)
            pairwise_similarity_values.append(float(sim_weight))
            candidate_edges.append((ids[i], ids[j], float(sim_weight)))
    if auto_threshold:
        threshold_used, threshold_distribution = compute_auto_threshold_from_distribution(
            pairwise_similarity_values,
            threshold_grid=threshold_grid,
        )
        threshold_sensitivity = compute_threshold_sensitivity_analysis(
            ids,
            candidate_edges,
            threshold_grid=threshold_grid,
            lcc_only=lcc_only,
            force_louvain_lcc=force_louvain_lcc,
        )
        threshold_sensitivity = merge_threshold_distribution_with_sensitivity(
            threshold_distribution,
            threshold_sensitivity,
        )
        threshold_distribution = threshold_sensitivity
    else:
        try:
            threshold_used = float(threshold_val)
        except (TypeError, ValueError):
            threshold_used = 0.4
    for u, v, sim_weight in candidate_edges:
        if sim_weight >= threshold_used:
            G.add_edge(u, v, weight=sim_weight)

    if G.number_of_edges() == 0:
        return None
    G_lcc = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    G_target = G_lcc if lcc_only else G.copy()
    partition_graph = G_lcc if force_louvain_lcc else G_target

    partition_raw = community_louvain.best_partition(partition_graph, weight='weight', random_state=42)
    basis_for_cluster_order = resolve_basis_column(df_v, basis_col)
    if basis_for_cluster_order:
        cluster_means = {
            cid: np.mean(
                [
                    _safe_float_metric(G_target.nodes[n].get(basis_for_cluster_order), default=0.0)
                    for n, c in partition_raw.items()
                    if c == cid
                ]
            )
            for cid in set(partition_raw.values())
        }
    else:
        cluster_means = {
            cid: float(
                np.mean([G_target.degree(n, weight="weight") for n, c in partition_raw.items() if c == cid])
            )
            for cid in set(partition_raw.values())
        }
    reorder_map = {old: new for new, (old, _) in enumerate(sorted(cluster_means.items(), key=lambda x: x[1]))}
    partition = {node: reorder_map[cid] for node, cid in partition_raw.items()}
    if not lcc_only and force_louvain_lcc:
        for n in G_target.nodes():
            if n not in partition:
                partition[n] = -1
    nx.set_node_attributes(G_target, partition, 'cluster')

    meta = {
        "raw_nodes": G.number_of_nodes(),
        "raw_edges": G.number_of_edges(),
        "lcc_nodes": G_lcc.number_of_nodes(),
        "lcc_edges": G_lcc.number_of_edges(),
        "similarity_method": method_norm,
        "threshold_selected": threshold_used,
        "threshold_auto": bool(auto_threshold),
        "threshold_distribution": threshold_distribution,
        "threshold_sensitivity": threshold_sensitivity,
        "pairwise_similarity_values": pairwise_similarity_values,
        "mode": "LCC only" if lcc_only else "Semua komponen",
        "onehot_round_decimals": int(onehot_round_decimals),
    }
    return G_target, partition, sorted(list(set(reorder_map.values()))), meta


def render_journal_q1_page(
    graph_obj,
    partition,
    df_v,
    meta,
    selected_desa,
    basis_col,
    method_label,
    threshold_used,
    col_spasial=None,
):
    """Konsolidasi temuan siap-publikasi Q1 (metode + kebijakan + inklusi digital).

    Seluruh angka dihitung otomatis dari graf, klaster, assortativity, dan data KK
    yang telah diunggah. Halaman ini dinamis penuh: butuh data dan graf valid.
    """
    G = graph_obj
    st.markdown(
        f"<h1 class='main-header'>Ringkasan Temuan untuk Jurnal Q1: {selected_desa}</h1>",
        unsafe_allow_html=True,
    )

    if G is None or G.number_of_nodes() < 3 or G.number_of_edges() == 0:
        st.warning(
            "Graf terlalu kecil untuk menyusun temuan Q1. Ubah desa, basis jaringan, "
            "atau mode komponen pada sidebar agar terbentuk jaringan yang memadai."
        )
        return

    # ============================================================
    # 1. HITUNG SELURUH METRIK INTI
    # ============================================================
    node_ids = list(G.nodes())
    if "family_id" in df_v.columns:
        df_net = df_v[df_v["family_id"].astype(str).isin([str(n) for n in node_ids])].copy()
    else:
        df_net = df_v.copy()

    n_nodes = int(G.number_of_nodes())
    n_edges = int(G.number_of_edges())
    density = float(nx.density(G)) if n_nodes > 1 else 0.0
    avg_degree = float(2.0 * n_edges / n_nodes) if n_nodes else 0.0
    cluster_labels = sorted({c for c in partition.values()}) if partition else []
    n_clusters = len([c for c in cluster_labels if c != -1])
    try:
        modularity_q = _safe_float_metric(
            community_louvain.modularity(partition, G, weight="weight"), default=0.0
        )
    except Exception:
        modularity_q = 0.0
    q_dir = "kuat" if modularity_q >= 0.30 else "cukup" if modularity_q >= 0.10 else "lemah"

    # Assortativity numerik lima dimensi + agregat
    df_assort = build_ikr_assortativity_table(G)
    try:
        r_overall = float(
            df_assort.loc[df_assort["Jenis"] == "Agregat", "Assortativity r"].iloc[0]
        )
    except Exception:
        r_overall = 0.0
    dir_overall, lvl_overall = interpret_assortativity_value(r_overall)

    # Dekomposisi within-between (Montes) untuk kategori kesejahteraan BPS per klaster
    montes = compute_montes_within_between_assortativity(
        G,
        category_attr="kategori_ikr_code",
        group_attr="cluster",
        invalid_category_values={0},
    )
    q_w_star = _safe_float_metric(montes.get("q_w_star"), default=0.0)
    q_b_star = _safe_float_metric(montes.get("q_b_star"), default=0.0)

    # Homofili atribut biner (kebijakan & inklusi digital)
    r_bansos = safe_attribute_assortativity(G, "bansos_num", default=0.0)
    r_internet = safe_attribute_assortativity(G, "internet_num", default=0.0)
    r_ponsel = safe_attribute_assortativity(G, "ponsel_num", default=0.0)

    # Peran aktor strategis empat centrality (dipakai abstrak, KPI, dan Temuan Kunci 6)
    dusun_attr_journal = "dusun" if "dusun" in df_v.columns else col_spasial
    try:
        df_role_journal, centrality_name_journal, _ = prepare_centrality_policy_dataframe(
            G,
            partition,
            "degree",
            dusun_attr_journal,
            publish_mode=True,
        )
    except Exception:
        df_role_journal, centrality_name_journal = pd.DataFrame(), "Degree Centrality"
    if not df_role_journal.empty and "Peran Struktural" in df_role_journal.columns:
        role_counts_journal = df_role_journal["Peran Struktural"].value_counts()
        n_strategic = int(df_role_journal["Peran Struktural"].ne("Node umum").sum())
        pct_strategic = 100.0 * n_strategic / max(len(df_role_journal), 1)
        n_role_multi = int(role_counts_journal.get("Aktor strategis multiperan", 0))
        n_role_core = int(role_counts_journal.get("Aktor sentral berpengaruh", 0))
        n_role_broker = int(role_counts_journal.get("Broker antar-kelompok", 0))
        n_role_fast = int(role_counts_journal.get("Penyebar cepat", 0))
        strategic_txt = f"{n_strategic}"
    else:
        role_counts_journal = pd.Series(dtype=int)
        n_strategic = n_role_multi = n_role_core = n_role_broker = n_role_fast = 0
        pct_strategic = 0.0
        strategic_txt = "n/a"

    # Analisis spasial sebaran jaringan per dusun (dipakai abstrak dan Temuan Kunci 7)
    df_dusun_journal = pd.DataFrame()
    df_mix_dusun_journal = pd.DataFrame()
    intra_dusun_share = np.nan
    r_dusun = np.nan
    dissim_bansos = np.nan
    dissim_rendah = np.nan
    spatial_abstract_txt = ""
    if not df_role_journal.empty and "Dusun/Kode Dusun" in df_role_journal.columns:
        work_spasial = df_role_journal.copy()
        work_spasial["_dusun"] = work_spasial["Dusun/Kode Dusun"].fillna("Tidak tersedia").astype(str)
        if work_spasial["_dusun"].nunique() > 1:
            # Kohesi spasial: proporsi edge yang terbentuk di dalam dusun yang sama
            node_dusun_map = dict(zip(work_spasial["family_id"].astype(str), work_spasial["_dusun"]))
            same_dusun_edges = 0
            counted_edges = 0
            for edge_u, edge_v in G.edges():
                dusun_u = node_dusun_map.get(str(edge_u))
                dusun_v = node_dusun_map.get(str(edge_v))
                if dusun_u is None or dusun_v is None:
                    continue
                counted_edges += 1
                if dusun_u == dusun_v:
                    same_dusun_edges += 1
            if counted_edges > 0:
                intra_dusun_share = float(same_dusun_edges) / float(counted_edges)
            try:
                r_dusun = float(nx.attribute_assortativity_coefficient(G, dusun_attr_journal))
            except Exception:
                r_dusun = np.nan

            # Indeks disimilaritas Duncan & Duncan (1955): segregasi spasial bansos & kategori rentan
            def _duncan_dissimilarity(mask):
                grp_a = work_spasial[mask].groupby("_dusun").size()
                grp_b = work_spasial[~mask].groupby("_dusun").size()
                total_a = float(grp_a.sum())
                total_b = float(grp_b.sum())
                if total_a <= 0 or total_b <= 0:
                    return np.nan
                all_dusun = sorted(set(grp_a.index) | set(grp_b.index))
                return 0.5 * float(
                    sum(abs(grp_a.get(d, 0) / total_a - grp_b.get(d, 0) / total_b) for d in all_dusun)
                )

            mask_bansos = work_spasial["Status Bansos"].eq("Penerima")
            mask_rendah = (
                work_spasial["Status BPS"].astype(str).str.strip().str.lower().isin(["rendah", "sedang"])
            )
            dissim_bansos = _duncan_dissimilarity(mask_bansos)
            dissim_rendah = _duncan_dissimilarity(mask_rendah)

            # Profil per dusun: kesejahteraan, cakupan bansos, exclusion error, aktor strategis
            rows_dusun = []
            for dusun_name, sub_dusun in work_spasial.groupby("_dusun"):
                low_mask = sub_dusun["Status BPS"].astype(str).str.strip().str.lower().isin(["rendah", "sedang"])
                n_low = int(low_mask.sum())
                excl_dusun = (
                    float((sub_dusun.loc[low_mask, "Status Bansos"] != "Penerima").mean()) if n_low > 0 else np.nan
                )
                rerata_ikd = pd.to_numeric(sub_dusun["IKD Agregat"], errors="coerce").mean()
                rows_dusun.append(
                    {
                        "Dusun/Kode Dusun": dusun_name,
                        "Jumlah KK": int(len(sub_dusun)),
                        "Rerata IKD Agregat": float(rerata_ikd) if np.isfinite(_safe_float_metric(rerata_ikd, default=np.nan)) else np.nan,
                        "Kategori Rendah/Sedang (%)": 100.0 * float(low_mask.mean()),
                        "Penerima Bansos (%)": 100.0 * float(sub_dusun["Status Bansos"].eq("Penerima").mean()),
                        "Exclusion Error Dusun (%)": 100.0 * excl_dusun if np.isfinite(_safe_float_metric(excl_dusun, default=np.nan)) else np.nan,
                        "Aktor Strategis": int(sub_dusun["Peran Struktural"].ne("Node umum").sum()),
                        "Jumlah Klaster Hadir": int(sub_dusun["Klaster Louvain"].nunique()),
                    }
                )
            df_dusun_journal = pd.DataFrame(rows_dusun).sort_values("Jumlah KK", ascending=False).reset_index(drop=True)

            # Komposisi klaster per dusun (sebaran spasial komunitas)
            df_mix_dusun_journal = (
                work_spasial.groupby(["_dusun", "Klaster Louvain"], as_index=False)
                .size()
                .rename(columns={"size": "Jumlah KK", "_dusun": "Dusun/Kode Dusun"})
            )
            df_mix_dusun_journal["Klaster"] = df_mix_dusun_journal["Klaster Louvain"].map(lambda v: f"Klaster {int(v)}")

            if np.isfinite(_safe_float_metric(intra_dusun_share, default=np.nan)):
                spatial_abstract_txt = (
                    f"Secara spasial, <b>{intra_dusun_share:.0%}</b> edge terbentuk di dalam dusun yang sama"
                )
                if np.isfinite(_safe_float_metric(r_dusun, default=np.nan)):
                    spatial_abstract_txt += f" (assortativity dusun r=<b>{r_dusun:.3f}</b>)"
                if np.isfinite(_safe_float_metric(dissim_bansos, default=np.nan)):
                    spatial_abstract_txt += f"; indeks disimilaritas Duncan penerima bansos D=<b>{dissim_bansos:.2f}</b>"
                spatial_abstract_txt += ". "

    # Penargetan bansos: exclusion/inclusion error berbasis kategori kesejahteraan
    excl_rate = np.nan
    incl_rate = np.nan
    n_eligible = 0
    n_nonpoor = 0
    cov_df = pd.DataFrame()
    if {"kategori_ikr_code", "bansos_num"}.issubset(df_net.columns):
        d_err = df_net[df_net["kategori_ikr_code"].isin([1, 2, 3, 4])].copy()
        d_err["bansos_num"] = pd.to_numeric(d_err["bansos_num"], errors="coerce").fillna(0).astype(int)
        eligible = d_err[d_err["kategori_ikr_code"] <= 2]        # Rendah + Sedang = layak prioritas
        nonpoor = d_err[d_err["kategori_ikr_code"] >= 3]          # Tinggi + Sangat Tinggi = relatif mampu
        n_eligible = int(len(eligible))
        n_nonpoor = int(len(nonpoor))
        if n_eligible > 0:
            excl_rate = float((eligible["bansos_num"] == 0).mean())
        if n_nonpoor > 0:
            incl_rate = float((nonpoor["bansos_num"] == 1).mean())
        # Tabel cakupan bansos per kategori
        order_labels = ["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"]
        code_by_label = {"Rendah": 1, "Sedang": 2, "Tinggi": 3, "Sangat Tinggi": 4}
        rows_cov = []
        for lbl in order_labels:
            sub = d_err[d_err["kategori_ikr_code"] == code_by_label[lbl]]
            if len(sub) == 0:
                continue
            penerima = int((sub["bansos_num"] == 1).sum())
            total = int(len(sub))
            rows_cov.append(
                {
                    "Kategori Kesejahteraan": lbl,
                    "Jumlah KK": total,
                    "Penerima Bansos": penerima,
                    "Cakupan (%)": round(100.0 * penerima / total, 1) if total else 0.0,
                }
            )
        cov_df = pd.DataFrame(rows_cov)

    # ============================================================
    # 2. ABSTRAK TERSTRUKTUR (OTOMATIS)
    # ============================================================
    excl_txt = f"{excl_rate:.0%}" if np.isfinite(excl_rate) else "n/a"
    incl_txt = f"{incl_rate:.0%}" if np.isfinite(incl_rate) else "n/a"
    st.markdown(
        "<div class='premium-hero'>"
        "<b>Abstrak terstruktur (dihitung otomatis dari data).</b><br>"
        f"<b>Konteks.</b> Studi mengonstruksi jaringan kemiripan antar-rumah tangga dari lima dimensi "
        f"Indeks Kesejahteraan Desa (IKD) pada Data Desa Presisi di Desa <b>{selected_desa}</b>. "
        f"<b>Metode.</b> Basis <b>{basis_col}</b>, pembobotan <b>{method_label}</b>, ambang kemiripan "
        f"<b>{threshold_used:.2f}</b>; komunitas dideteksi dengan Louvain; homofili diukur via koefisien "
        f"assortativity dan dekomposisi within-between (Montes et al., 2018). "
        f"<b>Hasil.</b> Terbentuk jaringan <b>{n_nodes}</b> node dan <b>{n_edges}</b> edge dengan "
        f"<b>{n_clusters}</b> komunitas (modularitas Q=<b>{modularity_q:.3f}</b>, {q_dir}). Homofili "
        f"kesejahteraan agregat r=<b>{r_overall:.3f}</b> ({dir_overall.lower()}); dekomposisi Montes "
        f"Qw*=<b>{q_w_star:.3f}</b> (intra-klaster) dan Qb*=<b>{q_b_star:.3f}</b> (antar-klaster). "
        f"Audit penargetan bansos menemukan <i>exclusion error</i> <b>{excl_txt}</b> dan "
        f"<i>inclusion error</i> <b>{incl_txt}</b>. "
        f"Pemetaan peran empat centrality (degree, betweenness, closeness, eigenvector; ambang kuartil Q75) "
        f"menandai <b>{strategic_txt}</b> aktor strategis ({pct_strategic:.1f}% node), terdiri atas "
        f"<b>{n_role_multi}</b> aktor multiperan, <b>{n_role_core}</b> aktor sentral berpengaruh, dan "
        f"<b>{n_role_broker}</b> broker antar-kelompok. "
        f"{spatial_abstract_txt}"
        f"<b>Implikasi.</b> Struktur relasional desa memberi lapisan bukti baru untuk memperbaiki "
        f"akurasi penargetan bantuan sosial, pemerataan inklusi digital, serta pemilihan aktor strategis "
        f"sebagai agen difusi program."
        "</div>",
        unsafe_allow_html=True,
    )

    # KPI utama
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Node (KK)", n_nodes)
    k2.metric("Komunitas Louvain", n_clusters, help="Jumlah kelompok padat hasil deteksi Louvain.")
    k3.metric("Modularitas Q", f"{modularity_q:.3f}", help="Semakin tinggi, struktur komunitas makin tegas.")
    k4.metric("Exclusion Error", excl_txt, help="KK layak (kategori Rendah/Sedang) yang tidak menerima bansos.")
    k5.metric("Inclusion Error", incl_txt, help="KK relatif mampu (Tinggi/Sangat Tinggi) yang menerima bansos.")
    k6.metric("Aktor Strategis", strategic_txt, help="Node dengan peran strategis dari empat metrik centrality (ambang kuartil Q75).")

    # ============================================================
    # 3. NOVELTY & GAP
    # ============================================================
    with subbab_dropdown("1. Kebaruan (Novelty) dan Celah Penelitian", expanded=True):
        st.markdown(
            "<b>Celah.</b> Penargetan bantuan sosial dan pengukuran inklusi digital desa umumnya berbasis "
            "atribut individual (proxy means test), sehingga <i>mengabaikan struktur relasional</i> antar "
            "rumah tangga yang membentuk pola homofili dan segregasi sosial-ekonomi.<br><br>"
            "<b>Kebaruan yang ditawarkan studi ini:</b>"
            "<ul>"
            "<li><b>Metodologis-1:</b> jaringan kemiripan Data Desa Presisi multi-metrik (Cosine/Jaccard/Pearson) "
            "dengan <i>penentuan ambang otomatis dan uji sensitivitas</i> — memberi reprodusibilitas yang jarang "
            "dilaporkan pada studi SNA kebijakan desa.</li>"
            "<li><b>Metodologis-2:</b> penerapan <i>dekomposisi assortativity within-between</i> (Montes et al., 2018) "
            "untuk mengukur segregasi kategori kesejahteraan di dalam vs antar-komunitas — belum lazim pada domain "
            "kebijakan sosial.</li>"
            "<li><b>Empiris/Kebijakan:</b> kuantifikasi <i>exclusion &amp; inclusion error</i> penargetan bansos "
            "berbasis komunitas jaringan, bukan sekadar agregat administratif.</li>"
            "<li><b>Inklusi digital:</b> pengukuran homofili akses internet/ponsel sebagai indikator "
            "<i>kesenjangan digital</i> yang terstruktur secara relasional.</li>"
            "</ul>",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 4. METODOLOGI RINGKAS (REPRODUCIBLE)
    # ============================================================
    with subbab_dropdown("2. Kerangka Metodologi Ringkas (untuk bagian Methods)", expanded=False):
        method_rows = [
            {"Komponen": "Unit analisis", "Spesifikasi": "Kepala keluarga (KK) pada Data Desa Presisi"},
            {"Komponen": "Basis fitur jaringan", "Spesifikasi": f"{basis_col} + lima dimensi IKD (one-hot)"},
            {"Komponen": "Metrik kemiripan (pembobotan edge)", "Spesifikasi": method_label},
            {"Komponen": "Ambang kemiripan (threshold)", "Spesifikasi": f"{threshold_used:.2f} (otomatis dari distribusi)"},
            {"Komponen": "Deteksi komunitas", "Spesifikasi": "Louvain (bobot edge, random_state=42)"},
            {"Komponen": "Ukuran homofili", "Spesifikasi": "Assortativity numerik/atribut + within-between Montes (Qw*, Qb*)"},
            {"Komponen": "Sentralitas", "Spesifikasi": "Degree, Betweenness, Closeness, Eigenvector + klasifikasi peran aktor strategis (ambang kuartil Q75)"},
            {"Komponen": "Etika data", "Spesifikasi": "Anonimisasi node; hasil agregat; tidak menunjuk individu"},
        ]
        st.dataframe(pd.DataFrame(method_rows), use_container_width=True, hide_index=True)
        st.caption(
            f"Konfigurasi aktual run ini — Node: {n_nodes}, Edge: {n_edges}, Densitas: {density:.3f}, "
            f"Derajat rata-rata: {avg_degree:.2f}. Nilai bersifat reprodusibel untuk seed dan parameter yang sama."
        )

    # ============================================================
    # 5. TEMUAN 1 — STRUKTUR JARINGAN & KOMUNITAS
    # ============================================================
    with subbab_dropdown("3. Temuan Kunci 1 — Struktur Jaringan dan Komunitas", expanded=False):
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Edge", n_edges)
        s2.metric("Densitas", f"{density:.3f}")
        s3.metric("Derajat rata-rata", f"{avg_degree:.2f}")
        s4.metric("Modularitas Q", f"{modularity_q:.3f}")
        # Ukuran tiap komunitas
        size_rows = []
        for c in cluster_labels:
            if c == -1:
                continue
            size_rows.append({"Komunitas": f"Klaster {c}", "Jumlah KK": sum(1 for v in partition.values() if v == c)})
        if size_rows:
            df_size = pd.DataFrame(size_rows)
            fig_size = px.bar(df_size, x="Komunitas", y="Jumlah KK", text="Jumlah KK", color="Komunitas")
            style_publication_figure(
                fig_size, title="Distribusi Ukuran Komunitas Louvain", height=380,
                xaxis_title="Komunitas", yaxis_title="Jumlah KK", showlegend=False,
            )
            st.plotly_chart(fig_size, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.markdown(
            f"Jaringan membentuk <b>{n_clusters}</b> komunitas dengan modularitas <b>{modularity_q:.3f}</b> "
            f"(struktur komunitas <b>{q_dir}</b>). Nilai ini menandakan bahwa kemiripan kesejahteraan antar-KK "
            "tidak acak, melainkan mengelompok — dasar bagi analisis segregasi dan penargetan berbasis kelompok.",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 6. TEMUAN 2 — HOMOFILI KESEJAHTERAAN (ASSORTATIVITY)
    # ============================================================
    with subbab_dropdown("4. Temuan Kunci 2 — Homofili Kesejahteraan (Assortativity per Dimensi)", expanded=False):
        if not df_assort.empty:
            df_show = df_assort[["Dimensi IKD", "Assortativity r", "Arah", "Kekuatan"]].copy()
            fig_assort = px.bar(
                df_assort.sort_values("Assortativity r"),
                x="Assortativity r", y="Dimensi IKD", orientation="h",
                color="Assortativity r", color_continuous_scale="RdBu", range_color=[-0.6, 0.6],
                text=df_assort.sort_values("Assortativity r")["Assortativity r"].round(3),
            )
            style_publication_figure(
                fig_assort, title="Koefisien Assortativity per Dimensi Kesejahteraan", height=430,
                xaxis_title="Assortativity r (+ homofili / - heterofili)", yaxis_title="",
            )
            st.plotly_chart(fig_assort, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        st.markdown(
            f"Homofili agregat r=<b>{r_overall:.3f}</b> ({dir_overall}, {lvl_overall}). Nilai positif berarti "
            "KK cenderung terhubung dengan KK berkesejahteraan serupa (<i>indikasi segregasi ekonomi</i>); "
            "nilai negatif berarti pola lintas-strata.",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 7. TEMUAN 3 — DEKOMPOSISI WITHIN-BETWEEN (MONTES) [NOVELTY]
    # ============================================================
    with subbab_dropdown("5. Temuan Kunci 3 — Dekomposisi Within-Between Montes (Kontribusi Metodologis)", expanded=False):
        m1, m2, m3 = st.columns(3)
        m1.metric("Qw* (intra-klaster)", f"{q_w_star:.3f}", help="Homogenitas kategori kesejahteraan DI DALAM komunitas.")
        m2.metric("Qb* (antar-klaster)", f"{q_b_star:.3f}", help="Homogenitas kategori kesejahteraan ANTAR komunitas.")
        m3.metric("Steinley (intra)", steinley_segregation_label(q_w_star))
        fig_m = px.bar(
            pd.DataFrame({"Komponen": ["Qw* (intra)", "Qb* (antar)"], "Nilai": [q_w_star, q_b_star]}),
            x="Komponen", y="Nilai", text="Nilai", color="Komponen",
        )
        fig_m.update_traces(texttemplate="%{text:.3f}")
        style_publication_figure(
            fig_m, title="Dekomposisi Assortativity Within-Between (Montes)", height=360,
            xaxis_title="", yaxis_title="Q*", showlegend=False,
        )
        st.plotly_chart(fig_m, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.markdown(
            f"Qw*=<b>{q_w_star:.3f}</b> menunjukkan kategori kesejahteraan {interpret_q_strength(q_w_star)} homogen "
            f"di dalam komunitas, sedangkan Qb*=<b>{q_b_star:.3f}</b> menggambarkan pola antar-komunitas. "
            "Kesenjangan Qw* &gt; Qb* memperkuat interpretasi bahwa <i>segregasi kesejahteraan terjadi terutama "
            "di dalam sekat komunitas</i> — temuan yang sulit ditangkap oleh indeks assortativity tunggal.",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 8. TEMUAN 4 — TARGETING ERROR BANSOS (EMPIRIS/KEBIJAKAN)
    # ============================================================
    with subbab_dropdown("6. Temuan Kunci 4 — Akurasi Penargetan Bansos (Exclusion/Inclusion Error)", expanded=False):
        e1, e2, e3 = st.columns(3)
        e1.metric("Exclusion Error", excl_txt, help=f"Dari {n_eligible} KK kategori Rendah/Sedang.")
        e2.metric("Inclusion Error", incl_txt, help=f"Dari {n_nonpoor} KK kategori Tinggi/Sangat Tinggi.")
        e3.metric("Homofili status bansos (r)", f"{r_bansos:.3f}", help="Positif = penerima cenderung mengelompok.")
        if not cov_df.empty:
            fig_cov = px.bar(
                cov_df, x="Kategori Kesejahteraan", y="Cakupan (%)", text="Cakupan (%)",
                color="Cakupan (%)", color_continuous_scale="Blues",
            )
            style_publication_figure(
                fig_cov, title="Cakupan Bansos menurut Kategori Kesejahteraan", height=380,
                xaxis_title="Kategori Kesejahteraan (BPS)", yaxis_title="Cakupan Bansos (%)",
            )
            st.plotly_chart(fig_cov, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            st.dataframe(cov_df, use_container_width=True, hide_index=True)
        st.markdown(
            f"<i>Exclusion error</i> <b>{excl_txt}</b>: KK layak prioritas (Rendah/Sedang) yang belum menerima "
            f"bansos. <i>Inclusion error</i> <b>{incl_txt}</b>: KK relatif mampu (Tinggi/Sangat Tinggi) yang justru "
            "menerima. Homofili status penerima (r=" f"{r_bansos:.3f}) mengindikasikan apakah bantuan menyebar "
            "mengikuti sekat sosial. Hasil ini merupakan indikasi awal untuk verifikasi lapangan, bukan penetapan "
            "individu sasaran.",
            unsafe_allow_html=True,
        )

    # ============================================================
    # 9. TEMUAN 5 — INKLUSI DIGITAL & AKTOR STRATEGIS
    # ============================================================
    with subbab_dropdown("7. Temuan Kunci 5 — Inklusi Digital dan Aktor Strategis Difusi", expanded=False):
        d1, d2 = st.columns(2)
        d1.metric("Homofili akses internet (r)", f"{r_internet:.3f}")
        d2.metric("Homofili kepemilikan ponsel (r)", f"{r_ponsel:.3f}")
        st.caption(
            "Homofili digital positif menandakan akses internet/ponsel terdistribusi secara berkelompok "
            "(kesenjangan digital terstruktur); mendekati nol menandakan akses relatif menyebar lintas kelompok."
        )
        # Aktor strategis (anonim) berdasarkan degree & betweenness
        deg_vals = compute_centrality_on_similarity_graph(G, "degree")
        bet_vals = compute_centrality_on_similarity_graph(G, "betweenness")
        anon_map = make_anonymized_node_mapping(node_ids)
        actor_rows = []
        for n in node_ids:
            actor_rows.append(
                {
                    "Kode Node": anon_map.get(str(n), "N-000"),
                    "Klaster": partition.get(n, -1),
                    "Degree": round(float(deg_vals.get(n, 0.0)), 4),
                    "Betweenness": round(float(bet_vals.get(n, 0.0)), 4),
                    "Kategori IKD": G.nodes[n].get("kategori_ikr", "-"),
                    "Bansos": "YA" if int(_safe_float_metric(G.nodes[n].get("bansos_num"), 0)) == 1 else "TIDAK",
                }
            )
        df_actor = pd.DataFrame(actor_rows).sort_values("Betweenness", ascending=False).head(8)
        st.markdown("<b>Delapan aktor paling strategis</b> (jembatan antar-kelompok, kandidat agen difusi kebijakan):", unsafe_allow_html=True)
        st.dataframe(df_actor, use_container_width=True, hide_index=True)
        st.caption(
            "Aktor dengan betweenness tinggi menghubungkan komunitas berbeda — titik ungkit efisien untuk "
            "sosialisasi program, verifikasi data, atau intervensi inklusi digital. Identitas disamarkan (etika data). "
            "Pemetaan peran aktor strategis selengkapnya (empat centrality) disajikan pada Temuan Kunci 6."
        )

    # ============================================================
    # 10. TEMUAN 6 — PERAN AKTOR STRATEGIS EMPAT CENTRALITY
    # ============================================================
    with subbab_dropdown("8. Temuan Kunci 6 — Peran Aktor Strategis Empat Centrality", expanded=False):
        if df_role_journal.empty or "Peran Struktural" not in df_role_journal.columns:
            st.info(
                "Peran aktor strategis belum dapat dihitung untuk graf saat ini. "
                "Pastikan jaringan memiliki node dan edge yang memadai."
            )
        else:
            st.markdown(
                "Analisis ini mengklasifikasikan setiap KK berdasarkan posisi strukturalnya pada empat metrik "
                "centrality (degree, betweenness, closeness, eigenvector). Node yang berada pada kuartil atas "
                "(&ge;Q75) satu metrik atau lebih ditandai sebagai <b>aktor strategis</b> dengan peran berbeda: "
                "multiperan, sentral berpengaruh, broker antar-kelompok, penyebar cepat, hub lokal aktif, "
                "atau dekat inti jaringan. Pemetaan ini melengkapi temuan difusi (Temuan Kunci 5) dan menjadi "
                "basis pemilihan agen sosialisasi/verifikasi program.",
                unsafe_allow_html=True,
            )
            ar1, ar2, ar3, ar4 = st.columns(4)
            ar1.metric(
                "Aktor Strategis",
                f"{n_strategic}",
                help=f"{pct_strategic:.1f}% dari {len(df_role_journal)} node; semua peran selain 'Node umum'.",
            )
            ar2.metric("Multiperan", f"{n_role_multi}", help=">=3 metrik centrality pada kuartil atas (Q75).")
            ar3.metric("Broker Antar-Kelompok", f"{n_role_broker}", help="Betweenness Q75 — jembatan antarbagian jaringan.")
            ar4.metric("Penyebar Cepat", f"{n_role_fast}", help="Closeness Q75 — jangkauan cepat ke banyak node.")

            # Distribusi peran aktor
            role_dist_journal = (
                df_role_journal.groupby("Peran Struktural", as_index=False)
                .size()
                .rename(columns={"size": "Jumlah Node"})
            )
            role_dist_journal["Basis Metrik"] = role_dist_journal["Peran Struktural"].map(centrality_role_metric_basis)
            role_dist_journal["Persentase (%)"] = (
                role_dist_journal["Jumlah Node"] / max(len(df_role_journal), 1)
            ) * 100.0
            role_order_rank = {role: idx for idx, role in enumerate(CENTRALITY_ROLE_ORDER)}
            role_dist_journal["_order"] = role_dist_journal["Peran Struktural"].map(role_order_rank).fillna(len(role_order_rank))
            role_dist_journal = role_dist_journal.sort_values("_order").drop(columns="_order").reset_index(drop=True)
            fig_role_dist = px.bar(
                role_dist_journal.iloc[::-1],
                x="Jumlah Node",
                y="Peran Struktural",
                orientation="h",
                color="Peran Struktural",
                color_discrete_map=CENTRALITY_ROLE_COLORS,
                text=role_dist_journal.iloc[::-1]["Persentase (%)"].map(lambda v: f"{v:.1f}%"),
                custom_data=["Basis Metrik"],
            )
            fig_role_dist.update_traces(
                textposition="outside",
                cliponaxis=False,
                hovertemplate="Peran: %{y}<br>Basis metrik: %{customdata[0]}<br>Jumlah node: %{x}<extra></extra>",
            )
            style_publication_figure(
                fig_role_dist,
                title="Distribusi Peran Aktor Empat Centrality",
                height=max(380, 60 * len(role_dist_journal) + 140),
                xaxis_title="Jumlah node",
                yaxis_title="",
                showlegend=False,
            )
            st.plotly_chart(fig_role_dist, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            st.dataframe(
                role_dist_journal.style.format({"Persentase (%)": "{:.1f}"}),
                use_container_width=True,
            )
            st.info(build_centrality_policy_narrative(df_role_journal, centrality_name_journal))

            # Peta empat centrality dan matriks degree-eigenvector (reuse halaman Analisis Centrality)
            st.markdown("<b>Peta Aktor Strategis Empat Centrality</b>", unsafe_allow_html=True)
            render_strategic_actor_centrality_map(df_role_journal)
            st.markdown("<b>Matriks Degree-Eigenvector Aktor Strategis</b>", unsafe_allow_html=True)
            render_degree_eigenvector_role_matrix(df_role_journal)

            # Profil aktor strategis teratas (anonim, siap lampiran jurnal)
            st.markdown("<b>Profil Aktor Strategis Teratas (anonim)</b>", unsafe_allow_html=True)
            df_actor_journal = df_role_journal[df_role_journal["Peran Struktural"].ne("Node umum")].copy()
            df_actor_journal["_role_rank"] = df_actor_journal["Peran Struktural"].map(role_order_rank).fillna(len(role_order_rank))
            df_actor_journal = (
                df_actor_journal.sort_values(["_role_rank", "Degree Centrality"], ascending=[True, False])
                .head(12)
                .drop(columns="_role_rank")
            )
            actor_profile_cols = unique_existing_columns(
                df_actor_journal,
                [
                    "Kode Node",
                    "Klaster Louvain",
                    "Dusun/Kode Dusun",
                    "Degree Centrality",
                    "Betweenness Centrality",
                    "Closeness Centrality",
                    "Eigenvector Centrality",
                    "Jumlah Metrik Tinggi",
                    "Sinyal Centrality",
                    "Peran Aktor",
                    "Status BPS",
                    "Status Bansos",
                    "Implikasi Program",
                ],
            )
            st.dataframe(
                df_actor_journal[actor_profile_cols].style.format(
                    {
                        "Degree Centrality": "{:.6f}",
                        "Betweenness Centrality": "{:.6f}",
                        "Closeness Centrality": "{:.6f}",
                        "Eigenvector Centrality": "{:.6f}",
                    }
                ),
                use_container_width=True,
            )
            st.download_button(
                "Unduh Profil Aktor Strategis (Anonim)",
                data=df_actor_journal[actor_profile_cols].to_csv(index=False).encode("utf-8"),
                file_name="profil_aktor_strategis_jurnal.csv",
                mime="text/csv",
                key="journal_actor_profile_download",
            )

            # Keterkaitan peran aktor dengan kesejahteraan (IKD) dan bansos
            st.markdown("<b>Keterkaitan Peran Aktor dengan Kesejahteraan (IKD) dan Bansos</b>", unsafe_allow_html=True)
            link_rows = []
            for role in CENTRALITY_ROLE_ORDER:
                sub_role = df_role_journal[df_role_journal["Peran Struktural"] == role]
                if sub_role.empty:
                    continue
                ikd_mean = pd.to_numeric(sub_role.get("IKD Agregat"), errors="coerce").mean()
                status_bps = sub_role.get("Status BPS", pd.Series(dtype=str)).astype(str).str.strip().str.lower()
                link_rows.append(
                    {
                        "Peran Aktor": role,
                        "Basis Metrik": centrality_role_metric_basis(role),
                        "Jumlah Node": int(len(sub_role)),
                        "Rerata IKD Agregat": float(ikd_mean) if np.isfinite(_safe_float_metric(ikd_mean, default=np.nan)) else np.nan,
                        "Kategori Rendah/Sedang (%)": 100.0 * float(status_bps.isin(["rendah", "sedang"]).mean()),
                        "Penerima Bansos (%)": 100.0 * float(sub_role.get("Status Bansos", pd.Series(dtype=str)).eq("Penerima").mean()),
                    }
                )
            df_role_link = pd.DataFrame(link_rows)
            if not df_role_link.empty:
                st.dataframe(
                    df_role_link.style.format(
                        {
                            "Rerata IKD Agregat": "{:.2f}",
                            "Kategori Rendah/Sedang (%)": "{:.1f}",
                            "Penerima Bansos (%)": "{:.1f}",
                        }
                    ),
                    use_container_width=True,
                )
                st.caption(
                    "Tabel ini menjawab pertanyaan kebijakan: apakah aktor strategis berasal dari KK sejahtera atau "
                    "rentan, dan seberapa besar mereka sudah tersentuh bansos. Aktor strategis dari kategori "
                    "Rendah/Sedang yang belum menerima bansos adalah kandidat verifikasi prioritas sekaligus "
                    "agen difusi yang dekat dengan kelompok sasaran."
                )

            # Komposisi peran per klaster & dusun + kuartil (legenda dirender inline
            # karena subbab ini sudah berupa expander — expander tidak boleh bersarang)
            st.markdown("<b>Komposisi Aktor Strategis per Klaster dan Dusun</b>", unsafe_allow_html=True)
            render_role_composition_charts(df_role_journal, publish_mode=True, include_legend=False)
            st.markdown("<b>Keterangan Peran Aktor</b>", unsafe_allow_html=True)
            st.dataframe(build_centrality_role_legend_df(), use_container_width=True, hide_index=True)

            # Dasar metodologis ambang kuartil (justifikasi untuk reviewer Q1)
            st.markdown(
                "<b>Dasar metodologis pembagian peran dengan ambang kuartil (&ge;Q75).</b>"
                "<ul>"
                "<li><b>Robust terhadap distribusi condong.</b> Distribusi metrik centrality pada jaringan sosial "
                "umumnya sangat condong (<i>heavy-tailed</i>): sedikit node bernilai sangat tinggi, mayoritas rendah. "
                "Ambang berbasis kuartil (kuartil atas, &ge;Q75) adalah pemisah nonparametrik yang tahan pencilan, "
                "mengikuti konvensi eksplorasi data Tukey (1977) — berbeda dari ambang absolut yang arbitrer.</li>"
                "<li><b>Relatif terhadap jaringan yang diamati.</b> Nilai centrality tidak dapat dibandingkan lintas "
                "jaringan berbeda ukuran/densitas; ambang kuartil menstandardisasi 'tinggi' sebagai posisi relatif "
                "dalam jaringan itu sendiri, sejalan dengan temuan stabilitas ukuran centrality "
                "(Costenbader &amp; Valente, 2003).</li>"
                "<li><b>Tradisi identifikasi aktor kunci.</b> Kerangka konseptual empat centrality merujuk Freeman "
                "(1979); pemetaan aktor kunci untuk intervensi merujuk <i>key player problem</i> (Borgatti, 2006) "
                "dan praktik pemilihan <i>opinion leader</i> difusi program (Valente &amp; Pumpuang, 2007; "
                "Valente, 2012 — <i>network interventions</i>).</li>"
                "<li><b>Taksonomi peran multi-metrik.</b> Penggabungan beberapa sinyal centrality menjadi peran "
                "(multiperan, broker, penyebar cepat, hub, dekat inti) analog dengan kartografi peran node berbasis "
                "ambang statistik pada Guimer&agrave; &amp; Amaral (2005): node diklasifikasikan menurut posisinya "
                "terhadap distribusi metrik, bukan nilai mentahnya.</li>"
                "<li><b>Pengaman teknis.</b> Label 'tinggi' hanya diberikan bila metrik memiliki sebaran "
                "(max &gt; min); jaringan dengan metrik konstan tidak menghasilkan aktor strategis palsu.</li>"
                "</ul>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Seluruh identitas disamarkan (Kode Node dan Kode Dusun). Peran aktor hanya membaca posisi jaringan "
                "dari empat metrik centrality; bukan status sosial, tingkat kesejahteraan, atau kelayakan bantuan — "
                "hasil dipakai sebagai indikasi awal pemetaan agen difusi dan wajib diverifikasi lapangan."
            )

    # ============================================================
    # 11. TEMUAN 7 — ANALISIS SPASIAL SEBARAN JARINGAN PER DUSUN
    # ============================================================
    with subbab_dropdown("9. Temuan Kunci 7 — Analisis Spasial: Sebaran Jaringan, Kesejahteraan, dan Bansos per Dusun", expanded=False):
        if df_dusun_journal.empty:
            st.info(
                "Analisis spasial per dusun belum dapat disusun — data dusun tidak tersedia atau hanya ada satu "
                "dusun pada jaringan aktif."
            )
        else:
            st.markdown(
                "Analisis ini membaca dimensi <b>spasial</b> jaringan pada level dusun (unit administratif): "
                "seberapa besar relasi kemiripan kesejahteraan terkurung di dalam dusun, bagaimana komunitas "
                "Louvain tersebar antar-dusun, di dusun mana KK rentan dan <i>exclusion error</i> terkonsentrasi, "
                "serta di mana aktor strategis berada. Segregasi spasial diukur dengan proporsi edge intra-dusun, "
                "assortativity atribut dusun (Newman, 2003), dan indeks disimilaritas Duncan &amp; Duncan (1955).",
                unsafe_allow_html=True,
            )
            sp1, sp2, sp3, sp4 = st.columns(4)
            intra_txt = f"{intra_dusun_share:.0%}" if np.isfinite(_safe_float_metric(intra_dusun_share, default=np.nan)) else "n/a"
            r_dusun_txt = f"{r_dusun:.3f}" if np.isfinite(_safe_float_metric(r_dusun, default=np.nan)) else "n/a"
            d_bansos_txt = f"{dissim_bansos:.2f}" if np.isfinite(_safe_float_metric(dissim_bansos, default=np.nan)) else "n/a"
            d_rendah_txt = f"{dissim_rendah:.2f}" if np.isfinite(_safe_float_metric(dissim_rendah, default=np.nan)) else "n/a"
            sp1.metric("Edge Intra-Dusun", intra_txt, help="Proporsi edge kemiripan yang menghubungkan dua KK dalam dusun yang sama.")
            sp2.metric("Assortativity Dusun (r)", r_dusun_txt, help="Newman (2003): positif = relasi cenderung terkurung dalam dusun (segregasi spasial).")
            sp3.metric("Duncan D — Bansos", d_bansos_txt, help="Duncan & Duncan (1955): 0 = penerima bansos tersebar merata antar dusun, 1 = terpisah total.")
            sp4.metric("Duncan D — KK Rentan", d_rendah_txt, help="Segregasi spasial KK kategori Rendah/Sedang antar dusun.")

            # Sebaran komunitas Louvain antar dusun
            if not df_mix_dusun_journal.empty:
                fig_mix_dusun = px.bar(
                    df_mix_dusun_journal,
                    x="Dusun/Kode Dusun",
                    y="Jumlah KK",
                    color="Klaster",
                    barmode="stack",
                    text="Jumlah KK",
                )
                fig_mix_dusun.update_traces(textposition="inside", insidetextanchor="middle", cliponaxis=False)
                style_publication_figure(
                    fig_mix_dusun,
                    title="Sebaran Spasial Komunitas Louvain per Dusun",
                    height=max(420, 340 + 14 * df_mix_dusun_journal["Dusun/Kode Dusun"].nunique()),
                    xaxis_title="Dusun/Kode Dusun",
                    yaxis_title="Jumlah KK",
                    legend_title="Komunitas",
                )
                st.plotly_chart(fig_mix_dusun, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

            # Exclusion error per dusun (prioritas kewilayahan)
            df_excl_dusun = df_dusun_journal.dropna(subset=["Exclusion Error Dusun (%)"]).copy()
            if not df_excl_dusun.empty:
                fig_excl_dusun = px.bar(
                    df_excl_dusun.sort_values("Exclusion Error Dusun (%)", ascending=True),
                    x="Exclusion Error Dusun (%)",
                    y="Dusun/Kode Dusun",
                    orientation="h",
                    color="Exclusion Error Dusun (%)",
                    color_continuous_scale="Reds",
                    text=df_excl_dusun.sort_values("Exclusion Error Dusun (%)", ascending=True)["Exclusion Error Dusun (%)"].map(lambda v: f"{v:.0f}%"),
                )
                fig_excl_dusun.update_traces(textposition="outside", cliponaxis=False)
                style_publication_figure(
                    fig_excl_dusun,
                    title="Exclusion Error Bansos per Dusun (KK Rendah/Sedang yang Belum Menerima)",
                    height=max(380, 130 + 34 * len(df_excl_dusun)),
                    xaxis_title="Exclusion error (%)",
                    yaxis_title="",
                    showlegend=False,
                )
                st.plotly_chart(fig_excl_dusun, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

            # Tabel profil spasial per dusun
            st.markdown("<b>Profil Spasial per Dusun</b>", unsafe_allow_html=True)
            st.dataframe(
                df_dusun_journal.style.format(
                    {
                        "Rerata IKD Agregat": "{:.2f}",
                        "Kategori Rendah/Sedang (%)": "{:.1f}",
                        "Penerima Bansos (%)": "{:.1f}",
                        "Exclusion Error Dusun (%)": "{:.1f}",
                    }
                ).background_gradient(cmap="Reds", subset=["Exclusion Error Dusun (%)"]),
                use_container_width=True,
            )
            st.download_button(
                "Unduh Profil Spasial per Dusun (Anonim)",
                data=df_dusun_journal.to_csv(index=False).encode("utf-8"),
                file_name="profil_spasial_dusun_jurnal.csv",
                mime="text/csv",
                key="journal_spatial_dusun_download",
            )

            # Narasi spasial otomatis
            spatial_sentences = []
            if np.isfinite(_safe_float_metric(intra_dusun_share, default=np.nan)):
                arah_spasial = "terkurung di dalam dusun" if intra_dusun_share >= 0.5 else "banyak menembus batas dusun"
                spatial_sentences.append(
                    f"Sebanyak {intra_dusun_share:.0%} edge kemiripan berada di dalam dusun yang sama, "
                    f"sehingga struktur kesejahteraan relasional cenderung {arah_spasial}."
                )
            if not df_excl_dusun.empty:
                worst_dusun = df_excl_dusun.sort_values("Exclusion Error Dusun (%)", ascending=False).iloc[0]
                spatial_sentences.append(
                    f"Exclusion error tertinggi berada di {worst_dusun['Dusun/Kode Dusun']} "
                    f"({worst_dusun['Exclusion Error Dusun (%)']:.0f}% dari KK rentannya belum menerima bansos)."
                )
            top_actor_dusun = df_dusun_journal.sort_values("Aktor Strategis", ascending=False).iloc[0]
            spatial_sentences.append(
                f"Aktor strategis terbanyak berada di {top_actor_dusun['Dusun/Kode Dusun']} "
                f"({int(top_actor_dusun['Aktor Strategis'])} aktor) — kandidat titik masuk difusi program berbasis wilayah."
            )
            st.info(" ".join(spatial_sentences))
            st.caption(
                "Kode dusun dianonimkan untuk publikasi. Analisis level dusun bersifat agregat administratif — "
                "bukan koordinat presisi — sehingga aman etika data namun tetap informatif untuk prioritas kewilayahan."
            )

    # ============================================================
    # 12. ROBUSTNESS / SENSITIVITY (RIGOR METODOLOGIS)
    # ============================================================
    with subbab_dropdown("10. Robustness — Sensitivitas Threshold (untuk menjawab reviewer)", expanded=False):
        sens = meta.get("threshold_sensitivity") or meta.get("threshold_distribution") or []
        df_sens = pd.DataFrame(sens)
        if not df_sens.empty and "threshold" in df_sens.columns:
            df_sens = df_sens.sort_values("threshold")
            y_cols = [c for c in ["jumlah_cluster", "modularity"] if c in df_sens.columns]
            if y_cols:
                fig_sens = px.line(
                    df_sens, x="threshold", y=y_cols, markers=True,
                )
                fig_sens.add_vline(
                    x=float(threshold_used), line_width=2, line_dash="dash", line_color="#B91C1C",
                    annotation_text=f"Threshold terpilih {threshold_used:.2f}",
                )
                style_publication_figure(
                    fig_sens, title="Sensitivitas Jumlah Klaster & Modularitas terhadap Threshold", height=400,
                    xaxis_title="Threshold kemiripan", yaxis_title="Nilai", showlegend=True, legend_title="Metrik",
                )
                st.plotly_chart(fig_sens, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            show_cols = [c for c in ["threshold", "edge_count", "node_lcc", "jumlah_cluster", "modularity", "density_analisis"] if c in df_sens.columns]
            st.dataframe(df_sens[show_cols], use_container_width=True, hide_index=True)
            st.caption(
                "Struktur komunitas yang stabil pada rentang threshold di sekitar ambang terpilih menunjukkan "
                "temuan tidak artefak dari satu nilai ambang — argumen robustness yang diminta reviewer Q1."
            )
        else:
            st.info("Data sensitivitas threshold belum tersedia untuk run ini (aktifkan mode threshold otomatis).")

    # ============================================================
    # 13. IMPLIKASI KEBIJAKAN & POSITIONING JURNAL
    # ============================================================
    with subbab_dropdown("11. Implikasi Kebijakan dan Positioning Jurnal Q1", expanded=False):
        st.markdown(
            "<b>Implikasi kebijakan.</b>"
            "<ul>"
            "<li>Perbaikan penargetan bansos: prioritaskan verifikasi pada KK <i>exclusion error</i> dan tinjau "
            "ulang <i>inclusion error</i> berbasis komunitas, bukan hanya atribut individual.</li>"
            f"<li>Efisiensi intervensi: manfaatkan aktor strategis hasil pemetaan empat centrality "
            f"({strategic_txt} node; {n_role_broker} broker antar-kelompok dan {n_role_multi} aktor multiperan) "
            "sebagai agen sosialisasi, verifikasi data, dan difusi program.</li>"
            "<li>Prioritas kewilayahan: fokuskan verifikasi lapangan pada dusun dengan <i>exclusion error</i> "
            "tertinggi (Temuan Kunci 7) dan libatkan aktor strategis yang berada di dusun tersebut sebagai "
            "titik masuk program.</li>"
            "<li>Pemerataan digital: sasar kelompok dengan homofili digital tinggi agar kesenjangan tidak menetap.</li>"
            "</ul>",
            unsafe_allow_html=True,
        )
        journal_rows = [
            {"Temuan/Kontribusi": "Dekomposisi within-between (Montes) untuk kesejahteraan", "Angle": "Metodologis", "Kandidat Jurnal Q1 (contoh)": "Social Networks; PLOS ONE; Applied Network Science"},
            {"Temuan/Kontribusi": "Audit exclusion/inclusion error bansos berbasis jaringan", "Angle": "Kebijakan sosial", "Kandidat Jurnal Q1 (contoh)": "World Development; Social Indicators Research"},
            {"Temuan/Kontribusi": "Homofili & segregasi inklusi digital desa", "Angle": "ICT4D / digital divide", "Kandidat Jurnal Q1 (contoh)": "Telematics and Informatics; Information Technology for Development"},
            {"Temuan/Kontribusi": "Pipeline SNA Data Desa Presisi + robustness threshold", "Angle": "Metodologis/reprodusibilitas", "Kandidat Jurnal Q1 (contoh)": "PLOS ONE; Applied Network Science"},
            {"Temuan/Kontribusi": "Pemetaan peran aktor strategis empat centrality (ambang Q75) untuk agen difusi program", "Angle": "SNA terapan/kebijakan", "Kandidat Jurnal Q1 (contoh)": "Social Networks; Network Science; PLOS ONE"},
            {"Temuan/Kontribusi": "Segregasi spasial jaringan & exclusion error per dusun (Duncan D, assortativity dusun)", "Angle": "Kebijakan/geografi sosial", "Kandidat Jurnal Q1 (contoh)": "World Development; Applied Geography; Social Indicators Research"},
        ]
        st.dataframe(pd.DataFrame(journal_rows), use_container_width=True, hide_index=True)

        st.markdown("<b>Kontribusi menurut bidang ilmu (positioning lintas disiplin).</b>", unsafe_allow_html=True)
        scope_rows = [
            {
                "Bidang/Scope": "Ilmu Komputer / Data Sains",
                "Kontribusi yang Ditonjolkan": "Pipeline SNA end-to-end yang reprodusibel: konstruksi graf kemiripan multi-metrik, "
                "penentuan threshold otomatis + uji sensitivitas, deteksi komunitas Louvain, dan klasifikasi peran aktor "
                "multi-metrik berbasis kuartil (nonparametrik, robust terhadap distribusi heavy-tailed).",
                "Subbab Pendukung": "2 (Metodologi), 8 (Aktor Strategis), 10 (Robustness)",
            },
            {
                "Bidang/Scope": "Ilmu Sosial / Kebijakan Publik",
                "Kontribusi yang Ditonjolkan": "Kuantifikasi segregasi kesejahteraan (assortativity + dekomposisi Montes), audit "
                "exclusion/inclusion error bansos, segregasi spasial per dusun (Duncan D), dan identifikasi agen difusi "
                "program berbasis posisi jaringan.",
                "Subbab Pendukung": "4-7 (Homofili, Montes, Bansos, Digital), 9 (Spasial)",
            },
            {
                "Bidang/Scope": "Interdisipliner (Computational Social Science)",
                "Kontribusi yang Ditonjolkan": "Menjembatani data administratif Data Desa Presisi dengan indikator relasional "
                "kebijakan: dari data mikro rumah tangga menjadi bukti struktural (jaringan, komunitas, spasial) yang "
                "dapat ditindaklanjuti pemerintah desa — kerangka yang dapat direplikasi lintas desa.",
                "Subbab Pendukung": "1 (Novelty), 3 (Struktur), 11 (Implikasi)",
            },
        ]
        st.dataframe(pd.DataFrame(scope_rows), use_container_width=True, hide_index=True)

        st.markdown(
            "<b>Checklist kesiapan naskah Q1.</b>"
            "<ul>"
            "<li><b>Novelty eksplisit</b>: dekomposisi within-between + audit targeting berbasis jaringan pada data "
            "sensus desa presisi (bukan sampel survei).</li>"
            "<li><b>Rigor &amp; robustness</b>: threshold otomatis dengan uji sensitivitas (subbab 10) dan justifikasi "
            "metodologis ambang kuartil peran aktor (subbab 8).</li>"
            "<li><b>Reprodusibilitas</b>: parameter lengkap dilaporkan (basis fitur, metrik kemiripan, threshold, "
            "seed Louvain); pipeline dapat dijalankan ulang pada data yang sama.</li>"
            "<li><b>Etika data</b>: anonimisasi node/dusun, hasil agregat, pernyataan batasan interpretasi di setiap "
            "temuan.</li>"
            "<li><b>Keterbatasan</b>: jaringan kemiripan atribut (bukan relasi sosial teramati), satu desa studi kasus, "
            "perlu verifikasi lapangan — dinyatakan eksplisit agar kredibel di mata reviewer.</li>"
            "<li><b>Data availability statement</b>: sebutkan skema akses data (data mikro tidak dibagikan terbuka; "
            "agregat/kode analisis dapat dibagikan atas permintaan).</li>"
            "</ul>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<b>Referensi metodologis kunci.</b><br>"
            "Blondel, V.D., dkk. (2008). Fast unfolding of communities in large networks. <i>J. Stat. Mech.</i> — deteksi komunitas Louvain.<br>"
            "Newman, M.E.J. (2003). Mixing patterns in networks. <i>Physical Review E</i> — assortativity.<br>"
            "Montes, F., dkk. (2018). Benchmarking seeding strategies... (dekomposisi within-between assortativity).<br>"
            "Freeman, L.C. (1979). Centrality in social networks: Conceptual clarification. <i>Social Networks</i>.<br>"
            "Borgatti, S.P. (2006). Identifying sets of key players in a social network. <i>Comput. Math. Organ. Theory</i>.<br>"
            "Valente, T.W. &amp; Pumpuang, P. (2007). Identifying opinion leaders to promote behavior change. <i>Health Educ. Behav.</i><br>"
            "Valente, T.W. (2012). Network interventions. <i>Science</i>, 337(6090).<br>"
            "Guimer&agrave;, R. &amp; Amaral, L.A.N. (2005). Functional cartography of complex metabolic networks. <i>Nature</i>, 433 — taksonomi peran node berbasis ambang statistik.<br>"
            "Costenbader, E. &amp; Valente, T.W. (2003). The stability of centrality measures... <i>Social Networks</i>.<br>"
            "Duncan, O.D. &amp; Duncan, B. (1955). A methodological analysis of segregation indexes. <i>Am. Sociol. Rev.</i> — indeks disimilaritas.<br>"
            "Tukey, J.W. (1977). <i>Exploratory Data Analysis</i> — konvensi kuartil.",
            unsafe_allow_html=True,
        )
        st.caption(
            "Catatan etika: seluruh hasil bersifat agregat dan anonim; temuan adalah indikasi awal berbasis data "
            "sekunder dan memerlukan verifikasi lapangan sebelum digunakan untuk keputusan penetapan sasaran."
        )


def render_weighting_methods_page(
    df_v,
    edge_feature_cols,
    rounding_decimals=2,
    threshold_grid=None,
    sample_max_nodes=120,
):
    threshold_grid = threshold_grid or [round(x, 1) for x in np.arange(0.1, 1.0, 0.1)]
    demo_threshold = 0.30
    st.markdown("<h1 class='main-header'>Halaman Metode Pembobotan: Cosine Similarity</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='premium-hero'><b>Fokus Halaman:</b> Simulasi data pseudo untuk menjelaskan pembobotan edge "
        "dengan <b>Cosine Similarity</b> pada representasi one-hot dari 5 dimensi IKD.</div>",
        unsafe_allow_html=True,
    )
    feature_cols = PSEUDO_DIMENSION_COLS
    pseudo_two_nodes = pd.DataFrame(
        [
            {
                "family_id": "KK_A",
                "Sandang, Pangan, dan Papan": 33,
                "Pendidikan": 70,
                "Sosial, Hukum, dan HAM": 55,
                "Kesehatan dan Pekerjaan": 80,
                "Lingkungan dan Infrastruktur": 61,
            },
            {
                "family_id": "KK_B",
                "Sandang, Pangan, dan Papan": 33,
                "Pendidikan": 70,
                "Sosial, Hukum, dan HAM": 55,
                "Kesehatan dan Pekerjaan": 79,
                "Lingkungan dan Infrastruktur": 62,
            },
        ]
    )
    pseudo_for_onehot = pseudo_two_nodes.copy()
    onehot_two = build_onehot_feature_matrix(
        pseudo_for_onehot,
        feature_cols,
        rounding_decimals=rounding_decimals,
    )

    tab_alur, tab_rumus, tab_sim, tab_dist = st.tabs(
        ["Alur Metode", "Rumus Matematis", "Simulasi 2 Node (Pseudo)", "Distribusi Cosine (Pseudo)"]
    )

    with tab_alur:
        st.markdown(
            "<div class='soft-card'><b>Alur Pembentukan Bobot Edge</b><br>"
            "Input dimensi: <b>Sandang, Pangan, dan Papan; Pendidikan; Sosial, Hukum, dan HAM; "
            "Kesehatan dan Pekerjaan; Lingkungan dan Infrastruktur</b>.<br>"
            "Setiap <b>kepala keluarga (KK)</b> didefinisikan sebagai satu node.<br>"
            "Pembuatan edge dimulai dari pembobotan similarity antar-node (Cosine).<br>"
            "Aturan keputusan threshold:<br>"
            "- Jika similarity <b>&ge; threshold rata-rata</b> -> edge dibuat.<br>"
            "- Jika similarity <b>&lt; threshold rata-rata</b> -> edge tidak dibuat.<br>"
            "Output akhir: <b>graf base siap diproses algoritma Louvain</b>."
            "</div>",
            unsafe_allow_html=True,
        )
        flow_df = pd.DataFrame(
            [
                {"Tahap": "Mulai", "Deskripsi": "Inisialisasi pembentukan graf base."},
                {
                    "Tahap": "Input 5 Dimensi",
                    "Deskripsi": "Masukkan lima skor dimensi kesejahteraan per KK dari rekap IKD.",
                },
                {"Tahap": "Definisi Node", "Deskripsi": "Setiap kepala keluarga (KK) didefinisikan sebagai 1 node."},
                {
                    "Tahap": "Transformasi One-Hot",
                    "Deskripsi": (
                        "Nilai dibulatkan ke bilangan bulat lalu di-encode menjadi vektor biner 0/1."
                        if int(rounding_decimals) == 0
                        else f"Nilai dibulatkan {rounding_decimals} desimal lalu di-encode menjadi vektor biner 0/1."
                    ),
                },
                {
                    "Tahap": "Pembobotan Edge",
                    "Deskripsi": "Hitung similarity antar pasangan node dengan Cosine Similarity: s_ij.",
                },
                {
                    "Tahap": "Rule Threshold",
                    "Deskripsi": "Jika s_ij >= threshold rata-rata -> buat edge (w_ij = s_ij). Jika s_ij < threshold -> edge tidak dibuat.",
                },
                {"Tahap": "Output", "Deskripsi": "Graf base berbobot siap diproses algoritma Louvain."},
            ]
        )
        fig_flow = px.funnel(
            flow_df,
            y="Tahap",
            x=[1] * len(flow_df),
            title="Tahapan Pembobotan Graf Base",
        )
        fig_flow.update_traces(
            marker_color="#1d4ed8",
            text=flow_df["Deskripsi"],
            textposition="inside",
            texttemplate="<b>%{y}</b><br>%{text}",
            insidetextfont=dict(size=12, color="#ffffff"),
        )
        fig_flow.update_layout(
            showlegend=False,
            yaxis_title="",
            xaxis_title="",
            height=640,
            template="plotly_white",
        )
        st.plotly_chart(fig_flow, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(flow_df, use_container_width=True)

    with tab_rumus:
        st.markdown("#### Cosine Similarity")
        st.latex(r"s_{ij}^{(\cos)} = \frac{\mathbf{x}_i^\top \mathbf{x}_j}{\|\mathbf{x}_i\|_2 \, \|\mathbf{x}_j\|_2}")
        st.latex(r"\mathbf{x}_i^\top \mathbf{x}_j = \sum_{k=1}^{p} x_{ik}x_{jk}")
        st.latex(r"\|\mathbf{x}_i\|_2 = \sqrt{\sum_{k=1}^{p} x_{ik}^2}")
        st.latex(r"w_{ij} = s_{ij}^{(\cos)} \;\;\text{dan edge terbentuk jika}\;\; s_{ij}^{(\cos)} \ge 0.30")
        st.caption(
            "x_i adalah vektor one-hot node i, x_j adalah vektor one-hot node j, "
            "dan s_ij menjadi bobot edge saat lolos threshold."
        )
        st.markdown("#### Notasi Matematis")
        notation_rows = [
            (r"\mathbf{x}_i = [x_{i1},\ldots,x_{ip}]", "Vektor one-hot node i."),
            (r"\mathbf{x}_j = [x_{j1},\ldots,x_{jp}]", "Vektor one-hot node j."),
            (r"x_{ik}\in\{0,1\}", "Komponen ke-k dari node i (aktif/tidak aktif)."),
            (r"\mathbf{x}_i^\top \mathbf{x}_j=\sum_{k=1}^{p}x_{ik}x_{jk}", "Dot product (jumlah kecocokan komponen aktif)."),
            (r"\|\mathbf{x}_i\|_2=\sqrt{\sum_{k=1}^{p}x_{ik}^2}", "Panjang vektor node i."),
            (r"s_{ij}^{(\cos)}=\frac{\mathbf{x}_i^\top \mathbf{x}_j}{\|\mathbf{x}_i\|_2\|\mathbf{x}_j\|_2}", "Skor cosine similarity."),
            (r"w_{ij}=s_{ij}^{(\cos)}", "Bobot edge yang dipakai di graf."),
        ]
        for expr, meaning in notation_rows:
            st.latex(expr)
            st.caption(meaning)

    with tab_sim:
        st.markdown("#### Data 2 Node Terpilih")
        st.dataframe(pseudo_two_nodes, use_container_width=True)
        active_cols = onehot_two.columns[(onehot_two.sum(axis=0) > 0)].tolist()
        onehot_view = onehot_two[active_cols].copy() if active_cols else onehot_two.copy()
        onehot_view.index = pseudo_two_nodes["family_id"].astype(str).tolist()
        st.markdown("#### Hasil One-Hot (kolom aktif)")
        st.dataframe(onehot_view, use_container_width=True)

        vec_a = onehot_two.iloc[0].to_numpy(dtype=float)
        vec_b = onehot_two.iloc[1].to_numpy(dtype=float)
        dot_val = float(np.dot(vec_a, vec_b))
        norm_a = float(np.linalg.norm(vec_a))
        norm_b = float(np.linalg.norm(vec_b))
        cos_val = compute_cosine_similarity(vec_a, vec_b)
        edge_decision = "TERBENTUK" if cos_val >= demo_threshold else "TIDAK TERBENTUK"
        c1, c2 = st.columns(2)
        c1.metric("Cosine", f"{cos_val:.4f}")
        c2.metric("Dot Product", f"{dot_val:.4f}")
        c3, c4 = st.columns(2)
        c3.metric("Threshold Contoh", f"{demo_threshold:.2f}")
        c4.metric("Status Edge", edge_decision)
        st.caption("Contoh 2 node ini disusun agar tingkat kemiripan lolos threshold 0,30.")
        st.markdown("#### Detail Hitung Cosine (2 Node)")
        st.latex(r"\mathbf{x}_i^\top \mathbf{x}_j = \sum_{k=1}^{p}x_{ik}x_{jk}")
        st.latex(rf"\mathbf{{x}}_i^\top \mathbf{{x}}_j = {dot_val:.4f}")
        st.latex(r"\|\mathbf{x}_i\|_2=\sqrt{\sum_{k=1}^{p}x_{ik}^2},\quad \|\mathbf{x}_j\|_2=\sqrt{\sum_{k=1}^{p}x_{jk}^2}")
        st.latex(rf"\|\mathbf{{x}}_i\|_2 = {norm_a:.4f},\quad \|\mathbf{{x}}_j\|_2 = {norm_b:.4f}")
        st.latex(r"s_{ij}^{(\cos)}=\frac{\mathbf{x}_i^\top \mathbf{x}_j}{\|\mathbf{x}_i\|_2\|\mathbf{x}_j\|_2}")
        st.markdown("#### Substitusi Angka ke Persamaan")
        st.latex(rf"s_{{ij}}^{{(\cos)}}=\frac{{{dot_val:.4f}}}{{{norm_a:.4f}\times {norm_b:.4f}}}={cos_val:.4f}")
        st.latex(rf"w_{{ij}} = s_{{ij}}^{{(\cos)}} = {cos_val:.4f}")
        st.latex(rf"\text{{Edge terbentuk jika }} s_{{ij}}^{{(\cos)}} \ge {demo_threshold:.2f}")
        st.latex(rf"{cos_val:.4f} \; {'\\ge' if cos_val >= demo_threshold else '<'} \; {demo_threshold:.2f} \Rightarrow \text{{{edge_decision}}}")
        st.caption(
            "Dot product adalah jumlah hasil kali komponen seposisi pada dua vektor. "
            "Pada one-hot, dot product merepresentasikan jumlah kategori yang sama-sama aktif."
        )

    with tab_dist:
        st.markdown("#### Distribusi Cosine dari Sampel Pseudo")
        rng = np.random.default_rng(42)
        value_pool = {
            "Sandang, Pangan, dan Papan": [33.40, 33.50, 33.60, 34.00],
            "Pendidikan": [70.00, 70.50, 71.00, 71.50],
            "Sosial, Hukum, dan HAM": [55.00, 55.20, 55.40, 55.60],
            "Kesehatan dan Pekerjaan": [79.50, 80.00, 80.50, 81.00],
            "Lingkungan dan Infrastruktur": [61.20, 61.30, 61.40, 61.50],
        }
        n_nodes = int(max(20, sample_max_nodes))
        pseudo_nodes = []
        for idx in range(n_nodes):
            row = {"family_id": f"PS_{idx+1:03d}"}
            for c in feature_cols:
                row[c] = float(rng.choice(value_pool[c]))
            pseudo_nodes.append(row)
        pseudo_df = pd.DataFrame(pseudo_nodes)
        onehot_sample = build_onehot_feature_matrix(pseudo_df, feature_cols, rounding_decimals=rounding_decimals)
        ids = pseudo_df["family_id"].tolist()
        vectors = onehot_sample.to_numpy(dtype=float)
        cos_values = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                vec_i = vectors[i]
                vec_j = vectors[j]
                cos_values.append(float(compute_cosine_similarity(vec_i, vec_j)))
        if not cos_values:
            st.warning("Pasangan node pseudo belum cukup.")
            return

        fig_hist = px.histogram(
            x=cos_values,
            nbins=24,
            title="Histogram Cosine Similarity (Data Pseudo)",
        )
        fig_hist.update_layout(xaxis_title="Cosine Similarity", yaxis_title="Frekuensi")
        st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

        edge_at_demo = int(np.sum(np.array(cos_values) >= demo_threshold))
        summary_df = pd.DataFrame(
            [
                {
                    "Metode": "Cosine",
                    "Similarity Rata-rata": float(np.mean(cos_values)),
                    "Similarity Median": float(np.median(cos_values)),
                    "Threshold (Contoh)": float(demo_threshold),
                    "Edge Count @ Threshold": int(edge_at_demo),
                }
            ]
        )
        st.dataframe(summary_df, use_container_width=True)
        st.caption(
            f"Pada halaman metode ini, keputusan edge didemokan dengan threshold tetap {demo_threshold:.2f}."
        )


def render_louvain_methods_page(
    n_nodes=60,
    rounding_decimals=2,
    threshold=0.30,
    seed=42,
):
    st.markdown("<h1 class='main-header'>Halaman Metode Louvain (Simulasi Pseudo)</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='premium-hero'><b>Fokus Halaman:</b> Menjelaskan logika penerapan Louvain dari graf base berbobot "
        "yang dibangun dari data pseudo lima dimensi kesejahteraan.</div>",
        unsafe_allow_html=True,
    )
    tab_alur, tab_rumus, tab_sim, tab_out = st.tabs(
        ["Alur Louvain", "Rumus Modularity", "Simulasi dari Graf Base Pseudo", "Output Komunitas"]
    )

    with tab_alur:
        louvain_flow = pd.DataFrame(
            [
                {"Tahap": "Input Graf Base", "Deskripsi": "Gunakan graf berbobot hasil similarity antar node."},
                {"Tahap": "Inisialisasi", "Deskripsi": "Setiap node mulai sebagai komunitas sendiri."},
                {"Tahap": "Local Moving", "Deskripsi": "Pindahkan node ke komunitas tetangga jika modularity naik."},
                {"Tahap": "Agregasi", "Deskripsi": "Gabungkan komunitas jadi super-node (graf baru)."},
                {"Tahap": "Iterasi", "Deskripsi": "Ulangi Local Moving + Agregasi sampai Q tidak naik lagi."},
                {"Tahap": "Output", "Deskripsi": "Partisi komunitas final Louvain."},
            ]
        )
        fig_louvain_flow = px.funnel(
            louvain_flow,
            y="Tahap",
            x=[1] * len(louvain_flow),
            title="Tahapan Penerapan Louvain dari Graf Base",
        )
        fig_louvain_flow.update_traces(
            marker_color="#1d4ed8",
            text=louvain_flow["Deskripsi"],
            textposition="inside",
            texttemplate="<b>%{y}</b><br>%{text}",
            insidetextfont=dict(size=12, color="#ffffff"),
        )
        fig_louvain_flow.update_layout(height=560, template="plotly_white", xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_louvain_flow, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(louvain_flow, use_container_width=True)

    with tab_rumus:
        st.markdown("#### Fungsi Modularity (Q)")
        st.latex(
            r"Q = \frac{1}{2m}\sum_{i,j}\left(A_{ij} - \frac{k_i k_j}{2m}\right)\delta(c_i, c_j)"
        )
        st.markdown("#### Arti Simbol")
        st.latex(r"A_{ij}: \text{bobot edge antara node } i \text{ dan } j")
        st.latex(r"k_i: \text{weighted degree node } i,\;\; k_i=\sum_j A_{ij}")
        st.latex(r"2m: \sum_{i,j} A_{ij}")
        st.latex(r"c_i: \text{komunitas node } i")
        st.latex(r"\delta(c_i,c_j)=1 \text{ jika sama komunitas, selain itu }0")
        st.caption(
            "Louvain mencari partisi komunitas yang memaksimalkan Q. "
            "Node dipindahkan lokal jika meningkatkan modularity."
        )

    # Bangun graf base pseudo dari 5 dimensi, lalu jalankan Louvain.
    rng = np.random.default_rng(int(seed))
    pools = {
        "Sandang, Pangan, dan Papan": [33.40, 33.50, 33.60, 34.00],
        "Pendidikan": [70.00, 70.50, 71.00, 71.50],
        "Sosial, Hukum, dan HAM": [55.00, 55.20, 55.40, 55.60],
        "Kesehatan dan Pekerjaan": [79.50, 80.00, 80.50, 81.00],
        "Lingkungan dan Infrastruktur": [61.20, 61.30, 61.40, 61.50],
    }
    pseudo_rows = []
    for i in range(int(max(20, n_nodes))):
        row = {"family_id": f"LV_{i+1:03d}"}
        for c in PSEUDO_DIMENSION_COLS:
            row[c] = float(rng.choice(pools[c]))
        pseudo_rows.append(row)
    pseudo_df = pd.DataFrame(pseudo_rows)
    onehot = build_onehot_feature_matrix(
        pseudo_df,
        PSEUDO_DIMENSION_COLS,
        rounding_decimals=rounding_decimals,
    )

    G = nx.Graph()
    for _, r in pseudo_df.iterrows():
        G.add_node(r["family_id"], **r.to_dict())
    ids = pseudo_df["family_id"].tolist()
    vecs = onehot.to_numpy(dtype=float)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sim = float(compute_cosine_similarity(vecs[i], vecs[j]))
            if sim >= float(threshold):
                G.add_edge(ids[i], ids[j], weight=sim)

    if G.number_of_edges() == 0:
        # fallback agar simulasi tetap jalan jika threshold terlalu tinggi.
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                sim = float(compute_cosine_similarity(vecs[i], vecs[j]))
                if sim >= 0.20:
                    G.add_edge(ids[i], ids[j], weight=sim)

    if G.number_of_edges() > 0:
        init_partition = {n: idx for idx, n in enumerate(G.nodes())}
        q_init = _safe_float_metric(community_louvain.modularity(init_partition, G, weight="weight"), default=0.0)
        final_partition = community_louvain.best_partition(G, weight="weight", random_state=int(seed))
        q_final = _safe_float_metric(community_louvain.modularity(final_partition, G, weight="weight"), default=0.0)
    else:
        init_partition = {n: 0 for n in G.nodes()}
        final_partition = init_partition.copy()
        q_init = 0.0
        q_final = 0.0

    with tab_sim:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Node", G.number_of_nodes())
        c2.metric("Edge", G.number_of_edges())
        c3.metric("Q Awal", f"{q_init:.5f}")
        c4.metric("Q Final Louvain", f"{q_final:.5f}", f"ΔQ = {q_final - q_init:.5f}")

        if G.number_of_edges() > 0:
            pos = nx.spring_layout(G, seed=int(seed), weight="weight")
            nodes = list(G.nodes())
            comm_ids = [final_partition.get(n, 0) for n in nodes]
            fig_graph = go.Figure()
            for u, v, d in G.edges(data=True):
                cu = int(final_partition.get(u, 0))
                cv = int(final_partition.get(v, 0))
                edge_weight = _safe_float_metric(d.get("weight"), 0.0)
                edge_color = (
                    rgba_from_hex(CONTRAST_COLORS[cu % len(CONTRAST_COLORS)], 0.44)
                    if cu == cv
                    else rgba_from_hex(CONTRAST_COLORS[((cu + 1) * 7 + (cv + 1) * 13) % len(CONTRAST_COLORS)], 0.32)
                )
                fig_graph.add_trace(
                    go.Scatter(
                        x=[pos[u][0], pos[v][0], None],
                        y=[pos[u][1], pos[v][1], None],
                        mode="lines",
                        line=dict(width=1.0 + (1.6 * edge_weight), color=edge_color),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )
            fig_graph.add_trace(
                go.Scatter(
                    x=[pos[n][0] for n in nodes],
                    y=[pos[n][1] for n in nodes],
                    mode="markers",
                    marker=dict(
                        size=10,
                        color=comm_ids,
                        colorscale="Blues",
                        showscale=True,
                        colorbar=dict(title="Komunitas"),
                                        line=dict(color=NETWORK_NODE_LINE, width=0.7),
                    ),
                    text=[f"Node: {n}<br>Komunitas: {final_partition.get(n, 0)}" for n in nodes],
                    hoverinfo="text",
                    showlegend=False,
                )
            )
            fig_graph.update_layout(
                title="Graf Base Pseudo setelah Louvain (warna = komunitas)",
                height=560,
                template="plotly_white",
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
            )
            st.plotly_chart(fig_graph, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        else:
            st.warning("Graf pseudo tidak memiliki edge pada konfigurasi saat ini.")

    with tab_out:
        if G.number_of_nodes() == 0:
            st.warning("Tidak ada node untuk dianalisis.")
        else:
            out_df = pd.DataFrame(
                [{"family_id": n, "Komunitas Louvain": int(final_partition.get(n, 0))} for n in G.nodes()]
            )
            degree_map = {n: float(G.degree(n, weight="weight")) for n in G.nodes()}
            pseudo_profile = pseudo_df.copy()
            pseudo_profile["Komunitas Louvain"] = pseudo_profile["family_id"].map(
                lambda n: int(final_partition.get(n, -1))
            )
            pseudo_profile["Weighted Degree"] = pseudo_profile["family_id"].map(
                lambda n: float(degree_map.get(n, 0.0))
            )
            size_df = (
                out_df["Komunitas Louvain"]
                .value_counts()
                .rename_axis("Komunitas Louvain")
                .reset_index(name="Jumlah Node")
                .sort_values("Komunitas Louvain")
                .reset_index(drop=True)
            )
            total_clusters = int(size_df["Komunitas Louvain"].nunique())
            st.markdown("#### Ringkasan Komunitas Louvain")
            csum1, csum2 = st.columns(2)
            csum1.metric("Jumlah Klaster Terbentuk", f"{total_clusters}")
            csum2.metric("Total Node Terpartisi", f"{int(size_df['Jumlah Node'].sum())}")
            st.dataframe(size_df, use_container_width=True)

            cluster_desc = (
                pseudo_profile.groupby("Komunitas Louvain", as_index=False)
                .agg(
                    Jumlah_Node=("family_id", "count"),
                    Rerata_Sandang_Pangan_Papan=("Sandang, Pangan, dan Papan", "mean"),
                    Rerata_Pendidikan=("Pendidikan", "mean"),
                    Rerata_Sosial_Hukum_HAM=("Sosial, Hukum, dan HAM", "mean"),
                    Rerata_Kesehatan_Pekerjaan=("Kesehatan dan Pekerjaan", "mean"),
                    Rerata_Lingkungan_Infrastruktur=("Lingkungan dan Infrastruktur", "mean"),
                    Rerata_Weighted_Degree=("Weighted Degree", "mean"),
                )
                .sort_values("Komunitas Louvain")
                .reset_index(drop=True)
            )
            cluster_desc["Rerata_IKD_Agregat"] = cluster_desc[
                [
                    "Rerata_Sandang_Pangan_Papan",
                    "Rerata_Pendidikan",
                    "Rerata_Sosial_Hukum_HAM",
                    "Rerata_Kesehatan_Pekerjaan",
                    "Rerata_Lingkungan_Infrastruktur",
                ]
            ].mean(axis=1)
            st.markdown("#### Statistik Deskriptif per Klaster")
            st.dataframe(
                cluster_desc.style.format(
                    {
                        "Rerata_Sandang_Pangan_Papan": "{:.2f}",
                        "Rerata_Pendidikan": "{:.2f}",
                        "Rerata_Sosial_Hukum_HAM": "{:.2f}",
                        "Rerata_Kesehatan_Pekerjaan": "{:.2f}",
                        "Rerata_Lingkungan_Infrastruktur": "{:.2f}",
                        "Rerata_IKD_Agregat": "{:.2f}",
                        "Rerata_Weighted_Degree": "{:.2f}",
                    }
                ),
                use_container_width=True,
            )

            cluster_profile_long = cluster_desc.melt(
                id_vars=["Komunitas Louvain"],
                value_vars=[
                    "Rerata_Sandang_Pangan_Papan",
                    "Rerata_Pendidikan",
                    "Rerata_Sosial_Hukum_HAM",
                    "Rerata_Kesehatan_Pekerjaan",
                    "Rerata_Lingkungan_Infrastruktur",
                    "Rerata_IKD_Agregat",
                ],
                var_name="Indikator",
                value_name="Rerata Nilai",
            )
            cluster_profile_long["Indikator"] = cluster_profile_long["Indikator"].map(
                {
                    "Rerata_Sandang_Pangan_Papan": "Sandang, Pangan, dan Papan",
                    "Rerata_Pendidikan": "Pendidikan",
                    "Rerata_Sosial_Hukum_HAM": "Sosial, Hukum, dan HAM",
                    "Rerata_Kesehatan_Pekerjaan": "Kesehatan dan Pekerjaan",
                    "Rerata_Lingkungan_Infrastruktur": "Lingkungan dan Infrastruktur",
                    "Rerata_IKD_Agregat": "IKD Agregat",
                }
            )
            fig_cluster_profile = px.bar(
                cluster_profile_long,
                x="Komunitas Louvain",
                y="Rerata Nilai",
                color="Indikator",
                barmode="group",
                title="Profil Rerata Dimensi per Klaster Louvain",
            )
            st.plotly_chart(fig_cluster_profile, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

            st.markdown("#### Narasi Otomatis Karakter Tiap Klaster")
            for _, row in cluster_desc.iterrows():
                cid = int(row["Komunitas Louvain"])
                n_k = int(row["Jumlah_Node"])
                avg_ikr = float(row["Rerata_IKD_Agregat"])
                ikr_lbl, _ = categorize_ikr_bps(avg_ikr)
                if avg_ikr >= 75:
                    tone = "klaster relatif kuat secara skor dimensi"
                elif avg_ikr >= 65:
                    tone = "klaster menengah dengan kapasitas campuran"
                else:
                    tone = "klaster dengan kerentanan dimensi yang perlu prioritas"
                st.markdown(
                    f"<div class='soft-card'><b>Klaster {cid}</b> berisi <b>{n_k}</b> node, "
                    f"rerata IKD agregat simulasi <b>{avg_ikr:.2f}</b> (kategori <b>{ikr_lbl}</b>), "
                    f"dengan rerata weighted degree <b>{float(row['Rerata_Weighted_Degree']):.2f}</b>. "
                    f"Interpretasi cepat: {tone}.</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("#### Sampel Hasil Partisi Node")
            st.dataframe(out_df.head(30), use_container_width=True)
            st.caption(
                "Logika penerapan: graf base pseudo -> optimasi modularity (Louvain) -> partisi komunitas final."
            )


def render_assortativity_methods_page(
    n_nodes=90,
    seed=42,
):
    st.markdown("<h1 class='main-header'>Halaman Metode Assortativity (Komprehensif)</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='premium-hero'><b>Fokus Halaman:</b> Membahas semua jenis assortativity pada kode ini: "
        "numeric assortativity, attribute assortativity (biner/kategorikal), dan within-between assortativity (Montes).</div>",
        unsafe_allow_html=True,
    )

    rng = np.random.default_rng(int(seed))
    n_nodes = int(max(30, n_nodes))
    cluster_count = 3
    cluster_ids = [int(i % cluster_count) for i in range(n_nodes)]
    node_ids = [f"AS_{i+1:03d}" for i in range(n_nodes)]

    G = nx.Graph()
    rows = []
    for idx, nid in enumerate(node_ids):
        c = int(cluster_ids[idx])
        base = 62 + (c * 7)
        f_a = float(np.clip(rng.normal(base + 1.5, 2.2), 45, 95))
        f_b = float(np.clip(rng.normal(base + 0.8, 2.5), 45, 95))
        f_c = float(np.clip(rng.normal(base - 0.5, 2.4), 45, 95))
        f_d = float(np.clip(rng.normal(base + 1.2, 2.6), 45, 95))
        f_e = float(np.clip(rng.normal(base + 0.2, 2.7), 45, 95))
        f_ikr = float(np.mean([f_a, f_b, f_c, f_d, f_e]))

        bansos_num = int(rng.random() < (0.70 if c == 0 else 0.40 if c == 1 else 0.18))
        internet_num = int(rng.random() < (0.28 if c == 0 else 0.56 if c == 1 else 0.82))
        ponsel_num = int(rng.random() < (0.45 if c == 0 else 0.66 if c == 1 else 0.86))
        dusun = f"Dusun-{c+1}"
        cat_label, cat_code = categorize_ikr_bps(f_ikr)

        attrs = {
            "family_id": nid,
            "cluster": c,
            "f_a_dari_rekap_kk": f_a,
            "f_b_dari_rekap_kk": f_b,
            "f_c_dari_rekap_kk": f_c,
            "f_d_dari_rekap_kk": f_d,
            "f_e_dari_rekap_kk": f_e,
            "f_ikr_dari_rekap_kk": f_ikr,
            "bansos_num": bansos_num,
            "internet_num": internet_num,
            "ponsel_num": ponsel_num,
            "dusun": dusun,
            "kategori_ikr": cat_label,
            "kategori_ikr_code": int(cat_code),
        }
        G.add_node(nid, **attrs)
        rows.append(attrs)

    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            ci = cluster_ids[i]
            cj = cluster_ids[j]
            p_edge = 0.18 if ci == cj else 0.045
            if rng.random() < p_edge:
                si = rows[i]["f_ikr_dari_rekap_kk"]
                sj = rows[j]["f_ikr_dari_rekap_kk"]
                w = float(np.clip(1.0 - (abs(si - sj) / 60.0), 0.05, 1.0))
                G.add_edge(node_ids[i], node_ids[j], weight=w)

    if G.number_of_edges() == 0:
        st.warning("Graf pseudo assortativity belum memiliki edge. Ubah seed/jumlah node.")
        return

    tab_alur, tab_konsep, tab_num, tab_attr, tab_montes, tab_ringkas = st.tabs(
        ["Alur Assortativity", "Konsep & Rumus", "Numeric Assortativity", "Attribute Assortativity", "Within-Between Montes", "Ringkasan Interpretasi"]
    )

    with tab_alur:
        flow_assort = pd.DataFrame(
            [
                {"Tahap": "Input Graf Base", "Deskripsi": "Gunakan graf berbobot beserta atribut node."},
                {"Tahap": "Pilih Jenis Assortativity", "Deskripsi": "Numeric / Attribute / Within-Between (Montes)."},
                {"Tahap": "Hitung Metrik", "Deskripsi": "Dapatkan r (numeric/attribute), Qw*, dan Qb*."},
                {"Tahap": "Bandingkan Hasil", "Deskripsi": "Bandingkan antar dimensi/atribut untuk menemukan yang dominan."},
                {"Tahap": "Interpretasi", "Deskripsi": "Baca arah (asortatif/disasortatif) dan kekuatan pola."},
                {"Tahap": "Output Analitik", "Deskripsi": "Rekomendasi audit sosial-kebijakan berbasis hasil assortativity."},
            ]
        )
        fig_flow_assort = px.funnel(
            flow_assort,
            y="Tahap",
            x=[1] * len(flow_assort),
            title="Tahapan Analisis Assortativity",
        )
        fig_flow_assort.update_traces(
            marker_color="#1d4ed8",
            text=flow_assort["Deskripsi"],
            textposition="inside",
            texttemplate="<b>%{y}</b><br>%{text}",
            insidetextfont=dict(size=12, color="#ffffff"),
        )
        fig_flow_assort.update_layout(height=560, template="plotly_white", xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_flow_assort, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(flow_assort, use_container_width=True)

    with tab_konsep:
        k1, k2, k3 = st.columns(3)
        k1.metric("Jumlah Node (Pseudo)", G.number_of_nodes())
        k2.metric("Jumlah Edge (Pseudo)", G.number_of_edges())
        k3.metric("Jumlah Klaster Simulasi", cluster_count)
        st.markdown(
            "<div class='soft-card'><b>Cara Baca Nilai Assortativity (r):</b><br>"
            "<b>r > 0</b> = cenderung terhubung dengan node yang mirip (asortatif).<br>"
            "<b>r = 0</b> = cenderung acak/campuran.<br>"
            "<b>r < 0</b> = cenderung terhubung dengan node yang berbeda (disasortatif).<br>"
            "Semakin besar |r|, semakin kuat pola pemilahannya.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### 1) Numeric Assortativity (Newman)")
        st.latex(r"r = \mathrm{corr}(x_u, x_v)\;\; \text{untuk setiap edge } (u,v)")
        st.markdown("#### 2) Attribute Assortativity (Kategorikal/Biner)")
        st.latex(r"r = \frac{\sum_i e_{ii} - \sum_i a_i b_i}{1 - \sum_i a_i b_i}")
        st.markdown("#### 3) Within-Between Assortativity (Montes)")
        st.latex(r"Q_w^* = \frac{Q_w}{Q_{w,\max}},\quad Q_b^* = \frac{Q_b}{Q_{b,\max}}")
        st.caption(
            "Di kode ini: numeric assortativity dihitung untuk lima dimensi kesejahteraan dan IKD agregat; "
            "attribute assortativity untuk bansos, internet, ponsel, dan dusun; "
            "Within-Between memakai kategori IKD (BPS) sebagai category_attr dan klaster sebagai group_attr."
        )
        cara_baca_df = pd.DataFrame(
            [
                {"Rentang Nilai": "r >= 0.50", "Interpretasi": "Asortatif kuat (pengelompokan tegas)"},
                {"Rentang Nilai": "0.30 <= r < 0.50", "Interpretasi": "Asortatif sedang"},
                {"Rentang Nilai": "0.10 <= r < 0.30", "Interpretasi": "Asortatif lemah"},
                {"Rentang Nilai": "-0.10 < r < 0.10", "Interpretasi": "Campuran / mendekati acak"},
                {"Rentang Nilai": "r <= -0.10", "Interpretasi": "Disasortatif (lebih sering lintas kategori)"},
            ]
        )
        st.dataframe(cara_baca_df, use_container_width=True)
        st.markdown("#### Kenapa Masuk Jenis Ini?")
        jenis_df = pd.DataFrame(
            [
                {
                    "Objek/Metrik": "Lima dimensi kesejahteraan dan IKD agregat",
                    "Jenis Assortativity": "Numeric Assortativity",
                    "Alasan Metodologis": "Nilai berbentuk skor kontinu, sehingga yang diukur adalah korelasi nilai antar-node pada edge.",
                    "Rumus Inti": "r = corr(x_u, x_v) pada edge (u,v)",
                },
                {
                    "Objek/Metrik": "Bansos, Internet, Ponsel, Dusun",
                    "Jenis Assortativity": "Attribute Assortativity",
                    "Alasan Metodologis": "Nilai berbentuk kategori/biner, sehingga yang diukur adalah kecenderungan edge menghubungkan kategori yang sama.",
                    "Rumus Inti": "r berbasis matriks mixing kategori",
                },
                {
                    "Objek/Metrik": "Kategori IKD BPS + Klaster",
                    "Jenis Assortativity": "Within-Between (Montes)",
                    "Alasan Metodologis": "Tujuannya memisahkan pola homogenitas di dalam klaster vs antar-klaster.",
                    "Rumus Inti": "Qw* (within), Qb* (between)",
                },
            ]
        )
        st.dataframe(jenis_df, use_container_width=True)
        fig_class = px.treemap(
            jenis_df,
            path=["Jenis Assortativity", "Objek/Metrik"],
            values=[1, 1, 1],
            color="Jenis Assortativity",
            color_discrete_sequence=["#1d4ed8", "#2563eb", "#60a5fa"],
            title="Peta Klasifikasi Jenis Assortativity di Dashboard",
        )
        st.plotly_chart(fig_class, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    df_nodes = pd.DataFrame(rows)
    edge_pairs = []
    for u, v, d in G.edges(data=True):
        au = G.nodes[u]
        av = G.nodes[v]
        edge_pairs.append(
            {
                "u": u,
                "v": v,
                "weight": _safe_float_metric(d.get("weight"), 0.0),
                "cluster_u": int(au.get("cluster", -1)),
                "cluster_v": int(av.get("cluster", -1)),
                "f_a_u": _safe_float_metric(au.get("f_a_dari_rekap_kk"), np.nan),
                "f_a_v": _safe_float_metric(av.get("f_a_dari_rekap_kk"), np.nan),
                "f_b_u": _safe_float_metric(au.get("f_b_dari_rekap_kk"), np.nan),
                "f_b_v": _safe_float_metric(av.get("f_b_dari_rekap_kk"), np.nan),
                "f_c_u": _safe_float_metric(au.get("f_c_dari_rekap_kk"), np.nan),
                "f_c_v": _safe_float_metric(av.get("f_c_dari_rekap_kk"), np.nan),
                "f_d_u": _safe_float_metric(au.get("f_d_dari_rekap_kk"), np.nan),
                "f_d_v": _safe_float_metric(av.get("f_d_dari_rekap_kk"), np.nan),
                "f_e_u": _safe_float_metric(au.get("f_e_dari_rekap_kk"), np.nan),
                "f_e_v": _safe_float_metric(av.get("f_e_dari_rekap_kk"), np.nan),
                "f_ikr_u": _safe_float_metric(au.get("f_ikr_dari_rekap_kk"), np.nan),
                "f_ikr_v": _safe_float_metric(av.get("f_ikr_dari_rekap_kk"), np.nan),
                "bansos_u": str(au.get("bansos_num", "NA")),
                "bansos_v": str(av.get("bansos_num", "NA")),
                "internet_u": str(au.get("internet_num", "NA")),
                "internet_v": str(av.get("internet_num", "NA")),
                "ponsel_u": str(au.get("ponsel_num", "NA")),
                "ponsel_v": str(av.get("ponsel_num", "NA")),
                "dusun_u": str(au.get("dusun", "NA")),
                "dusun_v": str(av.get("dusun", "NA")),
            }
        )
    df_edges = pd.DataFrame(edge_pairs)
    numeric_specs = list(IKD_DIMENSION_MAP) + [IKD_OVERALL_METRIC]
    numeric_rows = []
    for lbl, col in numeric_specs:
        r_val = safe_numeric_assortativity(G, col, default=0.0)
        direction, strength = interpret_assortativity_value(r_val)
        numeric_rows.append(
            {"Metrik": lbl, "Sumber Skor": format_dimension_source_label(col), "r": float(r_val), "Arah": direction, "Kekuatan": strength}
        )
    df_num = pd.DataFrame(numeric_rows)

    with tab_num:
        st.markdown("#### Assortativity Numerik per Dimensi")
        st.caption(
            "Tab ini menjawab: dimensi skor mana yang paling mendorong pemilahan keterhubungan antar node."
        )
        with st.expander("Langkah Hitung Numeric Assortativity (Detail)", expanded=False):
            st.markdown("1. Ambil semua pasangan node yang terhubung (edge).")
            st.markdown("2. Untuk tiap edge, ambil nilai dimensi di node kiri dan kanan.")
            st.markdown("3. Hitung korelasi pasangan nilai tersebut.")
            st.markdown("4. Korelasi itulah nilai `r` numeric assortativity.")
        df_num_sorted = df_num.sort_values("r", ascending=False).reset_index(drop=True)
        fig_num = px.bar(
            df_num_sorted,
            x="r",
            y="Metrik",
            orientation="h",
            color="r",
            color_continuous_scale="Blues",
            range_color=[-1, 1],
            title="Perbandingan Numeric Assortativity",
            hover_data=["Sumber Skor", "Arah", "Kekuatan"],
        )
        fig_num.add_vline(x=0.0, line_dash="dash", line_color="#475569")
        fig_num.update_traces(text=df_num_sorted["r"].map(lambda x: f"{x:.3f}"), textposition="outside")
        st.plotly_chart(fig_num, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(df_num.style.background_gradient(cmap="Blues", subset=["r"]), use_container_width=True)
        top_num_local = df_num.iloc[df_num["r"].abs().idxmax()]
        st.markdown(
            f"<div class='soft-card'><b>Interpretasi Cepat Numeric:</b><br>"
            f"Dimensi paling dominan adalah <b>{top_num_local['Metrik']}</b> dengan r=<b>{float(top_num_local['r']):.4f}</b> "
            f"({top_num_local['Arah']} | {top_num_local['Kekuatan']}).</div>",
            unsafe_allow_html=True,
        )
        numeric_pair_map = {
            "Sandang, Pangan, dan Papan": ("f_a_u", "f_a_v"),
            "Pendidikan": ("f_b_u", "f_b_v"),
            "Sosial, Hukum, dan HAM": ("f_c_u", "f_c_v"),
            "Kesehatan dan Pekerjaan": ("f_d_u", "f_d_v"),
            "Lingkungan dan Infrastruktur": ("f_e_u", "f_e_v"),
            "IKD Agregat": ("f_ikr_u", "f_ikr_v"),
        }
        chosen_metric = st.selectbox(
            "Visual Pair Nilai per Edge (Numeric)",
            options=list(numeric_pair_map.keys()),
            index=5,
        )
        ux, vx = numeric_pair_map[chosen_metric]
        if not df_edges.empty:
            fig_pair = px.scatter(
                df_edges,
                x=ux,
                y=vx,
                color="weight",
                color_continuous_scale="Blues",
                title=f"Pasangan Nilai pada Setiap Edge - {chosen_metric}",
                labels={ux: f"{chosen_metric} (Node U)", vx: f"{chosen_metric} (Node V)", "weight": "Bobot Edge"},
                hover_data=["u", "v", "cluster_u", "cluster_v"],
            )
            min_xy = float(np.nanmin([df_edges[ux].min(), df_edges[vx].min()]))
            max_xy = float(np.nanmax([df_edges[ux].max(), df_edges[vx].max()]))
            fig_pair.add_trace(
                go.Scatter(
                    x=[min_xy, max_xy],
                    y=[min_xy, max_xy],
                    mode="lines",
                    line=dict(color="#334155", dash="dash"),
                    name="Garis x=y",
                )
            )
            st.plotly_chart(fig_pair, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            st.caption("Semakin rapat titik di sekitar garis x=y, semakin tinggi kecenderungan asortatif untuk dimensi itu.")

    attr_specs = [
        ("Bansos", "bansos_num"),
        ("Internet", "internet_num"),
        ("Ponsel", "ponsel_num"),
        ("Dusun", "dusun"),
    ]
    attr_rows = []
    for lbl, col in attr_specs:
        r_attr = safe_attribute_assortativity(G, col, default=0.0)
        d_attr, s_attr = interpret_assortativity_value(r_attr)
        montes_attr = compute_montes_within_between_assortativity(
            G,
            category_attr=col,
            group_attr="cluster",
            invalid_category_values=None,
        )
        attr_rows.append(
            {
                "Metrik": lbl,
                "Kolom": col,
                "r": float(r_attr),
                "Qw*": float(montes_attr["q_w_star"]),
                "Qb*": float(montes_attr["q_b_star"]),
                "Arah": d_attr,
                "Kekuatan": s_attr,
                "Label Steinley": steinley_segregation_label(r_attr),
            }
        )
    df_attr = pd.DataFrame(attr_rows)
    audit_qw_mean = float(df_attr["Qw*"].mean()) if not df_attr.empty else 0.0
    audit_qb_mean = float(df_attr["Qb*"].mean()) if not df_attr.empty else 0.0

    with tab_attr:
        st.markdown("#### Assortativity Atribut (Biner/Kategorikal)")
        st.caption(
            "Tab ini menunjukkan atribut kebijakan/spasial mana yang paling homogen dalam jaringan."
        )
        st.markdown(
            "<div class='soft-card'><b>Cara Baca Khusus Audit (Bansos/Internet/Ponsel/Dusun):</b><br>"
            "<b>Nilai r</b> menilai seberapa kuat atribut tersebut mengikuti struktur keterhubungan pada <b>graf base</b> "
            "(semakin besar |r|, semakin kuat keterkaitannya dengan pola graf base).<br>"
            "<b>Nilai Qw*</b> dan <b>Qb*</b> baru dipakai untuk memecah konteks relasi menjadi "
            "<b>intra-klaster (within)</b> dan <b>inter-klaster (between)</b>."
            "</div>",
            unsafe_allow_html=True,
        )
        with st.expander("Langkah Hitung Attribute Assortativity (Detail)", expanded=False):
            st.markdown("1. Untuk tiap edge, baca kategori atribut di kedua ujung edge.")
            st.markdown("2. Hitung proporsi edge yang menghubungkan kategori sama vs berbeda.")
            st.markdown("3. Bandingkan dengan proporsi acak yang diharapkan.")
            st.markdown("4. Hasil normalisasinya menjadi nilai `r` attribute assortativity.")
        fig_attr = px.bar(
            df_attr,
            x="Metrik",
            y="r",
            color="r",
            color_continuous_scale="Blues",
            range_color=[-1, 1],
            title="Perbandingan Attribute Assortativity",
            hover_data=["Kolom", "Qw*", "Qb*", "Arah", "Kekuatan", "Label Steinley"],
        )
        fig_attr.add_hline(y=0.0, line_dash="dash", line_color="#475569")
        st.plotly_chart(fig_attr, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(df_attr.style.background_gradient(cmap="Blues", subset=["r"]), use_container_width=True)
        melt_attr = df_attr.melt(
            id_vars=["Metrik"],
            value_vars=["r", "Qw*", "Qb*"],
            var_name="Komponen",
            value_name="Nilai",
        )
        fig_attr_comp = px.bar(
            melt_attr,
            x="Metrik",
            y="Nilai",
            color="Komponen",
            barmode="group",
            title="Perbandingan Komponen r vs Qw* vs Qb*",
            color_discrete_sequence=["#1d4ed8", "#60a5fa", "#93c5fd"],
        )
        fig_attr_comp.add_hline(y=0.0, line_dash="dash", line_color="#475569")
        st.plotly_chart(fig_attr_comp, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        attr_choice = st.selectbox(
            "Detail Matriks Kategori per Edge",
            options=["Bansos", "Internet", "Ponsel", "Dusun"],
            index=0,
        )
        attr_edge_cols = {
            "Bansos": ("bansos_u", "bansos_v"),
            "Internet": ("internet_u", "internet_v"),
            "Ponsel": ("ponsel_u", "ponsel_v"),
            "Dusun": ("dusun_u", "dusun_v"),
        }
        cu, cv = attr_edge_cols[attr_choice]
        if not df_edges.empty:
            ct = pd.crosstab(df_edges[cu], df_edges[cv]).sort_index().sort_index(axis=1)
            heat = go.Figure(
                data=go.Heatmap(
                    z=ct.values,
                    x=[str(x) for x in ct.columns],
                    y=[str(y) for y in ct.index],
                    colorscale="Blues",
                    colorbar=dict(title="Jumlah Edge"),
                    text=ct.values,
                    texttemplate="%{text}",
                )
            )
            heat.update_layout(
                title=f"Matriks Kategori Edge: {attr_choice} (Node U vs Node V)",
                xaxis_title=f"{attr_choice} Node V",
                yaxis_title=f"{attr_choice} Node U",
                height=430,
                template="plotly_white",
            )
            st.plotly_chart(heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            same_ratio = float(np.mean(df_edges[cu].astype(str).values == df_edges[cv].astype(str).values))
            pie_df = pd.DataFrame(
                [
                    {"Kondisi Edge": "Kategori Sama", "Proporsi": same_ratio},
                    {"Kondisi Edge": "Kategori Berbeda", "Proporsi": 1.0 - same_ratio},
                ]
            )
            fig_pie = px.pie(
                pie_df,
                names="Kondisi Edge",
                values="Proporsi",
                color="Kondisi Edge",
                color_discrete_sequence=["#1d4ed8", "#93c5fd"],
                hole=0.55,
                title=f"Komposisi Edge Sama vs Berbeda - {attr_choice}",
            )
            st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            st.caption(
                "Semakin besar porsi 'Kategori Sama', biasanya r attribute cenderung makin positif."
            )

    montes_res = compute_montes_within_between_assortativity(
        G,
        category_attr="kategori_ikr_code",
        group_attr="cluster",
        invalid_category_values={0},
    )
    q_w_star = float(montes_res["q_w_star"])
    q_b_star = float(montes_res["q_b_star"])

    with tab_montes:
        st.markdown("#### Within-Between Assortativity (Montes) dengan Kategori BPS")
        st.markdown(
            "<div class='soft-card'><b>Pembeda Inti Audit vs BPS:</b><br>"
            "<b>Within-Between Audit</b> di sini dihitung per atribut kebijakan/spasial (Bansos, Internet, Ponsel, Dusun). "
            "Artinya category_attr berubah sesuai atribut yang diaudit.<br>"
            "<b>Within-Between BPS</b> dihitung khusus dari kategori IKD BPS (kategori_ikr_code), "
            "sehingga fokusnya stratifikasi kesejahteraan, bukan atribut program tertentu."
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Ringkasnya: pada audit, r = kekuatan keterkaitan atribut dengan graf base; "
            "Qw*/Qb* = pemisahan pola intra vs inter klaster."
        )
        with st.expander("Langkah Hitung Within-Between (Detail)", expanded=False):
            st.markdown("1. Tetapkan `x` = kategori IKD (BPS), dan `h` = klaster.")
            st.markdown("2. Pisahkan kontribusi edge dalam-klaster (within) dan antar-klaster (between).")
            st.markdown("3. Hitung skor mentah Qw, Qb lalu normalisasi jadi Qw*, Qb*.")
            st.markdown("4. Interpretasikan: Qw* tinggi = homogen dalam klaster; Qb* tinggi = homogen antar-klaster.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Qw*", f"{q_w_star:.5f}")
        m2.metric("Qb*", f"{q_b_star:.5f}")
        m3.metric("m_w", f"{float(montes_res['m_w']):.4f}")
        m4.metric("m_b", f"{float(montes_res['m_b']):.4f}")
        df_montes = pd.DataFrame(
            [
                {"Komponen": "Qw* (Within)", "Nilai": q_w_star},
                {"Komponen": "Qb* (Between)", "Nilai": q_b_star},
            ]
        )
        fig_montes = px.bar(
            df_montes,
            x="Komponen",
            y="Nilai",
            color="Nilai",
            color_continuous_scale="Blues",
            title="Skor Normalized Within-Between Assortativity",
        )
        fig_montes.add_hline(y=0.0, line_dash="dash", line_color="#475569")
        st.plotly_chart(fig_montes, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        wb_compare_df = pd.DataFrame(
            [
                {"Kelompok": "Audit (Rata-rata 4 atribut)", "Komponen": "Qw*", "Nilai": audit_qw_mean},
                {"Kelompok": "Audit (Rata-rata 4 atribut)", "Komponen": "Qb*", "Nilai": audit_qb_mean},
                {"Kelompok": "BPS (Kategori IKD)", "Komponen": "Qw*", "Nilai": q_w_star},
                {"Kelompok": "BPS (Kategori IKD)", "Komponen": "Qb*", "Nilai": q_b_star},
            ]
        )
        fig_wb_cmp = px.bar(
            wb_compare_df,
            x="Kelompok",
            y="Nilai",
            color="Komponen",
            barmode="group",
            color_discrete_sequence=["#1d4ed8", "#93c5fd"],
            title="Perbandingan Within-Between: Audit vs BPS",
        )
        fig_wb_cmp.add_hline(y=0.0, line_dash="dash", line_color="#475569")
        st.plotly_chart(fig_wb_cmp, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(wb_compare_df, use_container_width=True)
        fig_quad = go.Figure()
        fig_quad.add_shape(type="line", x0=-1, x1=1, y0=0, y1=0, line=dict(color="#64748b", dash="dash"))
        fig_quad.add_shape(type="line", x0=0, x1=0, y0=-1, y1=1, line=dict(color="#64748b", dash="dash"))
        fig_quad.add_annotation(x=0.55, y=0.75, text="Within kuat<br>Between kuat", showarrow=False, font=dict(size=11, color="#1e3a8a"))
        fig_quad.add_annotation(x=-0.55, y=0.75, text="Within kuat<br>Between lemah", showarrow=False, font=dict(size=11, color="#1e3a8a"))
        fig_quad.add_annotation(x=0.55, y=-0.75, text="Within lemah<br>Between kuat", showarrow=False, font=dict(size=11, color="#1e3a8a"))
        fig_quad.add_annotation(x=-0.55, y=-0.75, text="Within lemah<br>Between lemah", showarrow=False, font=dict(size=11, color="#1e3a8a"))
        fig_quad.add_trace(
            go.Scatter(
                x=[q_b_star],
                y=[q_w_star],
                mode="markers+text",
                marker=dict(size=14, color="#1d4ed8"),
                text=[f"(Qb*={q_b_star:.3f}, Qw*={q_w_star:.3f})"],
                textposition="top center",
                name="Posisi Hasil",
            )
        )
        fig_quad.update_layout(
            title="Peta Interpretasi Within-Between (sumbu X=Qb*, Y=Qw*)",
            xaxis_title="Qb* (Between)",
            yaxis_title="Qw* (Within)",
            xaxis=dict(range=[-1, 1]),
            yaxis=dict(range=[-1, 1]),
            height=430,
            template="plotly_white",
        )
        st.plotly_chart(fig_quad, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        if q_w_star >= 0.30 and q_b_star >= 0.30:
            montes_note = "Homogenitas kuat baik intra maupun antar-klaster."
        elif q_w_star >= 0.30 and q_b_star < 0.10:
            montes_note = "Homogenitas kuat di dalam klaster, melemah antar-klaster."
        elif q_w_star < 0.10 and q_b_star >= 0.30:
            montes_note = "Dalam klaster campuran, tetapi antar-klaster cenderung mirip."
        else:
            montes_note = "Pola within-between cenderung campuran/netral."
        st.markdown(
            f"<div class='soft-card'><b>Interpretasi Cepat Montes:</b><br>"
            f"Qw* menunjukkan homogenitas kategori dalam klaster; Qb* menunjukkan homogenitas kategori antar-klaster.<br>"
            f"Hasil saat ini: <b>{montes_note}</b></div>",
            unsafe_allow_html=True,
        )

    with tab_ringkas:
        top_num = df_num.iloc[df_num["r"].abs().idxmax()]
        top_attr = df_attr.iloc[df_attr["r"].abs().idxmax()]
        st.markdown(
            f"<div class='soft-card'><b>Ringkasan Otomatis Assortativity:</b><br>"
            f"Numeric paling dominan: <b>{top_num['Metrik']}</b> dengan r=<b>{float(top_num['r']):.4f}</b> "
            f"({top_num['Arah']} | {top_num['Kekuatan']}).<br><br>"
            f"Attribute paling dominan: <b>{top_attr['Metrik']}</b> dengan r=<b>{float(top_attr['r']):.4f}</b> "
            f"({top_attr['Arah']} | {top_attr['Kekuatan']}).<br><br>"
            f"Within-Between BPS: Qw*=<b>{q_w_star:.4f}</b>, Qb*=<b>{q_b_star:.4f}</b>."
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Checklist Membaca Hasil (Praktis)")
        st.markdown(
            "1. Lihat tanda `r`: positif (homogen), negatif (heterogen), sekitar nol (campuran)."
        )
        st.markdown(
            "2. Lihat besar `|r|`: semakin besar semakin kuat pola pemilahannya."
        )
        st.markdown(
            "3. Bandingkan `Qw*` vs `Qb*`: apakah pemilahan dominan di dalam klaster atau juga lintas klaster."
        )
        st.dataframe(df_num, use_container_width=True)
        st.dataframe(df_attr, use_container_width=True)


def render_centrality_methods_page(
    n_nodes=80,
    threshold=0.30,
    seed=42,
):
    st.markdown("<h1 class='main-header'>Halaman Metode Centrality (Simulasi Pseudo)</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='premium-hero'><b>Fokus Halaman:</b> Menjelaskan logika centrality pada graf hasil Louvain: "
        "<b>Degree, Betweenness, Closeness, dan Eigenvector</b>.</div>",
        unsafe_allow_html=True,
    )

    tab_alur, tab_rumus, tab_sim, tab_out = st.tabs(
        ["Alur Centrality", "Rumus Matematis", "Simulasi Graf Pseudo", "Output & Interpretasi"]
    )

    with tab_alur:
        flow_df = pd.DataFrame(
            [
                {"Tahap": "Input Graf Louvain", "Deskripsi": "Gunakan graf berbobot hasil proses pembobotan dan Louvain."},
                {"Tahap": "Pilih Metrik", "Deskripsi": "Pilih Degree / Betweenness / Closeness / Eigenvector."},
                {"Tahap": "Hitung Skor Node", "Deskripsi": "Setiap node mendapat nilai centrality sesuai metrik terpilih."},
                {"Tahap": "Peringkat Node", "Deskripsi": "Urutkan node dari nilai centrality tertinggi ke terendah."},
                {"Tahap": "Analisis Segmentasi", "Deskripsi": "Bandingkan top node per klaster Louvain dan per dusun."},
                {"Tahap": "Output", "Deskripsi": "Graf visual (ukuran/warna node) + tabel top node untuk keputusan audit."},
            ]
        )
        fig_flow = px.funnel(
            flow_df,
            y="Tahap",
            x=[1] * len(flow_df),
            title="Tahapan Analisis Centrality di Graf Hasil Louvain",
        )
        fig_flow.update_traces(
            marker_color="#1d4ed8",
            text=flow_df["Deskripsi"],
            textposition="inside",
            texttemplate="<b>%{y}</b><br>%{text}",
            insidetextfont=dict(size=12, color="#ffffff"),
        )
        fig_flow.update_layout(height=620, template="plotly_white", xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_flow, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
        st.dataframe(flow_df, use_container_width=True)

    with tab_rumus:
        st.markdown("#### 1) Degree Centrality (weighted degree)")
        st.latex(r"C_D(i) = \sum_{j=1}^{N} A_{ij}")
        st.caption("Makna praktis: node dengan koneksi langsung paling banyak/kuat akan bernilai tinggi.")

        st.markdown("#### 2) Betweenness Centrality")
        st.latex(r"C_B(i) = \sum_{j\neq k \in V}\frac{\sigma_{jk}(i)}{\sigma_{jk}}")
        st.caption("Makna praktis: node penghubung antarbagian graf (broker/jembatan) akan bernilai tinggi.")

        st.markdown("#### 3) Closeness Centrality")
        st.latex(r"C_C(i)=\frac{1}{\sum_{j\in V}\mathrm{dist}(i,j)}")
        st.caption("Makna praktis: node yang rata-rata jaraknya paling dekat ke node lain akan bernilai tinggi.")

        st.markdown("#### 4) Eigenvector Centrality")
        st.latex(r"\lambda_{\max}\mathbf{E}=A\mathbf{E}, \quad C_E(i)=\frac{E_i}{\|\mathbf{E}\|}")
        st.caption("Makna praktis: node penting jika terhubung ke node-node penting lainnya.")

    rng = np.random.default_rng(int(seed))
    n_nodes = int(max(30, n_nodes))
    cluster_count = 3
    node_ids = [f"CT_{i+1:03d}" for i in range(n_nodes)]
    G = nx.Graph()
    rows = []
    for i, nid in enumerate(node_ids):
        cid = int(i % cluster_count)
        base = 60 + (cid * 8)
        f_a = float(np.clip(rng.normal(base + 1.0, 2.0), 40, 98))
        f_b = float(np.clip(rng.normal(base + 0.6, 2.2), 40, 98))
        f_c = float(np.clip(rng.normal(base - 0.4, 2.3), 40, 98))
        f_d = float(np.clip(rng.normal(base + 0.9, 2.1), 40, 98))
        f_e = float(np.clip(rng.normal(base + 0.2, 2.4), 40, 98))
        f_ikr = float(np.mean([f_a, f_b, f_c, f_d, f_e]))
        dusun = f"Dusun-{cid+1}"
        rows.append(
            {
                "family_id": nid,
                "nama": f"Keluarga {i+1}",
                "f_a_dari_rekap_kk": f_a,
                "f_b_dari_rekap_kk": f_b,
                "f_c_dari_rekap_kk": f_c,
                "f_d_dari_rekap_kk": f_d,
                "f_e_dari_rekap_kk": f_e,
                "f_ikr_dari_rekap_kk": f_ikr,
                "dusun": dusun,
                "cluster": cid,
            }
        )
    pseudo_df = pd.DataFrame(rows)
    for _, r in pseudo_df.iterrows():
        G.add_node(r["family_id"], **r.to_dict())
    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            ui, uj = node_ids[i], node_ids[j]
            ai, aj = G.nodes[ui], G.nodes[uj]
            vi = np.array(
                [
                    ai["f_a_dari_rekap_kk"],
                    ai["f_b_dari_rekap_kk"],
                    ai["f_c_dari_rekap_kk"],
                    ai["f_d_dari_rekap_kk"],
                    ai["f_e_dari_rekap_kk"],
                ],
                dtype=float,
            )
            vj = np.array(
                [
                    aj["f_a_dari_rekap_kk"],
                    aj["f_b_dari_rekap_kk"],
                    aj["f_c_dari_rekap_kk"],
                    aj["f_d_dari_rekap_kk"],
                    aj["f_e_dari_rekap_kk"],
                ],
                dtype=float,
            )
            sim = float(compute_cosine_similarity(vi, vj))
            if sim >= float(threshold):
                G.add_edge(ui, uj, weight=sim)
    if G.number_of_edges() == 0:
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                ui, uj = node_ids[i], node_ids[j]
                ai, aj = G.nodes[ui], G.nodes[uj]
                vi = np.array(
                    [
                        ai["f_a_dari_rekap_kk"],
                        ai["f_b_dari_rekap_kk"],
                        ai["f_c_dari_rekap_kk"],
                        ai["f_d_dari_rekap_kk"],
                        ai["f_e_dari_rekap_kk"],
                    ],
                    dtype=float,
                )
                vj = np.array(
                    [
                        aj["f_a_dari_rekap_kk"],
                        aj["f_b_dari_rekap_kk"],
                        aj["f_c_dari_rekap_kk"],
                        aj["f_d_dari_rekap_kk"],
                        aj["f_e_dari_rekap_kk"],
                    ],
                    dtype=float,
                )
                sim = float(compute_cosine_similarity(vi, vj))
                if sim >= 0.20:
                    G.add_edge(ui, uj, weight=sim)

    if G.number_of_edges() > 0:
        partition = community_louvain.best_partition(G, weight="weight", random_state=int(seed))
        nx.set_node_attributes(G, partition, "cluster")
    else:
        partition = {n: 0 for n in G.nodes()}
        nx.set_node_attributes(G, partition, "cluster")

    deg_vals = compute_centrality_on_similarity_graph(G, "degree")
    bet_vals = compute_centrality_on_similarity_graph(G, "betweenness")
    clo_vals = compute_centrality_on_similarity_graph(G, "closeness")
    eig_vals = compute_centrality_on_similarity_graph(G, "eigenvector")

    with tab_sim:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Node", f"{int(G.number_of_nodes())}")
        c2.metric("Edge", f"{int(G.number_of_edges())}")
        c3.metric("Threshold Similarity", f"{float(threshold):.2f}")
        c4.metric("Jumlah Klaster Louvain", f"{int(len(set(partition.values())))}")

        pos = nx.spring_layout(G, seed=int(seed), weight="weight")
        nodes = list(G.nodes())
        size_vals = [9.0 + (22.0 * float(deg_vals.get(n, 0.0)) / max(max(deg_vals.values()) if deg_vals else 1.0, 1e-9)) for n in nodes]
        fig_graph = go.Figure()
        for u, v, d in G.edges(data=True):
            cu = int(partition.get(u, 0))
            cv = int(partition.get(v, 0))
            edge_weight = _safe_float_metric(d.get("weight"), 0.0)
            edge_color = (
                rgba_from_hex(CONTRAST_COLORS[cu % len(CONTRAST_COLORS)], 0.44)
                if cu == cv
                else rgba_from_hex(CONTRAST_COLORS[((cu + 1) * 7 + (cv + 1) * 13) % len(CONTRAST_COLORS)], 0.32)
            )
            fig_graph.add_trace(
                go.Scatter(
                    x=[pos[u][0], pos[v][0], None],
                    y=[pos[u][1], pos[v][1], None],
                    mode="lines",
                    line=dict(width=1.0 + (1.6 * edge_weight), color=edge_color),
                    hoverinfo="none",
                    showlegend=False,
                )
            )
        fig_graph.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in nodes],
                y=[pos[n][1] for n in nodes],
                mode="markers",
                marker=dict(
                    size=size_vals,
                    color=[float(eig_vals.get(n, 0.0)) for n in nodes],
                                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Eigenvector"),
                    line=dict(color=NETWORK_NODE_LINE, width=0.7),
                ),
                text=[
                    f"Node: {n}<br>Klaster: {int(partition.get(n, 0))}"
                    f"<br>Degree: {float(deg_vals.get(n, 0.0)):.4f}"
                    f"<br>Betweenness: {float(bet_vals.get(n, 0.0)):.4f}"
                    f"<br>Closeness: {float(clo_vals.get(n, 0.0)):.4f}"
                    f"<br>Eigenvector: {float(eig_vals.get(n, 0.0)):.4f}"
                    for n in nodes
                ],
                hoverinfo="text",
                showlegend=False,
            )
        )
        fig_graph.update_layout(
            title="Graf Pseudo Centrality (ukuran = Degree, warna = Eigenvector)",
            height=560,
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        st.plotly_chart(fig_graph, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

    with tab_out:
        df_cent = pd.DataFrame(
            [
                {
                    "family_id": n,
                    "Klaster Louvain": int(partition.get(n, 0)),
                    "Dusun": G.nodes[n].get("dusun", "-"),
                    "Degree": float(deg_vals.get(n, 0.0)),
                    "Betweenness": float(bet_vals.get(n, 0.0)),
                    "Closeness": float(clo_vals.get(n, 0.0)),
                    "Eigenvector": float(eig_vals.get(n, 0.0)),
                }
                for n in G.nodes()
            ]
        ).sort_values("Degree", ascending=False).reset_index(drop=True)
        st.markdown("#### Top 10 Node per Metrik")
        m1, m2 = st.columns(2)
        with m1:
            st.caption("Top 10 Degree")
            st.dataframe(df_cent.sort_values("Degree", ascending=False).head(10), use_container_width=True)
            st.caption("Top 10 Betweenness")
            st.dataframe(df_cent.sort_values("Betweenness", ascending=False).head(10), use_container_width=True)
        with m2:
            st.caption("Top 10 Closeness")
            st.dataframe(df_cent.sort_values("Closeness", ascending=False).head(10), use_container_width=True)
            st.caption("Top 10 Eigenvector")
            st.dataframe(df_cent.sort_values("Eigenvector", ascending=False).head(10), use_container_width=True)

        st.markdown("#### Ringkasan per Klaster")
        df_cluster = (
            df_cent.groupby("Klaster Louvain", as_index=False)
            .agg(
                Jumlah_Node=("family_id", "count"),
                Rerata_Degree=("Degree", "mean"),
                Rerata_Betweenness=("Betweenness", "mean"),
                Rerata_Closeness=("Closeness", "mean"),
                Rerata_Eigenvector=("Eigenvector", "mean"),
            )
            .sort_values("Klaster Louvain")
            .reset_index(drop=True)
        )
        st.dataframe(df_cluster, use_container_width=True)
        st.caption(
            "Cara baca sederhana: Degree tinggi = pusat interaksi lokal; Betweenness tinggi = node jembatan; "
            "Closeness tinggi = cepat menjangkau node lain; Eigenvector tinggi = penting karena terhubung ke node penting."
        )


# =========================================================
# 3. SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    logo_col, title_col = st.columns([1, 3], gap="small")
    with logo_col:
        logo_data_uri = get_logo_data_uri(LOGO_PATH)
        logo_inner_html = (
            f"<img src='{logo_data_uri}' class='sidebar-logo-img' alt='Logo SNA' />"
            if logo_data_uri
            else "<div class='sidebar-logo-fallback'>SNA</div>"
        )
        st.markdown(
            f"<div class='sidebar-logo-shell'><div class='sidebar-logo-disc'>{logo_inner_html}</div></div>",
            unsafe_allow_html=True,
        )
    with title_col:
        st.markdown(
            "<div style='padding-top:8px; font-size:1.05rem; font-weight:700; color:#E5E7EB;'>SNA Data Desa Presisi</div>",
            unsafe_allow_html=True,
        )
page_mode = st.sidebar.radio(
    "Pilih Halaman",
    [
        "Dashboard Audit",
        "Rangkuman Threshold Otomatis",
        "Analisis Centrality",
        "Profil Klaster Louvain",
        "Analisis Bansos Spasial",
        "Metode Pembobotan",
        "Metode Louvain",
        "Metode Assortativity",
        "Metode Centrality",
        "Ringkasan Jurnal Q1",
    ],
    index=0,
)
st.sidebar.caption(f"Mode aktif: {page_mode}")
uploaded_file = st.sidebar.file_uploader("Unggah Database Pengganti", type=['csv', 'xlsx'])
default_data_exists = os.path.exists(DEFAULT_DATA_PATH)
active_data_source = uploaded_file if uploaded_file is not None else (DEFAULT_DATA_PATH if default_data_exists else None)
if uploaded_file is not None:
    st.sidebar.success(f"Data aktif: {uploaded_file.name}")
elif default_data_exists:
    st.sidebar.info(f"Data aktif default: {DEFAULT_DATA_PATH}")
else:
    st.sidebar.warning(f"Data default tidak ditemukan: {DEFAULT_DATA_PATH}")
render_global_header()

if page_mode == "Metode Louvain" and active_data_source is None:
    render_louvain_methods_page(n_nodes=60, rounding_decimals=2, threshold=0.30, seed=42)
    st.stop()
if page_mode == "Analisis Bansos Spasial" and active_data_source is None:
    st.markdown("<h1 class='main-header'>Analisis Bansos Spasial</h1>", unsafe_allow_html=True)
    st.info("Data default belum tersedia. Unggah database desa terlebih dahulu untuk menampilkan peta ArcGIS analisis bansos.")
    st.stop()
if page_mode == "Rangkuman Threshold Otomatis" and active_data_source is None:
    st.markdown("<h1 class='main-header'>Rangkuman Threshold Otomatis</h1>", unsafe_allow_html=True)
    st.info("Data default belum tersedia. Unggah database desa terlebih dahulu untuk menjalankan sensitivity analysis threshold otomatis.")
    st.stop()
if page_mode == "Analisis Centrality" and active_data_source is None:
    st.markdown("<h1 class='main-header'>Analisis Centrality</h1>", unsafe_allow_html=True)
    st.info("Data default belum tersedia. Unggah database desa terlebih dahulu untuk menampilkan analisis centrality berbasis jaringan Louvain.")
    st.stop()
if page_mode == "Profil Klaster Louvain" and active_data_source is None:
    st.markdown("<h1 class='main-header'>Profil Karakteristik Klaster Louvain</h1>", unsafe_allow_html=True)
    st.info("Data default belum tersedia. Unggah database desa terlebih dahulu untuk menampilkan profil karakteristik klaster Louvain.")
    st.stop()
if page_mode == "Ringkasan Jurnal Q1" and active_data_source is None:
    st.markdown("<h1 class='main-header'>Ringkasan Temuan untuk Jurnal Q1</h1>", unsafe_allow_html=True)
    st.info(
        "Halaman ini menyusun temuan siap-publikasi (novelty, metode, hasil kunci, robustness, implikasi) "
        "secara otomatis dari data. Unggah database desa terlebih dahulu untuk menjalankannya."
    )
    st.stop()
if page_mode == "Metode Pembobotan" and active_data_source is None:
    render_weighting_methods_page(
        df_v=pd.DataFrame(),
        edge_feature_cols=EDGE_REKAP_COLS,
        rounding_decimals=2,
        threshold_grid=[round(x, 1) for x in np.arange(0.1, 1.0, 0.1)],
        sample_max_nodes=120,
    )
    st.stop()
if page_mode == "Metode Assortativity" and active_data_source is None:
    render_assortativity_methods_page(n_nodes=90, seed=42)
    st.stop()
if page_mode == "Metode Centrality" and active_data_source is None:
    render_centrality_methods_page(n_nodes=80, threshold=0.30, seed=42)
    st.stop()

if active_data_source is not None:
    df_kk = load_and_clean_ddp(active_data_source)
    if df_kk is None or df_kk.empty:
        st.stop()
    col_desa = 'deskel' if 'deskel' in df_kk.columns else 'desa'
    col_spasial = 'dusun' if 'dusun' in df_kk.columns else 'rt'
    show_map_edges = True
    selected_centrality_key = "none"
    graph_spatial_mode = "Layout Jaringan"

    with st.sidebar:
        selected_desa = st.selectbox("Pilih Desa", sorted(df_kk[col_desa].unique()))
        basis_candidates = [
            ("IKD Rekap KK", "f_ikr_dari_rekap_kk"),
            ("IPM Mikro", "ipm_mikro"),
            ("Ekonomi", "indeks_pengeluaran"),
            ("Kesehatan", "indeks_kesehatan"),
            ("Pendidikan", "indeks_pendidikan"),
        ]
        available_basis = []
        for label, col in basis_candidates:
            if col in df_kk.columns:
                available_basis.append((label, col))
        if not available_basis:
            numeric_cols = []
            for c in df_kk.columns:
                s = pd.to_numeric(df_kk[c], errors="coerce")
                if s.notna().sum() >= max(3, int(0.2 * len(df_kk))):
                    numeric_cols.append(c)
            available_basis = [(f"Kolom Numerik: {c}", c) for c in numeric_cols[:10]]
        if not available_basis:
            st.error("Tidak ada kolom numerik yang bisa dijadikan basis jaringan.")
            st.stop()
        onehot_round_decimals = st.selectbox(
            "Pembulatan One-Hot",
            options=[0, 2, 1],
            format_func=lambda d: "Bilangan bulat (tanpa koma)" if d == 0 else f"{d} angka di belakang koma",
            index=0,
        )
        threshold_grid = [round(x, 1) for x in np.arange(0.1, 1.0, 0.1)]

        if page_mode in {"Dashboard Audit", "Rangkuman Threshold Otomatis", "Analisis Centrality", "Profil Klaster Louvain", "Ringkasan Jurnal Q1"}:
            basis_col = st.selectbox("Basis Jaringan", available_basis, format_func=lambda x: x[0])[1]
            weighting_mode = st.selectbox(
                "Metode Pembobotan Graf",
                options=[
                    ("Cosine Similarity", "cosine"),
                    ("Jaccard Index", "jaccard"),
                    ("Pearson Correlation", "pearson"),
                ],
                format_func=lambda x: x[0],
            )[1]
            if page_mode in {"Rangkuman Threshold Otomatis", "Analisis Centrality", "Profil Klaster Louvain", "Ringkasan Jurnal Q1"}:
                auto_threshold_mode = True
                threshold_val = 0.40
                if page_mode == "Rangkuman Threshold Otomatis":
                    st.caption("Halaman ini menjalankan threshold otomatis dan membandingkan seluruh kandidat ambang.")
                elif page_mode == "Analisis Centrality":
                    st.caption("Halaman ini memakai graf Louvain yang sama, lalu fokus pada centrality dan interpretasi kebijakan.")
                elif page_mode == "Ringkasan Jurnal Q1":
                    st.caption("Halaman ini merangkum seluruh temuan siap-publikasi Q1 dari graf, klaster, assortativity, dan penargetan bansos.")
                else:
                    st.caption("Halaman ini memakai graf Louvain yang sama, lalu merangkum karakteristik sosial-kesejahteraan tiap klaster.")
            else:
                threshold_mode = st.radio("Mode Threshold", ["Otomatis (Distribusi)", "Manual"], index=0)
                auto_threshold_mode = threshold_mode.startswith("Otomatis")
                if auto_threshold_mode:
                    threshold_val = 0.40
                else:
                    threshold_val = st.slider("Threshold Manual", 0.1, 0.9, 0.4, 0.1)
                    st.caption("Threshold manual aktif: edge dibentuk jika similarity >= threshold.")
            comp_mode = st.radio("Mode Komponen", ["LCC only", "Semua komponen"], index=0, help="LCC only menganalisis komponen terbesar saja.")
            lcc_only = comp_mode == "LCC only"
            if page_mode in {"Analisis Centrality", "Profil Klaster Louvain"}:
                layout_spread = st.slider(
                    "Sebaran Layout Jaringan",
                    min_value=1.0,
                    max_value=3.4,
                    value=2.2,
                    step=0.1,
                    help="Semakin besar nilai ini, jarak visual antarklaster makin renggang.",
                )
                graph_spatial_mode = "Layout Jaringan"
                if page_mode == "Analisis Centrality":
                    selected_centrality_key = st.selectbox(
                        "Metrik Centrality",
                        options=[
                            ("Degree Centrality", "degree"),
                            ("Betweenness Centrality", "betweenness"),
                            ("Closeness Centrality", "closeness"),
                            ("Eigenvector Centrality", "eigenvector"),
                        ],
                        format_func=lambda x: x[0],
                        index=0,
                    )[1]
                else:
                    selected_centrality_key = "degree"
            elif page_mode == "Dashboard Audit":
                layout_spread = st.slider(
                    "Sebaran Layout Jaringan",
                    min_value=1.0,
                    max_value=3.4,
                    value=2.2,
                    step=0.1,
                    help="Semakin besar nilai ini, jarak visual antarklaster makin renggang.",
                )
                selected_dim_key = st.selectbox(
                    "Drill-Down Dimensi",
                    options=list(DRILLDOWN_DIMENSIONS.keys()),
                    format_func=lambda k: DRILLDOWN_DIMENSIONS[k]["label"],
                )
                selected_graph_dim = st.selectbox(
                    "Visual Jaringan Dimensi Kesejahteraan",
                    options=[IKD_OVERALL_METRIC] + list(IKD_DIMENSION_MAP),
                    format_func=lambda x: f"{x[0]} ({x[1]})",
                )
                graph_spatial_mode = st.selectbox(
                    "Mode Visualisasi Jaringan",
                    options=["Layout Jaringan", "Spasial OSM", "Spasial ArcGIS"],
                    index=0,
                    help="Jika memilih mode spasial, node ditampilkan di peta berdasarkan lat/lon tanpa edge.",
                )
                selected_centrality_key = "none"
                st.caption("Analisis centrality dipisahkan ke halaman khusus: Analisis Centrality.")
        elif page_mode == "Analisis Bansos Spasial":
            basis_col = st.selectbox("Basis Jaringan", available_basis, format_func=lambda x: x[0])[1]
            weighting_mode = st.selectbox(
                "Metode Pembobotan Graf",
                options=[
                    ("Cosine Similarity", "cosine"),
                    ("Jaccard Index", "jaccard"),
                    ("Pearson Correlation", "pearson"),
                ],
                format_func=lambda x: x[0],
                index=0,
            )[1]
            threshold_mode = st.radio("Mode Threshold", ["Otomatis (Distribusi)", "Manual"], index=0)
            auto_threshold_mode = threshold_mode.startswith("Otomatis")
            if auto_threshold_mode:
                threshold_val = 0.40
            else:
                threshold_val = st.slider("Threshold Manual", 0.1, 0.9, 0.4, 0.1)
            comp_mode = st.radio("Mode Komponen", ["LCC only", "Semua komponen"], index=0)
            lcc_only = comp_mode == "LCC only"
            graph_spatial_mode = st.selectbox(
                "Basemap Spasial",
                options=["Spasial ArcGIS", "Spasial OSM"],
                index=0,
            )
            selected_bansos_dimension = st.selectbox(
                "Dimensi Analisis Bansos",
                options=[col for _, col in IKD_DIMENSION_MAP],
                format_func=lambda c: next((label for label, col in IKD_DIMENSION_MAP if col == c), c),
            )
            bansos_map_color_mode = st.selectbox(
                "Warna Node Peta",
                options=["IKD Agregat", "Status Bansos (YA/TIDAK)", "Status BPS-Bansos"],
                index=0,
            )
            bansos_filter_mode = st.selectbox(
                "Filter Node di Peta",
                options=[
                    "Semua KK",
                    "Penerima Bansos",
                    "Rendah - Penerima",
                    "Rendah - Belum Menerima",
                    "Sedang - Penerima",
                    "Sedang - Belum Menerima",
                    "Tinggi - Penerima",
                    "Tinggi - Belum Menerima",
                    "Sangat Tinggi - Penerima",
                    "Sangat Tinggi - Belum Menerima",
                    "Rentan Dimensi Terpilih",
                    "Penerima pada Dimensi Terpilih",
                ],
                index=0,
            )
            st.markdown("**Ambang Skor Tiap Dimensi IKD**")
            bansos_dim_thresholds = {}
            for dim_label, dim_col in IKD_DIMENSION_MAP:
                slider_label = dim_label.split("(", 1)[0].strip()
                bansos_dim_thresholds[dim_col] = st.slider(
                    f"{slider_label}",
                    min_value=0.0,
                    max_value=100.0,
                    value=60.0,
                    step=1.0,
                    help=f"KK dengan skor {slider_label} <= nilai ini ditandai rentan.",
                )
        elif page_mode == "Metode Pembobotan":
            sample_max_nodes = st.slider(
                "Maks Node Simulasi",
                min_value=30,
                max_value=250,
                value=120,
                step=10,
                help="Batas node untuk perbandingan distribusi similarity agar performa tetap ringan.",
            )
        elif page_mode == "Metode Louvain":
            louvain_n_nodes = st.slider(
                "Jumlah Node Pseudo Louvain",
                min_value=30,
                max_value=220,
                value=80,
                step=10,
            )
            louvain_threshold = st.slider(
                "Threshold Graf Base (Pseudo)",
                min_value=0.10,
                max_value=0.90,
                value=0.30,
                step=0.05,
            )
            louvain_seed = st.number_input("Random Seed Louvain", min_value=1, max_value=9999, value=42, step=1)
        elif page_mode == "Metode Assortativity":
            assort_n_nodes = st.slider(
                "Jumlah Node Pseudo Assortativity",
                min_value=40,
                max_value=260,
                value=90,
                step=10,
            )
            assort_seed = st.number_input("Random Seed Assortativity", min_value=1, max_value=9999, value=42, step=1)
        else:
            centrality_n_nodes = st.slider(
                "Jumlah Node Pseudo Centrality",
                min_value=40,
                max_value=260,
                value=80,
                step=10,
            )
            centrality_threshold = st.slider(
                "Threshold Graf Pseudo (Centrality)",
                min_value=0.10,
                max_value=0.90,
                value=0.30,
                step=0.05,
            )
            centrality_seed = st.number_input("Random Seed Centrality", min_value=1, max_value=9999, value=42, step=1)

    # --- PROCESS ---
    if page_mode == "Metode Louvain":
        render_louvain_methods_page(
            n_nodes=louvain_n_nodes,
            rounding_decimals=onehot_round_decimals,
            threshold=louvain_threshold,
            seed=louvain_seed,
        )
        st.stop()
    if page_mode == "Metode Assortativity":
        render_assortativity_methods_page(
            n_nodes=assort_n_nodes,
            seed=assort_seed,
        )
        st.stop()
    if page_mode == "Metode Centrality":
        render_centrality_methods_page(
            n_nodes=centrality_n_nodes,
            threshold=centrality_threshold,
            seed=centrality_seed,
        )
        st.stop()

    df_v = df_kk[df_kk[col_desa] == selected_desa].copy()
    df_v = add_bps_ikr_category(df_v, ikr_col="f_ikr_dari_rekap_kk")

    if page_mode == "Metode Pembobotan":
        render_weighting_methods_page(
            df_v=df_v,
            edge_feature_cols=EDGE_REKAP_COLS,
            rounding_decimals=onehot_round_decimals,
            threshold_grid=threshold_grid,
            sample_max_nodes=sample_max_nodes,
        )
        st.stop()

    res = build_sna_network(
        df_v,
        basis_col,
        threshold_val,
        auto_threshold=auto_threshold_mode,
        lcc_only=lcc_only,
        similarity_method=weighting_mode,
        force_louvain_lcc=lcc_only,
        threshold_grid=threshold_grid,
        edge_feature_cols=EDGE_REKAP_COLS,
        onehot_round_decimals=onehot_round_decimals,
    )

    if res:
        G, partition, cluster_list, meta = res
        if page_mode == "Analisis Bansos Spasial":
            render_bansos_spatial_analysis_page(
                df_v=df_v,
                graph_obj=G,
                partition=partition,
                spatial_mode=graph_spatial_mode,
                selected_dimension_col=selected_bansos_dimension,
                map_color_mode=bansos_map_color_mode,
                filter_mode=bansos_filter_mode,
                dim_thresholds=bansos_dim_thresholds,
            )
            st.stop()
        method_used = meta.get("similarity_method")
        threshold_used = float(meta.get("threshold_selected", threshold_val))
        if method_used == "cosine":
            method_label = "Cosine Similarity"
            kernel_info = "Vektor one-hot dari lima dimensi kesejahteraan"
        elif method_used == "jaccard":
            method_label = "Jaccard Index"
            kernel_info = "Irisan/union fitur aktif dari vektor one-hot lima dimensi kesejahteraan"
        elif method_used == "pearson":
            method_label = "Pearson Correlation"
            kernel_info = "Korelasi antar vektor one-hot lima dimensi kesejahteraan"
        else:
            method_label = str(method_used).upper() if method_used else "-"
            kernel_info = "Metode custom"
        rounding_label = (
            "Bilangan bulat"
            if int(meta.get("onehot_round_decimals", 2)) == 0
            else f"{int(meta.get('onehot_round_decimals', 2))} desimal"
        )
        if page_mode == "Rangkuman Threshold Otomatis":
            st.markdown(f"<h1 class='main-header'>Rangkuman Threshold Otomatis: {selected_desa}</h1>", unsafe_allow_html=True)
            render_auto_threshold_summary(
                meta=meta,
                graph_obj=G,
                partition=partition,
                selected_desa=selected_desa,
                basis_col=basis_col,
                method_label=method_label,
                kernel_info=kernel_info,
                rounding_label=rounding_label,
                compact=False,
            )
            st.stop()
        if page_mode == "Analisis Centrality":
            render_centrality_analysis_page(
                graph_obj=G,
                partition=partition,
                df_v=df_v,
                selected_desa=selected_desa,
                selected_centrality_key=selected_centrality_key,
                col_spasial=col_spasial,
                layout_spread=layout_spread,
            )
            st.stop()
        if page_mode == "Profil Klaster Louvain":
            render_louvain_cluster_profile_page(
                graph_obj=G,
                partition=partition,
                df_v=df_v,
                selected_desa=selected_desa,
                col_spasial=col_spasial,
                layout_spread=layout_spread,
            )
            st.stop()
        if page_mode == "Ringkasan Jurnal Q1":
            render_journal_q1_page(
                graph_obj=G,
                partition=partition,
                df_v=df_v,
                meta=meta,
                selected_desa=selected_desa,
                basis_col=basis_col,
                method_label=method_label,
                threshold_used=threshold_used,
                col_spasial=col_spasial,
            )
            st.stop()

        st.markdown(f"<h1 class='main-header'>Dashboard Master SNA Audit: {selected_desa}</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='premium-hero'><b>Ringkasan Konfigurasi</b><br>"
            f"Basis: <b>{basis_col}</b> | Threshold Kemiripan Terpilih: <b>{threshold_used:.0%} ({threshold_used:.2f})</b> | "
            f"Metode: <b>{method_label}</b> ({kernel_info}) | One-Hot Rounding: <b>{rounding_label}</b> | Komponen: <b>{meta['mode']}</b><br>"
            f"Node dianalisis: <b>{G.number_of_nodes()}</b> (Raw {meta['raw_nodes']}, LCC {meta['lcc_nodes']})"
            f"</div>",
            unsafe_allow_html=True,
        )
        if meta.get("threshold_distribution"):
            with subbab_dropdown("Audit Distribusi Similarity dan Threshold Otomatis", expanded=False):
                c_auto_1, c_auto_2 = st.columns([1.2, 1.0])
                with c_auto_1:
                    sim_vals = meta.get("pairwise_similarity_values", [])
                    if sim_vals:
                        fig_dist = px.histogram(
                            x=sim_vals,
                            nbins=20,
                            title="Distribusi Nilai Similarity Antar-Pasangan Node",
                            labels={"x": "Similarity"},
                        )
                        fig_dist.update_layout(
                            xaxis_title="Similarity",
                            yaxis_title="Frekuensi",
                            template="plotly_white",
                        )
                        fig_dist.add_vline(
                            x=threshold_used,
                            line_width=2,
                            line_dash="dash",
                            line_color="#B91C1C",
                            annotation_text=f"Threshold terpilih {threshold_used:.2f}",
                        )
                        st.plotly_chart(fig_dist, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                with c_auto_2:
                    df_thr = pd.DataFrame(meta["threshold_distribution"]).sort_values("threshold").reset_index(drop=True)
                    if not df_thr.empty:
                        total_edge_kumulatif = int(df_thr["edge_count"].sum())
                        jumlah_kandidat = int(len(df_thr))
                        rata2_edge_umum = float(total_edge_kumulatif / max(jumlah_kandidat, 1))
                        pair_total = int(len(meta.get("pairwise_similarity_values", [])))
                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("Total Pair Kandidat", pair_total)
                        s2.metric("Total Edge Kumulatif", total_edge_kumulatif)
                        s3.metric("Rata-rata Umum (Total/9)", f"{rata2_edge_umum:.2f}")
                        s4.metric("Jumlah Parameter", jumlah_kandidat)

                        fig_thr_cmp = px.line(
                            df_thr,
                            x="threshold",
                            y="edge_count",
                            markers=True,
                            title="Perbandingan Semua Parameter Threshold vs Edge",
                        )
                        fig_thr_cmp.add_hline(
                            y=rata2_edge_umum,
                            line_dash="dash",
                            line_color="#B91C1C",
                            annotation_text=f"Rata-rata umum = {rata2_edge_umum:.2f}",
                        )
                        st.plotly_chart(fig_thr_cmp, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                    thr_selected = round(float(threshold_used), 1)
                    if "threshold" in df_thr.columns:
                        df_thr["threshold"] = df_thr["threshold"].round(1)
                    def _highlight_selected_threshold(row):
                        if float(row.get("threshold", -999)) == thr_selected:
                            return ["background-color: #22c55e; color: #052e16; font-weight: 700;"] * len(row)
                        return [""] * len(row)
                    st.dataframe(
                        df_thr.style.apply(_highlight_selected_threshold, axis=1),
                        use_container_width=True,
                    )
                df_sens_dashboard = get_threshold_sensitivity_dataframe(meta)
                if not df_sens_dashboard.empty:
                    render_threshold_sensitivity_heatmap(df_sens_dashboard)
        with subbab_dropdown("Alur Jaringan: Pembentukan Base Graph, Louvain, dan Audit", expanded=True):
            c_base = st.columns(4)
            with c_base[0]:
                st.metric("Node", G.number_of_nodes())
            with c_base[1]:
                st.metric("Edge", G.number_of_edges())
            with c_base[2]:
                st.metric("Density", f"{nx.density(G):.4f}")
            with c_base[3]:
                st.metric("Komponen", nx.number_connected_components(G))

            modularity_focus = _safe_float_metric(community_louvain.modularity(partition, G, weight="weight"), default=0.0)
            c_louv = st.columns(3)
            with c_louv[0]:
                st.metric("Jumlah Klaster Louvain", len(set(partition.values())))
            with c_louv[1]:
                st.metric("Modularity Q", f"{modularity_focus:.4f}")
            with c_louv[2]:
                st.metric("Threshold Terpilih", f"{threshold_used:.2f}")

            n_nodes_layout = max(G.number_of_nodes(), 2)
            pos_focus = build_clustered_network_layout(
                G,
                partition=partition,
                layout_spread=layout_spread,
                seed=42,
            )
            edge_weights = [_safe_float_metric(d.get("weight"), default=0.0) for _, _, d in G.edges(data=True)]
            edge_min = float(min(edge_weights)) if edge_weights else 0.0
            edge_max = float(max(edge_weights)) if edge_weights else 1.0
            edge_span = max(edge_max - edge_min, 1e-9)
            visible_edge_limit = int(np.clip(n_nodes_layout * 1.45, 180, 950))
            visible_edges_focus = select_representative_edges(
                G,
                max_edges=visible_edge_limit,
                per_node=1,
            )
            node_size_main = network_marker_size(n_nodes_layout, base=9.0)
            node_line_width = 0.42 if n_nodes_layout >= 300 else 0.6
            cluster_ids_sorted = sorted(set(partition.values()))
            # Palet diskret yang ramah cetak dan tetap kontras untuk publikasi akademik.
            cluster_palette_base = [
                "#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9", "#E69F00",
                "#332288", "#88CCEE", "#44AA99", "#117733", "#999933", "#882255",
                "#AA4499", "#DDCC77", "#CC6677", "#6699CC", "#661100", "#999999",
            ] + px.colors.qualitative.Dark24 + px.colors.qualitative.Alphabet
            cluster_palette = cluster_palette_base[:len(cluster_ids_sorted)]
            cid_to_idx = {cid: idx for idx, cid in enumerate(cluster_ids_sorted)}

            def build_discrete_colorscale(colors):
                if len(colors) <= 1:
                    c = colors[0] if colors else "#b91c1c"
                    return [[0.0, c], [1.0, c]]
                n = len(colors)
                cs = []
                for i, c in enumerate(colors):
                    start = i / n
                    end = (i + 1) / n
                    cs.append([start, c])
                    cs.append([end, c])
                return cs

            cluster_colorscale = build_discrete_colorscale(cluster_palette)
            node_ids = list(G.nodes())
            cluster_color_map = {cid: cluster_palette[cid_to_idx.get(cid, 0)] for cid in cluster_ids_sorted}
            edge_weight_palette = ["#B91C1C", "#D97706", "#0F766E", "#2563EB"]

            def edge_color_by_weight(_u, _v, _d=None, w_norm=0.0):
                color_idx = int(np.clip(np.floor(float(w_norm) * len(edge_weight_palette)), 0, len(edge_weight_palette) - 1))
                return rgba_from_hex(edge_weight_palette[color_idx], 0.36)

            def edge_color_by_interaction(u, v, _d=None, _w_norm=0.0):
                cu = partition.get(u, -1)
                cv = partition.get(v, -1)
                if cu == cv:
                    return rgba_from_hex(cluster_color_map.get(cu, "#64748b"), 0.46)
                iu, iv = sorted([cid_to_idx.get(cu, 0), cid_to_idx.get(cv, 0)])
                pair_idx = ((iu + 1) * 7 + (iv + 1) * 13) % len(CONTRAST_COLORS)
                return rgba_from_hex(CONTRAST_COLORS[pair_idx], 0.34)

            def node_meta(nid):
                n_attr = G.nodes[nid]
                nama = n_attr.get("nama", "-")
                usia = n_attr.get("usia", n_attr.get("usia (y)", "-"))
                profesi = n_attr.get("profesi pekerjaan", n_attr.get("profesi_pekerjaan", "-"))
                f_ikr = n_attr.get("f_ikr_dari_rekap_kk", "-")
                cluster_id = partition.get(nid, -1)
                return [str(nama), str(usia), str(profesi), str(f_ikr), int(cluster_id)]

            node_customdata = [node_meta(n) for n in node_ids]

            fig_base = go.Figure()
            add_network_edge_traces(
                fig_base,
                visible_edges_focus,
                pos_focus,
                edge_min,
                edge_span,
                color_fn=edge_color_by_weight,
                base_width=0.28,
                width_scale=0.82,
                hover=True,
            )
            fig_base.add_trace(
                go.Scatter(
                    x=[pos_focus[n][0] for n in node_ids],
                    y=[pos_focus[n][1] for n in node_ids],
                    mode="markers",
                    marker=dict(
                        size=node_size_main,
                        color="#0ea5e9",
                        opacity=0.86,
                        line=dict(color=NETWORK_NODE_LINE, width=node_line_width),
                    ),
                    customdata=node_customdata,
                    hovertemplate=(
                        "Nama: %{customdata[0]}<br>"
                        "Usia: %{customdata[1]}<br>"
                        "Profesi: %{customdata[2]}<br>"
                        "IKD Agregat: %{customdata[3]}<br>"
                        "Klaster: %{customdata[4]}<extra></extra>"
                    ),
                    name="Node KK",
                )
            )
            style_network_figure(
                fig_base,
                title="Jaringan Kemiripan Rumah Tangga Sebelum Deteksi Komunitas",
                height=650,
            )
            if graph_spatial_mode == "Layout Jaringan":
                st.plotly_chart(fig_base, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            else:
                base_hover = [
                    (
                        f"Nama: {cd[0]}<br>Usia: {cd[1]}<br>Profesi: {cd[2]}"
                        f"<br>IKD Agregat: {cd[3]}<br>Klaster: {cd[4]}"
                    )
                    for cd in node_customdata
                ]
                fig_base_spatial = build_spatial_node_figure(
                    G,
                    node_ids=node_ids,
                    node_color_vals=[0.0 for _ in node_ids],
                    node_hover_text=base_hover,
                    title="Sebaran Spasial Node pada Jaringan Kemiripan",
                    spatial_mode=graph_spatial_mode,
                    marker_size=10,
                    colorscale=[[0.0, "#0ea5e9"], [1.0, "#0ea5e9"]],
                    cmin=0.0,
                    cmax=1.0,
                    colorbar=dict(title="Node"),
                )
                if fig_base_spatial is not None:
                    st.plotly_chart(fig_base_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                else:
                    st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                    st.plotly_chart(fig_base, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

            fig_louvain_focus = go.Figure()
            add_network_edge_traces(
                fig_louvain_focus,
                visible_edges_focus,
                pos_focus,
                edge_min,
                edge_span,
                color_fn=edge_color_by_interaction,
                base_width=0.3,
                width_scale=0.95,
                hover=True,
            )
            fig_louvain_focus.add_trace(
                go.Scatter(
                    x=[pos_focus[n][0] for n in node_ids],
                    y=[pos_focus[n][1] for n in node_ids],
                    mode="markers",
                    marker=dict(
                        size=node_size_main + 0.8,
                        color=[cid_to_idx.get(partition.get(n, -1), 0) for n in node_ids],
                        colorscale=cluster_colorscale,
                        cmin=-0.5,
                        cmax=max(len(cluster_ids_sorted) - 0.5, 0.5),
                        opacity=0.9,
                        line=dict(color=NETWORK_NODE_LINE, width=node_line_width),
                        showscale=True,
                        colorbar=dict(
                            title="Klaster Louvain",
                            tickmode="array",
                            tickvals=list(range(len(cluster_ids_sorted))),
                            ticktext=[f"Klaster {cid}" for cid in cluster_ids_sorted],
                        ),
                    ),
                    customdata=node_customdata,
                    hovertemplate=(
                        "Nama: %{customdata[0]}<br>"
                        "Usia: %{customdata[1]}<br>"
                        "Profesi: %{customdata[2]}<br>"
                        "IKD Agregat: %{customdata[3]}<br>"
                        "Klaster: %{customdata[4]}<extra></extra>"
                    ),
                    name="Node KK",
                )
            )
            style_network_figure(
                fig_louvain_focus,
                title="Jaringan Komunitas Louvain Berdasarkan Kemiripan Dimensi Kesejahteraan",
                height=670,
            )
            if graph_spatial_mode == "Layout Jaringan":
                st.plotly_chart(fig_louvain_focus, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            else:
                louvain_hover = [
                    (
                        f"Nama: {cd[0]}<br>Usia: {cd[1]}<br>Profesi: {cd[2]}"
                        f"<br>IKD Agregat: {cd[3]}<br>Klaster: {cd[4]}"
                    )
                    for cd in node_customdata
                ]
                louvain_color_vals = [cid_to_idx.get(partition.get(n, -1), 0) for n in node_ids]
                fig_louvain_spatial = build_spatial_node_figure(
                    G,
                    node_ids=node_ids,
                    node_color_vals=louvain_color_vals,
                    node_hover_text=louvain_hover,
                    title="Sebaran Spasial Komunitas Louvain",
                    spatial_mode=graph_spatial_mode,
                    marker_size=12,
                    colorscale=cluster_colorscale,
                    cmin=-0.5,
                    cmax=max(len(cluster_ids_sorted) - 0.5, 0.5),
                    colorbar=dict(
                        title="Klaster Louvain",
                        tickmode="array",
                        tickvals=list(range(len(cluster_ids_sorted))),
                        ticktext=[f"Klaster {cid}" for cid in cluster_ids_sorted],
                    ),
                )
                if fig_louvain_spatial is not None:
                    st.plotly_chart(fig_louvain_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                else:
                    st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                    st.plotly_chart(fig_louvain_focus, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

        with subbab_dropdown("Proporsi Klaster Louvain per Dusun", expanded=True):
            dusun_attr_cluster = "dusun" if "dusun" in df_v.columns else col_spasial
            df_dusun_cluster, df_dusun_cluster_wide, df_cluster_overall = build_dusun_cluster_composition(
                G,
                dusun_attr=dusun_attr_cluster,
                partition=partition,
            )
            if df_dusun_cluster.empty:
                st.info("Komposisi klaster per dusun belum dapat dihitung karena atribut dusun atau node graf belum tersedia.")
            else:
                st.caption(
                    "Proporsi dihitung dari KK yang masuk graf aktif. Persentase pada diagram dusun dibaca terhadap total KK di dusun masing-masing."
                )
                dominant_cluster_row = df_cluster_overall.sort_values("Jumlah KK", ascending=False).iloc[0]
                m_prop1, m_prop2, m_prop3, m_prop4 = st.columns(4)
                m_prop1.metric("KK Terpetakan", f"{int(df_cluster_overall['Jumlah KK'].sum())}")
                m_prop2.metric("Jumlah Klaster", f"{int(df_cluster_overall['Klaster Louvain'].nunique())}")
                m_prop3.metric("Jumlah Dusun", f"{int(df_dusun_cluster['Dusun'].nunique())}")
                m_prop4.metric(
                    "Klaster Dominan",
                    dominant_cluster_row["Klaster Louvain"],
                    f"{float(dominant_cluster_row['Persentase KK (%)']):.1f}%",
                )

                cluster_label_order = df_cluster_overall["Klaster Louvain"].tolist()
                cluster_label_color_map = {}
                for _, row_cluster in df_cluster_overall.iterrows():
                    cid = int(row_cluster["ID Klaster Internal"])
                    label = row_cluster["Klaster Louvain"]
                    cluster_label_color_map[label] = (
                        "#94A3B8"
                        if cid < 0
                        else cluster_color_map.get(cid, cluster_palette[cid_to_idx.get(cid, 0) % len(cluster_palette)])
                    )

                plot_prop_1, plot_prop_2 = st.columns([0.9, 1.35])
                with plot_prop_1:
                    fig_cluster_overall = px.bar(
                        df_cluster_overall,
                        x="Klaster Louvain",
                        y="Persentase KK (%)",
                        color="Klaster Louvain",
                        color_discrete_map=cluster_label_color_map,
                        text="Label Batang",
                        hover_data={
                            "Jumlah KK": True,
                            "Persentase KK (%)": ":.2f",
                            "ID Klaster Internal": True,
                            "Klaster Louvain": False,
                        },
                        category_orders={"Klaster Louvain": cluster_label_order},
                    )
                    fig_cluster_overall.update_traces(
                        textposition="outside",
                        cliponaxis=False,
                        marker_line_color="#111827",
                        marker_line_width=0.5,
                    )
                    style_publication_figure(
                        fig_cluster_overall,
                        title="Proporsi KK Menurut Klaster",
                        height=430,
                        xaxis_title="",
                        yaxis_title="Persentase KK (%)",
                        showlegend=False,
                    )
                    fig_cluster_overall.update_yaxes(range=[0, 100], ticksuffix="%")
                    st.plotly_chart(fig_cluster_overall, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                with plot_prop_2:
                    dusun_order_for_plot = (
                        df_dusun_cluster.groupby("Dusun")["Total KK Dusun"]
                        .max()
                        .sort_values(ascending=True)
                        .index
                        .tolist()
                    )
                    fig_dusun_cluster = px.bar(
                        df_dusun_cluster,
                        x="Persentase dalam Dusun (%)",
                        y="Dusun",
                        color="Klaster Louvain",
                        orientation="h",
                        barmode="stack",
                        text="Label Persen",
                        color_discrete_map=cluster_label_color_map,
                        category_orders={
                            "Dusun": dusun_order_for_plot,
                            "Klaster Louvain": cluster_label_order,
                        },
                        hover_data={
                            "Jumlah KK": True,
                            "Total KK Dusun": True,
                            "Persentase dalam Dusun (%)": ":.2f",
                            "Persentase dari Total Graf (%)": ":.2f",
                            "ID Klaster Internal": True,
                        },
                    )
                    fig_dusun_cluster.update_traces(
                        textposition="inside",
                        insidetextanchor="middle",
                        marker_line_color="#FFFFFF",
                        marker_line_width=0.6,
                    )
                    style_publication_figure(
                        fig_dusun_cluster,
                        title=f"Proporsi Klaster dalam Setiap {dusun_attr_cluster.title()}",
                        height=max(430, min(820, 230 + (28 * len(dusun_order_for_plot)))),
                        xaxis_title="Proporsi dalam dusun (%)",
                        yaxis_title="",
                        legend_title="Klaster",
                    )
                    fig_dusun_cluster.update_xaxes(range=[0, 100], ticksuffix="%")
                    st.plotly_chart(fig_dusun_cluster, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                pct_cols = [c for c in df_dusun_cluster_wide.columns if c.endswith("Persentase (%)")]
                fmt_cols = {c: "{:.1f}" for c in pct_cols}
                count_cols = [c for c in df_dusun_cluster_wide.columns if c.endswith("Jumlah KK") or c == "Total KK Dusun"]
                fmt_cols.update({c: "{:,.0f}" for c in count_cols})
                st.markdown("##### Tabel Proporsi Klaster per Dusun")
                tab_prop_wide, tab_prop_long = st.tabs(["Ringkas per Dusun", "Detail Dusun-Klaster"])
                with tab_prop_wide:
                    st.dataframe(
                        df_dusun_cluster_wide.style.format(fmt_cols).background_gradient(cmap="YlGnBu", subset=pct_cols),
                        use_container_width=True,
                    )
                with tab_prop_long:
                    detail_cols = [
                        "Dusun",
                        "Klaster Louvain",
                        "ID Klaster Internal",
                        "Jumlah KK",
                        "Total KK Dusun",
                        "Persentase dalam Dusun (%)",
                        "Persentase dari Total Graf (%)",
                        "Persentase dari Klaster (%)",
                    ]
                    st.dataframe(
                        df_dusun_cluster[detail_cols].style.format(
                            {
                                "Jumlah KK": "{:,.0f}",
                                "Total KK Dusun": "{:,.0f}",
                                "Persentase dalam Dusun (%)": "{:.2f}",
                                "Persentase dari Total Graf (%)": "{:.2f}",
                                "Persentase dari Klaster (%)": "{:.2f}",
                            }
                        ).background_gradient(cmap="YlGnBu", subset=["Persentase dalam Dusun (%)"]),
                        use_container_width=True,
                    )

        if selected_centrality_key != "none":
            centrality_name = {
                "degree": "Degree Centrality",
                "betweenness": "Betweenness Centrality",
                "closeness": "Closeness Centrality",
                "eigenvector": "Eigenvector Centrality",
            }.get(selected_centrality_key, "Centrality")
            all_centrality_specs = CENTRALITY_METRIC_SPECS
            centrality_metric_values = {
                metric_label: compute_centrality_on_similarity_graph(G, metric_key)
                for metric_label, metric_key in all_centrality_specs
            }
            centrality_vals = centrality_metric_values.get(centrality_name, {})
            if centrality_vals:
                st.markdown(f"### Analisis {centrality_name} pada Jaringan Louvain")
                st.caption(centrality_help_text(selected_centrality_key))
                publish_mode = st.toggle(
                    "Mode publikasi / anonimisasi",
                    value=True,
                    key=f"centrality_publish_mode_{selected_centrality_key}",
                    help="Jika aktif, nama, family_id, dusun asli, dan koordinat presisi tidak ditampilkan pada bagian centrality.",
                )
                highlight_roles = st.toggle(
                    "Highlight Aktor Strategis",
                    value=False,
                    key=f"centrality_highlight_roles_{selected_centrality_key}",
                    help="Tampilkan visual tambahan yang mewarnai node berdasarkan peran aktor strategis dari empat metrik centrality.",
                )
                if publish_mode and graph_spatial_mode != "Layout Jaringan":
                    st.info("Mode publikasi aktif: visual centrality memakai layout jaringan agar koordinat rumah tangga tidak diekspos.")
                dusun_attr_centrality = "dusun" if "dusun" in df_v.columns else col_spasial
                anon_node_map = make_anonymized_node_mapping(node_ids)
                dusun_values_all = sorted(
                    {
                        str(G.nodes[n].get(dusun_attr_centrality, "Tidak tersedia"))
                        for n in node_ids
                    }
                )
                dusun_code_map = {val: f"Dusun-{idx + 1}" for idx, val in enumerate(dusun_values_all)}
                node_centrality_rows = []
                for n in node_ids:
                    n_attr = G.nodes[n]
                    profesi_raw = n_attr.get(
                        "profesi pekerjaan",
                        n_attr.get("profesi_pekerjaan", n_attr.get("pekerjaan", n_attr.get("profesi", "Tidak diketahui"))),
                    )
                    bansos_status = "Penerima" if int(_safe_float_metric(n_attr.get("bansos_num"), default=0.0) > 0) == 1 else "Tidak Menerima"
                    row = {
                        "family_id": n,
                        "Nama": n_attr.get("nama", "-"),
                        "Kode Node": anon_node_map.get(str(n), "N-000"),
                        "Klaster Louvain": int(partition.get(n, -1)),
                        "Dusun": n_attr.get(dusun_attr_centrality, "-"),
                        "Dusun/Kode Dusun": (
                            dusun_code_map.get(str(n_attr.get(dusun_attr_centrality, "Tidak tersedia")), "Dusun-0")
                            if publish_mode
                            else str(n_attr.get(dusun_attr_centrality, "-"))
                        ),
                        "Profesi/Pekerjaan": str(profesi_raw).strip() if pd.notnull(profesi_raw) else "Tidak diketahui",
                        "Status Bansos": bansos_status,
                        "IKD Agregat": _safe_float_metric(n_attr.get("f_ikr_dari_rekap_kk"), default=np.nan),
                        "internet_num": n_attr.get("internet_num", n_attr.get("digital_num", np.nan)),
                        "ponsel_num": n_attr.get("ponsel_num", np.nan),
                    }
                    for metric_label, _ in all_centrality_specs:
                        row[metric_label] = float(centrality_metric_values.get(metric_label, {}).get(n, 0.0))
                    row["Status BPS"] = n_attr.get("kategori_ikr", categorize_ikr_bps(row["IKD Agregat"])[0])
                    for dim_label, dim_col in IKD_DIMENSION_MAP:
                        row[dim_label] = _safe_float_metric(n_attr.get(dim_col), default=np.nan)
                    node_centrality_rows.append(row)
                df_centrality = pd.DataFrame(node_centrality_rows).sort_values(centrality_name, ascending=False).reset_index(drop=True)
                c_series_full = pd.to_numeric(df_centrality[centrality_name], errors="coerce").fillna(0.0)
                c_q25 = float(c_series_full.quantile(0.25)) if not c_series_full.empty else 0.0
                c_q75 = float(c_series_full.quantile(0.75)) if not c_series_full.empty else 0.0
                df_centrality["_centrality_q25"] = c_q25
                df_centrality["_centrality_q75"] = c_q75
                df_centrality["Level Centrality"] = df_centrality[centrality_name].map(
                    lambda v: centrality_level_from_quantile(v, c_q25, c_q75)
                )
                df_centrality["Level IKD"] = df_centrality.apply(
                    lambda r: ikr_level_from_value(r.get("IKD Agregat"), r.get("Status BPS")),
                    axis=1,
                )
                df_centrality["Akses Informasi"] = df_centrality.apply(access_info_label, axis=1)
                df_centrality = add_centrality_role_features(df_centrality)
                df_centrality["Centrality terpilih"] = df_centrality[centrality_name]
                df_centrality["Hover Aman"] = df_centrality.apply(lambda r: safe_hover_text(r, publish_mode=publish_mode), axis=1)

                display_identity_cols = ["Kode Node", "Klaster Louvain", "Dusun/Kode Dusun"] if publish_mode else [
                    "Kode Node",
                    "Nama",
                    "family_id",
                    "Klaster Louvain",
                    "Dusun",
                ]
                display_cols = [
                    *display_identity_cols,
                    centrality_name,
                    "Degree Centrality",
                    "Betweenness Centrality",
                    "Closeness Centrality",
                    "Eigenvector Centrality",
                    "Sinyal Centrality",
                    "Jumlah Metrik Tinggi",
                    "Peran Struktural",
                    "Basis Metrik Peran",
                    "Peran Aktor",
                ]
                display_cols = unique_existing_columns(df_centrality, display_cols)

                st.markdown("#### Filter Visual Jaringan Centrality")
                cluster_opts_all = sorted(df_centrality["Klaster Louvain"].dropna().unique().tolist())
                dusun_opts_all = sorted(df_centrality["Dusun"].fillna("Tidak Valid").astype(str).unique().tolist())
                f1, f2 = st.columns(2)
                with f1:
                    selected_clusters_view = st.multiselect(
                        "Pilih Klaster untuk Visual",
                        options=cluster_opts_all,
                        default=cluster_opts_all,
                        key=f"cent_filter_cluster_{selected_centrality_key}",
                    )
                with f2:
                    selected_dusun_view = st.multiselect(
                        "Pilih Dusun untuk Visual",
                        options=dusun_opts_all,
                        default=dusun_opts_all,
                        format_func=lambda x: dusun_code_map.get(str(x), str(x)) if publish_mode else str(x),
                        key=f"cent_filter_dusun_{selected_centrality_key}",
                    )

                df_centrality_view = df_centrality[
                    df_centrality["Klaster Louvain"].isin(selected_clusters_view)
                    & df_centrality["Dusun"].astype(str).isin([str(x) for x in selected_dusun_view])
                ].copy()
                if df_centrality_view.empty:
                    st.warning("Filter klaster/dusun tidak memiliki node. Silakan ubah filter.")
                else:
                    selected_node_set = set(df_centrality_view["family_id"].tolist())
                    G_view = G.subgraph(selected_node_set).copy()
                    centrality_view_metric_values = {
                        metric_label: compute_centrality_on_similarity_graph(G_view, metric_key)
                        for metric_label, metric_key in all_centrality_specs
                    }
                    for metric_label, _ in all_centrality_specs:
                        fallback_vals = centrality_metric_values.get(metric_label, {})
                        view_vals = centrality_view_metric_values.get(metric_label, {})
                        df_centrality_view[metric_label] = df_centrality_view["family_id"].map(
                            lambda nid, vals=view_vals, fallback=fallback_vals: float(vals.get(nid, fallback.get(nid, 0.0)))
                        )
                    c_series_view = pd.to_numeric(df_centrality_view[centrality_name], errors="coerce").fillna(0.0)
                    c_q25_view = float(c_series_view.quantile(0.25)) if not c_series_view.empty else 0.0
                    c_q75_view = float(c_series_view.quantile(0.75)) if not c_series_view.empty else 0.0
                    df_centrality_view["_centrality_q25"] = c_q25_view
                    df_centrality_view["_centrality_q75"] = c_q75_view
                    df_centrality_view["Level Centrality"] = df_centrality_view[centrality_name].map(
                        lambda v: centrality_level_from_quantile(v, c_q25_view, c_q75_view)
                    )
                    df_centrality_view["Level IKD"] = df_centrality_view.apply(
                        lambda r: ikr_level_from_value(r.get("IKD Agregat"), r.get("Status BPS")),
                        axis=1,
                    )
                    df_centrality_view["Akses Informasi"] = df_centrality_view.apply(access_info_label, axis=1)
                    df_centrality_view = add_centrality_role_features(df_centrality_view)
                    df_centrality_view["Centrality terpilih"] = df_centrality_view[centrality_name]
                    df_centrality_view["Hover Aman"] = df_centrality_view.apply(lambda r: safe_hover_text(r, publish_mode=publish_mode), axis=1)
                    df_centrality_view = df_centrality_view.sort_values(centrality_name, ascending=False).reset_index(drop=True)

                    m_cent1, m_cent2, m_cent3, m_cent4 = st.columns(4)
                    m_cent1.metric("Node Terpilih", f"{int(df_centrality_view.shape[0])}")
                    m_cent2.metric("Edge Terpilih", f"{int(G_view.number_of_edges())}")
                    m_cent3.metric("Nilai Tertinggi", f"{float(df_centrality_view[centrality_name].max()):.6f}")
                    m_cent4.metric("Aktor Strategis", f"{int(df_centrality_view['Peran Struktural'].ne('Node umum').sum())}")

                    st.markdown(f"#### Visual Jaringan Louvain Dinamis ({centrality_name})")
                    if G_view.number_of_nodes() >= 1:
                        fig_cent = go.Figure()
                        edge_weights_view = [_safe_float_metric(d.get("weight"), default=0.0) for _, _, d in G_view.edges(data=True)]
                        edge_min_v = float(min(edge_weights_view)) if edge_weights_view else 0.0
                        edge_max_v = float(max(edge_weights_view)) if edge_weights_view else 1.0
                        edge_span_v = max(edge_max_v - edge_min_v, 1e-9)
                        visible_edges_view = select_representative_edges(
                            G_view,
                            max_edges=int(np.clip(G_view.number_of_nodes() * 1.25, 120, 650)),
                            per_node=1,
                        )
                        add_network_edge_traces(
                            fig_cent,
                            visible_edges_view,
                            pos_focus,
                            edge_min_v,
                            edge_span_v,
                            color_fn=edge_color_by_interaction,
                            base_width=0.26,
                            width_scale=0.78,
                            hover=False,
                        )
                        node_order = list(G_view.nodes())
                        df_cent_lookup = df_centrality_view.set_index("family_id")
                        node_val_arr = np.array(
                            [float(df_cent_lookup.loc[n, centrality_name]) for n in node_order],
                            dtype=float,
                        )
                        cmin_n = float(np.nanmin(node_val_arr)) if len(node_val_arr) else 0.0
                        cmax_n = float(np.nanmax(node_val_arr)) if len(node_val_arr) else 1.0
                        size_vals = centrality_marker_sizes(node_val_arr, len(node_order))
                        cent_hover_text = [
                            safe_hover_text(df_cent_lookup.loc[n], publish_mode=publish_mode)
                            for n in node_order
                        ]
                        fig_cent.add_trace(
                            go.Scatter(
                                x=[pos_focus[n][0] for n in node_order],
                                y=[pos_focus[n][1] for n in node_order],
                                mode="markers",
                                marker=dict(
                                    size=size_vals,
                                    color=node_val_arr.tolist(),
                                    colorscale="Viridis",
                                    showscale=True,
                                    cmin=cmin_n,
                                    cmax=cmax_n if cmax_n > cmin_n else (cmin_n + 1e-6),
                                    colorbar=dict(title=centrality_name),
                                    opacity=0.82,
                                    line=dict(color=NETWORK_NODE_LINE, width=0.4),
                                ),
                                text=cent_hover_text,
                                hoverinfo="text",
                                showlegend=False,
                            )
                        )
                        top_ring_n = int(min(14, max(5, round(len(node_order) * 0.025))))
                        top_ring_nodes = df_centrality_view.head(top_ring_n)["family_id"].tolist()
                        top_ring_size = {
                            n: min(float(size_vals[idx]) + 4.0, max(size_vals) + 5.0)
                            for idx, n in enumerate(node_order)
                        }
                        if top_ring_nodes:
                            fig_cent.add_trace(
                                go.Scatter(
                                    x=[pos_focus[n][0] for n in top_ring_nodes if n in pos_focus],
                                    y=[pos_focus[n][1] for n in top_ring_nodes if n in pos_focus],
                                    mode="markers",
                                    marker=dict(
                                        size=[top_ring_size.get(n, 13.0) for n in top_ring_nodes if n in pos_focus],
                                        color="rgba(255,255,255,0)",
                                        line=dict(color="#111827", width=1.4),
                                    ),
                                    hoverinfo="skip",
                                    showlegend=False,
                                )
                            )
                        style_network_figure(
                            fig_cent,
                            title=f"Jaringan Louvain Terfilter Menurut {centrality_name}",
                            height=690,
                        )
                        if graph_spatial_mode == "Layout Jaringan" or publish_mode:
                            st.plotly_chart(fig_cent, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                        else:
                            fig_cent_spatial = build_spatial_node_figure(
                                G_view,
                                node_ids=node_order,
                                node_color_vals=node_val_arr.tolist(),
                                node_hover_text=cent_hover_text,
                                title=f"Sebaran Spasial Louvain Terfilter Menurut {centrality_name}",
                                spatial_mode=graph_spatial_mode,
                                marker_size=13,
                                colorscale="Viridis",
                                cmin=cmin_n,
                                cmax=cmax_n if cmax_n > cmin_n else (cmin_n + 1e-6),
                                colorbar=dict(title=centrality_name),
                            )
                            if fig_cent_spatial is not None:
                                st.plotly_chart(fig_cent_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                            else:
                                st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                                st.plotly_chart(fig_cent, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                    role_narrative = build_centrality_policy_narrative(df_centrality_view, centrality_name)
                    st.markdown("#### Interpretasi Struktural dan Implikasi Program")
                    st.info(role_narrative)

                    with subbab_dropdown("Catatan Etika dan Batasan Interpretasi", expanded=publish_mode):
                        st.markdown(
                            """
                            - Data mikro rumah tangga adalah data sensitif.
                            - Identitas individu/KK perlu disamarkan dalam visualisasi publik.
                            - Peran aktor hanya membaca posisi jaringan dari degree, betweenness, closeness, dan eigenvector.
                            - Centrality tidak boleh dimaknai sebagai status sosial, tingkat kesejahteraan, atau kelayakan bantuan.
                            - Degree, betweenness, closeness, dan eigenvector memiliki tafsir berbeda sehingga perlu dibaca bersama konteks lapangan.
                            - Hasil ini mendukung pemetaan aktor strategis, bukan dasar tunggal penetapan tokoh atau sasaran program.
                            - Hindari penyebutan nama orang, alamat spesifik, atau koordinat presisi pada materi presentasi/publikasi.
                            """
                        )

                    if highlight_roles and G_view.number_of_nodes() >= 1:
                        st.markdown("#### Network Highlight Node Strategis")
                        fig_role = go.Figure()
                        role_edge_weights = [_safe_float_metric(d.get("weight"), default=0.0) for _, _, d in G_view.edges(data=True)]
                        role_edge_min = float(min(role_edge_weights)) if role_edge_weights else 0.0
                        role_edge_max = float(max(role_edge_weights)) if role_edge_weights else 1.0
                        role_edge_span = max(role_edge_max - role_edge_min, 1e-9)
                        role_visible_edges = select_representative_edges(
                            G_view,
                            max_edges=int(np.clip(G_view.number_of_nodes() * 1.25, 120, 650)),
                            per_node=1,
                        )
                        add_network_edge_traces(
                            fig_role,
                            role_visible_edges,
                            pos_focus,
                            role_edge_min,
                            role_edge_span,
                            color_fn=lambda *_args, **_kwargs: "rgba(148, 163, 184, 0.18)",
                            base_width=0.22,
                            width_scale=0.55,
                            hover=False,
                        )
                        role_lookup = df_centrality_view.set_index("family_id")
                        role_node_order = [n for n in G_view.nodes() if n in role_lookup.index and n in pos_focus]
                        role_values = np.array([float(role_lookup.loc[n, centrality_name]) for n in role_node_order], dtype=float)
                        role_sizes = centrality_marker_sizes(role_values, len(role_node_order))
                        size_lookup = {n: role_sizes[idx] for idx, n in enumerate(role_node_order)}
                        present_roles = [
                            role for role in CENTRALITY_ROLE_ORDER
                            if role in set(df_centrality_view["Peran Struktural"].astype(str))
                        ]
                        for role in present_roles:
                            role_nodes = [
                                n for n in role_node_order
                                if str(role_lookup.loc[n, "Peran Struktural"]) == role
                            ]
                            if not role_nodes:
                                continue
                            is_general = role == "Node umum"
                            fig_role.add_trace(
                                go.Scatter(
                                    x=[pos_focus[n][0] for n in role_nodes],
                                    y=[pos_focus[n][1] for n in role_nodes],
                                    mode="markers",
                                    marker=dict(
                                        size=[size_lookup.get(n, node_size_main) for n in role_nodes],
                                        color=CENTRALITY_ROLE_COLORS.get(role, "#94A3B8"),
                                        opacity=0.26 if is_general else 0.9,
                                        line=dict(
                                            color="rgba(71, 85, 105, 0.35)" if is_general else NETWORK_NODE_LINE,
                                            width=0.35 if is_general else 0.85,
                                        ),
                                    ),
                                    text=[safe_hover_text(role_lookup.loc[n], publish_mode=publish_mode) for n in role_nodes],
                                    hoverinfo="text",
                                    name=centrality_role_display_label(role),
                                )
                            )
                        top5_role_nodes = df_centrality_view.head(5)["family_id"].tolist()
                        top5_role_nodes = [n for n in top5_role_nodes if n in pos_focus]
                        if top5_role_nodes:
                            fig_role.add_trace(
                                go.Scatter(
                                    x=[pos_focus[n][0] for n in top5_role_nodes],
                                    y=[pos_focus[n][1] for n in top5_role_nodes],
                                    mode="markers",
                                    marker=dict(
                                        size=[size_lookup.get(n, node_size_main) + 5.0 for n in top5_role_nodes],
                                        color="rgba(255,255,255,0)",
                                        line=dict(color="#111827", width=1.8),
                                    ),
                                    hoverinfo="skip",
                                    name="Top 5 centrality",
                                    showlegend=True,
                                )
                            )
                        style_network_figure(
                            fig_role,
                            title=f"Highlight Aktor Strategis Berdasarkan {centrality_name}",
                            height=690,
                            showlegend=True,
                        )
                        st.plotly_chart(fig_role, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                    st.markdown("#### Peta Aktor Strategis Empat Centrality")
                    render_strategic_actor_centrality_map(df_centrality_view)

                    st.markdown("#### Matriks Degree-Eigenvector Aktor Strategis")
                    render_degree_eigenvector_role_matrix(df_centrality_view)

                    st.markdown("#### Profil Aktor Strategis")
                    top_n_profile = st.slider(
                        "Jumlah node pada tabel profil",
                        min_value=5,
                        max_value=30,
                        value=15,
                        step=5,
                        key=f"centrality_profile_topn_{selected_centrality_key}",
                    )
                    role_rank = {role: idx for idx, role in enumerate(CENTRALITY_ROLE_ORDER)}
                    df_profile = df_centrality_view.copy()
                    df_profile["_role_rank"] = df_profile["Peran Struktural"].map(role_rank).fillna(len(role_rank))
                    df_profile = (
                        df_profile.sort_values(["_role_rank", centrality_name], ascending=[True, False])
                        .head(int(top_n_profile))
                        .copy()
                    )
                    profile_cols = [
                        "Kode Node",
                        "Klaster Louvain",
                        "Dusun/Kode Dusun",
                        "Centrality terpilih",
                        "Degree Centrality",
                        "Betweenness Centrality",
                        "Closeness Centrality",
                        "Eigenvector Centrality",
                        "Sinyal Centrality",
                        "Jumlah Metrik Tinggi",
                        "Peran Struktural",
                        "Basis Metrik Peran",
                        "Peran Aktor",
                        "Implikasi Program",
                        "Catatan Etika",
                    ]
                    if not publish_mode:
                        profile_cols = ["Nama", "family_id", "Dusun", *profile_cols]
                    profile_display = df_profile[[c for c in profile_cols if c in df_profile.columns]].copy()
                    st.dataframe(
                        profile_display.style.format(
                            {
                                "Centrality terpilih": "{:.6f}",
                                "Degree Centrality": "{:.6f}",
                                "Betweenness Centrality": "{:.6f}",
                                "Closeness Centrality": "{:.6f}",
                                "Eigenvector Centrality": "{:.6f}",
                            }
                        ),
                        use_container_width=True,
                    )
                    anonymous_download_cols = [c for c in profile_cols if c not in {"Nama", "family_id", "Dusun"}]
                    anonymous_source_cols = list(dict.fromkeys(["family_id", "Nama", "Dusun", *anonymous_download_cols]))
                    anonymous_download_df = apply_privacy_view(
                        df_profile[[c for c in anonymous_source_cols if c in df_profile.columns]],
                        publish_mode=True,
                    )
                    anonymous_download_df = anonymous_download_df[
                        [c for c in anonymous_download_cols if c in anonymous_download_df.columns]
                    ].copy()
                    st.download_button(
                        "Unduh Tabel Anonim",
                        data=anonymous_download_df.to_csv(index=False).encode("utf-8"),
                        file_name=f"profil_node_strategis_anonim_{selected_centrality_key}.csv",
                        mime="text/csv",
                        key=f"download_centrality_profile_{selected_centrality_key}",
                    )

                    st.markdown("#### Komposisi Aktor Strategis per Klaster dan Dusun")
                    render_role_composition_charts(df_centrality_view, publish_mode=publish_mode)

                    st.markdown("#### Top 5 Centrality per Pilar (Filter Aktif)")
                    st.caption(
                        "Tabel ini menampilkan 5 node dengan skor tertinggi untuk setiap metrik centrality. "
                        "Gunakan ikon kamera pada kanan atas tabel untuk mengunduh PNG."
                    )
                    all_centrality_specs = CENTRALITY_METRIC_SPECS
                    top_table_config = {
                        **PLOTLY_DRAW_CONFIG,
                        "toImageButtonOptions": {
                            "format": "png",
                            "filename": "top-centrality-table",
                            "height": 700,
                            "width": 1400,
                            "scale": 2,
                        },
                    }
                    df_centrality_all = df_centrality_view[
                        [
                            "family_id",
                            "Kode Node",
                            "Nama",
                            "Dusun",
                            "Dusun/Kode Dusun",
                            "Peran Struktural",
                            "Basis Metrik Peran",
                            "Peran Aktor",
                            "Sinyal Centrality",
                            "Degree Centrality",
                            "Betweenness Centrality",
                            "Closeness Centrality",
                            "Eigenvector Centrality",
                        ]
                    ].copy()
                    rename_metric_map = {}
                    for metric_label_all, metric_key_all in all_centrality_specs:
                        metric_vals_all = compute_centrality_on_similarity_graph(G_view, metric_key_all)
                        df_centrality_all[metric_label_all] = df_centrality_all["family_id"].map(
                            lambda nid, vals=metric_vals_all: float(vals.get(nid, 0.0))
                        )
                        rename_metric_map[metric_label_all] = f"Skor {metric_label_all}"

                    top_tabs = st.tabs([label.replace(" Centrality", "") for label, _ in all_centrality_specs])
                    for tab_obj, (metric_label_all, _) in zip(top_tabs, all_centrality_specs):
                        score_col = rename_metric_map[metric_label_all]
                        node_display_col = "Kode Node" if publish_mode else "Nama"
                        dusun_display_col = "Dusun/Kode Dusun" if publish_mode else "Dusun"
                        df_top_table = (
                            df_centrality_all[
                                [
                                    node_display_col,
                                    dusun_display_col,
                                    "Peran Aktor",
                                    "Basis Metrik Peran",
                                    "Sinyal Centrality",
                                    metric_label_all,
                                ]
                            ]
                            .rename(
                                columns={
                                    node_display_col: "Nama",
                                    dusun_display_col: "Dusun",
                                    "Peran Aktor": "Peran",
                                    "Basis Metrik Peran": "Basis Metrik",
                                    "Sinyal Centrality": "Sinyal",
                                    metric_label_all: score_col,
                                }
                            )
                            .sort_values(score_col, ascending=False)
                            .head(5)
                            .reset_index(drop=True)
                        )
                        with tab_obj:
                            fig_top_table = build_centrality_top_table_figure(
                                df_top_table,
                                title=f"Top 5 {metric_label_all}",
                                score_col=score_col,
                            )
                            if fig_top_table is not None:
                                st.plotly_chart(fig_top_table, use_container_width=True, config=top_table_config)

                    st.markdown(f"#### Top 10 (Filter Aktif): {centrality_name}")
                    st.dataframe(
                        df_centrality_view[display_cols].head(10).style.format(
                            {
                                "Centrality terpilih": "{:.6f}",
                                "Degree Centrality": "{:.6f}",
                                "Betweenness Centrality": "{:.6f}",
                                "Closeness Centrality": "{:.6f}",
                                "Eigenvector Centrality": "{:.6f}",
                            }
                        ),
                        use_container_width=True,
                    )

                if not df_centrality_view.empty:
                    st.markdown("#### Analisis per Klaster dan per Dusun")
                    centrality_dusun_summary_col = "Dusun/Kode Dusun" if publish_mode else "Dusun"
                    c_tab1, c_tab2, c_tab3, c_tab4 = st.tabs(
                        ["Ringkasan Klaster", "Top 10 per Klaster", "Ringkasan Dusun", "Top 10 per Dusun"]
                    )
                    with c_tab1:
                        df_cluster_cent = (
                            df_centrality_view.groupby("Klaster Louvain", as_index=False)
                            .agg(
                                Jumlah_Node=("family_id", "count"),
                                Aktor_Strategis=("Peran Struktural", lambda s: int(s.ne("Node umum").sum())),
                                Rerata_Centrality=(centrality_name, "mean"),
                                Maks_Centrality=(centrality_name, "max"),
                                Rerata_Degree=("Degree Centrality", "mean"),
                                Rerata_Betweenness=("Betweenness Centrality", "mean"),
                                Rerata_Closeness=("Closeness Centrality", "mean"),
                                Rerata_Eigenvector=("Eigenvector Centrality", "mean"),
                            )
                            .sort_values("Rerata_Centrality", ascending=False)
                            .reset_index(drop=True)
                        )
                        st.dataframe(
                            df_cluster_cent.style.format(
                                {
                                    "Rerata_Centrality": "{:.6f}",
                                    "Maks_Centrality": "{:.6f}",
                                    "Rerata_Degree": "{:.6f}",
                                    "Rerata_Betweenness": "{:.6f}",
                                    "Rerata_Closeness": "{:.6f}",
                                    "Rerata_Eigenvector": "{:.6f}",
                                }
                            ),
                            use_container_width=True,
                        )
                    with c_tab2:
                        cluster_opts = sorted(df_centrality_view["Klaster Louvain"].dropna().unique().tolist())
                        selected_cluster_c = st.selectbox(
                            "Pilih Klaster",
                            options=cluster_opts,
                            key=f"centrality_cluster_{selected_centrality_key}",
                        )
                        st.dataframe(
                            df_centrality_view[df_centrality_view["Klaster Louvain"] == selected_cluster_c][display_cols]
                            .head(10)
                            .style.format(
                                {
                                    "Centrality terpilih": "{:.6f}",
                                    "Degree Centrality": "{:.6f}",
                                    "Betweenness Centrality": "{:.6f}",
                                    "Closeness Centrality": "{:.6f}",
                                    "Eigenvector Centrality": "{:.6f}",
                                }
                            ),
                            use_container_width=True,
                        )
                    with c_tab3:
                        df_dusun_cent = (
                            df_centrality_view.groupby(centrality_dusun_summary_col, as_index=False)
                            .agg(
                                Jumlah_Node=("family_id", "count"),
                                Aktor_Strategis=("Peran Struktural", lambda s: int(s.ne("Node umum").sum())),
                                Rerata_Centrality=(centrality_name, "mean"),
                                Maks_Centrality=(centrality_name, "max"),
                                Rerata_Degree=("Degree Centrality", "mean"),
                                Rerata_Betweenness=("Betweenness Centrality", "mean"),
                                Rerata_Closeness=("Closeness Centrality", "mean"),
                                Rerata_Eigenvector=("Eigenvector Centrality", "mean"),
                            )
                            .sort_values("Rerata_Centrality", ascending=False)
                            .reset_index(drop=True)
                        )
                        st.dataframe(
                            df_dusun_cent.style.format(
                                {
                                    "Rerata_Centrality": "{:.6f}",
                                    "Maks_Centrality": "{:.6f}",
                                    "Rerata_Degree": "{:.6f}",
                                    "Rerata_Betweenness": "{:.6f}",
                                    "Rerata_Closeness": "{:.6f}",
                                    "Rerata_Eigenvector": "{:.6f}",
                                }
                            ),
                            use_container_width=True,
                        )
                    with c_tab4:
                        dusun_opts = sorted(df_centrality_view[centrality_dusun_summary_col].fillna("Tidak Valid").astype(str).unique().tolist())
                        selected_dusun_c = st.selectbox(
                            "Pilih Dusun/Kode Dusun",
                            options=dusun_opts,
                            key=f"centrality_dusun_{selected_centrality_key}",
                        )
                        st.dataframe(
                            df_centrality_view[df_centrality_view[centrality_dusun_summary_col].astype(str) == str(selected_dusun_c)][display_cols]
                            .head(10)
                            .style.format(
                                {
                                    "Centrality terpilih": "{:.6f}",
                                    "Degree Centrality": "{:.6f}",
                                    "Betweenness Centrality": "{:.6f}",
                                    "Closeness Centrality": "{:.6f}",
                                    "Eigenvector Centrality": "{:.6f}",
                                }
                            ),
                            use_container_width=True,
                        )
            else:
                st.info("Nilai centrality belum bisa dihitung untuk graf saat ini.")

        with subbab_dropdown("Assortativity per Klaster Louvain", expanded=False):
            st.caption(
                "Perhitungan ini memakai subgraf tiap klaster (hanya node dan edge di dalam klaster tersebut), "
                "untuk melihat kekuatan homogenitas internal masing-masing klaster."
            )
            cluster_assort_rows = []
            for cid in cluster_ids_sorted:
                nodes_c = [n for n in node_ids if partition.get(n, -1) == cid]
                g_c = G.subgraph(nodes_c).copy()
                r_f_ikr_c = safe_numeric_assortativity(g_c, "f_ikr_dari_rekap_kk", default=0.0)
                r_fa_c = safe_numeric_assortativity(g_c, "f_a_dari_rekap_kk", default=0.0)
                r_fb_c = safe_numeric_assortativity(g_c, "f_b_dari_rekap_kk", default=0.0)
                r_fc_c = safe_numeric_assortativity(g_c, "f_c_dari_rekap_kk", default=0.0)
                r_fd_c = safe_numeric_assortativity(g_c, "f_d_dari_rekap_kk", default=0.0)
                r_fe_c = safe_numeric_assortativity(g_c, "f_e_dari_rekap_kk", default=0.0)
                r_dim_mean_c = float(np.nanmean([r_fa_c, r_fb_c, r_fc_c, r_fd_c, r_fe_c]))
                r_bansos_c = safe_attribute_assortativity(g_c, "bansos_num", default=0.0)
                r_internet_c = safe_attribute_assortativity(g_c, "internet_num", default=0.0)
                r_ponsel_c = safe_attribute_assortativity(g_c, "ponsel_num", default=0.0)
                r_spatial_c = safe_attribute_assortativity(g_c, col_spasial, default=0.0) if col_spasial in df_v.columns else np.nan
                dir_c, lvl_c = interpret_assortativity_value(r_f_ikr_c)
                cluster_assort_rows.append(
                    {
                        "Klaster": int(cid),
                        "Node": int(g_c.number_of_nodes()),
                        "Edge Internal": int(g_c.number_of_edges()),
                        "Density Internal": float(nx.density(g_c)) if g_c.number_of_nodes() > 1 else 0.0,
                        "r IKD Agregat": float(r_f_ikr_c),
                        "Arah IKD Agregat": dir_c,
                        "Kekuatan IKD Agregat": lvl_c,
                        "r Rata-rata Lima Dimensi": float(r_dim_mean_c),
                        "r Bansos": float(r_bansos_c),
                        "r Internet": float(r_internet_c),
                        "r Ponsel": float(r_ponsel_c),
                        "r Spasial": float(r_spatial_c) if pd.notnull(r_spatial_c) else np.nan,
                    }
                )
            df_cluster_assort = pd.DataFrame(cluster_assort_rows).sort_values("Klaster").reset_index(drop=True)
            st.dataframe(
                df_cluster_assort.style.format(
                    {
                        "Density Internal": "{:.4f}",
                        "r IKD Agregat": "{:.4f}",
                        "r Rata-rata Lima Dimensi": "{:.4f}",
                        "r Bansos": "{:.4f}",
                        "r Internet": "{:.4f}",
                        "r Ponsel": "{:.4f}",
                        "r Spasial": "{:.4f}",
                    }
                ),
                use_container_width=True,
            )
            fig_cluster_r = px.bar(
                df_cluster_assort,
                x="Klaster",
                y="r IKD Agregat",
                color="r IKD Agregat",
                color_continuous_scale="RdYlGn",
                range_color=[-1, 1],
                title="Perbandingan Assortativity IKD Agregat per Klaster Louvain",
                hover_data=["Node", "Edge Internal", "Density Internal", "Arah IKD Agregat", "Kekuatan IKD Agregat"],
            )
            fig_cluster_r.add_hline(y=0.0, line_dash="dash", line_color="#475569")
            fig_cluster_r.update_layout(template="plotly_white", xaxis_title="Klaster", yaxis_title="r IKD Agregat")
            st.plotly_chart(fig_cluster_r, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            cluster_metric_long = df_cluster_assort.melt(
                id_vars=["Klaster"],
                value_vars=["r Rata-rata Lima Dimensi", "r Bansos", "r Internet", "r Ponsel", "r Spasial"],
                var_name="Metrik",
                value_name="Nilai r",
            ).dropna(subset=["Nilai r"])
            if not cluster_metric_long.empty:
                fig_cluster_metric = px.bar(
                    cluster_metric_long,
                    x="Klaster",
                    y="Nilai r",
                    color="Metrik",
                    barmode="group",
                    title="Ringkasan r per Klaster (Dimensi Rata-rata & Atribut Audit)",
                )
                fig_cluster_metric.add_hline(y=0.0, line_dash="dash", line_color="#475569")
                fig_cluster_metric.update_layout(template="plotly_white", xaxis_title="Klaster", yaxis_title="Nilai r")
                st.plotly_chart(fig_cluster_metric, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

        with subbab_dropdown("Profil Deskriptif Tiap Klaster Louvain", expanded=False):
            node_profile_rows = []
            for n in node_ids:
                n_attr = G.nodes[n]
                usia_raw = n_attr.get("usia", n_attr.get("usia (y)", n_attr.get("umur", np.nan)))
                profesi_raw = n_attr.get(
                    "profesi pekerjaan",
                    n_attr.get("profesi_pekerjaan", n_attr.get("pekerjaan", n_attr.get("profesi", "Tidak diketahui"))),
                )
                node_profile_rows.append(
                    {
                        "family_id": n,
                        "Klaster Louvain": int(partition.get(n, -1)),
                        "Usia": pd.to_numeric(pd.Series([usia_raw]), errors="coerce").iloc[0],
                        "Profesi/Pekerjaan": str(profesi_raw).strip() if pd.notnull(profesi_raw) else "Tidak diketahui",
                        "IKD Agregat": _safe_float_metric(n_attr.get("f_ikr_dari_rekap_kk"), default=np.nan),
                        "Weighted Degree": float(G.degree(n, weight="weight")),
                    }
                )
            df_cluster_profile = pd.DataFrame(node_profile_rows)

            ccp1, ccp2, ccp3 = st.columns(3)
            ccp1.metric("Jumlah Klaster Terbentuk", f"{int(df_cluster_profile['Klaster Louvain'].nunique())}")
            ccp2.metric("Node Terpetakan", f"{int(len(df_cluster_profile))}")
            usia_valid_n = int(df_cluster_profile["Usia"].notna().sum())
            ccp3.metric("Node dengan Data Usia", f"{usia_valid_n}")

            summary_cluster = (
                df_cluster_profile.groupby("Klaster Louvain", as_index=False)
                .agg(
                    Jumlah_Node=("family_id", "count"),
                    Rerata_Usia=("Usia", "mean"),
                    Median_Usia=("Usia", "median"),
                    Rerata_IKD_Agregat=("IKD Agregat", "mean"),
                    Rerata_Weighted_Degree=("Weighted Degree", "mean"),
                )
                .sort_values("Klaster Louvain")
                .reset_index(drop=True)
            )
            top_prof_series = (
                df_cluster_profile.groupby("Klaster Louvain")["Profesi/Pekerjaan"]
                .agg(lambda s: ", ".join(s.value_counts().head(3).index.astype(str).tolist()))
                .rename("Top 3 Profesi/Pekerjaan")
                .reset_index()
            )
            summary_cluster = summary_cluster.merge(top_prof_series, on="Klaster Louvain", how="left")

            st.dataframe(
                summary_cluster.style.format(
                    {
                        "Rerata_Usia": "{:.1f}",
                        "Median_Usia": "{:.1f}",
                        "Rerata_IKD_Agregat": "{:.2f}",
                        "Rerata_Weighted_Degree": "{:.2f}",
                    }
                ),
                use_container_width=True,
            )

            vis_c1, vis_c2 = st.columns(2)
            with vis_c1:
                df_age_plot = df_cluster_profile[df_cluster_profile["Usia"].notna()].copy()
                if not df_age_plot.empty:
                    fig_age = px.histogram(
                        df_age_plot,
                        x="Usia",
                        color="Klaster Louvain",
                        nbins=18,
                        barmode="overlay",
                        opacity=0.65,
                        title="Distribusi Usia per Klaster",
                    )
                    fig_age.update_layout(template="plotly_white", xaxis_title="Usia", yaxis_title="Frekuensi")
                    st.plotly_chart(fig_age, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                else:
                    st.info("Data usia belum tersedia untuk histogram klaster.")
            with vis_c2:
                prof_counts = (
                    df_cluster_profile.groupby(["Klaster Louvain", "Profesi/Pekerjaan"], as_index=False)
                    .size()
                    .rename(columns={"size": "Jumlah"})
                    .sort_values(["Klaster Louvain", "Jumlah"], ascending=[True, False])
                )
                if not prof_counts.empty:
                    top_prof_plot = prof_counts.groupby("Klaster Louvain").head(5).copy()
                    fig_prof = px.bar(
                        top_prof_plot,
                        x="Klaster Louvain",
                        y="Jumlah",
                        color="Profesi/Pekerjaan",
                        barmode="stack",
                        title="Top Profesi/Pekerjaan per Klaster (Top 5)",
                    )
                    fig_prof.update_layout(template="plotly_white", xaxis_title="Klaster", yaxis_title="Jumlah Node")
                    st.plotly_chart(fig_prof, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                else:
                    st.info("Data profesi/pekerjaan belum tersedia untuk visual klaster.")

        with subbab_dropdown("Visual Jaringan Dimensi Kesejahteraan", expanded=False):
            graph_dim_label, graph_dim_col = selected_graph_dim
            raw_dim_vals = [G.nodes[n].get(graph_dim_col) for n in node_ids]
            dim_num = pd.to_numeric(pd.Series(raw_dim_vals), errors="coerce")
            dim_marker_cmin = None
            dim_marker_cmax = None
            if graph_dim_col == IKD_OVERALL_METRIC[1]:
                # Untuk IKD agregat, gunakan nilai asli lalu discretize berbasis rentang data (bukan kategori BPS).
                valid_vals = dim_num.dropna()
                if valid_vals.nunique() <= 1:
                    dim_marker_vals = [0 for _ in node_ids]
                    dim_colorscale = [[0.0, "#2563eb"], [1.0, "#2563eb"]]
                    dim_colorbar = dict(title="Kelas IKD Agregat")
                    dim_hover_vals = [f"{x:.3f}" if pd.notnull(x) else "NA" for x in dim_num]
                    dim_marker_cmin = 0
                    dim_marker_cmax = 1
                else:
                    n_bins = int(min(5, valid_vals.nunique()))
                    vmin = float(valid_vals.min())
                    vmax = float(valid_vals.max())
                    bin_edges = np.linspace(vmin, vmax, n_bins + 1)
                    bins = pd.cut(dim_num, bins=bin_edges, include_lowest=True, duplicates="drop")
                    uniq_bins = [b for b in bins.cat.categories]
                    bin_labels = [f"{float(iv.left):.2f} - {float(iv.right):.2f}" for iv in uniq_bins]
                    bin_map = {b: i for i, b in enumerate(uniq_bins)}
                    invalid_idx = len(uniq_bins)
                    dim_marker_vals = [bin_map.get(b, invalid_idx) for b in bins]
                    palette_main = ["#d73027", "#fc8d59", "#fee08b", "#d9ef8b", "#1a9850"][:len(uniq_bins)]
                    dim_palette = palette_main + ["#64748b"]
                    dim_colorscale = build_discrete_colorscale(dim_palette)
                    dim_colorbar = dict(
                        title="Rentang IKD Agregat",
                        tickvals=list(range(len(uniq_bins))),
                        ticktext=bin_labels,
                    )
                    dim_hover_vals = [
                        (
                            f"{_safe_float_metric(dim_num.iloc[idx], default=np.nan):.3f}"
                            f" ({bin_labels[bin_map[bins.iloc[idx]]]}" + ")"
                            if pd.notnull(dim_num.iloc[idx]) and bins.iloc[idx] in bin_map else "NA"
                        )
                        for idx in range(len(node_ids))
                    ]
                    dim_marker_cmin = 0
                    dim_marker_cmax = max(len(uniq_bins), 1)
            elif dim_num.notna().sum() >= 3:
                dim_marker_vals = dim_num.tolist()
                dim_colorscale = "Blues"
                dim_colorbar = dict(title=graph_dim_label)
                dim_hover_vals = [f"{x:.3f}" if pd.notnull(x) else "NA" for x in dim_num]
            else:
                dim_cat = pd.Series(raw_dim_vals).fillna("Tidak Valid").astype(str)
                dim_uniqs = sorted(dim_cat.unique().tolist())
                dim_map = {v: i for i, v in enumerate(dim_uniqs)}
                dim_marker_vals = [dim_map[v] for v in dim_cat]
                dim_colorscale = [[0.0, "#0ea5e9"], [1.0, "#0ea5e9"]] if len(dim_uniqs) == 1 else [[i / (len(dim_uniqs) - 1), CONTRAST_COLORS[i % len(CONTRAST_COLORS)]] for i in range(len(dim_uniqs))]
                dim_colorbar = dict(
                    title=graph_dim_label,
                    tickvals=list(range(len(dim_uniqs))),
                    ticktext=dim_uniqs,
                )
                dim_hover_vals = dim_cat.tolist()

            dim_node_text = [
                (
                    f"Nama: {G.nodes[n].get('nama', '-')}"
                    f"<br>{graph_dim_label}: {dim_hover_vals[idx]}"
                    f"<br>IKD Agregat: {_safe_float_metric(G.nodes[n].get('f_ikr_dari_rekap_kk'), default=np.nan):.3f}"
                    f"<br>Klaster Louvain: {partition.get(n, -1)}"
                )
                for idx, n in enumerate(node_ids)
            ]
            fig_dim = go.Figure()
            add_network_edge_traces(
                fig_dim,
                visible_edges_focus,
                pos_focus,
                edge_min,
                edge_span,
                color_fn=edge_color_by_interaction,
                base_width=0.28,
                width_scale=0.78,
                hover=False,
            )
            fig_dim.add_trace(
                go.Scatter(
                    x=[pos_focus[n][0] for n in node_ids],
                    y=[pos_focus[n][1] for n in node_ids],
                    mode="markers",
                    marker=dict(
                        size=node_size_main,
                        color=dim_marker_vals,
                        colorscale=dim_colorscale,
                        cmin=dim_marker_cmin,
                        cmax=dim_marker_cmax,
                        showscale=True,
                        colorbar=dim_colorbar,
                        opacity=0.86,
                        line=dict(color=NETWORK_NODE_LINE, width=node_line_width),
                    ),
                    text=dim_node_text,
                    hoverinfo="text",
                    showlegend=False,
                )
            )
            style_network_figure(
                fig_dim,
                title=f"Jaringan Kemiripan Rumah Tangga Menurut {graph_dim_label}",
                height=690,
            )
            if graph_spatial_mode == "Layout Jaringan":
                st.plotly_chart(fig_dim, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
            else:
                fig_dim_spatial = build_spatial_node_figure(
                    G,
                    node_ids=node_ids,
                    node_color_vals=dim_marker_vals,
                    node_hover_text=dim_node_text,
                    title=f"Sebaran Spasial Rumah Tangga Menurut {graph_dim_label}",
                    spatial_mode=graph_spatial_mode,
                    marker_size=11,
                    colorscale=dim_colorscale,
                    colorbar=dim_colorbar,
                    cmin=dim_marker_cmin,
                    cmax=dim_marker_cmax,
                )
                if fig_dim_spatial is not None:
                    st.plotly_chart(fig_dim_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                else:
                    st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                    st.plotly_chart(fig_dim, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

            with subbab_dropdown("Graf Louvain dengan Warna Node IKD Agregat", expanded=False):
                ikr_vals = pd.to_numeric(
                    pd.Series([G.nodes[n].get("f_ikr_dari_rekap_kk") for n in node_ids]),
                    errors="coerce",
                )
                ikr_hover_vals = [f"{x:.3f}" if pd.notnull(x) else "NA" for x in ikr_vals]
                fig_ikr_focus = go.Figure()
                add_network_edge_traces(
                    fig_ikr_focus,
                    visible_edges_focus,
                    pos_focus,
                    edge_min,
                    edge_span,
                    color_fn=edge_color_by_interaction,
                    base_width=0.28,
                    width_scale=0.78,
                    hover=False,
                )
                marker_ikr = dict(
                    size=node_size_main,
                    line=dict(color=NETWORK_NODE_LINE, width=node_line_width),
                    opacity=0.86,
                    showscale=True,
                    colorbar=dict(title="IKD Agregat"),
                )
                if ikr_vals.notna().sum() >= 1:
                    valid_ikr = ikr_vals.dropna()
                    ikr_min = float(valid_ikr.min())
                    ikr_max = float(valid_ikr.max())
                    marker_ikr["color"] = ikr_vals.tolist()
                    marker_ikr["colorscale"] = "RdYlGn"
                    marker_ikr["cmin"] = ikr_min
                    marker_ikr["cmax"] = ikr_max
                    if ikr_max > ikr_min:
                        ikr_edges = np.linspace(ikr_min, ikr_max, 6)
                        ikr_mids = ((ikr_edges[:-1] + ikr_edges[1:]) / 2.0).tolist()
                        ikr_labels = [f"{ikr_edges[i]:.2f} - {ikr_edges[i+1]:.2f}" for i in range(len(ikr_edges) - 1)]
                        marker_ikr["colorbar"] = dict(
                            title="IKD Agregat<br>Rentang Nilai",
                            tickvals=ikr_mids,
                            ticktext=ikr_labels,
                        )
                    else:
                        marker_ikr["colorbar"] = dict(
                            title="IKD Agregat",
                            tickvals=[ikr_min],
                            ticktext=[f"{ikr_min:.2f}"],
                        )
                else:
                    marker_ikr["color"] = "#0ea5e9"
                    marker_ikr["showscale"] = False
                fig_ikr_focus.add_trace(
                    go.Scatter(
                        x=[pos_focus[n][0] for n in node_ids],
                        y=[pos_focus[n][1] for n in node_ids],
                        mode="markers",
                        marker=marker_ikr,
                        text=[
                            (
                                f"Nama: {G.nodes[n].get('nama', '-')}"
                                f"<br>IKD Agregat: {ikr_hover_vals[idx]}"
                                f"<br>{graph_dim_label}: {dim_hover_vals[idx]}"
                                f"<br>Klaster Louvain: {partition.get(n, -1)}"
                            )
                            for idx, n in enumerate(node_ids)
                        ],
                        hoverinfo="text",
                        showlegend=False,
                    )
                )
                style_network_figure(
                    fig_ikr_focus,
                    title="Jaringan Louvain dengan Pewarnaan IKD Agregat",
                    height=690,
                )
                ikr_node_text = [
                    (
                        f"Nama: {G.nodes[n].get('nama', '-')}"
                        f"<br>IKD Agregat: {ikr_hover_vals[idx]}"
                        f"<br>{graph_dim_label}: {dim_hover_vals[idx]}"
                        f"<br>Klaster Louvain: {partition.get(n, -1)}"
                    )
                    for idx, n in enumerate(node_ids)
                ]
                if graph_spatial_mode == "Layout Jaringan":
                    st.plotly_chart(fig_ikr_focus, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                else:
                    fig_ikr_spatial = build_spatial_node_figure(
                        G,
                        node_ids=node_ids,
                        node_color_vals=marker_ikr.get("color", [0.0 for _ in node_ids]) if isinstance(marker_ikr.get("color", None), list) else [0.0 for _ in node_ids],
                        node_hover_text=ikr_node_text,
                        title="Sebaran Spasial Louvain Berdasarkan IKD Agregat",
                        spatial_mode=graph_spatial_mode,
                        marker_size=11,
                        colorscale=marker_ikr.get("colorscale", "RdYlGn"),
                        colorbar=marker_ikr.get("colorbar", dict(title="IKD Agregat")),
                        cmin=marker_ikr.get("cmin"),
                        cmax=marker_ikr.get("cmax"),
                    )
                    if fig_ikr_spatial is not None:
                        st.plotly_chart(fig_ikr_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                    else:
                        st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                        st.plotly_chart(fig_ikr_focus, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

        with subbab_dropdown("Assortativity Numerik per Dimensi Kesejahteraan", expanded=False):
            st.caption(
                "Sesuai Newman (2003), nilai r tiap dimensi dihitung sebagai korelasi Pearson antar nilai atribut pada pasangan node yang terhubung (edge)."
            )
            st.caption(
                "Tujuan: meskipun graf dibangun dari gabungan 5 dimensi IKD, asortativitas dihitung per dimensi untuk melihat dimensi yang paling berkontribusi terhadap sekat sosial."
            )
            df_assort_ikr = build_ikr_assortativity_table(G, IKD_DIMENSION_MAP)
            if not df_assort_ikr.empty:
                summary_base_row = compute_base_five_dimension_summary(df_assort_ikr)
                df_assort_dims = (
                    df_assort_ikr[df_assort_ikr["Jenis"] == "Dimensi"]
                    .sort_values("Assortativity r", ascending=False)
                    .reset_index(drop=True)
                )
                df_assort_agg = (
                    df_assort_ikr[df_assort_ikr["Jenis"] == "Agregat"]
                    .sort_values("Assortativity r", ascending=False)
                    .reset_index(drop=True)
                )
                if summary_base_row:
                    df_assort_agg = pd.concat([df_assort_agg, pd.DataFrame([summary_base_row])], ignore_index=True)
                    df_assort_agg = df_assort_agg.sort_values("Assortativity r", ascending=False).reset_index(drop=True)

                top_ikr = df_assort_dims.iloc[0] if not df_assort_dims.empty else df_assort_agg.iloc[0]

                st.markdown("#### Assortativity per Dimensi Kesejahteraan")
                df_assort_dims_display = df_assort_dims.drop(columns=["Kolom Internal"], errors="ignore")
                st.dataframe(
                    df_assort_dims_display.style.background_gradient(cmap="RdYlGn", subset=["Assortativity r"]),
                    use_container_width=True,
                )
                fig_assort_ikr_dim = px.bar(
                    df_assort_dims,
                    x="Assortativity r",
                    y="Dimensi IKD",
                    orientation="h",
                    color="Assortativity r",
                    color_continuous_scale="RdYlGn",
                    range_color=[-1, 1],
                    hover_data=["Sumber Skor", "Arah", "Kekuatan"],
                    title="Perbandingan Assortativity per Dimensi Kesejahteraan",
                )
                fig_assort_ikr_dim.add_vline(x=0.0, line_dash="dash", line_color="#64748b")
                fig_assort_ikr_dim.update_layout(height=420, yaxis_title="", xaxis_title="Koefisien Assortativity (r)")
                st.plotly_chart(fig_assort_ikr_dim, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                with subbab_dropdown("IKD Agregat dan Ringkasan Lima Dimensi", expanded=False):
                    df_assort_agg_display = df_assort_agg.drop(columns=["Kolom Internal"], errors="ignore")
                    st.dataframe(
                        df_assort_agg_display.style.background_gradient(cmap="RdYlGn", subset=["Assortativity r"]),
                        use_container_width=True,
                    )
                    fig_assort_ikr_agg = px.bar(
                        df_assort_agg,
                        x="Assortativity r",
                        y="Dimensi IKD",
                        orientation="h",
                        color="Assortativity r",
                        color_continuous_scale="RdYlGn",
                        range_color=[-1, 1],
                        hover_data=["Sumber Skor", "Arah", "Kekuatan"],
                        title="Perbandingan IKD Agregat dan Ringkasan Lima Dimensi",
                    )
                    fig_assort_ikr_agg.add_vline(x=0.0, line_dash="dash", line_color="#64748b")
                    fig_assort_ikr_agg.update_layout(height=320, yaxis_title="", xaxis_title="Koefisien Assortativity (r)")
                    st.plotly_chart(fig_assort_ikr_agg, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                with subbab_dropdown("Drill-Down Analitik: Dimensi -> Variabel", expanded=False):
                    dim_cfg = DRILLDOWN_DIMENSIONS[selected_dim_key]
                    dim_label = dim_cfg["label"]
                    dim_col = dim_cfg["aggregate_col"]
                    var_list = dim_cfg["variables"]

                    if dim_col in df_v.columns:
                        r_dim, method_dim = compute_assortativity_for_column(G, dim_col)
                        dir_dim, lvl_dim = interpret_assortativity_value(r_dim)
                    else:
                        r_dim, method_dim, dir_dim, lvl_dim = np.nan, "n/a", "Tidak tersedia", "-"

                    c_dr1, c_dr2, c_dr3 = st.columns(3)
                    c_dr1.metric("r Dimensi Terpilih", f"{_safe_float_metric(r_dim, default=0.0):.4f}", f"{dir_dim} | {lvl_dim}")
                    c_dr2.metric("Jumlah Variabel Penyusun", f"{len(var_list)}")
                    c_dr3.metric("Metode Layer Dimensi", method_dim)
                    r_ikr_agg, _ = compute_assortativity_for_column(G, "f_ikr_dari_rekap_kk")
                    dir_ikr_agg, lvl_ikr_agg = interpret_assortativity_value(r_ikr_agg)
                    c_ag1, c_ag2 = st.columns(2)
                    c_ag1.metric("r IKD Agregat", f"{_safe_float_metric(r_ikr_agg, default=0.0):.4f}", f"{dir_ikr_agg} | {lvl_ikr_agg}")
                    if summary_base_row:
                        c_ag2.metric(
                            "r Gabungan 5 Dimensi",
                            f"{float(summary_base_row['Assortativity r']):.4f}",
                            f"{summary_base_row['Arah']} | {summary_base_row['Kekuatan']}",
                        )
                    else:
                        c_ag2.metric("r Gabungan 5 Dimensi", "NA", "-")
                    st.caption(
                        f"Layer Struktural: {dim_label} | metode={method_dim}. "
                        "Layer Investigatif: seluruh variabel penyusun dimensi ditampilkan otomatis tanpa pemilihan variabel manual."
                    )
                    drill_rows = []
                    resolved_for_plot = []
                    for vcfg in var_list:
                        vcol = resolve_first_existing_column(df_v.columns, vcfg["candidates"])
                        if not vcol:
                            drill_rows.append(
                                {
                                    "Kode": vcfg["code"],
                                    "Variabel": vcfg["label"],
                                    "Kolom": "Tidak ditemukan",
                                    "r": np.nan,
                                    "Arah": "Tidak tersedia",
                                    "Kekuatan": "-",
                                    "Metode": "n/a",
                                    "Keterangan": vcfg["description"],
                                }
                            )
                            continue
                        r_v, m_v = compute_assortativity_for_column(G, vcol)
                        d_v, l_v = interpret_assortativity_value(r_v)
                        drill_rows.append(
                            {
                                "Kode": vcfg["code"],
                                "Variabel": vcfg["label"],
                                "Kolom": vcol,
                                "r": float(r_v),
                                "Arah": d_v,
                                "Kekuatan": l_v,
                                "Metode": m_v,
                                "Keterangan": vcfg["description"],
                            }
                        )
                        resolved_for_plot.append((vcfg, vcol, float(r_v)))

                    df_drill = pd.DataFrame(drill_rows)
                    st.dataframe(df_drill.style.background_gradient(cmap="RdYlGn", subset=["r"]), use_container_width=True)
                    if df_drill["r"].notna().any():
                        fig_drill_bar = px.bar(
                            df_drill[df_drill["r"].notna()].sort_values("r", ascending=False),
                            x="r",
                            y="Variabel",
                            orientation="h",
                            color="r",
                            color_continuous_scale="RdYlGn",
                            range_color=[-1, 1],
                            hover_data=["Kode", "Kolom", "Arah", "Kekuatan", "Metode"],
                            title=f"Perbandingan Assortativity Variabel Penyusun - {dim_label}",
                        )
                        fig_drill_bar.add_vline(x=0.0, line_dash="dash", line_color="#64748b")
                        fig_drill_bar.update_layout(height=420, yaxis_title="", xaxis_title="Koefisien Assortativity (r)")
                        st.plotly_chart(fig_drill_bar, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                    missing_vars = df_drill[df_drill["Kolom"] == "Tidak ditemukan"]["Kode"].tolist()
                    if missing_vars:
                        st.warning(f"Kolom belum terdeteksi untuk variabel: {', '.join(missing_vars)}")

                        with subbab_dropdown("Graf Pendukung per Variabel", expanded=False):
                            for vcfg, vcol, r_v in resolved_for_plot:
                                fig_var = go.Figure()
                                add_network_edge_traces(
                                    fig_var,
                                    visible_edges_focus,
                                    pos_focus,
                                    edge_min,
                                    edge_span,
                                    color_fn=edge_color_by_interaction,
                                    base_width=0.26,
                                    width_scale=0.72,
                                    hover=False,
                                )
                            raw_var_vals = [G.nodes[n].get(vcol) for n in node_ids]
                            num_var = pd.to_numeric(pd.Series(raw_var_vals), errors="coerce")
                            marker_cmin = None
                            marker_cmax = None
                            if num_var.notna().sum() >= 3:
                                marker_vals = num_var.tolist()
                                marker_scale = "RdYlGn"
                                marker_cbar = dict(title=vcfg["code"])
                                hover_vals = [f"{x:.3f}" if pd.notnull(x) else "NA" for x in num_var]
                                marker_cmin = float(num_var.min()) if num_var.notna().sum() > 0 else None
                                marker_cmax = float(num_var.max()) if num_var.notna().sum() > 0 else None
                            else:
                                cat_vals = pd.Series(raw_var_vals).fillna("Tidak Valid").astype(str)
                                uniq = sorted(cat_vals.unique().tolist())
                                cat_map = {v: i for i, v in enumerate(uniq)}
                                marker_vals = [cat_map[v] for v in cat_vals]
                                marker_scale = [[0.0, "#0ea5e9"], [1.0, "#0ea5e9"]] if len(uniq) == 1 else [[i / (len(uniq) - 1), CONTRAST_COLORS[i % len(CONTRAST_COLORS)]] for i in range(len(uniq))]
                                marker_cbar = dict(title=vcfg["code"], tickvals=list(range(len(uniq))), ticktext=uniq)
                                hover_vals = cat_vals.tolist()
                                marker_cmin = 0
                                marker_cmax = max(len(uniq) - 1, 1)
                                fig_var.add_trace(
                                    go.Scatter(
                                        x=[pos_focus[n][0] for n in node_ids],
                                        y=[pos_focus[n][1] for n in node_ids],
                                        mode="markers",
                                        marker=dict(
                                            size=node_size_main,
                                            color=marker_vals,
                                            colorscale=marker_scale,
                                            showscale=True,
                                            colorbar=marker_cbar,
                                            opacity=0.86,
                                            line=dict(color=NETWORK_NODE_LINE, width=node_line_width),
                                        ),
                                        text=[f"{G.nodes[n].get('nama','-')}<br>{vcfg['label']}: {hover_vals[idx]}<br>Klaster: {partition.get(n, -1)}" for idx, n in enumerate(node_ids)],
                                        hoverinfo="text",
                                        showlegend=False,
                                )
                            )
                                style_network_figure(
                                    fig_var,
                                    title=f"Jaringan Variabel {vcfg['label']} | r={r_v:.4f}",
                                    height=660,
                                )
                            var_hover_text = [
                                f"{G.nodes[n].get('nama','-')}<br>{vcfg['label']}: {hover_vals[idx]}<br>Klaster: {partition.get(n, -1)}"
                                for idx, n in enumerate(node_ids)
                            ]
                            if graph_spatial_mode == "Layout Jaringan":
                                st.plotly_chart(fig_var, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                            else:
                                fig_var_spatial = build_spatial_node_figure(
                                    G,
                                    node_ids=node_ids,
                                    node_color_vals=marker_vals,
                                    node_hover_text=var_hover_text,
                                    title=f"Sebaran Spasial Variabel {vcfg['label']} | r={r_v:.4f}",
                                    spatial_mode=graph_spatial_mode,
                                    marker_size=11,
                                    colorscale=marker_scale,
                                    cmin=marker_cmin,
                                    cmax=marker_cmax,
                                    colorbar=marker_cbar,
                                )
                                if fig_var_spatial is not None:
                                    st.plotly_chart(fig_var_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                                else:
                                    st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                                    st.plotly_chart(fig_var, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                    glossary_rows = []
                    for _, dcfg in DRILLDOWN_DIMENSIONS.items():
                        for vcfg in dcfg["variables"]:
                            glossary_rows.append(
                                {
                                    "Dimensi": dcfg["label"],
                                    "Variabel": vcfg["label"],
                                    "Deskripsi": vcfg["description"],
                                }
                            )
                    with st.expander("Kamus Variabel Penyusun Dimensi", expanded=False):
                        st.dataframe(pd.DataFrame(glossary_rows), use_container_width=True)
                        st.caption(
                            "Metode Assortativity dihitung berdasarkan Newman (2002) dan konteks segregasi merujuk pada Montes et al. (2018)."
                        )
                    st.markdown(
                        f"<div class='soft-card'><b>Interpretasi Dominan:</b><br>"
                        f"Dimensi dengan nilai r tertinggi saat ini adalah <b>{top_ikr['Dimensi IKD']}</b> "
                        f"({top_ikr['Sumber Skor']}) dengan r = <b>{float(top_ikr['Assortativity r']):.4f}</b> "
                        f"({top_ikr['Arah']} | {top_ikr['Kekuatan']}). "
                        f"Ini menunjukkan dimensi tersebut paling kuat berkontribusi pada pola sekat sosial dalam jaringan desa terpilih."
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            with subbab_dropdown("Audit Kebijakan: Assortativity Variabel Biner (Newman, 2003)", expanded=False):
                st.caption(
                    "Base graph tetap dibentuk dari lima dimensi kesejahteraan. Variabel Bansos, Internet, Ponsel, dan Spasial (dusun) hanya dipakai pada tahap audit assortativity atribut."
                )
                st.caption(
                    "Variabel dusun tidak diikutkan ke pembobotan graf, sehingga hasil audit spasial tetap objektif terhadap struktur graf dasar."
                )
                dusun_attr = "dusun" if "dusun" in df_v.columns else col_spasial
                dusun_codes = (
                    pd.Series([G.nodes[n].get(dusun_attr) for n in G.nodes()])
                    .fillna("Tidak Valid")
                    .astype("category")
                    .cat.codes
                    .tolist()
                )
                dusun_code_attr = "__audit_dusun_code"
                nx.set_node_attributes(G, {n: int(dusun_codes[idx]) for idx, n in enumerate(list(G.nodes()))}, dusun_code_attr)

                audit_specs = [
                    {"metric": "Assortativity Bansos", "col": "bansos_num", "kind": "binary"},
                    {"metric": "Assortativity Internet", "col": "internet_num", "kind": "binary"},
                    {"metric": "Assortativity Ponsel", "col": "ponsel_num", "kind": "binary"},
                    {"metric": f"Assortativity Spasial ({dusun_attr})", "col": dusun_attr, "kind": "categorical", "code_col": dusun_code_attr},
                ]

                biner_rows = []
                for spec in audit_specs:
                    r_attr = safe_attribute_assortativity(G, spec["col"], default=0.0)
                    direction_attr, strength_attr = interpret_assortativity_value(r_attr)
                    q_source_col = spec["col"] if spec["kind"] == "binary" else spec["code_col"]
                    montes_attr = compute_montes_within_between_assortativity(
                        G,
                        category_attr=q_source_col,
                        group_attr="cluster",
                        invalid_category_values=None,
                    )
                    biner_rows.append(
                        {
                            "Metrik": spec["metric"],
                            "Kolom": spec["col"],
                            "r": float(r_attr),
                            "Qw*": float(montes_attr["q_w_star"]),
                            "Qb*": float(montes_attr["q_b_star"]),
                            "Arah": direction_attr,
                            "Kekuatan": strength_attr,
                            "Label Steinley": steinley_segregation_label(r_attr),
                        }
                    )
                df_assort_biner = pd.DataFrame(biner_rows)
                fig_biner = px.bar(
                    df_assort_biner,
                    x="Metrik",
                    y="r",
                    color="r",
                    color_continuous_scale="RdYlGn",
                    range_color=[-1, 1],
                    title="Perbandingan Assortativity Audit Kebijakan & Spasial",
                    hover_data=["Kolom", "Qw*", "Qb*", "Arah", "Kekuatan", "Label Steinley"],
                )
                fig_biner.add_hline(y=0.0, line_dash="dash", line_color="#475569")
                fig_biner.update_traces(marker_line_color="#111827", marker_line_width=0.45)
                style_publication_figure(
                    fig_biner,
                    title="Perbandingan Assortativity Audit Kebijakan & Spasial",
                    height=420,
                    xaxis_title="",
                    yaxis_title="Koefisien Assortativity (r)",
                    showlegend=False,
                )
                st.plotly_chart(fig_biner, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                st.dataframe(
                    df_assort_biner.style.background_gradient(cmap="RdYlGn", subset=["r"]),
                    use_container_width=True,
                )
                with subbab_dropdown("Sebaran Dimensi dan IKD Agregat", expanded=False):
                    st.caption(
                        "Distribusi ini ditempatkan di bawah audit kebijakan karena dipakai untuk membaca konteks bansos/spasial terhadap kondisi dimensi dan IKD agregat desa."
                    )
                    df_graph_dims = pd.DataFrame(
                        [
                            {
                                "family_id": n,
                                "Klaster Louvain": int(partition.get(n, -1)),
                                "Sandang, Pangan, dan Papan": _safe_float_metric(G.nodes[n].get("f_a_dari_rekap_kk"), default=np.nan),
                                "Pendidikan": _safe_float_metric(G.nodes[n].get("f_b_dari_rekap_kk"), default=np.nan),
                                "Sosial, Hukum, dan HAM": _safe_float_metric(G.nodes[n].get("f_c_dari_rekap_kk"), default=np.nan),
                                "Kesehatan dan Pekerjaan": _safe_float_metric(G.nodes[n].get("f_d_dari_rekap_kk"), default=np.nan),
                                "Lingkungan dan Infrastruktur": _safe_float_metric(G.nodes[n].get("f_e_dari_rekap_kk"), default=np.nan),
                                "IKD Agregat": _safe_float_metric(G.nodes[n].get("f_ikr_dari_rekap_kk"), default=np.nan),
                            }
                            for n in node_ids
                        ]
                    )
                    dim_long = df_graph_dims.melt(
                        id_vars=["family_id", "Klaster Louvain"],
                        value_vars=list(PSEUDO_DIMENSION_COLS),
                        var_name="Dimensi",
                        value_name="Skor",
                    ).dropna(subset=["Skor"])

                    dist_tab1, dist_tab2, dist_tab3 = st.tabs(
                        ["Distribusi Lima Dimensi", "Per Dimensi per Klaster", "IKD Agregat Database"]
                    )
                    with dist_tab1:
                        if not dim_long.empty:
                            fig_dim_hist = px.histogram(
                                dim_long,
                                x="Skor",
                                color="Dimensi",
                                nbins=22,
                                barmode="overlay",
                                opacity=0.62,
                                title="Histogram Sebaran Skor Lima Dimensi (Node Graf)",
                            )
                            fig_dim_hist.update_layout(template="plotly_white", xaxis_title="Skor", yaxis_title="Frekuensi")
                            st.plotly_chart(fig_dim_hist, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                            fig_dim_box = px.box(
                                dim_long,
                                x="Dimensi",
                                y="Skor",
                                color="Dimensi",
                                title="Ringkasan Sebaran Lima Dimensi",
                            )
                            fig_dim_box.update_layout(template="plotly_white")
                            st.plotly_chart(fig_dim_box, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                            dim_summary = (
                                dim_long.groupby("Dimensi", as_index=False)
                                .agg(
                                    N=("Skor", "count"),
                                    Mean=("Skor", "mean"),
                                    Median=("Skor", "median"),
                                    Min=("Skor", "min"),
                                    Max=("Skor", "max"),
                                    Std=("Skor", "std"),
                                )
                                .sort_values("Dimensi")
                                .reset_index(drop=True)
                            )
                            st.dataframe(
                                dim_summary.style.format(
                                    {"Mean": "{:.2f}", "Median": "{:.2f}", "Min": "{:.2f}", "Max": "{:.2f}", "Std": "{:.2f}"}
                                ),
                                use_container_width=True,
                            )
                        else:
                            st.info("Data dimensi node graf belum cukup untuk visual distribusi.")

                    with dist_tab2:
                        if not dim_long.empty:
                            fig_cluster_violin = px.violin(
                                dim_long,
                                x="Dimensi",
                                y="Skor",
                                color="Klaster Louvain",
                                box=True,
                                points="outliers",
                                title="Sebaran Tiap Dimensi Menurut Klaster Louvain",
                            )
                            fig_cluster_violin.update_layout(template="plotly_white")
                            st.plotly_chart(fig_cluster_violin, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                        else:
                            st.info("Data per klaster untuk dimensi belum cukup.")

                    with dist_tab3:
                        df_db_ikr = df_v.copy()
                        if "f_ikr_dari_rekap_kk" in df_db_ikr.columns:
                            ikr_series = pd.to_numeric(df_db_ikr["f_ikr_dari_rekap_kk"], errors="coerce").dropna()
                            if not ikr_series.empty:
                                d1, d2, d3, d4 = st.columns(4)
                                d1.metric("N Data IKD Agregat", f"{int(ikr_series.shape[0])}")
                                d2.metric("Mean IKD Agregat", f"{float(ikr_series.mean()):.2f}")
                                d3.metric("Median IKD Agregat", f"{float(ikr_series.median()):.2f}")
                                d4.metric("Std IKD Agregat", f"{float(ikr_series.std()):.2f}")

                                fig_ikr_hist = px.histogram(
                                    x=ikr_series,
                                    nbins=24,
                                    title="Histogram IKD Agregat Keseluruhan (Database Desa Terpilih)",
                                    labels={"x": "IKD Agregat"},
                                )
                                fig_ikr_hist.add_vline(x=float(ikr_series.mean()), line_dash="dash", line_color="#1d4ed8", annotation_text="Mean")
                                fig_ikr_hist.add_vline(x=float(ikr_series.median()), line_dash="dot", line_color="#0f766e", annotation_text="Median")
                                fig_ikr_hist.update_layout(template="plotly_white", yaxis_title="Frekuensi")
                                st.plotly_chart(fig_ikr_hist, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                                cat_df = add_bps_ikr_category(df_db_ikr, ikr_col="f_ikr_dari_rekap_kk")
                                cat_order = ordered_existing_categories(cat_df["kategori_ikr"], BPS_CATEGORY_ORDER)
                                cat_count = (
                                    cat_df["kategori_ikr"]
                                    .value_counts()
                                    .reindex(cat_order, fill_value=0)
                                    .rename_axis("Kategori BPS")
                                    .reset_index(name="Jumlah")
                                )
                                if cat_count.empty:
                                    st.info("Kategori BPS valid belum tersedia pada data desa terpilih.")
                                else:
                                    fig_cat = px.bar(
                                        cat_count,
                                        x="Kategori BPS",
                                        y="Jumlah",
                                        color="Kategori BPS",
                                        color_discrete_map=BPS_CATEGORY_COLORS,
                                        title="Komposisi Kategori BPS dari IKD Agregat Database",
                                    )
                                    fig_cat.update_layout(template="plotly_white", showlegend=False)
                                    st.plotly_chart(fig_cat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                                    st.dataframe(cat_count, use_container_width=True)

                                    top_cat_row = cat_count.iloc[cat_count["Jumlah"].idxmax()]
                                    st.markdown(
                                        f"<div class='soft-card'><b>Interpretasi IKD Agregat Database:</b><br>"
                                        f"Distribusi IKD agregat desa ini memiliki rerata <b>{float(ikr_series.mean()):.2f}</b> "
                                        f"dan median <b>{float(ikr_series.median()):.2f}</b>. "
                                        f"Kategori BPS paling dominan adalah <b>{top_cat_row['Kategori BPS']}</b> "
                                        f"dengan jumlah <b>{int(top_cat_row['Jumlah'])}</b> rumah tangga.</div>",
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.info("Kolom IKD agregat tersedia, tetapi nilainya belum valid untuk distribusi.")
                        else:
                            st.info("Kolom IKD agregat tidak ditemukan di database desa terpilih.")
            with subbab_dropdown("Visualisasi Jaringan Audit Kebijakan", expanded=False):
                raw_bansos_col = resolve_first_existing_column(df_v.columns, ["bansos", "keikutsertaan program bantuan"])
                raw_media_col = resolve_first_existing_column(df_v.columns, ["media informasi", "media_informasi", "wifi", "medsos"])
                raw_ponsel_col = resolve_first_existing_column(df_v.columns, ["kepemilikan ponsel", "kepemilikan_ponsel", "ponsel", "hp"])
                audit_graph_specs = [
                    {
                        "title": "Jaringan Audit Bantuan Sosial",
                        "col": "bansos_num",
                        "label": "Status Bansos",
                        "yes_label": "Penerima Bantuan",
                        "no_label": "Tidak Menerima Bantuan",
                        "raw_col": raw_bansos_col,
                    },
                    {
                        "title": "Jaringan Audit Akses Internet dan Media Informasi",
                        "col": "internet_num",
                        "label": "Akses Internet/Media Informasi",
                        "yes_label": "Memiliki Akses Informasi",
                        "no_label": "Tidak Memiliki Akses Informasi",
                        "raw_col": raw_media_col,
                    },
                    {
                        "title": "Jaringan Audit Kepemilikan Ponsel",
                        "col": "ponsel_num",
                        "label": "Kepemilikan Ponsel",
                        "yes_label": "Memiliki Ponsel",
                        "no_label": "Tidak Memiliki Ponsel",
                        "raw_col": raw_ponsel_col,
                    },
                    {
                        "title": f"Jaringan Audit Spasial ({dusun_attr})",
                        "col": dusun_attr,
                        "label": f"Wilayah {dusun_attr}",
                        "kind": "categorical",
                        "raw_col": dusun_attr,
                    },
                ]
                tabs_audit = st.tabs([s["title"] for s in audit_graph_specs])
                for idx_tab, spec in enumerate(audit_graph_specs):
                    with tabs_audit[idx_tab]:
                        row_m = df_assort_biner[df_assort_biner["Kolom"] == spec["col"]]
                        if row_m.empty and spec.get("kind") == "categorical":
                            row_m = df_assort_biner[df_assort_biner["Kolom"] == dusun_attr]
                        if not row_m.empty:
                            m1, m2, m3 = st.columns(3)
                            m1.metric("r", f"{float(row_m.iloc[0]['r']):.4f}")
                            m2.metric("Qw*", f"{float(row_m.iloc[0]['Qw*']):.4f}")
                            m3.metric("Qb*", f"{float(row_m.iloc[0]['Qb*']):.4f}")
                        fig_audit_graph = go.Figure()
                        add_network_edge_traces(
                            fig_audit_graph,
                            visible_edges_focus,
                            pos_focus,
                            edge_min,
                            edge_span,
                            color_fn=edge_color_by_interaction,
                            base_width=0.26,
                            width_scale=0.72,
                            hover=False,
                        )
                        if spec.get("kind") == "categorical":
                            cat_vals = pd.Series([G.nodes[n].get(spec["col"]) for n in node_ids]).fillna("Tidak Valid").astype(str)
                            if spec["col"] == dusun_attr and graph_spatial_mode != "Layout Jaringan":
                                node_color_vals = [cid_to_idx.get(partition.get(n, -1), 0) for n in node_ids]
                                node_colorscale = cluster_colorscale
                                colorbar_cfg = dict(
                                    title="Klaster Louvain",
                                    tickvals=list(range(len(cluster_ids_sorted))),
                                    ticktext=[f"Klaster {cid}" for cid in cluster_ids_sorted],
                                )
                            else:
                                uniq = sorted(cat_vals.unique().tolist())
                                cmap = {v: i for i, v in enumerate(uniq)}
                                node_color_vals = [cmap[v] for v in cat_vals]
                                node_colorscale = [[0.0, "#0ea5e9"], [1.0, "#0ea5e9"]] if len(uniq) == 1 else [[i / (len(uniq) - 1), CONTRAST_COLORS[i % len(CONTRAST_COLORS)]] for i in range(len(uniq))]
                                colorbar_cfg = dict(
                                    title=spec["label"],
                                    tickvals=list(range(len(uniq))),
                                    ticktext=uniq,
                                )
                            state_text = cat_vals.tolist()
                        else:
                            bin_vals = [int(_safe_float_metric(G.nodes[n].get(spec["col"]), default=0.0) > 0) for n in node_ids]
                            node_color_vals = bin_vals
                            node_colorscale = [[0.0, DDP_RED], [1.0, BINARY_COLOR_MAP["YA"]]]
                            colorbar_cfg = dict(
                                title=spec["label"],
                                tickvals=[0, 1],
                                ticktext=[spec["no_label"], spec["yes_label"]],
                            )
                            state_text = [spec["yes_label"] if v == 1 else spec["no_label"] for v in bin_vals]
                        fig_audit_graph.add_trace(
                            go.Scatter(
                                x=[pos_focus[n][0] for n in node_ids],
                                y=[pos_focus[n][1] for n in node_ids],
                                mode="markers",
                                    marker=dict(
                                        size=node_size_main,
                                        color=node_color_vals,
                                        colorscale=node_colorscale,
                                        cmin=0,
                                        cmax=1 if spec.get("kind") != "categorical" else max(len(set(node_color_vals)) - 1, 1),
                                        showscale=True,
                                        colorbar=colorbar_cfg,
                                        opacity=0.86,
                                        line=dict(color=NETWORK_NODE_LINE, width=node_line_width),
                                    ),
                                text=[
                                    (
                                        f"Nama: {G.nodes[n].get('nama', '-')}"
                                        f"<br>{graph_dim_label}: {_safe_float_metric(G.nodes[n].get(graph_dim_col), default=np.nan):.3f}"
                                        f"<br>IKD Agregat: {_safe_float_metric(G.nodes[n].get('f_ikr_dari_rekap_kk'), default=np.nan):.3f}"
                                        f"<br>{spec['label']}: {state_text[i]}"
                                        f"<br>Jenis/Detail: {G.nodes[n].get(spec['raw_col'], '-') if spec['raw_col'] else '-'}"
                                    )
                                    for i, n in enumerate(node_ids)
                                ],
                                hoverinfo="text",
                                showlegend=False,
                            )
                        )
                        audit_node_text = [
                            (
                                f"Nama: {G.nodes[n].get('nama', '-')}"
                                f"<br>{graph_dim_label}: {_safe_float_metric(G.nodes[n].get(graph_dim_col), default=np.nan):.3f}"
                                f"<br>IKD Agregat: {_safe_float_metric(G.nodes[n].get('f_ikr_dari_rekap_kk'), default=np.nan):.3f}"
                                f"<br>{spec['label']}: {state_text[i]}"
                                f"<br>Jenis/Detail: {G.nodes[n].get(spec['raw_col'], '-') if spec['raw_col'] else '-'}"
                            )
                            for i, n in enumerate(node_ids)
                        ]
                        style_network_figure(fig_audit_graph, title=spec["title"], height=660)
                        if graph_spatial_mode == "Layout Jaringan":
                            st.plotly_chart(fig_audit_graph, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                        else:
                            fig_audit_spatial = build_spatial_node_figure(
                                G,
                                node_ids=node_ids,
                                node_color_vals=node_color_vals,
                                node_hover_text=audit_node_text,
                                title=f"{spec['title']} (Sebaran Spasial Node)",
                                spatial_mode=graph_spatial_mode,
                                marker_size=11,
                                colorscale=node_colorscale,
                                cmin=0,
                                cmax=1 if spec.get("kind") != "categorical" else max(len(set(node_color_vals)) - 1, 1),
                                colorbar=colorbar_cfg,
                            )
                            if fig_audit_spatial is not None:
                                st.plotly_chart(fig_audit_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                            else:
                                st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                                st.plotly_chart(fig_audit_graph, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                        if spec.get("kind") == "categorical" and spec["col"] == dusun_attr:
                            st.markdown("##### Komposisi Klaster per Dusun (Mengacu Graf Base Louvain)")
                            if "df_dusun_cluster_wide" in locals() and not df_dusun_cluster_wide.empty:
                                pct_cols_tab = [c for c in df_dusun_cluster_wide.columns if c.endswith("Persentase (%)")]
                                fmt_cols_tab = {c: "{:.1f}" for c in pct_cols_tab}
                                count_cols_tab = [c for c in df_dusun_cluster_wide.columns if c.endswith("Jumlah KK") or c == "Total KK Dusun"]
                                fmt_cols_tab.update({c: "{:,.0f}" for c in count_cols_tab})
                                st.dataframe(
                                    df_dusun_cluster_wide.style.format(fmt_cols_tab).background_gradient(cmap="YlGnBu", subset=pct_cols_tab),
                                    use_container_width=True,
                                )
                            else:
                                st.info("Tabel proporsi klaster per dusun belum tersedia untuk graf aktif.")

            with subbab_dropdown("Rincian Persentase Keterhubungan Audit Biner", expanded=False):
                st.caption(
                    "Bagian ini memecah nilai audit bansos, internet, dan ponsel menjadi pasangan `YA-YA`, `YA-TIDAK`, dan `TIDAK-TIDAK`, "
                    "lalu dipisah ke ruang `Within` dan `Between` agar nilai r, Qw*, dan Qb* lebih mudah dijelaskan."
                )
                binary_breakdown_specs = [
                    {
                        "title": "Bansos",
                        "col": "bansos_num",
                        "yes_label": "Penerima",
                        "no_label": "Non-Penerima",
                    },
                    {
                        "title": "Internet",
                        "col": "internet_num",
                        "yes_label": "Punya Akses",
                        "no_label": "Tidak Punya Akses",
                    },
                    {
                        "title": "Ponsel",
                        "col": "ponsel_num",
                        "yes_label": "Punya Ponsel",
                        "no_label": "Tidak Punya Ponsel",
                    },
                ]
                tabs_binary_detail = st.tabs([f"Rincian {spec['title']}" for spec in binary_breakdown_specs])
                for spec, tab in zip(binary_breakdown_specs, tabs_binary_detail):
                    with tab:
                        _, df_bin_summary, df_bin_matrix = build_labeled_attribute_connection_breakdown(
                            G,
                            attr_name=spec["col"],
                            value_map={
                                1: spec["yes_label"],
                                0: spec["no_label"],
                                "1": spec["yes_label"],
                                "0": spec["no_label"],
                                "1.0": spec["yes_label"],
                                "0.0": spec["no_label"],
                            },
                            group_attr="cluster",
                            category_order=[spec["yes_label"], spec["no_label"], "Tidak Valid"],
                            invalid_label="Tidak Valid",
                        )
                        if df_bin_summary.empty:
                            st.info(f"Belum ada edge yang cukup untuk audit rinci {spec['title']}.")
                            continue

                        same_share_bin = (
                            df_bin_summary[df_bin_summary["Jenis Pasangan"] == "Sama"]
                            .groupby("Ruang")["Persentase Bobot (%)"]
                            .sum()
                            .to_dict()
                        )
                        top_within_bin = (
                            df_bin_summary[df_bin_summary["Ruang"] == "Within"]
                            .sort_values("Persentase Bobot (%)", ascending=False)
                            .head(1)
                        )
                        top_between_bin = (
                            df_bin_summary[df_bin_summary["Ruang"] == "Between"]
                            .sort_values("Persentase Bobot (%)", ascending=False)
                            .head(1)
                        )
                        c_bd_1, c_bd_2, c_bd_3, c_bd_4 = st.columns(4)
                        c_bd_1.metric("Share Sama Within", f"{float(same_share_bin.get('Within', 0.0)):.2f}%")
                        c_bd_2.metric("Share Sama Between", f"{float(same_share_bin.get('Between', 0.0)):.2f}%")
                        c_bd_3.metric(
                            "Dominan Within",
                            top_within_bin.iloc[0]["Pasangan"] if not top_within_bin.empty else "-",
                            f"{float(top_within_bin.iloc[0]['Persentase Bobot (%)']):.2f}%" if not top_within_bin.empty else None,
                        )
                        c_bd_4.metric(
                            "Dominan Between",
                            top_between_bin.iloc[0]["Pasangan"] if not top_between_bin.empty else "-",
                            f"{float(top_between_bin.iloc[0]['Persentase Bobot (%)']):.2f}%" if not top_between_bin.empty else None,
                        )

                        scope_tabs = st.tabs(["Within", "Between"])
                        for scope_name, scope_tab in zip(["Within", "Between"], scope_tabs):
                            with scope_tab:
                                df_scope_bin = df_bin_summary[df_bin_summary["Ruang"] == scope_name].copy()
                                if df_scope_bin.empty:
                                    st.info(f"Tidak ada edge pada ruang {scope_name}.")
                                    continue
                                st.dataframe(
                                    df_scope_bin[
                                        [
                                            "Pasangan",
                                            "Jenis Pasangan",
                                            "Bobot Edge",
                                            "Persentase Bobot (%)",
                                            "Jumlah Edge",
                                            "Persentase Edge (%)",
                                        ]
                                    ].style.background_gradient(cmap="YlGnBu", subset=["Persentase Bobot (%)", "Persentase Edge (%)"]),
                                    use_container_width=True,
                                )
                                df_scope_bin_matrix = df_bin_matrix[df_bin_matrix["Ruang"] == scope_name].copy()
                                if not df_scope_bin_matrix.empty:
                                    heat_bin = (
                                        df_scope_bin_matrix.pivot_table(
                                            index="Kategori Baris",
                                            columns="Kategori Kolom",
                                            values="Persentase Bobot (%)",
                                            aggfunc="sum",
                                            fill_value=0.0,
                                        )
                                        .reindex(index=[spec["yes_label"], spec["no_label"], "Tidak Valid"], columns=[spec["yes_label"], spec["no_label"], "Tidak Valid"], fill_value=0.0)
                                    )
                                    fig_bin_heat = px.imshow(
                                        heat_bin,
                                        text_auto=".1f",
                                        color_continuous_scale="YlGnBu",
                                        aspect="auto",
                                        title=f"Heatmap Persentase Bobot Edge - {spec['title']} ({scope_name})",
                                        labels=dict(x="Kategori Kolom", y="Kategori Baris", color="% Bobot"),
                                    )
                                    fig_bin_heat.update_layout(height=380)
                                    st.plotly_chart(fig_bin_heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                                same_scope_bin = df_scope_bin[df_scope_bin["Jenis Pasangan"] == "Sama"]["Persentase Bobot (%)"].sum()
                                diff_scope_bin = df_scope_bin[df_scope_bin["Jenis Pasangan"] == "Beda"]["Persentase Bobot (%)"].sum()
                                st.markdown(
                                    f"<div class='soft-card'><b>Interpretasi {spec['title']} - {scope_name}:</b><br>"
                                    f"Pasangan status yang sama menyumbang <b>{same_scope_bin:.2f}% bobot edge</b>, "
                                    f"sedangkan pasangan campuran menyumbang <b>{diff_scope_bin:.2f}%</b>. "
                                    f"Pasangan dominan adalah <b>{df_scope_bin.iloc[0]['Pasangan']}</b> "
                                    f"dengan kontribusi <b>{float(df_scope_bin.iloc[0]['Persentase Bobot (%)']):.2f}%</b>."
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )

            with subbab_dropdown("Audit Spasial per Dusun untuk Bansos, Internet, dan Ponsel", expanded=False):
                st.caption(
                    "Bagian ini melihat dusun sebagai unit wilayah. Hasilnya menunjukkan komposisi `YA` per dusun "
                    "serta seberapa besar bobot koneksi internal dusun yang terjadi pada pasangan `YA-YA`, `YA-TIDAK`, dan `TIDAK-TIDAK`."
                )
                spatial_indicator_specs = [
                    {"label": "Bansos", "col": "bansos_num"},
                    {"label": "Internet", "col": "internet_num"},
                    {"label": "Ponsel", "col": "ponsel_num"},
                ]
                df_spatial_profile = build_spatial_indicator_profile(
                    G,
                    dusun_attr=dusun_attr,
                    indicator_specs=spatial_indicator_specs,
                )
                if df_spatial_profile.empty:
                    st.info("Profil spasial per dusun belum dapat dihitung karena data dusun atau edge internal belum mencukupi.")
                else:
                    st.dataframe(
                        df_spatial_profile.style.background_gradient(
                            cmap="YlGnBu",
                            subset=[
                                "Bansos - Persentase YA (%)",
                                "Internet - Persentase YA (%)",
                                "Ponsel - Persentase YA (%)",
                                "Bansos - YA-YA Bobot (%)",
                                "Internet - YA-YA Bobot (%)",
                                "Ponsel - YA-YA Bobot (%)",
                            ],
                        ),
                        use_container_width=True,
                    )

                    heat_share = (
                        df_spatial_profile.set_index("Dusun")[
                            [
                                "Bansos - Persentase YA (%)",
                                "Internet - Persentase YA (%)",
                                "Ponsel - Persentase YA (%)",
                            ]
                        ]
                        .rename(
                            columns={
                                "Bansos - Persentase YA (%)": "Bansos (YA)",
                                "Internet - Persentase YA (%)": "Internet (YA)",
                                "Ponsel - Persentase YA (%)": "Ponsel (YA)",
                            }
                        )
                    )
                    fig_spatial_share = px.imshow(
                        heat_share,
                        text_auto=".1f",
                        color_continuous_scale="Blues",
                        aspect="auto",
                        title="Heatmap Persentase Status YA per Dusun",
                        labels=dict(x="Indikator", y="Dusun", color="% YA"),
                    )
                    fig_spatial_share.update_layout(height=420)
                    st.plotly_chart(fig_spatial_share, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                    heat_yy = (
                        df_spatial_profile.set_index("Dusun")[
                            [
                                "Bansos - YA-YA Bobot (%)",
                                "Internet - YA-YA Bobot (%)",
                                "Ponsel - YA-YA Bobot (%)",
                            ]
                        ]
                        .rename(
                            columns={
                                "Bansos - YA-YA Bobot (%)": "Bansos (YA-YA)",
                                "Internet - YA-YA Bobot (%)": "Internet (YA-YA)",
                                "Ponsel - YA-YA Bobot (%)": "Ponsel (YA-YA)",
                            }
                        )
                    )
                    fig_spatial_yy = px.imshow(
                        heat_yy,
                        text_auto=".1f",
                        color_continuous_scale="YlGnBu",
                        aspect="auto",
                        title="Heatmap Persentase Bobot Edge YA-YA Internal per Dusun",
                        labels=dict(x="Indikator", y="Dusun", color="% Bobot"),
                    )
                    fig_spatial_yy.update_layout(height=420)
                    st.plotly_chart(fig_spatial_yy, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                    dusun_rank_tabs = st.tabs(["Bansos per Dusun", "Internet per Dusun", "Ponsel per Dusun"])
                    for spec, rank_tab in zip(spatial_indicator_specs, dusun_rank_tabs):
                        with rank_tab:
                            label = spec["label"]
                            show_cols = [
                                "Dusun",
                                "Jumlah KK",
                                "Jumlah Edge Internal",
                                f"{label} - Jumlah YA",
                                f"{label} - Persentase YA (%)",
                                f"{label} - YA-YA Bobot (%)",
                                f"{label} - YA-TIDAK Bobot (%)",
                                f"{label} - TIDAK-TIDAK Bobot (%)",
                                f"{label} - YA-YA Edge (%)",
                            ]
                            df_rank = df_spatial_profile[show_cols].sort_values(f"{label} - YA-YA Bobot (%)", ascending=False).reset_index(drop=True)
                            st.dataframe(
                                df_rank.style.background_gradient(cmap="YlGnBu", subset=[f"{label} - Persentase YA (%)", f"{label} - YA-YA Bobot (%)"]),
                                use_container_width=True,
                            )
                            top_row = df_rank.iloc[0]
                            st.markdown(
                                f"<div class='soft-card'><b>Ringkasan {label} per Dusun:</b><br>"
                                f"Dusun dengan kekuatan koneksi internal `YA-YA` tertinggi adalah <b>{top_row['Dusun']}</b> "
                                f"dengan kontribusi <b>{float(top_row[f'{label} - YA-YA Bobot (%)']):.2f}% bobot edge internal</b>. "
                                f"Proporsi warga berstatus `YA` di dusun ini adalah <b>{float(top_row[f'{label} - Persentase YA (%)']):.2f}%</b>."
                                f"</div>",
                                unsafe_allow_html=True,
                            )

            with subbab_dropdown("Evaluasi Ketepatan Targeting (Layak = IKD Agregat Rendah + Sedang)", expanded=False):
                eval_cols_needed = {"family_id", "f_ikr_dari_rekap_kk", "kategori_ikr"}
                if not eval_cols_needed.issubset(set(df_v.columns)):
                    st.warning(
                        "Kolom evaluasi targeting belum lengkap. Pastikan tersedia family_id, IKD agregat, dan kategori IKD."
                    )
                else:
                    node_set_eval = set(node_ids)
                    df_eval = df_v[df_v["family_id"].isin(node_set_eval)].copy()
                    dropped_rows = int(df_v.shape[0] - df_eval.shape[0])
                    if dropped_rows > 0:
                        st.caption(
                            f"Catatan: {dropped_rows} KK berada di luar graf analisis aktif sehingga tidak masuk evaluasi targeting."
                        )
                    df_eval["IKD Agregat"] = pd.to_numeric(df_eval["f_ikr_dari_rekap_kk"], errors="coerce")
                    df_eval["Layak_Target"] = df_eval["kategori_ikr"].isin(["Rendah", "Sedang"]).astype(int)
                    df_eval["Klaster Louvain"] = df_eval["family_id"].map(
                        lambda fid: int(partition.get(fid, -1)) if fid in partition else -1
                    )
                    if "nama" not in df_eval.columns:
                        df_eval["nama"] = df_eval["family_id"].astype(str)
                    if "bansos_num" not in df_eval.columns:
                        st.info("Kolom `bansos_num` belum tersedia untuk evaluasi targeting bansos.")
                    else:
                        status = (pd.to_numeric(df_eval["bansos_num"], errors="coerce").fillna(0) > 0).astype(int)
                        layak = df_eval["Layak_Target"].astype(int)
                        tp = int(((layak == 1) & (status == 1)).sum())
                        fn = int(((layak == 1) & (status == 0)).sum())
                        fp = int(((layak == 0) & (status == 1)).sum())
                        tn = int(((layak == 0) & (status == 0)).sum())
                        coverage = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
                        exclusion = (fn / (tp + fn)) if (tp + fn) > 0 else 0.0
                        inclusion = (fp / (tp + fp)) if (tp + fp) > 0 else 0.0
                        st.dataframe(
                            pd.DataFrame(
                                [{
                                    "Audit": "Bansos",
                                    "TP (Layak & Targeted)": tp,
                                    "FN (Layak & Tidak Targeted)": fn,
                                    "FP (Tidak Layak & Targeted)": fp,
                                    "TN (Tidak Layak & Tidak Targeted)": tn,
                                    "Coverage Layak (%)": coverage * 100.0,
                                    "Exclusion Error (%)": exclusion * 100.0,
                                    "Inclusion Error (%)": inclusion * 100.0,
                                }]
                            ).style.format(
                                {
                                    "Coverage Layak (%)": "{:.2f}",
                                    "Exclusion Error (%)": "{:.2f}",
                                    "Inclusion Error (%)": "{:.2f}",
                                }
                            ),
                            use_container_width=True,
                        )

                        show_cols = ["family_id", "nama", "Klaster Louvain", "IKD Agregat", "kategori_ikr"]
                        if dusun_attr in df_eval.columns:
                            show_cols.append(dusun_attr)
                        temp = df_eval.copy()
                        temp["status_target"] = status.values
                        exclusion_df = temp[(temp["Layak_Target"] == 1) & (temp["status_target"] == 0)].copy().sort_values("IKD Agregat", ascending=True)
                        inclusion_df = temp[(temp["Layak_Target"] == 0) & (temp["status_target"] == 1)].copy().sort_values("IKD Agregat", ascending=False)

                        c_ex, c_in = st.columns(2)
                        with c_ex:
                            st.markdown("**Bansos: 10 Teratas Exclusion (paling kritis)**")
                            st.dataframe(exclusion_df[show_cols].head(10), use_container_width=True)
                        with c_in:
                            st.markdown("**Bansos: 10 Teratas Inclusion (paling kritis)**")
                            st.dataframe(inclusion_df[show_cols].head(10), use_container_width=True)

            top_audit_row = df_assort_biner.iloc[df_assort_biner["r"].abs().idxmax()]
            audit_auto_lines = build_audit_auto_narrative(df_assort_biner)
            st.markdown(
                f"<div class='soft-card'><b>Narasi Otomatis Audit (r, Qw*, Qb*):</b><br>"
                f"{audit_auto_lines}<br><br>"
                f"<b>Ringkasan Dominan:</b> atribut dengan pola paling kuat saat ini adalah "
                f"<b>{top_audit_row['Metrik']}</b> (|r|={abs(float(top_audit_row['r'])):.3f})."
                f"</div>",
                unsafe_allow_html=True,
            )
            with subbab_dropdown("Within-Between Assortativity (Montes et al., 2018) dengan Kategori BPS 2014", expanded=False):
                if "f_ikr_dari_rekap_kk" not in df_v.columns:
                    st.warning("Kolom IKD agregat tidak tersedia, sehingga audit Within-Between Montes belum dapat dihitung.")
                else:
                    ikr_cat_lookup = (
                        df_v[["family_id", "kategori_ikr", "kategori_ikr_code"]]
                        .dropna(subset=["family_id"])
                        .drop_duplicates("family_id")
                        .set_index("family_id")
                        .to_dict("index")
                    )
                    nx.set_node_attributes(
                        G,
                        {
                            fid: {
                                "kategori_ikr": vals.get("kategori_ikr", "Tidak Valid"),
                                "kategori_ikr_code": int(vals.get("kategori_ikr_code", 0)),
                            }
                            for fid, vals in ikr_cat_lookup.items()
                            if fid in G.nodes()
                        },
                    )

                    cat_order = ordered_existing_categories(df_v["kategori_ikr"], BPS_CATEGORY_ORDER)
                    cat_dist = (
                        df_v["kategori_ikr"]
                        .value_counts()
                        .reindex(cat_order, fill_value=0)
                        .rename_axis("Kategori BPS")
                        .reset_index(name="Jumlah KK")
                    )
                    cat_dist["Persentase (%)"] = np.where(
                        cat_dist["Jumlah KK"].sum() > 0,
                        (cat_dist["Jumlah KK"] / cat_dist["Jumlah KK"].sum()) * 100.0,
                        0.0,
                    )
                    if cat_dist.empty:
                        st.info("Kategori BPS valid belum tersedia pada data desa terpilih.")
                    else:
                        st.dataframe(cat_dist, use_container_width=True)

                    montes_res = compute_montes_within_between_assortativity(
                        G,
                        category_attr="kategori_ikr_code",
                        group_attr="cluster",
                        invalid_category_values={0},
                    )
                    q_w_star = float(montes_res["q_w_star"])
                    q_b_star = float(montes_res["q_b_star"])

                    st.markdown("##### Visual Jaringan Louvain dengan Pewarnaan Kategori BPS")
                    st.caption(
                        "Node mengikuti hasil graf Louvain yang sama, tetapi warna node kini ditempelkan berdasarkan "
                        "kategori BPS (`kategori_ikr`) agar pola stratifikasi lebih mudah dilihat sebelum membaca Qw* dan Qb*. "
                        f"Mode aktif mengikuti sidebar: `{graph_spatial_mode}`."
                    )
                    if G.number_of_nodes() > 0 and cat_order:
                        fig_montes_graph = go.Figure()
                        node_ids_montes = list(G.nodes())
                        if "pos_focus" in locals() and isinstance(pos_focus, dict) and len(pos_focus) == G.number_of_nodes():
                            pos_montes = pos_focus
                        else:
                            pos_montes = build_clustered_network_layout(
                                G,
                                partition=partition,
                                layout_spread=layout_spread if "layout_spread" in locals() else 2.2,
                                seed=42,
                            )

                        edge_weights_montes = [
                            _safe_float_metric(d.get("weight"), default=0.0) for _, _, d in G.edges(data=True)
                        ]
                        edge_min_montes = float(min(edge_weights_montes)) if edge_weights_montes else 0.0
                        edge_max_montes = float(max(edge_weights_montes)) if edge_weights_montes else 1.0
                        edge_span_montes = max(edge_max_montes - edge_min_montes, 1e-9)

                        visible_edges_montes = (
                            visible_edges_focus
                            if "visible_edges_focus" in locals()
                            else select_representative_edges(G, max_edges=int(np.clip(G.number_of_nodes() * 1.45, 180, 950)), per_node=1)
                        )
                        add_network_edge_traces(
                            fig_montes_graph,
                            visible_edges_montes,
                            pos_montes,
                            edge_min_montes,
                            edge_span_montes,
                            color_fn=edge_color_by_interaction if "edge_color_by_interaction" in locals() else edge_color_by_weight,
                            base_width=0.26,
                            width_scale=0.72,
                            hover=True,
                        )

                        montes_hover_map = {
                            n: (
                                f"Nama: {G.nodes[n].get('nama', '-')}"
                                f"<br>family_id: {n}"
                                f"<br>Kategori BPS: {G.nodes[n].get('kategori_ikr', 'Tidak Valid')}"
                                f"<br>Kode BPS: {G.nodes[n].get('kategori_ikr_code', 0)}"
                                f"<br>IKD Agregat: {_safe_float_metric(G.nodes[n].get('f_ikr_dari_rekap_kk'), default=np.nan):.3f}"
                                f"<br>Klaster Louvain: {G.nodes[n].get('cluster', '-')}"
                            )
                            for n in node_ids_montes
                        }

                        for cat_label in cat_order:
                            cat_nodes = [
                                n for n in node_ids_montes
                                if str(G.nodes[n].get("kategori_ikr", "Tidak Valid")).strip() == cat_label
                            ]
                            if not cat_nodes:
                                continue
                            fig_montes_graph.add_trace(
                                go.Scatter(
                                    x=[pos_montes[n][0] for n in cat_nodes],
                                    y=[pos_montes[n][1] for n in cat_nodes],
                                    mode="markers",
                                        name=cat_label,
                                        marker=dict(
                                            size=node_size_main if "node_size_main" in locals() else network_marker_size(len(node_ids_montes), base=9.0),
                                            color=BPS_CATEGORY_COLORS.get(cat_label, BPS_FALLBACK_COLOR),
                                            opacity=0.86,
                                            line=dict(color=NETWORK_NODE_LINE, width=node_line_width if "node_line_width" in locals() else 0.45),
                                        ),
                                    text=[montes_hover_map[n] for n in cat_nodes],
                                    hoverinfo="text",
                                )
                            )

                        montes_hover_text = [montes_hover_map[n] for n in node_ids_montes]

                        style_network_figure(
                            fig_montes_graph,
                            title="Jaringan Louvain Menurut Kategori BPS",
                            height=660,
                            showlegend=True,
                        )
                        fig_montes_graph.update_layout(
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="left",
                                x=0.0,
                                title="Kategori BPS",
                            )
                        )
                        if graph_spatial_mode == "Layout Jaringan":
                            st.plotly_chart(fig_montes_graph, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                        else:
                            category_to_idx = {cat: idx for idx, cat in enumerate(cat_order)}
                            montes_color_vals = [
                                category_to_idx.get(str(G.nodes[n].get("kategori_ikr", "Tidak Valid")).strip(), len(cat_order) - 1)
                                for n in node_ids_montes
                            ]
                            bps_colorscale = build_discrete_colorscale(
                                [BPS_CATEGORY_COLORS.get(cat, BPS_FALLBACK_COLOR) for cat in cat_order]
                            )
                            fig_montes_spatial = build_spatial_node_figure(
                                G,
                                node_ids=node_ids_montes,
                                node_color_vals=montes_color_vals,
                                node_hover_text=montes_hover_text,
                                title="Sebaran Spasial Louvain Menurut Kategori BPS",
                                spatial_mode=graph_spatial_mode,
                                marker_size=12,
                                colorscale=bps_colorscale,
                                cmin=-0.5,
                                cmax=max(len(cat_order) - 0.5, 0.5),
                                colorbar=dict(
                                    title="Kategori BPS",
                                    tickmode="array",
                                    tickvals=list(range(len(cat_order))),
                                    ticktext=cat_order,
                                ),
                            )
                            if fig_montes_spatial is not None:
                                st.plotly_chart(fig_montes_spatial, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                            else:
                                st.warning("Mode spasial aktif, tetapi kolom lat/lon belum valid. Ditampilkan mode layout jaringan.")
                                st.plotly_chart(fig_montes_graph, use_container_width=True, config=PLOTLY_DRAW_CONFIG)
                    elif not cat_order:
                        st.info("Tidak ada kategori BPS valid untuk pewarnaan graf; visual kategori tidak ditampilkan.")
                    else:
                        st.info("Graf Louvain belum memiliki node yang cukup untuk divisualisasikan.")

                    m_m1, m_m2, m_m3, m_m4 = st.columns(4)
                    m_m1.metric("Qw*", f"{q_w_star:.5f}")
                    m_m2.metric("Qb*", f"{q_b_star:.5f}")
                    m_m3.metric("m_w (within weight)", f"{float(montes_res['m_w']):.4f}")
                    m_m4.metric("m_b (between weight)", f"{float(montes_res['m_b']):.4f}")

                    if q_w_star >= 0.40:
                        qw_interp = "Di dalam kelompok, warga sangat kompak pada strata IKD yang sama."
                    elif q_w_star >= 0.10:
                        qw_interp = "Di dalam kelompok, ada kecenderungan kompak pada strata IKD yang sama."
                    elif q_w_star > -0.10:
                        qw_interp = "Di dalam kelompok, kekompakan strata IKD masih campuran/lemah."
                    else:
                        qw_interp = "Di dalam kelompok, justru lebih banyak keterhubungan lintas strata IKD."

                    if q_b_star <= -0.40:
                        qb_interp = "Hampir tidak ada warga lintas klaster dari strata IKD yang sama saling terhubung."
                    elif q_b_star < -0.10:
                        qb_interp = "Hubungan lintas klaster cenderung terpisah menurut strata IKD."
                    elif q_b_star < 0.10:
                        qb_interp = "Hubungan lintas klaster untuk strata IKD bersifat campuran/netral."
                    else:
                        qb_interp = "Hubungan lintas klaster menunjukkan kemiripan strata IKD yang relatif kuat."

                    st.markdown(
                        f"<div class='soft-card'><b>Penjelasan Otomatis Within-Between:</b><br>"
                        f"<b>Qw (Within)</b>: Mengukur seberapa sering warga dalam satu klaster memiliki kategori IKD yang sama. "
                        f"(Hasil <b>{q_w_star:.2f}</b> berarti: {qw_interp})<br><br>"
                        f"<b>Qb (Between)</b>: Mengukur kemiripan strata IKD pada hubungan lintas klaster. "
                        f"(Hasil <b>{q_b_star:.2f}</b> berarti: {qb_interp})"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    valid_cat_dist = cat_dist.copy()
                    if not valid_cat_dist.empty and valid_cat_dist["Jumlah KK"].sum() > 0:
                        dominant_idx = valid_cat_dist["Jumlah KK"].idxmax()
                        dominant_cat = str(valid_cat_dist.loc[dominant_idx, "Kategori BPS"])
                        dominant_share = float(valid_cat_dist.loc[dominant_idx, "Persentase (%)"])
                    else:
                        dominant_cat = "Belum tersedia"
                        dominant_share = 0.0

                    if q_w_star >= 0.30 and q_b_star >= 0.30:
                        strat_joint = "Stratifikasi IKD kuat baik intra maupun antar-klaster; kesamaan strata IKD terbawa lintas komunitas."
                    elif q_w_star >= 0.30 and q_b_star < 0.10:
                        strat_joint = "Stratifikasi IKD kuat di dalam klaster, tetapi melemah saat lintas klaster; ada batas antarkomunitas."
                    elif q_w_star < 0.10 and q_b_star >= 0.30:
                        strat_joint = "Di dalam klaster masih campuran, tetapi lintas klaster justru memperlihatkan kesamaan strata yang kuat."
                    else:
                        strat_joint = "Pola stratifikasi IKD cenderung campuran; tidak ada pemisahan yang sangat tegas pada level klaster."

                    st.markdown(
                        f"<div class='soft-card'><b>Narasi Otomatis Stratifikasi BPS:</b><br>"
                        f"Kategori BPS dominan saat ini adalah <b>{dominant_cat}</b> "
                        f"dengan proporsi <b>{dominant_share:.2f}%</b> dari data valid.<br><br>"
                        f"{strat_joint}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    df_montes_plot = pd.DataFrame(
                        [
                            {"Komponen": "Qw* (Within)", "Nilai": q_w_star},
                            {"Komponen": "Qb* (Between)", "Nilai": q_b_star},
                        ]
                    )
                    fig_montes = px.bar(
                        df_montes_plot,
                        x="Komponen",
                        y="Nilai",
                        color="Nilai",
                        color_continuous_scale="RdYlGn",
                        title="Skor Normalized Within-Between Assortativity",
                    )
                    fig_montes.add_hline(y=0.0, line_dash="dash", line_color="#475569")
                    fig_montes.update_layout(height=380, yaxis_title="Nilai Q*")
                    st.plotly_chart(fig_montes, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                    st.caption(
                        "Implementasi delta(x_i, x_j) menggunakan kategori BPS 2014 dari IKD agregat; "
                        "delta(h_i, h_j) menggunakan keanggotaan klaster Louvain."
                    )

                    with subbab_dropdown("Rincian Persentase Keterhubungan per Pasangan Kategori BPS", expanded=False):
                        st.caption(
                            "Bagian ini memecah nilai Qw*/Qb* ke level pasangan kategori: misalnya `Rendah-Rendah`, `Rendah-Sedang`, "
                            "dan seterusnya. Persentase dihitung dari total bobot edge dalam ruang `Within` atau `Between`."
                        )
                        _, df_pair_summary, df_pair_matrix = build_category_connection_breakdown(
                            G,
                            category_attr="kategori_ikr",
                            group_attr="cluster",
                            category_order=cat_order,
                            invalid_label="Tidak Valid",
                        )
                        if df_pair_summary.empty:
                            st.info("Belum ada edge yang cukup untuk merinci pasangan kategori BPS pada level within/between.")
                        else:
                            same_share = (
                                df_pair_summary[df_pair_summary["Jenis Pasangan"] == "Sama"]
                                .groupby("Ruang")["Persentase Bobot (%)"]
                                .sum()
                                .to_dict()
                            )
                            top_within = df_pair_summary[df_pair_summary["Ruang"] == "Within"].sort_values("Bobot Edge", ascending=False).head(1)
                            top_between = df_pair_summary[df_pair_summary["Ruang"] == "Between"].sort_values("Bobot Edge", ascending=False).head(1)
                            c_pair_1, c_pair_2, c_pair_3, c_pair_4 = st.columns(4)
                            c_pair_1.metric("Share Sama Within", f"{float(same_share.get('Within', 0.0)):.2f}%")
                            c_pair_2.metric("Share Sama Between", f"{float(same_share.get('Between', 0.0)):.2f}%")
                            c_pair_3.metric(
                                "Pasangan Dominan Within",
                                top_within.iloc[0]["Pasangan"] if not top_within.empty else "-",
                                f"{float(top_within.iloc[0]['Persentase Bobot (%)']):.2f}%" if not top_within.empty else None,
                            )
                            c_pair_4.metric(
                                "Pasangan Dominan Between",
                                top_between.iloc[0]["Pasangan"] if not top_between.empty else "-",
                                f"{float(top_between.iloc[0]['Persentase Bobot (%)']):.2f}%" if not top_between.empty else None,
                            )

                            tabs_pair = st.tabs(["Within Klaster", "Between Klaster"])
                            for scope_name, tab in zip(["Within", "Between"], tabs_pair):
                                with tab:
                                    df_scope = df_pair_summary[df_pair_summary["Ruang"] == scope_name].copy()
                                    if df_scope.empty:
                                        st.info(f"Tidak ada edge untuk ruang {scope_name}.")
                                        continue
                                    df_scope_display = df_scope[
                                        [
                                            "Pasangan",
                                            "Jenis Pasangan",
                                            "Bobot Edge",
                                            "Persentase Bobot (%)",
                                            "Jumlah Edge",
                                            "Persentase Edge (%)",
                                        ]
                                    ].copy()
                                    st.dataframe(
                                        df_scope_display.style.background_gradient(cmap="YlGnBu", subset=["Persentase Bobot (%)", "Persentase Edge (%)"]),
                                        use_container_width=True,
                                    )

                                    df_scope_matrix = df_pair_matrix[df_pair_matrix["Ruang"] == scope_name].copy()
                                    if not df_scope_matrix.empty:
                                        heatmap_df = (
                                            df_scope_matrix.pivot_table(
                                                index="Kategori Baris",
                                                columns="Kategori Kolom",
                                                values="Persentase Bobot (%)",
                                                aggfunc="sum",
                                                fill_value=0.0,
                                            )
                                            .reindex(index=cat_order, columns=cat_order, fill_value=0.0)
                                        )
                                        fig_pair_heat = px.imshow(
                                            heatmap_df,
                                            text_auto=".1f",
                                            color_continuous_scale="YlGnBu",
                                            aspect="auto",
                                            title=f"Heatmap Persentase Bobot Edge - {scope_name}",
                                            labels=dict(x="Kategori Kolom", y="Kategori Baris", color="% Bobot"),
                                        )
                                        fig_pair_heat.update_layout(height=430)
                                        st.plotly_chart(fig_pair_heat, use_container_width=True, config=PLOTLY_DRAW_CONFIG)

                                    same_scope = df_scope[df_scope["Jenis Pasangan"] == "Sama"]["Persentase Bobot (%)"].sum()
                                    diff_scope = df_scope[df_scope["Jenis Pasangan"] == "Beda"]["Persentase Bobot (%)"].sum()
                                    st.markdown(
                                        f"<div class='soft-card'><b>Interpretasi {scope_name}:</b><br>"
                                        f"Pasangan kategori yang sama menyumbang <b>{same_scope:.2f}% bobot edge</b>, "
                                        f"sedangkan pasangan beda kategori menyumbang <b>{diff_scope:.2f}%</b>. "
                                        f"Pasangan dominan adalah <b>{df_scope.iloc[0]['Pasangan']}</b> "
                                        f"dengan kontribusi <b>{float(df_scope.iloc[0]['Persentase Bobot (%)']):.2f}%</b>."
                                        f"</div>",
                                        unsafe_allow_html=True,
                                    )

        st.info("Mode fokus aktif: proses dibatasi sampai graf base, Louvain, graf hasil, audit assortativity 5 dimensi IKD, audit kebijakan biner, dan audit Within-Between Montes (BPS 2014).")
        st.stop()

    else: st.error("Data tidak mencukupi untuk wilayah ini.")
else: st.info("Selamat Datang. Data default belum tersedia. Silakan unggah database desa untuk memulai Audit SNA.")





