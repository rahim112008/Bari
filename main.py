"""
🌾🐄🐝 AgriFood Innovation Hub v3.0 — Plateforme Universelle
Master IDEAS — Université de Bari Aldo Moro

Plateforme intégrée d'innovation agroalimentaire couvrant les 3 règnes :
végétal, animal, insectes. Pipeline rigoureux en 7 phases avec portes de qualité.

Modules : 17 modules ultra-complets
Applications intégrées : LiveGene, GenSmart, Apitrack, MetaInsight

Installation : pip install -r requirements.txt
Lancement    : streamlit run aih_app.py
"""

# ============================================================
# IMPORTS
# ============================================================
import gzip
import io
import json
import os
import sqlite3
import uuid
import warnings
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="🌾🐄🐝 AIH v3.0 — AgriFood Innovation Hub",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "aih_v3.db"
PHOTO_DIR = "aih_photos"
MORPHO_DIR = "aih_morpho"
EXPORT_DIR = "aih_exports"

for d in [PHOTO_DIR, MORPHO_DIR, EXPORT_DIR]:
    os.makedirs(d, exist_ok=True)

# Palette
VERT = "#2E7D32"
ORANGE = "#FF6F00"
BLEU = "#1565C0"
ROUGE = "#C62828"
VIOLET = "#6A1B9A"
CYAN = "#00838F"
MARRON = "#5D4037"
ROSE = "#C2185B"

LINKS = {
    "LiveGene Suite": "https://rahim112008-prchristinebaes-christinebaes-crxzog.streamlit.app/",
    "GenSmart": "https://rahim112008-genesmart-main-8fscxj.streamlit.app/",
    "Apitrack": "https://rahim112008-abeille8-abeille8-mgzzep.streamlit.app/",
    "MetaInsight v8": "https://metainseight9-genomics.streamlit.app/",
}

# ============================================================
# STYLES
# ============================================================
st.markdown("""
<style>
.main-header { font-size: 2.4rem; font-weight: bold; color: #2E7D32;
    text-align: center; margin-bottom: 0.2rem; }
.sub-header { font-size: 1.1rem; color: #666; text-align: center;
    margin-bottom: 1.5rem; }
.kpi-card { background-color: #F1F8E9; border-radius: 10px;
    padding: 18px; text-align: center; border-left: 5px solid #2E7D32;
    margin-bottom: 12px; }
.kpi-value { font-size: 1.8rem; font-weight: 700; color: #2E7D32; }
.kpi-label { font-size: 0.85rem; color: #666; text-transform: uppercase; }
.module-card { background: white; border-radius: 10px; padding: 18px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    border-top: 4px solid #2E7D32; margin-bottom: 12px; min-height: 130px; }
.info-box { background: #EAF5EA; border-left: 4px solid #2E7D32;
    padding: 12px; border-radius: 0 6px 6px 0; margin: 8px 0; }
.warn-box { background: #FFF8E1; border-left: 4px solid #FF6F00;
    padding: 12px; border-radius: 0 6px 6px 0; margin: 8px 0; }
.err-box { background: #FFEBEE; border-left: 4px solid #C62828;
    padding: 12px; border-radius: 0 6px 6px 0; margin: 8px 0; }
.phase-box { background: #F5F5F5; border-radius: 8px; padding: 12px;
    margin: 6px 0; border-left: 4px solid #1565C0; }
.gate-passed { background: #E8F5E9; border-left: 4px solid #2E7D32;
    padding: 10px; border-radius: 0 6px 6px 0; margin: 5px 0; }
.gate-failed { background: #FFEBEE; border-left: 4px solid #C62828;
    padding: 10px; border-radius: 0 6px 6px 0; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# UTILITAIRES
# ============================================================
def kpi(label, value, color=VERT):
    st.markdown(f'<div class="kpi-card" style="border-left-color:{color};">'
                f'<div class="kpi-value" style="color:{color};">{value}</div>'
                f'<div class="kpi-label">{label}</div></div>',
                unsafe_allow_html=True)


def header(icon, title, subtitle=""):
    st.markdown(f"## {icon} {title}")
    if subtitle:
        st.caption(subtitle)


def info(txt):
    st.markdown(f'<div class="info-box">{txt}</div>', unsafe_allow_html=True)


def warn(txt):
    st.markdown(f'<div class="warn-box">{txt}</div>', unsafe_allow_html=True)


def err(txt):
    st.markdown(f'<div class="err-box">{txt}</div>', unsafe_allow_html=True)


def dist(p1, p2):
    return float(np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2))


# ============================================================
# BASE DE DONNÉES
# ============================================================
@st.cache_resource
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    tables = [
        """CREATE TABLE IF NOT EXISTS exploitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, region TEXT,
            superficie_ha REAL, type_production TEXT, latitude REAL,
            longitude REAL, date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS parcelles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exploitation_id INTEGER,
            nom TEXT, culture TEXT, superficie_ha REAL, date_semis DATE)""",
        """CREATE TABLE IF NOT EXISTS animaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exploitation_id INTEGER,
            espece TEXT, identifiant TEXT, race TEXT, sexe TEXT,
            date_naissance DATE, poids_kg REAL, etat_sante TEXT)""",
        """CREATE TABLE IF NOT EXISTS ruches (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exploitation_id INTEGER,
            identifiant TEXT, reine_id TEXT, date_installation DATE,
            production_miel_kg REAL, etat_sante TEXT, population_estimee INTEGER)""",
        """CREATE TABLE IF NOT EXISTS phenotypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, parcelle_id INTEGER,
            animal_id INTEGER, ruche_id INTEGER, sujet_type TEXT,
            date_mesure DATE, hauteur_cm REAL, largeur_cm REAL,
            nombre_feuilles INTEGER, nombre_fruits INTEGER, poids_kg REAL,
            production_lait_l REAL, rendement_t_ha REAL, stade TEXT,
            etat_sanitaire TEXT, notes TEXT)""",
        """CREATE TABLE IF NOT EXISTS meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exploitation_id INTEGER,
            date DATE, temperature_c REAL, humidite_pct REAL,
            precipitation_mm REAL, vent_kmh REAL, pression_hpa REAL,
            description TEXT, source TEXT)""",
        """CREATE TABLE IF NOT EXISTS capteurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, parcelle_id INTEGER,
            date TIMESTAMP, temperature_sol_c REAL, humidite_sol_pct REAL,
            ph_sol REAL, ec_ds_m REAL, luminosite_lux REAL, source TEXT)""",
        """CREATE TABLE IF NOT EXISTS morphometrie (
            id INTEGER PRIMARY KEY AUTOINCREMENT, parcelle_id INTEGER,
            animal_id INTEGER, ruche_id INTEGER, sujet_type TEXT,
            date_mesure TIMESTAMP, photo_path TEXT, etalon_type TEXT,
            facteur_px_cm REAL, longueur_cm REAL, largeur_cm REAL,
            hauteur_cm REAL, diametre_cm REAL, surface_cm2 REAL,
            perimetre_cm REAL, ratio_forme REAL, notes TEXT)""",
        """CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, parcelle_id INTEGER,
            date TIMESTAMP, photo_path TEXT, latitude REAL, longitude REAL,
            description TEXT, type TEXT)""",
        """CREATE TABLE IF NOT EXISTS innovations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, titre TEXT, description TEXT,
            trl_actuel INTEGER, trl_cible INTEGER, secteur TEXT,
            impact INTEGER, faisabilite INTEGER,
            date_soumission TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS empreinte (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exploitation_id INTEGER,
            date DATE, production_kg REAL, co2_kg REAL, eau_l REAL,
            energie_kwh REAL, azote_kg REAL, notes TEXT)""",
        """CREATE TABLE IF NOT EXISTS biodiversite (
            id INTEGER PRIMARY KEY AUTOINCREMENT, parcelle_id INTEGER,
            date DATE, richesse_specifique INTEGER, shannon REAL,
            pollinisateurs INTEGER, auxiliaires INTEGER, notes TEXT)""",
        """CREATE TABLE IF NOT EXISTS pipeline_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TIMESTAMP,
            phase TEXT, action TEXT, details TEXT, operateur TEXT)""",
    ]
    for t in tables:
        cur.execute(t)
    conn.commit()


init_db()


def log_action(phase, action, details=""):
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO pipeline_logs (timestamp, phase, action, details) "
            "VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), phase, action, details))
        conn.commit()
    except Exception:
        pass


# ============================================================
# PIPELINE STATE
# ============================================================
PIPELINE_PHASES = [
    ("1_collecte", "📥 Collecte"),
    ("2_qc", "✅ Contrôle Qualité"),
    ("3_phenotypage", "📊 Phénotypage"),
    ("4_analyse", "🔬 Analyse"),
    ("5_modelisation", "🤖 Modélisation"),
    ("6_innovation", "💡 Innovation"),
    ("7_rapport", "📄 Rapport"),
]


def init_state():
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = {
            "phase_actuelle": "1_collecte",
            "phases_completees": [],
            "gates": {},
            "timestamp_debut": datetime.now().isoformat(),
        }
    if "current_module" not in st.session_state:
        st.session_state.current_module = "🏠 Tableau de bord"
    if "morpho_etalon" not in st.session_state:
        st.session_state.morpho_etalon = []
    if "morpho_mesure" not in st.session_state:
        st.session_state.morpho_mesure = []


init_state()


def show_pipeline_progress():
    cols = st.columns(len(PIPELINE_PHASES))
    current = st.session_state.pipeline["phase_actuelle"]
    for i, (key, label) in enumerate(PIPELINE_PHASES):
        with cols[i]:
            if key in st.session_state.pipeline["phases_completees"]:
                st.success(f"✅ {label}")
            elif key == current:
                st.info(f"🔄 {label}")
            else:
                st.markdown(f"⬜ {label}")


def check_gate(gate_id, conditions: Dict[str, bool]) -> bool:
    passed = all(conditions.values())
    st.session_state.pipeline["gates"][gate_id] = {
        "passed": passed, "conditions": conditions,
        "timestamp": datetime.now().isoformat()
    }
    for cond, ok in conditions.items():
        cls = "gate-passed" if ok else "gate-failed"
        mark = "✅" if ok else "❌"
        st.markdown(f'<div class="{cls}">{mark} {cond}</div>',
                    unsafe_allow_html=True)
    return passed


def mark_phase_complete(phase_key):
    if phase_key not in st.session_state.pipeline["phases_completees"]:
        st.session_state.pipeline["phases_completees"].append(phase_key)
    phases = [p[0] for p in PIPELINE_PHASES]
    idx = phases.index(phase_key)
    if idx + 1 < len(phases):
        st.session_state.pipeline["phase_actuelle"] = phases[idx + 1]
    log_action(phase_key, "Phase complétée")


# ============================================================
# BASE DES GÈNES OVINS (GenSmart)
# ============================================================
GENES_OVINS = {
    "BMP15":  {"nom": "Bone Morphogenetic Protein 15", "chr": "X",  "effet": "Fécondité",           "cat": "Reproduction"},
    "GDF9":   {"nom": "Growth Differentiation Factor 9", "chr": "5", "effet": "Fécondité",          "cat": "Reproduction"},
    "BMPR1B": {"nom": "BMP Receptor 1B (Booroola)", "chr": "6",    "effet": "Prolificité",         "cat": "Reproduction"},
    "MSTN":   {"nom": "Myostatin",                    "chr": "2",    "effet": "Hypertrophie musculaire", "cat": "Croissance"},
    "IGF2":   {"nom": "Insulin-like Growth Factor 2", "chr": "2",    "effet": "Croissance",          "cat": "Croissance"},
    "GH":     {"nom": "Growth Hormone",               "chr": "19",   "effet": "Croissance",          "cat": "Croissance"},
    "GHR":    {"nom": "Growth Hormone Receptor",      "chr": "16",   "effet": "Efficacité alimentaire", "cat": "Croissance"},
    "LALBA":  {"nom": "Alpha-Lactalbumin",            "chr": "3",    "effet": "Protéines lait",      "cat": "Lait"},
    "CSN3":   {"nom": "Kappa-Casein",                 "chr": "6",    "effet": "Qualité fromagère",   "cat": "Lait"},
    "DGAT1":  {"nom": "Diacylglycerol Acyltransferase 1", "chr": "14", "effet": "Matière grasse lait", "cat": "Lait"},
    "SCD":    {"nom": "Stearoyl-CoA Desaturase",      "chr": "22",   "effet": "Acides gras insaturés", "cat": "Lait"},
    "TLR4":   {"nom": "Toll-like Receptor 4",         "chr": "1",    "effet": "Résistance infections", "cat": "Résistance"},
    "MHC":    {"nom": "Major Histocompatibility Complex", "chr": "20", "effet": "Immunité",          "cat": "Résistance"},
    "PRNP":   {"nom": "Prion Protein",                "chr": "13",   "effet": "Résistance tremblante", "cat": "Résistance"},
    "CAST":   {"nom": "Calpastatin",                  "chr": "7",    "effet": "Tendreté viande",     "cat": "Qualité viande"},
    "CAPN1":  {"nom": "Calpain 1",                    "chr": "16",   "effet": "Tendreté viande",     "cat": "Qualité viande"},
    "FABP4":  {"nom": "Fatty Acid Binding Protein 4", "chr": "8",    "effet": "Marbling",            "cat": "Qualité viande"},
}

RACES_OVINES = {
    "Hamra":         {"origine": "Atlas saharien",      "aptitude": "Mixte",  "genes": ["BMP15", "GDF9"]},
    "Ouled Djellal": {"origine": "Steppes algériennes", "aptitude": "Viande", "genes": ["MSTN", "IGF2"]},
    "Sidahou":       {"origine": "Aurès",               "aptitude": "Lait",   "genes": ["LALBA", "CSN3", "DGAT1"]},
    "Rembi":         {"origine": "Tell",                "aptitude": "Mixte",  "genes": ["BMP15", "LALBA"]},
    "Autre":         {"origine": "Inconnue",            "aptitude": "Variable", "genes": []},
}

# ============================================================
# BASE DES GÈNES BOVINS (LiveGene)
# ============================================================
GENES_BOVINS = {
    "MSTN":   {"nom": "Myostatin",                    "chr": "2",  "effet": "Développement musculaire", "cat": "Croissance"},
    "IGF2":   {"nom": "Insulin-like Growth Factor 2", "chr": "2",  "effet": "Croissance",               "cat": "Croissance"},
    "GH":     {"nom": "Growth Hormone",               "chr": "19", "effet": "Croissance",               "cat": "Croissance"},
    "GHR":    {"nom": "Growth Hormone Receptor",      "chr": "16", "effet": "Efficacité alimentaire",   "cat": "Croissance"},
    "LALBA":  {"nom": "Alpha-Lactalbumin",            "chr": "3",  "effet": "Protéines lait",           "cat": "Lait"},
    "CSN3":   {"nom": "Kappa-Casein",                 "chr": "6",  "effet": "Qualité fromagère",        "cat": "Lait"},
    "DGAT1":  {"nom": "Diacylglycerol Acyltransferase 1", "chr": "14", "effet": "Matière grasse lait", "cat": "Lait"},
    "SCD":    {"nom": "Stearoyl-CoA Desaturase",      "chr": "22", "effet": "Acides gras insaturés",    "cat": "Lait"},
    "CAPN1":  {"nom": "Calpain 1",                    "chr": "16", "effet": "Tendreté viande",          "cat": "Qualité viande"},
    "CAST":   {"nom": "Calpastatin",                  "chr": "7",  "effet": "Tendreté viande",          "cat": "Qualité viande"},
    "FABP4":  {"nom": "Fatty Acid Binding Protein 4", "chr": "8",  "effet": "Marbling",                 "cat": "Qualité viande"},
    "TLR4":   {"nom": "Toll-like Receptor 4",         "chr": "1",  "effet": "Résistance infections",    "cat": "Résistance"},
    "MHC":    {"nom": "Major Histocompatibility Complex", "chr": "20", "effet": "Immunité",             "cat": "Résistance"},
}

RACES_BOVINES = {
    "Holstein":  {"origine": "Europe",         "aptitude": "Lait",   "genes": ["LALBA", "CSN3", "DGAT1", "SCD"]},
    "Montbéliarde": {"origine": "France",      "aptitude": "Mixte",  "genes": ["LALBA", "CSN3", "CAPN1"]},
    "Charolaise": {"origine": "France",        "aptitude": "Viande", "genes": ["MSTN", "IGF2", "CAPN1"]},
    "Limousine": {"origine": "France",         "aptitude": "Viande", "genes": ["MSTN", "CAPN1", "CAST"]},
    "Autre":     {"origine": "Inconnue",       "aptitude": "Variable", "genes": []},
}


# ============================================================
# MODULE 1 : TABLEAU DE BORD
# ============================================================
def mod_dashboard():
    st.markdown('<p class="main-header">🌾🐄🐝 AgriFood Innovation Hub v3.0</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Plateforme universelle d\'innovation '
                'agroalimentaire — Master IDEAS · Université de Bari</p>',
                unsafe_allow_html=True)

    conn = get_db()
    def cnt(t):
        try:
            return pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {t}", conn)["n"][0]
        except Exception:
            return 0

    n_exp = cnt("exploitations")
    n_parc = cnt("parcelles")
    n_anim = cnt("animaux")
    n_ruches = cnt("ruches")
    n_morpho = cnt("morphometrie")
    n_innov = cnt("innovations")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi("🏡 Exploitations", n_exp, VERT)
    with c2: kpi("🌾 Parcelles", n_parc, ORANGE)
    with c3: kpi("🐄 Animaux", n_anim, BLEU)
    with c4: kpi("🐝 Ruches", n_ruches, MARRON)
    with c5: kpi("📐 Morphométrie", n_morpho, VIOLET)
    with c6: kpi("💡 Innovations", n_innov, CYAN)

    st.divider()
    st.subheader("🚀 Pipeline rigoureux")
    show_pipeline_progress()

    st.divider()
    st.subheader("🧩 Architecture tripartite")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="module-card" style="border-top-color:{VERT};">'
                    f'<h3 style="color:{VERT};">🌾 VÉGÉTAL</h3>'
                    f'<p>Cultures · Arbres · Fruits · Légumes · Céréales</p></div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="module-card" style="border-top-color:{ORANGE};">'
                    f'<h3 style="color:{ORANGE};">🐄 ANIMAL</h3>'
                    f'<p>Bovins · Ovins · Caprins · Volailles</p></div>',
                    unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="module-card" style="border-top-color:{MARRON};">'
                    f'<h3 style="color:{MARRON};">🐝 INSECTES</h3>'
                    f'<p>Abeilles · Pollinisateurs · Insectes comestibles</p></div>',
                    unsafe_allow_html=True)

    st.divider()
    st.subheader("🔗 Applications liées")
    cols = st.columns(len(LINKS))
    for col, (name, url) in zip(cols, LINKS.items()):
        with col:
            st.markdown(f"**{name}**")
            st.markdown(f"[Ouvrir →]({url})")

    st.divider()
    info("💡 <b>AIH v3.0</b> intègre les <b>3 règnes du vivant</b> "
         "(végétal, animal, insectes), modélise leurs <b>interactions triangulaires</b>, "
         "et mobilise les <b>technologies les plus avancées</b> pour l'innovation agroalimentaire.")


# ============================================================
# MODULE 2 : COLLECTE DE DONNÉES
# ============================================================
def mod_collecte():
    header("📝", "Collecte de données",
           "Saisie de toutes les données terrain : exploitations, parcelles, "
           "animaux, ruches, phénotypes, météo, capteurs, photos, morphométrie.")

    tabs = st.tabs([
        "🏡 Exploitations", "🌾 Parcelles", "🐄 Animaux", "🐝 Ruches",
        "📏 Phénotypes", "🌤 Météo", "📡 Capteurs", "📷 Photos", "📐 Morphométrie"
    ])
    conn = get_db()

    # ---- TAB 1 : Exploitations ----
    with tabs[0]:
        st.subheader("🏡 Enregistrer une exploitation")
        with st.form("f_exp"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom *")
            region = c2.text_input("Région")
            sup = c1.number_input("Superficie (ha)", 0.0, 100000.0, 10.0, 0.5)
            typ = c2.selectbox("Type de production",
                ["Céréales", "Maraîchage", "Arboriculture", "Élevage",
                 "Oléagineux", "Apiculture", "Mixte", "Autre"])
            lat = c1.number_input("Latitude", -90.0, 90.0, 36.0, 0.001, format="%.6f")
            lon = c2.number_input("Longitude", -180.0, 180.0, 2.0, 0.001, format="%.6f")
            if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                if nom:
                    conn.execute(
                        "INSERT INTO exploitations (nom, region, superficie_ha, "
                        "type_production, latitude, longitude) VALUES (?,?,?,?,?,?)",
                        (nom, region, sup, typ, lat, lon))
                    conn.commit()
                    st.success(f"✅ Exploitation **{nom}** enregistrée.")
                    log_action("1_collecte", "Exploitation ajoutée", nom)
                else:
                    st.error("Le nom est obligatoire.")
        df = pd.read_sql_query("SELECT * FROM exploitations ORDER BY id DESC", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)

    # ---- TAB 2 : Parcelles ----
    with tabs[1]:
        st.subheader("🌾 Enregistrer une parcelle")
        df_exp = pd.read_sql_query("SELECT id, nom FROM exploitations", conn)
        if df_exp.empty:
            warn("⚠️ Enregistrez d'abord une exploitation.")
        else:
            opts = {f"{r['id']} — {r['nom']}": r['id'] for _, r in df_exp.iterrows()}
            with st.form("f_parc"):
                exp = st.selectbox("Exploitation *", list(opts.keys()))
                c1, c2 = st.columns(2)
                nom_p = c1.text_input("Nom de la parcelle *")
                cult = c2.selectbox("Culture",
                    ["Blé dur", "Blé tendre", "Orge", "Maïs", "Tomate",
                     "Olivier", "Agrumes", "Vigne", "Luzerne", "Caroubier", "Autre"])
                sup_p = c1.number_input("Superficie (ha)", 0.0, 1000.0, 1.0, 0.1)
                semis = c2.date_input("Date de semis", value=datetime.today().date())
                if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                    if nom_p:
                        conn.execute(
                            "INSERT INTO parcelles (exploitation_id, nom, culture, "
                            "superficie_ha, date_semis) VALUES (?,?,?,?,?)",
                            (opts[exp], nom_p, cult, sup_p, semis.isoformat()))
                        conn.commit()
                        st.success(f"✅ Parcelle **{nom_p}** enregistrée.")
                    else:
                        st.error("Le nom est obligatoire.")
            df_p = pd.read_sql_query("""
                SELECT p.*, e.nom AS exploitation FROM parcelles p
                LEFT JOIN exploitations e ON p.exploitation_id = e.id
                ORDER BY p.id DESC""", conn)
            if not df_p.empty:
                st.dataframe(df_p, use_container_width=True, hide_index=True)

    # ---- TAB 3 : Animaux ----
    with tabs[2]:
        st.subheader("🐄 Enregistrer un animal")
        df_exp = pd.read_sql_query("SELECT id, nom FROM exploitations", conn)
        if df_exp.empty:
            warn("⚠️ Enregistrez d'abord une exploitation.")
        else:
            opts = {f"{r['id']} — {r['nom']}": r['id'] for _, r in df_exp.iterrows()}
            with st.form("f_anim"):
                exp = st.selectbox("Exploitation *", list(opts.keys()))
                c1, c2, c3 = st.columns(3)
                esp = c1.selectbox("Espèce", ["Bovin", "Ovin", "Caprin", "Porcin", "Volaille"])
                ident = c2.text_input("Identifiant *")
                race = c3.text_input("Race")
                c1, c2, c3 = st.columns(3)
                sexe = c1.selectbox("Sexe", ["M", "F"])
                naiss = c2.date_input("Date de naissance", value=datetime.today().date())
                poids = c3.number_input("Poids (kg)", 0.0, 2000.0, 0.0, 0.5)
                sante = st.selectbox("État sanitaire",
                    ["Sain", "Surveillance", "Traitement", "Maladie"])
                if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                    if ident:
                        conn.execute(
                            "INSERT INTO animaux (exploitation_id, espece, identifiant, "
                            "race, sexe, date_naissance, poids_kg, etat_sante) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (opts[exp], esp, ident, race, sexe,
                             naiss.isoformat(), poids, sante))
                        conn.commit()
                        st.success(f"✅ Animal **{ident}** enregistré.")
                    else:
                        st.error("L'identifiant est obligatoire.")
            df_a = pd.read_sql_query("""
                SELECT a.*, e.nom AS exploitation FROM animaux a
                LEFT JOIN exploitations e ON a.exploitation_id = e.id
                ORDER BY a.id DESC""", conn)
            if not df_a.empty:
                st.dataframe(df_a, use_container_width=True, hide_index=True)

    # ---- TAB 4 : Ruches ----
    with tabs[3]:
        st.subheader("🐝 Enregistrer une ruche")
        df_exp = pd.read_sql_query("SELECT id, nom FROM exploitations", conn)
        if df_exp.empty:
            warn("⚠️ Enregistrez d'abord une exploitation.")
        else:
            opts = {f"{r['id']} — {r['nom']}": r['id'] for _, r in df_exp.iterrows()}
            with st.form("f_ruche"):
                exp = st.selectbox("Exploitation *", list(opts.keys()))
                c1, c2 = st.columns(2)
                ident = c1.text_input("Identifiant de la ruche *")
                reine = c2.text_input("ID de la reine")
                inst = c1.date_input("Date d'installation", value=datetime.today().date())
                miel = c2.number_input("Production miel (kg)", 0.0, 500.0, 0.0, 0.5)
                pop = c1.number_input("Population estimée", 0, 100000, 10000, 500)
                sante = c2.selectbox("État sanitaire",
                    ["Saine", "Varroa", "Loque", "Faible", "Essaimage"])
                if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                    if ident:
                        conn.execute(
                            "INSERT INTO ruches (exploitation_id, identifiant, reine_id, "
                            "date_installation, production_miel_kg, etat_sante, "
                            "population_estimee) VALUES (?,?,?,?,?,?,?)",
                            (opts[exp], ident, reine, inst.isoformat(),
                             miel, sante, pop))
                        conn.commit()
                        st.success(f"✅ Ruche **{ident}** enregistrée.")
                    else:
                        st.error("L'identifiant est obligatoire.")
            df_r = pd.read_sql_query("""
                SELECT r.*, e.nom AS exploitation FROM ruches r
                LEFT JOIN exploitations e ON r.exploitation_id = e.id
                ORDER BY r.id DESC""", conn)
            if not df_r.empty:
                st.dataframe(df_r, use_container_width=True, hide_index=True)

    # ---- TAB 5 : Phénotypes ----
    with tabs[4]:
        st.subheader("📏 Saisie de données phénotypiques")
        df_p = pd.read_sql_query("SELECT id, nom, culture FROM parcelles", conn)
        df_a = pd.read_sql_query("SELECT id, identifiant, espece FROM animaux", conn)
        df_r = pd.read_sql_query("SELECT id, identifiant FROM ruches", conn)

        sujet = st.radio("Type de sujet", ["🌾 Végétal", "🐄 Animal", "🐝 Ruche"],
                          horizontal=True)

        with st.form("f_pheno"):
            sujet_id = None
            if sujet == "🌾 Végétal" and not df_p.empty:
                opts = {f"{r['id']} — {r['nom']} ({r['culture']})": r['id']
                        for _, r in df_p.iterrows()}
                sujet_id = opts[st.selectbox("Parcelle", list(opts.keys()))]
            elif sujet == "🐄 Animal" and not df_a.empty:
                opts = {f"{r['id']} — {r['identifiant']} ({r['espece']})": r['id']
                        for _, r in df_a.iterrows()}
                sujet_id = opts[st.selectbox("Animal", list(opts.keys()))]
            elif sujet == "🐝 Ruche" and not df_r.empty:
                opts = {f"{r['id']} — {r['identifiant']}": r['id']
                        for _, r in df_r.iterrows()}
                sujet_id = opts[st.selectbox("Ruche", list(opts.keys()))]
            else:
                warn("⚠️ Aucun sujet disponible.")

            date_m = st.date_input("Date de mesure", value=datetime.today().date())
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("Hauteur (cm)", 0.0, 5000.0, 0.0, 0.5)
            l = c2.number_input("Largeur (cm)", 0.0, 5000.0, 0.0, 0.5)
            nf = c3.number_input("Nombre de feuilles", 0, 10000, 0)
            c1, c2, c3 = st.columns(3)
            nfr = c1.number_input("Nombre de fruits", 0, 10000, 0)
            poids = c2.number_input("Poids (kg)", 0.0, 5000.0, 0.0, 0.1)
            lait = c3.number_input("Production lait (L)", 0.0, 200.0, 0.0, 0.1)
            c1, c2 = st.columns(2)
            rend = c1.number_input("Rendement (t/ha)", 0.0, 100.0, 0.0, 0.1)
            stade = c2.selectbox("Stade / État",
                ["Germination", "Levée", "Croissance", "Floraison",
                 "Fructification", "Maturité", "Récolte",
                 "Lactation", "Gestation", "Tarie", "Ponte", "Hivernage"])
            sante = st.selectbox("État sanitaire",
                ["Sain", "Stress léger", "Stress sévère", "Maladie",
                 "Ravageurs", "Carence", "Varroa", "Loque"])
            notes = st.text_area("Notes", height=60)

            if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                if sujet_id:
                    conn.execute("""
                        INSERT INTO phenotypes (parcelle_id, animal_id, ruche_id,
                            sujet_type, date_mesure, hauteur_cm, largeur_cm,
                            nombre_feuilles, nombre_fruits, poids_kg,
                            production_lait_l, rendement_t_ha, stade,
                            etat_sanitaire, notes)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (sujet_id if sujet == "🌾 Végétal" else None,
                         sujet_id if sujet == "🐄 Animal" else None,
                         sujet_id if sujet == "🐝 Ruche" else None,
                         sujet, date_m.isoformat(), h, l, nf, nfr,
                         poids, lait, rend, stade, sante, notes))
                    conn.commit()
                    st.success("✅ Mesure phénotypique enregistrée.")

        df_ph = pd.read_sql_query(
            "SELECT * FROM phenotypes ORDER BY id DESC LIMIT 100", conn)
        if not df_ph.empty:
            st.dataframe(df_ph, use_container_width=True, hide_index=True)

    # ---- TAB 6 : Météo ----
    with tabs[5]:
        st.subheader("🌤 Collecte météorologique")
        df_exp = pd.read_sql_query(
            "SELECT id, nom, latitude, longitude FROM exploitations", conn)

        if df_exp.empty:
            warn("⚠️ Enregistrez d'abord une exploitation.")
        else:
            opts = {f"{r['id']} — {r['nom']}": r['id'] for _, r in df_exp.iterrows()}
            api_key = st.text_input("Clé API OpenWeather (optionnel)", type="password")
            exp_c = st.selectbox("Exploitation", list(opts.keys()))

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📡 Récupérer via API", use_container_width=True):
                    exp_id = opts[exp_c]
                    row = df_exp[df_exp["id"] == exp_id].iloc[0]
                    if api_key:
                        try:
                            url = (f"https://api.openweathermap.org/data/2.5/weather"
                                   f"?lat={row['latitude']}&lon={row['longitude']}"
                                   f"&appid={api_key}&units=metric")
                            r = requests.get(url, timeout=10)
                            if r.status_code == 200:
                                d = r.json()
                                conn.execute("""
                                    INSERT INTO meteo (exploitation_id, date,
                                        temperature_c, humidite_pct, precipitation_mm,
                                        vent_kmh, pression_hpa, description, source)
                                    VALUES (?,?,?,?,?,?,?,?,?)""",
                                    (exp_id, datetime.today().date().isoformat(),
                                     d["main"]["temp"], d["main"]["humidity"],
                                     d.get("rain", {}).get("1h", 0),
                                     d["wind"]["speed"] * 3.6,
                                     d["main"]["pressure"],
                                     d["weather"][0]["description"], "API"))
                                conn.commit()
                                st.success(f"✅ {d['main']['temp']}°C, "
                                           f"{d['main']['humidity']}% humidité")
                            else:
                                st.error("Erreur API")
                        except Exception as e:
                            st.error(f"Erreur : {e}")
                    else:
                        st.warning("Clé API manquante.")

            with c2:
                with st.expander("✍️ Saisie manuelle"):
                    with st.form("f_meteo_man"):
                        date_m = st.date_input("Date", value=datetime.today().date())
                        t = st.number_input("Température (°C)", -30.0, 60.0, 20.0, 0.5)
                        h = st.number_input("Humidité (%)", 0.0, 100.0, 60.0, 1.0)
                        p = st.number_input("Précipitations (mm)", 0.0, 500.0, 0.0, 0.5)
                        v = st.number_input("Vent (km/h)", 0.0, 200.0, 10.0, 0.5)
                        pr = st.number_input("Pression (hPa)", 900.0, 1100.0, 1013.0, 0.5)
                        d = st.text_input("Description", "Ensoleillé")
                        if st.form_submit_button("💾 Enregistrer"):
                            conn.execute("""
                                INSERT INTO meteo (exploitation_id, date,
                                    temperature_c, humidite_pct, precipitation_mm,
                                    vent_kmh, pression_hpa, description, source)
                                VALUES (?,?,?,?,?,?,?,?,?)""",
                                (opts[exp_c], date_m.isoformat(), t, h, p, v, pr, d, "Manuel"))
                            conn.commit()
                            st.success("✅ Météo enregistrée.")

            df_m = pd.read_sql_query(
                "SELECT * FROM meteo ORDER BY id DESC LIMIT 50", conn)
            if not df_m.empty:
                st.dataframe(df_m, use_container_width=True, hide_index=True)

    # ---- TAB 7 : Capteurs ----
    with tabs[6]:
        st.subheader("📡 Données capteurs")
        df_p = pd.read_sql_query("SELECT id, nom FROM parcelles", conn)
        if df_p.empty:
            warn("⚠️ Enregistrez d'abord une parcelle.")
        else:
            opts = {f"{r['id']} — {r['nom']}": r['id'] for _, r in df_p.iterrows()}
            parc_c = st.selectbox("Parcelle", list(opts.keys()))

            st.markdown("**Import CSV** (colonnes: date, temperature_sol_c, "
                        "humidite_sol_pct, ph_sol, ec_ds_m, luminosite_lux)")
            up = st.file_uploader("CSV capteurs", type=["csv"])
            if up:
                try:
                    df_csv = pd.read_csv(up)
                    if st.button("📥 Importer CSV"):
                        n = 0
                        for _, r in df_csv.iterrows():
                            try:
                                conn.execute("""
                                    INSERT INTO capteurs (parcelle_id, date,
                                        temperature_sol_c, humidite_sol_pct, ph_sol,
                                        ec_ds_m, luminosite_lux, source)
                                    VALUES (?,?,?,?,?,?,?,?)""",
                                    (opts[parc_c],
                                     str(r.get("date", datetime.now())),
                                     r.get("temperature_sol_c"),
                                     r.get("humidite_sol_pct"),
                                     r.get("ph_sol"),
                                     r.get("ec_ds_m"),
                                     r.get("luminosite_lux"), "CSV"))
                                n += 1
                            except Exception:
                                pass
                        conn.commit()
                        st.success(f"✅ {n} lignes importées.")
                except Exception as e:
                    st.error(f"Erreur : {e}")

            with st.expander("✍️ Saisie manuelle"):
                with st.form("f_capteur"):
                    c1, c2, c3 = st.columns(3)
                    ts = c1.number_input("T° sol (°C)", -20.0, 80.0, 20.0, 0.1)
                    hs = c2.number_input("Humidité sol (%)", 0.0, 100.0, 40.0, 0.5)
                    ph = c3.number_input("pH", 3.0, 10.0, 6.8, 0.1)
                    c1, c2 = st.columns(2)
                    ec = c1.number_input("EC (dS/m)", 0.0, 20.0, 1.5, 0.1)
                    lux = c2.number_input("Luminosité (lux)", 0.0, 150000.0, 20000.0, 1000.0)
                    if st.form_submit_button("💾 Enregistrer"):
                        conn.execute("""
                            INSERT INTO capteurs (parcelle_id, date, temperature_sol_c,
                                humidite_sol_pct, ph_sol, ec_ds_m, luminosite_lux, source)
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (opts[parc_c], datetime.now().isoformat(), ts, hs, ph, ec, lux, "Manuel"))
                        conn.commit()
                        st.success("✅ Enregistré.")

            df_c = pd.read_sql_query(
                "SELECT * FROM capteurs ORDER BY id DESC LIMIT 100", conn)
            if not df_c.empty:
                st.dataframe(df_c, use_container_width=True, hide_index=True)

    # ---- TAB 8 : Photos ----
    with tabs[7]:
        st.subheader("📷 Photos terrain")
        df_p = pd.read_sql_query("SELECT id, nom FROM parcelles", conn)
        if df_p.empty:
            warn("⚠️ Enregistrez d'abord une parcelle.")
        else:
            opts = {f"{r['id']} — {r['nom']}": r['id'] for _, r in df_p.iterrows()}
            with st.form("f_photo"):
                parc = st.selectbox("Parcelle", list(opts.keys()))
                photo = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
                c1, c2 = st.columns(2)
                lat = c1.number_input("Latitude", -90.0, 90.0, 36.0, 0.001)
                lon = c2.number_input("Longitude", -180.0, 180.0, 2.0, 0.001)
                desc = st.text_area("Description", height=60)
                if st.form_submit_button("💾 Enregistrer"):
                    if photo is not None:
                        fname = f"{uuid.uuid4().hex}.jpg"
                        fpath = os.path.join(PHOTO_DIR, fname)
                        with open(fpath, "wb") as f:
                            f.write(photo.getbuffer())
                        conn.execute("""
                            INSERT INTO photos (parcelle_id, date, photo_path,
                                latitude, longitude, description, type)
                            VALUES (?,?,?,?,?,?,?)""",
                            (opts[parc], datetime.now().isoformat(), fname,
                             lat, lon, desc, "terrain"))
                        conn.commit()
                        st.success("✅ Photo enregistrée.")
                        st.image(photo, width=400)

    # ---- TAB 9 : Morphométrie ----
    with tabs[8]:
        st.subheader("📐 Morphométrie 2D")
        st.markdown("**Principe** : placez un étalon visuel à côté de l'objet, "
                    "prenez une photo, cliquez sur les points de mesure.")

        ETALONS = {
            "reglet_30cm": ("Réglet 30 cm", 30.0),
            "piece_100da": ("Pièce 100 DA", 2.95),
            "carte_bancaire": ("Carte bancaire", 8.56),
            "feuille_a4": ("Feuille A4", 29.7),
        }

        df_p = pd.read_sql_query("SELECT id, nom FROM parcelles", conn)
        parc_options = ({"Aucune": None} if df_p.empty
                        else {f"{r['id']} — {r['nom']}": r['id']
                              for _, r in df_p.iterrows()})

        c1, c2 = st.columns(2)
        parc_c = c1.selectbox("Parcelle", list(parc_options.keys()))
        sujet = c2.selectbox("Type de sujet",
            ["Plante", "Feuille", "Fruit", "Épi", "Racine",
             "Animal", "Aile d'abeille", "Autre"])

        c1, c2 = st.columns(2)
        sujet_id = c1.text_input("ID du sujet", "S_001")
        etalon = c2.selectbox("Étalon", list(ETALONS.keys()),
                              format_func=lambda k: ETALONS[k][0])

        up = st.file_uploader("📷 Photo avec étalon", type=["jpg", "jpeg", "png"])

        if up:
            img = Image.open(up)
            img_arr = np.array(img.convert("RGB"))

            st.info("💡 Étape 1 : cliquez sur les 2 extrémités de l'étalon. "
                    "Étape 2 : cliquez sur les points de mesure.")

            try:
                from streamlit_image_coordinates import streamlit_image_coordinates

                st.markdown("### 🎯 Étape 1 : Calibration (2 points étalon)")
                coord1 = streamlit_image_coordinates(img, key="cal1")
                c1, c2 = st.columns(2)
                if c1.button("➕ Ajouter point étalon") and coord1:
                    if len(st.session_state.morpho_etalon) < 2:
                        st.session_state.morpho_etalon.append(
                            (coord1["x"], coord1["y"]))
                        st.rerun()
                if c2.button("🔄 Reset étalon"):
                    st.session_state.morpho_etalon = []
                    st.rerun()

                if len(st.session_state.morpho_etalon) == 2:
                    p1, p2 = st.session_state.morpho_etalon
                    d_px = dist(p1, p2)
                    reel = ETALONS[etalon][1]
                    facteur = d_px / reel
                    st.success(f"✅ Calibration : {d_px:.1f} px / {reel} cm "
                               f"→ **{facteur:.2f} px/cm**")

                    st.markdown("### 📐 Étape 2 : Points de mesure")
                    coord2 = streamlit_image_coordinates(img, key="mes")
                    c1, c2 = st.columns(2)
                    if c1.button("➕ Ajouter point mesure") and coord2:
                        st.session_state.morpho_mesure.append(
                            (coord2["x"], coord2["y"]))
                        st.rerun()
                    if c2.button("🗑️ Effacer mesures"):
                        st.session_state.morpho_mesure = []
                        st.rerun()

                    if len(st.session_state.morpho_mesure) >= 2:
                        pts = st.session_state.morpho_mesure
                        for i in range(len(pts) - 1):
                            d_px = dist(pts[i], pts[i + 1])
                            d_cm = d_px / facteur
                            st.metric(f"Distance point {i+1}→{i+2}",
                                      f"{d_cm:.2f} cm", f"{d_px:.0f} px")

                    st.divider()
                    st.markdown("### 🧮 Calculs morphométriques")
                    c1, c2, c3 = st.columns(3)
                    L = c1.number_input("Longueur (cm)", 0.0, 500.0, 0.0, 0.1)
                    W = c2.number_input("Largeur (cm)", 0.0, 500.0, 0.0, 0.1)
                    H = c3.number_input("Hauteur (cm)", 0.0, 500.0, 0.0, 0.1)

                    ratio = L / W if W > 0 else None
                    surface = L * W if L > 0 and W > 0 else None

                    if ratio:
                        st.markdown(f"- Ratio L/W : **{ratio:.3f}**")
                    if surface:
                        st.markdown(f"- Surface : **{surface:.2f} cm²**")

                    notes = st.text_area("Notes", height=60)

                    if st.button("💾 Enregistrer la mesure morphométrique",
                                 type="primary"):
                        fname = f"{uuid.uuid4().hex}.jpg"
                        fpath = os.path.join(MORPHO_DIR, fname)
                        cv2.imwrite(fpath, cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR))

                        conn.execute("""
                            INSERT INTO morphometrie (parcelle_id, sujet_type,
                                date_mesure, photo_path, etalon_type, facteur_px_cm,
                                longueur_cm, largeur_cm, hauteur_cm,
                                surface_cm2, ratio_forme, notes)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (parc_options[parc_c], sujet, datetime.now().isoformat(),
                             fname, etalon, facteur, L, W, H, surface, ratio, notes))
                        conn.commit()
                        st.success("✅ Mesure enregistrée.")
                        st.session_state.morpho_etalon = []
                        st.session_state.morpho_mesure = []

            except ImportError:
                st.error("Installez streamlit-image-coordinates : "
                         "`pip install streamlit-image-coordinates`")

        df_m = pd.read_sql_query(
            "SELECT * FROM morphometrie ORDER BY id DESC LIMIT 50", conn)
        if not df_m.empty:
            st.dataframe(df_m, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🚪 Porte de Qualité 1 — Complétude")
    n_exp = pd.read_sql_query("SELECT COUNT(*) AS n FROM exploitations", conn)["n"][0]
    n_parc = pd.read_sql_query("SELECT COUNT(*) AS n FROM parcelles", conn)["n"][0]
    n_pheno = pd.read_sql_query("SELECT COUNT(*) AS n FROM phenotypes", conn)["n"][0]

    conds = {
        "Au moins 1 exploitation": n_exp >= 1,
        "Au moins 1 parcelle": n_parc >= 1,
        "Au moins 5 mesures phénotypiques": n_pheno >= 5,
    }
    if check_gate("gate_1", conds):
        if st.button("➡️ Passer au Contrôle Qualité", type="primary"):
            mark_phase_complete("1_collecte")
            st.session_state.current_module = "✅ Contrôle Qualité"
            st.rerun()


# ============================================================
# MODULE 3 : CONTRÔLE QUALITÉ
# ============================================================
def mod_qc():
    header("✅", "Contrôle Qualité",
           "Détection et correction des anomalies avant analyse.")

    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM phenotypes", conn)

    if df.empty:
        warn("⚠️ Aucune donnée phénotypique. Complétez la Phase 1.")
        return

    st.markdown("### 🔍 Contrôles automatiques")
    pct_nan = df.isnull().mean().mean() * 100
    n_dup = int(df.duplicated().sum())

    cols_num = df.select_dtypes(include=[np.number]).columns
    aberrants = {}
    for col in cols_num:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr > 0:
            n_ab = int(((df[col] < q1 - 1.5 * iqr) |
                        (df[col] > q3 + 1.5 * iqr)).sum())
            if n_ab > 0:
                aberrants[col] = n_ab

    c1, c2, c3 = st.columns(3)
    c1.metric("Valeurs manquantes (%)", f"{pct_nan:.1f}")
    c2.metric("Doublons", n_dup)
    c3.metric("Colonnes avec aberrants", len(aberrants))

    if aberrants:
        st.warning(f"⚠️ Valeurs aberrantes : {aberrants}")

    st.divider()
    st.subheader("🚪 Porte de Qualité 2 — Fiabilité")
    conds = {
        "Manquants < 20%": pct_nan < 20,
        "Aucun doublon": n_dup == 0,
        "Aberrants < 5%": sum(aberrants.values()) / max(len(df), 1) < 0.05,
    }
    if check_gate("gate_2", conds):
        if st.button("➡️ Passer au Phénotypage", type="primary"):
            mark_phase_complete("2_qc")
            st.session_state.current_module = "📊 Phénotypage"
            st.rerun()
    else:
        err("🚫 Corrigez les problèmes avant de continuer.")


# ============================================================
# MODULE 4 : PHÉNOTYPAGE
# ============================================================
def mod_phenotypage():
    header("📊", "Phénotypage",
           "Analyse statistique des caractères mesurés.")

    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM phenotypes", conn)

    if df.empty or len(df) < 3:
        warn("⚠️ Pas assez de données. Complétez la Phase 1.")
        return

    st.subheader("📈 Statistiques descriptives")
    cols_num = df.select_dtypes(include=[np.number]).columns.tolist()
    if cols_num:
        st.dataframe(df[cols_num].describe().round(2), use_container_width=True)

    if cols_num:
        st.subheader("📊 Distributions")
        var = st.selectbox("Variable", [c for c in cols_num if df[c].std() > 0])
        if var:
            fig = px.histogram(df, x=var, nbins=30, template="plotly_white",
                               title=f"Distribution de {var}")
            st.plotly_chart(fig, use_container_width=True)

    if len(cols_num) >= 2:
        st.subheader("🔗 Corrélations")
        corr = df[cols_num].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                        zmin=-1, zmax=1, title="Matrice de corrélation")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🎯 ACP")
    df_clean = df[cols_num].dropna()
    if len(df_clean) >= 3 and len(cols_num) >= 2:
        scaler = StandardScaler()
        X = scaler.fit_transform(df_clean)
        n_comp = min(3, X.shape[1])
        pca = PCA(n_components=n_comp)
        scores = pca.fit_transform(X)
        var_exp = pca.explained_variance_ratio_ * 100

        fig = px.scatter(x=scores[:, 0], y=scores[:, 1],
                         labels={"x": f"PC1 ({var_exp[0]:.1f}%)",
                                 "y": f"PC2 ({var_exp[1]:.1f}%)"},
                         title="ACP des phénotypes", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🚪 Porte de Qualité 3 — Structure")
    conds = {
        "Au moins 3 variables avec variance": sum(df[c].std() > 0 for c in cols_num) >= 3,
        "ACP calculée": True,
        "Données suffisantes": len(df) >= 3,
    }
    if check_gate("gate_3", conds):
        if st.button("➡️ Passer à l'Analyse", type="primary"):
            mark_phase_complete("3_phenotypage")
            st.session_state.current_module = "🌱 Smart Farming"
            st.rerun()


# ============================================================
# MODULE 5 : SMART FARMING
# ============================================================
def mod_smart_farming():
    header("🌱", "Smart Farming — Capteurs proximaux",
           "Analyse des données de sol et microclimat.")

    conn = get_db()
    df = pd.read_sql_query("""
        SELECT c.*, p.nom AS parcelle FROM capteurs c
        LEFT JOIN parcelles p ON c.parcelle_id = p.id
        ORDER BY c.date""", conn)

    if df.empty:
        warn("⚠️ Aucune donnée capteur. Complétez la Phase 1.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("T° sol moy.", f"{df['temperature_sol_c'].mean():.1f} °C")
    c2.metric("Humidité sol", f"{df['humidite_sol_pct'].mean():.1f} %")
    c3.metric("pH moyen", f"{df['ph_sol'].mean():.2f}")
    c4.metric("EC moyen", f"{df['ec_ds_m'].mean():.2f} dS/m")

    st.divider()
    st.subheader("📈 Séries temporelles")
    var = st.selectbox("Variable", ["temperature_sol_c", "humidite_sol_pct",
                                     "ph_sol", "ec_ds_m", "luminosite_lux"])
    if "parcelle" in df.columns and df["parcelle"].nunique() > 1:
        fig = px.line(df, x="date", y=var, color="parcelle",
                      title=f"Évolution de {var}", markers=True)
    else:
        fig = px.line(df, x="date", y=var, title=f"Évolution de {var}",
                      markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("🚨 Alertes automatiques")
    alerts = []
    for p in df["parcelle"].dropna().unique():
        sub = df[df["parcelle"] == p]
        if sub["humidite_sol_pct"].mean() < 25:
            alerts.append(f"⚠️ {p} : humidité faible "
                          f"({sub['humidite_sol_pct'].mean():.1f}%)")
        if sub["temperature_sol_c"].max() > 32:
            alerts.append(f"⚠️ {p} : T° élevée "
                          f"({sub['temperature_sol_c'].max():.1f}°C)")
        if sub["ec_ds_m"].mean() > 2.5:
            alerts.append(f"⚠️ {p} : conductivité élevée "
                          f"({sub['ec_ds_m'].mean():.2f} dS/m)")

    if alerts:
        for a in alerts:
            warn(a)
    else:
        info("✅ Aucune alerte : paramètres dans les plages optimales.")


# ============================================================
# MODULE 6 : TÉLÉDÉTECTION
# ============================================================
def mod_remote_sensing():
    header("🛰", "Télédétection — Indices de végétation",
           "Calcul de NDVI à partir d'images multi-spectrales.")

    tab1, tab2 = st.tabs(["🧮 Calcul NDVI", "📊 Simulation"])

    with tab1:
        c1, c2 = st.columns(2)
        red_f = c1.file_uploader("Bande ROUGE", type=["png", "jpg", "jpeg"])
        nir_f = c2.file_uploader("Bande NIR", type=["png", "jpg", "jpeg"])

        if red_f and nir_f:
            try:
                red = np.array(Image.open(red_f).convert("L"), dtype=np.float32)
                nir = np.array(Image.open(nir_f).convert("L"), dtype=np.float32)

                if red.shape != nir.shape:
                    nir = np.array(Image.fromarray(nir.astype(np.uint8)).resize(
                        (red.shape[1], red.shape[0])), dtype=np.float32)

                ndvi = np.clip((nir - red) / (nir + red + 1e-9), -1, 1)

                c1, c2, c3 = st.columns(3)
                c1.metric("NDVI moyen", f"{ndvi.mean():.3f}")
                c2.metric("NDVI max", f"{ndvi.max():.3f}")
                c3.metric("Surface végétalisée", f"{(ndvi > 0.3).mean() * 100:.1f} %")

                fig = px.imshow(ndvi, color_continuous_scale="RdYlGn",
                                zmin=-1, zmax=1, title="Carte NDVI")
                st.plotly_chart(fig, use_container_width=True)

                mean_ndvi = ndvi.mean()
                if mean_ndvi < 0.1:
                    warn("🔴 NDVI faible — sol nu ou végétation stressée.")
                elif mean_ndvi < 0.3:
                    warn("🟡 NDVI modéré — végétation clairsemée.")
                elif mean_ndvi < 0.6:
                    info("🟢 NDVI bon — végétation saine.")
                else:
                    info("🌿 NDVI très élevé — couverture dense.")
            except Exception as e:
                st.error(f"Erreur : {e}")

    with tab2:
        rng = np.random.default_rng(42)
        days = pd.date_range(end=datetime.now(), periods=30, freq="D")
        sim = pd.DataFrame({
            "date": days,
            "NDVI": np.clip(0.35 + 0.25 * np.sin(np.arange(30) / 8) +
                            rng.normal(0, 0.03, 30), 0, 1),
            "NDRE": np.clip(0.25 + 0.20 * np.sin(np.arange(30) / 9) +
                            rng.normal(0, 0.025, 30), 0, 1),
            "SAVI": np.clip(0.30 + 0.22 * np.sin(np.arange(30) / 7) +
                            rng.normal(0, 0.03, 30), 0, 1),
        })
        fig = px.line(sim.melt(id_vars="date", var_name="Indice", value_name="Valeur"),
                      x="date", y="Valeur", color="Indice", markers=True)
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# MODULE 7 : RICCIARDI LAB
# ============================================================
def simulate_ou(theta, mu, sigma, dt, n, seed=42):
    rng = np.random.default_rng(seed)
    X = np.zeros(n)
    X[0] = mu + rng.normal(0, 1)
    for i in range(1, n):
        dW = rng.normal(0, np.sqrt(dt))
        X[i] = X[i-1] + theta * (mu - X[i-1]) * dt + sigma * dW
    return X


def fpt(X, threshold):
    crossings = np.where(X >= threshold)[0]
    if len(crossings) == 0:
        return None
    return crossings[0]


def fokker_planck(x_range, theta, mu, sigma):
    p = np.exp(-theta * (x_range - mu) ** 2 / (sigma ** 2))
    return p / np.trapz(p, x_range)


def mod_ricciardi():
    header("🔬", "Ricciardi Biomathematics Lab",
           "Processus stochastiques, FPT, Fokker-Planck — héritage de "
           "Luigi M. Ricciardi (1942–2011).")

    tabs = st.tabs(["🌾 Croissance", "⚠️ FPT", "🧠 Fokker-Planck", "🔗 Cybernétique"])

    with tabs[0]:
        st.subheader("Croissance stochastique (Ornstein-Uhlenbeck)")
        c1, c2, c3 = st.columns(3)
        theta = c1.slider("θ (rappel)", 0.05, 2.0, 0.5, 0.05)
        mu = c2.slider("μ (équilibre)", 5.0, 50.0, 20.0, 1.0)
        sigma = c3.slider("σ (bruit)", 0.1, 5.0, 2.0, 0.1)

        t = np.arange(0, 20, 0.01)
        fig = go.Figure()
        for k in range(5):
            X = simulate_ou(theta, mu, sigma, 0.01, len(t), seed=42 + k)
            fig.add_trace(go.Scatter(x=t, y=X, mode="lines",
                                     name=f"Sim {k+1}", opacity=0.7))
        fig.add_hline(y=mu, line_dash="dash", line_color="red",
                      annotation_text=f"μ = {mu}")
        fig.update_layout(title="Croissance stochastique",
                          xaxis_title="Temps", yaxis_title="Biomasse",
                          template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("Temps de Premier Passage (FPT)")
        info("Le FPT est le temps que met un processus à franchir un seuil "
             "critique pour la première fois.")

        c1, c2, c3, c4 = st.columns(4)
        theta_f = c1.slider("θ", 0.05, 2.0, 0.5, 0.05, key="fpt_theta")
        mu_f = c2.slider("μ", 5.0, 50.0, 20.0, 1.0, key="fpt_mu")
        sigma_f = c3.slider("σ", 0.1, 5.0, 2.0, 0.1, key="fpt_sigma")
        threshold = c4.slider("Seuil", 5.0, 60.0, 30.0, 1.0)

        fpts = []
        for k in range(100):
            X = simulate_ou(theta_f, mu_f, sigma_f, 0.01, 3000, seed=100 + k)
            f = fpt(X, threshold)
            if f is not None:
                fpts.append(f * 0.01)

        if fpts:
            arr = np.array(fpts)
            c1, c2, c3 = st.columns(3)
            c1.metric("FPT moyen", f"{arr.mean():.3f}")
            c2.metric("FPT médian", f"{np.median(arr):.3f}")
            c3.metric("Probabilité d'atteinte", f"{len(fpts)} %")

            fig = px.histogram(x=arr, nbins=25,
                               title=f"Distribution du FPT (seuil = {threshold})",
                               template="plotly_white",
                               color_discrete_sequence=[ORANGE])
            fig.add_vline(x=arr.mean(), line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("Équation de Fokker-Planck")
        info("Distribution stationnaire du potentiel membranaire ou d'un "
             "paramètre agricole.")

        c1, c2, c3 = st.columns(3)
        theta_n = c1.slider("θ", 0.1, 2.0, 0.5, 0.05, key="fp_theta")
        mu_n = c2.slider("μ", -80.0, -50.0, -65.0, 1.0)
        sigma_n = c3.slider("σ", 0.5, 10.0, 3.0, 0.5)

        x = np.linspace(mu_n - 4 * sigma_n, mu_n + 4 * sigma_n, 500)
        p = fokker_planck(x, theta_n, mu_n, sigma_n)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=p, mode="lines",
                                 line=dict(color=VIOLET, width=3),
                                 fill="tozeroy",
                                 fillcolor="rgba(106,27,154,0.2)"))
        fig.add_vline(x=mu_n, line_dash="dash", line_color="red",
                      annotation_text=f"μ = {mu_n:.0f}")
        fig.update_layout(title="Distribution stationnaire (Fokker-Planck)",
                          xaxis_title="Valeur", yaxis_title="Densité",
                          template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.subheader("Cybernétique agricole")
        concepts = pd.DataFrame({
            "Concept": ["Réverbération", "Contrôle", "Rétroaction",
                        "Apprentissage Hebbien", "Décision"],
            "Application": [
                "Propagation d'innovation dans un réseau d'agriculteurs",
                "Régulation d'un système d'irrigation intelligent",
                "Ajustement des intrants selon capteurs",
                "Renforcement des connexions utiles (ML)",
                "Arbres de décision pour sélection variétale"],
        })
        st.dataframe(concepts, use_container_width=True, hide_index=True)

        st.markdown("### 🎯 Simulation de propagation d'innovation")
        c1, c2, c3 = st.columns(3)
        N = c1.slider("Agriculteurs", 10, 200, 50)
        p_inf = c2.slider("Probabilité d'adoption", 0.01, 0.5, 0.1, 0.01)
        steps = c3.slider("Étapes", 10, 100, 50)

        S, I, R = N - 1, 1, 0
        hist = {"S": [S], "I": [I], "R": [R]}
        for _ in range(steps):
            new = min(S, int(p_inf * S * I / N))
            S -= new
            I += new - int(0.1 * I)
            R += int(0.1 * I)
            hist["S"].append(S)
            hist["I"].append(I)
            hist["R"].append(R)

        df_p = pd.DataFrame(hist)
        fig = px.area(df_p, title="Propagation d'une innovation agricole",
                      labels={"index": "Temps", "value": "Nombre",
                              "variable": "Statut"},
                      color_discrete_map={"S": "#FF6F00", "I": "#2E7D32",
                                           "R": "#1565C0"},
                      template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 📚 Références")
    st.markdown("""
    - Ricciardi, L. M. (1977). *Diffusion Processes and Related Topics in Biology*. Springer.
    - Capocelli, R. M., & Ricciardi, L. M. (1973). *J. Theor. Biol.*, 40(2), 369-387.
    - Caianiello, E. R., de Luca, A., & Ricciardi, L. M. (1967). *Kybernetik*, 4(1), 10-18.
    """)


# ============================================================
# MODULE 8 : MODÉLISATION RENDEMENT
# ============================================================
def mod_rendement():
    header("📈", "Modélisation du rendement",
           "Prédiction par machine learning.")

    rng = np.random.default_rng(42)
    n = 250
    df = pd.DataFrame({
        "azote_kg_ha": rng.uniform(40, 200, n),
        "irrigation_mm": rng.uniform(100, 600, n),
        "matiere_org_pct": rng.uniform(1.0, 4.5, n),
        "pluvio_mm": rng.uniform(200, 700, n),
        "temp_moy_C": rng.uniform(14, 28, n),
    })
    df["rendement_t_ha"] = np.clip(
        2.0 + 0.015 * df["azote_kg_ha"] + 0.004 * df["irrigation_mm"] +
        0.6 * df["matiere_org_pct"] + 0.0015 * df["pluvio_mm"] -
        0.05 * (df["temp_moy_C"] - 20) ** 2 + rng.normal(0, 0.35, n),
        0.5, 12.0)

    st.markdown("### 📊 Aperçu")
    st.dataframe(df.head(10), use_container_width=True)

    st.markdown("### 🤖 Modèle de régression")
    features = ["azote_kg_ha", "irrigation_mm", "matiere_org_pct",
                "pluvio_mm", "temp_moy_C"]
    X = df[features].values
    y = df["rendement_t_ha"].values
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)
    model = LinearRegression()
    model.fit(X_s, y)
    r2 = model.score(X_s, y)
    st.metric("R² du modèle", f"{r2:.3f}")

    coefs = pd.DataFrame({"Variable": features, "Coef": model.coef_})
    coefs = coefs.sort_values("Coef", key=abs, ascending=False)
    fig = px.bar(coefs, x="Coef", y="Variable", orientation="h",
                 color="Coef", color_continuous_scale="Viridis")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🎯 Simulateur interactif")
    c1, c2, c3 = st.columns(3)
    n_in = c1.slider("Azote (kg/ha)", 40, 200, 120)
    i_in = c2.slider("Irrigation (mm)", 100, 600, 350)
    s_in = c3.slider("Matière org. (%)", 1.0, 4.5, 2.5)
    c1, c2 = st.columns(2)
    r_in = c1.slider("Pluvio (mm)", 200, 700, 400)
    t_in = c2.slider("T° moy (°C)", 14, 28, 20)

    X_sim = scaler.transform([[n_in, i_in, s_in, r_in, t_in]])
    pred = model.predict(X_sim)[0]
    st.markdown(f'<div class="kpi-card"><div class="kpi-value">{pred:.2f} t/ha</div>'
                f'<div class="kpi-label">Rendement prédit</div></div>',
                unsafe_allow_html=True)


# ============================================================
# MODULE 9 : GENSMART (OVINS)
# ============================================================
def analyser_profil_racial_ovin(race):
    genes_race = RACES_OVINES.get(race, {}).get("genes", [])
    result = {"race": race, "genes": [],
              "score_reproduction": 0, "score_croissance": 0,
              "score_lait": 0, "recommandations": []}
    for g in genes_race:
        i = GENES_OVINS.get(g, {})
        result["genes"].append({
            "symbole": g, "nom": i.get("nom", ""),
            "effet": i.get("effet", ""),
            "chromosome": i.get("chr", ""),
            "categorie": i.get("cat", ""),
        })
        if g in ["BMP15", "GDF9", "BMPR1B"]:
            result["score_reproduction"] += 33
        if g in ["MSTN", "IGF2", "GH"]:
            result["score_croissance"] += 33
        if g in ["LALBA", "CSN3", "DGAT1"]:
            result["score_lait"] += 33

    result["score_reproduction"] = min(100, result["score_reproduction"])
    result["score_croissance"] = min(100, result["score_croissance"])
    result["score_lait"] = min(100, result["score_lait"])

    if result["score_reproduction"] > 70:
        result["recommandations"].append("✅ Excellente valeur reproductive")
    if result["score_croissance"] > 70:
        result["recommandations"].append("✅ Excellente conformation viande")
    if result["score_lait"] > 70:
        result["recommandations"].append("✅ Excellent potentiel laitier")
    return result


def predire_lait_ovin(score_mamelle, score_morpho, race, age):
    base = 0.5
    if score_mamelle >= 8:
        base += 1.5
    elif score_mamelle >= 6:
        base += 0.8
    if score_morpho >= 80:
        base += 0.3
    if race == "Sidahou":
        base *= 1.3
    if 3 <= age <= 6:
        base *= 1.2
    niveau = "Élite" if base > 1.5 else "Bon" if base > 1.0 else "Standard"
    return {"litres_jour": round(base, 2),
            "litres_lactation": round(base * 180, 2),
            "niveau": niveau}


def mod_gensmart():
    header("🐑", "GenSmart — Évaluation génomique ovine",
           "Prolificité · Qualité du lait · Résistance aux maladies.")

    tabs = st.tabs([
        "🔍 Profil racial",
        "🧬 Gènes d'intérêt",
        "🥛 Prédiction laitière",
        "📊 Base de données ovine",
        "🔗 Lien GenSmart externe",
    ])
    conn = get_db()

    with tabs[0]:
        st.subheader("Profil génétique par race ovine")
        info("Analysez le potentiel génétique d'une race algérienne.")

        c1, c2 = st.columns([1, 2])
        with c1:
            race = st.selectbox("Race ovine", list(RACES_OVINES.keys()))
            if st.button("🧬 Analyser", type="primary", use_container_width=True):
                st.session_state["gs_result"] = analyser_profil_racial_ovin(race)

        with c2:
            res = st.session_state.get("gs_result")
            if res and res["race"] == race:
                fig = go.Figure(data=go.Scatterpolar(
                    r=[res["score_reproduction"], res["score_croissance"],
                       res["score_lait"], res["score_reproduction"]],
                    theta=["Reproduction", "Croissance/Viande", "Lait", "Reproduction"],
                    fill="toself", name=race, line_color=VERT))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False, height=380,
                    title=f"Profil génétique : {race}")
                st.plotly_chart(fig, use_container_width=True)

        res = st.session_state.get("gs_result")
        if res and res["race"] == race:
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("🎯 Reproduction", f"{res['score_reproduction']}/100")
            c2.metric("💪 Croissance", f"{res['score_croissance']}/100")
            c3.metric("🥛 Lait", f"{res['score_lait']}/100")

            if res["recommandations"]:
                st.success("### ✅ Recommandations")
                for r in res["recommandations"]:
                    st.write(r)

            st.subheader("🧬 Gènes majeurs")
            st.dataframe(pd.DataFrame(res["genes"]),
                         use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("Base des gènes d'intérêt économique ovin")
        df_genes = pd.DataFrame([
            {"Symbole": s, "Nom": i["nom"], "Chr": i["chr"],
             "Effet": i["effet"], "Catégorie": i["cat"]}
            for s, i in GENES_OVINS.items()
        ])
        cat = st.selectbox("Filtrer",
                           ["Toutes"] + sorted(df_genes["Catégorie"].unique()))
        if cat != "Toutes":
            df_genes = df_genes[df_genes["Catégorie"] == cat]
        st.dataframe(df_genes, use_container_width=True, hide_index=True)

        rep = pd.DataFrame([
            {"Catégorie": s, "Nombre": n}
            for s, n in pd.Series([i["cat"] for i in GENES_OVINS.values()])
                             .value_counts().items()
        ])
        fig = px.pie(rep, values="Nombre", names="Catégorie",
                     title="Répartition des gènes d'intérêt ovin",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("🥛 Prédiction du potentiel laitier")
        c1, c2 = st.columns(2)
        with c1:
            score_mam = st.slider("Score mamelle", 1.0, 10.0, 7.0, 0.5)
            score_morpho = st.slider("Score morphologique", 0, 100, 75)
        with c2:
            race_p = st.selectbox("Race", list(RACES_OVINES.keys()), key="pred_race")
            age = st.number_input("Âge (années)", 1, 15, 4)

        if st.button("🔮 Prédire", type="primary", use_container_width=True):
            pred = predire_lait_ovin(score_mam, score_morpho, race_p, age)
            c1, c2, c3 = st.columns(3)
            c1.metric("Production/jour", f"{pred['litres_jour']} L")
            c2.metric("Production/lactation", f"{pred['litres_lactation']} L")
            c3.metric("Niveau", pred["niveau"])

    with tabs[3]:
        st.subheader("📊 Brebis enregistrées")
        df_ov = pd.read_sql_query("""
            SELECT a.*, e.nom AS exploitation FROM animaux a
            LEFT JOIN exploitations e ON a.exploitation_id = e.id
            WHERE a.espece = 'Ovin' ORDER BY a.id DESC""", conn)

        if df_ov.empty:
            warn("⚠️ Aucun ovin enregistré. Utilisez le module **Collecte**.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("🐑 Brebis", len(df_ov))
            c2.metric("Races", df_ov["race"].nunique() if "race" in df_ov else 0)
            c3.metric("Exploitations", df_ov["exploitation"].nunique())

            st.dataframe(df_ov, use_container_width=True, hide_index=True)

            if "race" in df_ov.columns and df_ov["race"].nunique() > 1:
                fig = px.pie(df_ov, names="race", title="Répartition par race")
                st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        st.subheader("🔗 Accès direct à GenSmart")
        info("L'application complète GenSmart est accessible ci-dessous.")
        st.link_button("🚀 Ouvrir GenSmart",
                       LINKS["GenSmart"], use_container_width=True)
        st.markdown("""
        ### Fonctionnalités de GenSmart
        - **Prolificité** : taille de portée, survie des agneaux
        - **Qualité du lait** : MG, protéines, score cellulaire
        - **Résistance aux maladies** : mammites, parasites
        - **Profil racial** : 4 races algériennes
        - **Prédiction laitière** : modèle ML
        """)


# ============================================================
# MODULE 10 : LIVEGENE (BOVINS)
# ============================================================
def analyser_profil_racial_bovin(race):
    genes_race = RACES_BOVINES.get(race, {}).get("genes", [])
    result = {"race": race, "genes": [],
              "score_production": 0, "score_viande": 0,
              "score_lait": 0, "recommandations": []}
    for g in genes_race:
        i = GENES_BOVINS.get(g, {})
        result["genes"].append({
            "symbole": g, "nom": i.get("nom", ""),
            "effet": i.get("effet", ""),
            "chromosome": i.get("chr", ""),
            "categorie": i.get("cat", ""),
        })
        if g in ["MSTN", "IGF2", "GH", "GHR"]:
            result["score_production"] += 25
        if g in ["CAPN1", "CAST", "FABP4"]:
            result["score_viande"] += 33
        if g in ["LALBA", "CSN3", "DGAT1", "SCD"]:
            result["score_lait"] += 25

    result["score_production"] = min(100, result["score_production"])
    result["score_viande"] = min(100, result["score_viande"])
    result["score_lait"] = min(100, result["score_lait"])

    if result["score_production"] > 70:
        result["recommandations"].append("✅ Excellente production")
    if result["score_viande"] > 70:
        result["recommandations"].append("✅ Excellente qualité bouchère")
    if result["score_lait"] > 70:
        result["recommandations"].append("✅ Excellent potentiel laitier")
    return result


def mod_livegene():
    header("🐄", "LiveGene Suite — Génétique bovine",
           "Sélection génomique · Morphométrie 2D · Pipeline complet.")

    tabs = st.tabs([
        "🔍 Profil racial",
        "🧬 Gènes d'intérêt",
        "📊 Base bovine",
        "🔗 Lien LiveGene externe",
    ])
    conn = get_db()

    with tabs[0]:
        st.subheader("Profil génétique par race bovine")
        info("Analysez le potentiel génétique d'une race bovine.")

        c1, c2 = st.columns([1, 2])
        with c1:
            race = st.selectbox("Race bovine", list(RACES_BOVINES.keys()))
            if st.button("🧬 Analyser", type="primary", use_container_width=True):
                st.session_state["lg_result"] = analyser_profil_racial_bovin(race)

        with c2:
            res = st.session_state.get("lg_result")
            if res and res["race"] == race:
                fig = go.Figure(data=go.Scatterpolar(
                    r=[res["score_production"], res["score_viande"],
                       res["score_lait"], res["score_production"]],
                    theta=["Production", "Viande", "Lait", "Production"],
                    fill="toself", name=race, line_color=BLEU))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False, height=380,
                    title=f"Profil génétique : {race}")
                st.plotly_chart(fig, use_container_width=True)

        res = st.session_state.get("lg_result")
        if res and res["race"] == race:
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("🏭 Production", f"{res['score_production']}/100")
            c2.metric("🥩 Viande", f"{res['score_viande']}/100")
            c3.metric("🥛 Lait", f"{res['score_lait']}/100")

            if res["recommandations"]:
                st.success("### ✅ Recommandations")
                for r in res["recommandations"]:
                    st.write(r)

            st.subheader("🧬 Gènes majeurs")
            st.dataframe(pd.DataFrame(res["genes"]),
                         use_container_width=True, hide_index=True)

    with tabs[1]:
        st.subheader("Base des gènes d'intérêt économique bovin")
        df_genes = pd.DataFrame([
            {"Symbole": s, "Nom": i["nom"], "Chr": i["chr"],
             "Effet": i["effet"], "Catégorie": i["cat"]}
            for s, i in GENES_BOVINS.items()
        ])
        cat = st.selectbox("Filtrer",
                           ["Toutes"] + sorted(df_genes["Catégorie"].unique()),
                           key="lg_cat")
        if cat != "Toutes":
            df_genes = df_genes[df_genes["Catégorie"] == cat]
        st.dataframe(df_genes, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("📊 Bovins enregistrés")
        df_bv = pd.read_sql_query("""
            SELECT a.*, e.nom AS exploitation FROM animaux a
            LEFT JOIN exploitations e ON a.exploitation_id = e.id
            WHERE a.espece = 'Bovin' ORDER BY a.id DESC""", conn)

        if df_bv.empty:
            warn("⚠️ Aucun bovin enregistré. Utilisez le module **Collecte**.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("🐄 Bovins", len(df_bv))
            c2.metric("Races", df_bv["race"].nunique() if "race" in df_bv else 0)
            c3.metric("Exploitations", df_bv["exploitation"].nunique())

            st.dataframe(df_bv, use_container_width=True, hide_index=True)

            if "race" in df_bv.columns and df_bv["race"].nunique() > 1:
                fig = px.pie(df_bv, names="race", title="Répartition par race")
                st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.subheader("🔗 Accès direct à LiveGene Suite")
        info("L'application complète LiveGene Suite est accessible ci-dessous.")
        st.link_button("🚀 Ouvrir LiveGene Suite",
                       LINKS["LiveGene Suite"], use_container_width=True)
        st.markdown("""
        ### Fonctionnalités de LiveGene Suite
        - **Pipeline génomique** : QC, phasing, imputation, GWAS
        - **Morphométrie 2D** : mesure sur photos d'animaux
        - **Sélection multi-caractères** : production, fertilité, santé
        - **Suivi de consanguinité**
        - **Simulateur de sélection**
        """)


# ============================================================
# MODULE 11 : APITRACK (ABEILLES)
# ============================================================
def mod_apitrack():
    header("🐝", "Apitrack — Généalogie et génétique des abeilles",
           "Traçabilité des reines · Évaluation génétique · Production.")

    tabs = st.tabs([
        "🐝 Ruches enregistrées",
        "📊 Analyse production",
        "🧬 Génétique des reines",
        "🔗 Lien Apitrack externe",
    ])
    conn = get_db()

    with tabs[0]:
        st.subheader("🐝 Ruches enregistrées")
        df_r = pd.read_sql_query("""
            SELECT r.*, e.nom AS exploitation FROM ruches r
            LEFT JOIN exploitations e ON r.exploitation_id = e.id
            ORDER BY r.id DESC""", conn)

        if df_r.empty:
            warn("⚠️ Aucune ruche enregistrée. Utilisez le module **Collecte**.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🐝 Ruches", len(df_r))
            c2.metric("🍯 Miel total (kg)", f"{df_r['production_miel_kg'].sum():.0f}")
            c3.metric("👑 Reines", df_r["reine_id"].nunique())
            c4.metric("🏡 Exploitations", df_r["exploitation"].nunique())

            st.dataframe(df_r, use_container_width=True, hide_index=True)

            if "etat_sante" in df_r.columns and df_r["etat_sante"].nunique() > 1:
                fig = px.pie(df_r, names="etat_sante",
                             title="État sanitaire des ruches")
                st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("📊 Analyse de la production de miel")
        df_r = pd.read_sql_query("SELECT * FROM ruches", conn)
        if df_r.empty:
            warn("⚠️ Aucune donnée.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Production moyenne", f"{df_r['production_miel_kg'].mean():.1f} kg")
            c2.metric("Production max", f"{df_r['production_miel_kg'].max():.1f} kg")
            c3.metric("Population moyenne",
                      f"{df_r['population_estimee'].mean():.0f} abeilles")

            fig = px.bar(df_r, x="identifiant", y="production_miel_kg",
                         color="etat_sante", title="Production par ruche",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        st.subheader("🧬 Génétique des reines")
        info("Les reines sont évaluées sur 3 critères : santé, productivité, "
             "douceur (comportement).")

        c1, c2, c3 = st.columns(3)
        sante = c1.slider("Score santé", 1, 10, 7)
        productivite = c2.slider("Score productivité", 1, 10, 8)
        douceur = c3.slider("Score douceur", 1, 10, 6)

        score = (sante + productivite + douceur) / 3
        niveau = "Élite" if score >= 8 else "Bon" if score >= 6 else "Standard"

        st.markdown(f"""
        ### 🏆 Évaluation de la reine
        - **Score global** : {score:.1f}/10
        - **Niveau** : **{niveau}**
        """)

        fig = go.Figure(data=go.Scatterpolar(
            r=[sante, productivite, douceur, sante],
            theta=["Santé", "Productivité", "Douceur", "Santé"],
            fill="toself", line_color=MARRON))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False, height=400,
            title="Profil génétique de la reine")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.subheader("🔗 Accès direct à Apitrack")
        info("L'application complète Apitrack est accessible ci-dessous.")
        st.link_button("🚀 Ouvrir Apitrack",
                       LINKS["Apitrack"], use_container_width=True)
        st.markdown("""
        ### Fonctionnalités d'Apitrack
        - **Généalogie des reines** : pedigrees sur plusieurs générations
        - **Évaluation génétique** : santé, productivité, douceur
        - **Traçabilité** : suivi des décisions de sélection
        - **Sélection assistée** : identification des meilleures reines
        """)


# ============================================================
# MODULE 12 : INNOVATION ALIMENTAIRE
# ============================================================
def mod_innovation_alim():
    header("🍽", "Innovation alimentaire",
           "Catalogue et priorisation des innovations agroalimentaires.")

    innovations = pd.DataFrame({
        "Innovation": ["Protéines d'insectes", "Protéines lactosérum",
                       "Biochar", "Pectines agrumes", "Polyphénols raisin",
                       "Biostimulants algues"],
        "Source": ["Hermetia, Tenebrio", "Sous-produits laitiers",
                   "Résidus végétaux", "Écorces agrumes",
                   "Marc de raisin", "Algues"],
        "Application": ["Alimentation animale", "Nutraceutiques",
                        "Amendement sol", "Gélifiants",
                        "Antioxydants", "Agriculture bio"],
        "TRL": [7, 9, 8, 9, 6, 7],
        "Impact": [9, 8, 9, 7, 8, 8],
        "Faisabilité": [8, 9, 7, 9, 6, 7],
    })
    st.dataframe(innovations, use_container_width=True, hide_index=True)

    st.markdown("### 🎨 Matrice Impact × Faisabilité")
    fig = px.scatter(innovations, x="Faisabilité", y="Impact",
                     text="Innovation", size=[15] * len(innovations),
                     color="TRL", color_continuous_scale="Viridis",
                     title="Priorisation des innovations")
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# MODULE 13 : BIOÉCONOMIE
# ============================================================
def mod_bioeconomie():
    header("♻️", "Bioéconomie circulaire",
           "Valorisation de la biomasse et des co-produits.")

    st.markdown("### Entrez les quantités de biomasse (t/an)")
    c1, c2, c3 = st.columns(3)
    paille = c1.number_input("Paille", 0.0, 10000.0, 500.0)
    fumier = c2.number_input("Fumier", 0.0, 10000.0, 300.0)
    marc = c3.number_input("Marc raisin/olive", 0.0, 5000.0, 100.0)
    c1, c2, c3 = st.columns(3)
    lacto = c1.number_input("Lactosérum", 0.0, 5000.0, 200.0)
    abattoir = c2.number_input("Co-produits abattoir", 0.0, 3000.0, 80.0)
    verts = c3.number_input("Déchets verts", 0.0, 5000.0, 150.0)

    total = paille + fumier + marc + lacto + abattoir + verts
    biogaz = fumier * 30 + verts * 25 + paille * 15 + abattoir * 40
    compost = (paille + verts + fumier) * 0.4
    biochar = (paille + marc) * 0.25
    proteines = abattoir * 0.15 + lacto * 0.05

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌱 Biogaz", f"{biogaz:,.0f} m³/an")
    c2.metric("🌿 Compost", f"{compost:,.0f} t/an")
    c3.metric("🔥 Biochar", f"{biochar:,.0f} t/an")
    c4.metric("🥩 Protéines alt.", f"{proteines:,.0f} t/an")

    data = pd.DataFrame({
        "Type": ["Paille", "Fumier", "Marc", "Lactosérum", "Abattoir", "Verts"],
        "Quantité": [paille, fumier, marc, lacto, abattoir, verts]
    })
    fig = px.pie(data, values="Quantité", names="Type",
                 title="Répartition de la biomasse",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

    info(f"Total biomasse : <b>{total:,.0f} t/an</b>")


# ============================================================
# MODULE 14 : INNOVATION BROKER
# ============================================================
def mod_broker():
    header("🔗", "Innovation Broker",
           "Évaluation TRL et matching science-industrie.")

    trl = pd.DataFrame({
        "TRL": range(1, 10),
        "Stade": ["Recherche fondamentale", "Concept technologique",
                  "Preuve de concept", "Prototype labo", "Prototype terrain",
                  "Démonstration", "Pilote", "Industrialisation",
                  "Commercialisation"],
    })
    st.dataframe(trl, use_container_width=True, hide_index=True)

    st.divider()
    c1, c2 = st.columns(2)
    t_cur = c1.slider("TRL actuel", 1, 9, 4)
    t_tgt = c2.slider("TRL cible", 1, 9, 8)

    gap = t_tgt - t_cur
    if gap > 0:
        warn(f"⚠️ Écart de <b>{gap} niveaux TRL</b> à combler.")
        for t in range(t_cur + 1, t_tgt + 1):
            row = trl[trl["TRL"] == t].iloc[0]
            st.markdown(f"- **TRL {t}** : {row['Stade']}")
    else:
        info("✅ Vous êtes au niveau TRL cible ou au-delà.")

    st.divider()
    st.subheader("🤝 Types de partenariats")
    partenaires = pd.DataFrame({
        "Partenaire": ["Universités", "Startups", "PME agro",
                       "Coopératives", "Instituts techniques", "Investisseurs"],
        "Rôle": ["Recherche amont", "Innovation rapide", "Industrialisation",
                 "Tests terrain", "Certification", "Financement"],
        "TRL idéal": ["1-4", "4-6", "6-8", "5-7", "6-9", "7-9"],
    })
    st.dataframe(partenaires, use_container_width=True, hide_index=True)


# ============================================================
# MODULE 15 : GENOMIQUE → PHENOTYPE
# ============================================================
def mod_genomique():
    header("🧬", "Génomique → Phénotype",
           "Passerelle vers vos outils de génomique.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🐄 LiveGene Suite — Bovins")
        st.markdown("Pipeline génomique complet, morphométrie 2D, "
                    "sélection multi-caractères.")
        st.link_button("Ouvrir LiveGene Suite →", LINKS["LiveGene Suite"],
                       use_container_width=True)

    with c2:
        st.markdown("### 🐑 GenSmart — Ovins")
        st.markdown("Évaluation génomique : prolificité, qualité du lait, "
                    "résistance aux maladies.")
        st.link_button("Ouvrir GenSmart →", LINKS["GenSmart"],
                       use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🐝 Apitrack — Abeilles")
        st.markdown("Traçabilité généalogique, évaluation génétique des reines.")
        st.link_button("Ouvrir Apitrack →", LINKS["Apitrack"],
                       use_container_width=True)

    with c2:
        st.markdown("### 📊 MetaInsight v8 — Multi-omique")
        st.markdown("Analyse génomique, transcriptomique, protéomique, "
                    "métabolomique.")
        st.link_button("Ouvrir MetaInsight v8 →", LINKS["MetaInsight v8"],
                       use_container_width=True)

    st.divider()
    st.markdown("### 🔗 Scénario intégré")
    steps = [
        ("1. Génotypage", "Collecte SNP sur bovins/ovins/abeilles",
         "LiveGene/GenSmart/Apitrack"),
        ("2. GWAS", "Identification des SNP associés", "LiveGene"),
        ("3. Prédiction", "Valeurs génétiques (GEBV)", "LiveGene/GenSmart"),
        ("4. Phénotype", "Mesures automatisées (morpho, poids)", "AIH Morphométrie"),
        ("5. Innovation", "Sélection des meilleurs reproducteurs", "AIH Broker"),
    ]
    for s, d, t in steps:
        st.markdown(f"**{s}** — {d}  \n*Outil : {t}*")


# ============================================================
# MODULE 16 : CONSEILLER IA
# ============================================================
def mod_ai():
    header("🤖", "Conseiller IA",
           "Aide à la décision par LLM (Groq gratuit).")

    api_key = st.text_input("Clé API Groq (https://console.groq.com/keys)",
                            type="password",
                            value=os.environ.get("GROQ_API_KEY", ""))

    with st.form("ai_form"):
        q = st.text_area("Votre question :",
                         "Comment valoriser le lactosérum de ma fromagerie ?",
                         height=120)
        sub = st.form_submit_button("🚀 Demander un conseil")

    if sub:
        if not api_key:
            warn("⚠️ Clé API Groq manquante.")
        else:
            try:
                prompt = (f"Expert en innovation agroalimentaire. Réponds en "
                          f"français (≤400 mots). Structure : 1) Analyse, "
                          f"2) Recommandations, 3) Étapes, 4) TRL.\n\n"
                          f"Question : {q}")
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}",
                             "Content-Type": "application/json"},
                    json={"model": "llama-3.3-70b-versatile",
                          "messages": [
                              {"role": "system",
                               "content": "Expert agroalimentaire."},
                              {"role": "user", "content": prompt}],
                          "temperature": 0.4, "max_tokens": 1200},
                    timeout=30)
                r.raise_for_status()
                st.markdown("### 📢 Réponse")
                st.markdown(r.json()["choices"][0]["message"]["content"])
            except Exception as e:
                st.error(f"Erreur LLM : {e}")

    st.divider()
    st.markdown("### 💡 Exemples de questions")
    st.markdown("""
    - Comment valoriser les co-produits d'une exploitation laitière ?
    - Quelle voie de valorisation pour le marc de raisin ?
    - Comment structurer un projet TRL 4 → TRL 8 ?
    - Quelles subventions européennes pour l'innovation agroalimentaire ?
    - Comment intégrer l'agriculture de précision dans une PME ?
    """)


# ============================================================
# MODULE 17 : RAPPORT & EXPORT
# ============================================================
def mod_rapport():
    header("📄", "Rapport & Export",
           "Synthèse complète et reproductibilité.")

    project = st.text_input("Nom du projet", "AIH_Project")

    conn = get_db()
    def cnt(t):
        try:
            return pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {t}", conn)["n"][0]
        except Exception:
            return 0

    n_exp = cnt("exploitations")
    n_parc = cnt("parcelles")
    n_anim = cnt("animaux")
    n_ruches = cnt("ruches")
    n_pheno = cnt("phenotypes")
    n_morpho = cnt("morphometrie")

    st.markdown("### 📊 Résumé des données")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Exploitations", n_exp)
    c2.metric("Parcelles", n_parc)
    c3.metric("Animaux", n_anim)
    c4.metric("Ruches", n_ruches)
    c5.metric("Phénotypes", n_pheno)
    c6.metric("Morpho", n_morpho)

    st.divider()
    st.markdown("### 📄 Génération du rapport Markdown")

    if st.button("📄 Générer le rapport", type="primary"):
        report = f"""# 🌾🐄🐝 Rapport AIH v3.0
**Projet :** {project}
**Date :** {datetime.now():%Y-%m-%d %H:%M}
**Pipeline :** {len(st.session_state.pipeline['phases_completees'])}/7 phases

## 1. Données collectées
- Exploitations : {n_exp}
- Parcelles : {n_parc}
- Animaux : {n_anim}
- Ruches : {n_ruches}
- Mesures phénotypiques : {n_pheno}
- Mesures morphométriques : {n_morpho}

## 2. Pipeline
{chr(10).join(f"- {p[0]}: {'✅' if p[0] in st.session_state.pipeline['phases_completees'] else '⬜'}" for p in PIPELINE_PHASES)}

## 3. Applications liées
{chr(10).join(f"- [{k}]({v})" for k, v in LINKS.items())}

## 4. Contact
**Slimane RAHIM**
+213 792 82 81 01 · rahim.slimane@gmail.com

---
*Généré par AgriFood Innovation Hub v3.0*
"""
        st.download_button(
            "⬇ Télécharger (Markdown)",
            data=report.encode("utf-8"),
            file_name=f"rapport_{project}_{datetime.now():%Y%m%d}.md",
            mime="text/markdown",
            use_container_width=True)
        st.success("✅ Rapport généré.")
        st.markdown(report)

    st.divider()
    st.markdown("### 📦 Export complet (ZIP)")
    if st.button("📦 Générer l'export ZIP", use_container_width=True):
        bio = BytesIO()
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
            for t in ["exploitations", "parcelles", "animaux", "ruches",
                      "phenotypes", "meteo", "capteurs", "morphometrie",
                      "photos", "innovations", "pipeline_logs"]:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {t}", conn)
                    zf.writestr(f"{t}.csv",
                                df.to_csv(index=False).encode("utf-8"))
                except Exception:
                    pass
            for d in [PHOTO_DIR, MORPHO_DIR]:
                if os.path.exists(d):
                    for f in os.listdir(d):
                        zf.write(os.path.join(d, f),
                                 arcname=f"{os.path.basename(d)}/{f}")
        bio.seek(0)
        st.download_button(
            "⬇ Télécharger ZIP",
            data=bio,
            file_name=f"aih_export_{datetime.now():%Y%m%d_%H%M}.zip",
            mime="application/zip",
            use_container_width=True)


# ============================================================
# NAVIGATION
# ============================================================
MODULES = {
    "🏠 Tableau de bord": mod_dashboard,
    "📝 Collecte de données": mod_collecte,
    "✅ Contrôle Qualité": mod_qc,
    "📊 Phénotypage": mod_phenotypage,
    "🌱 Smart Farming": mod_smart_farming,
    "🛰 Télédétection": mod_remote_sensing,
    "🔬 Ricciardi Lab": mod_ricciardi,
    "📈 Modélisation rendement": mod_rendement,
    "🐑 GenSmart — Ovins": mod_gensmart,
    "🐄 LiveGene — Bovins": mod_livegene,
    "🐝 Apitrack — Abeilles": mod_apitrack,
    "🍽 Innovation alimentaire": mod_innovation_alim,
    "♻️ Bioéconomie circulaire": mod_bioeconomie,
    "🔗 Innovation Broker": mod_broker,
    "🧬 Génomique → Phénotype": mod_genomique,
    "🤖 Conseiller IA": mod_ai,
    "📄 Rapport & Export": mod_rapport,
}


def main():
    with st.sidebar:
        st.markdown("## 🌾🐄🐝 AIH v3.0")
        st.caption("Master IDEAS · Université de Bari")
        st.divider()

        st.markdown("### 🔄 Pipeline")
        for key, label in PIPELINE_PHASES:
            if key in st.session_state.pipeline["phases_completees"]:
                st.markdown(f"✅ {label}")
            elif key == st.session_state.pipeline["phase_actuelle"]:
                st.markdown(f"🔄 **{label}**")
            else:
                st.markdown(f"⬜ {label}")

        st.divider()
        st.markdown("### 🧭 Navigation")

        for name in MODULES.keys():
            selected = st.session_state.current_module == name
            if st.button(
                name,
                key=f"btn_{name}",
                use_container_width=True,
                type="primary" if selected else "secondary"
            ):
                st.session_state.current_module = name
                st.rerun()

        st.divider()
        st.markdown("### 🔗 Apps liées")
        for n, u in LINKS.items():
            st.markdown(f"[{n}]({u})")

        st.divider()
        st.caption("v3.0 · Pipeline rigoureux · 3 règnes")

    current = st.session_state.current_module
    if current in MODULES:
        MODULES[current]()
    else:
        st.error(f"Module introuvable : {current}")


if __name__ == "__main__":
    main()
