# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from fpdf import FPDF
import base64
import os
import uuid
from icalendar import Calendar, Event

# Base de données
from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit_calendar as st_calendar

# --- Configuration base de données ---
Base = declarative_base()

class Cours(Base):
    __tablename__ = 'cours'
    id = Column(Integer, primary_key=True)
    nom = Column(String(200))
    type = Column(String(50))
    description = Column(Text)
    annee_univ = Column(String(20))
    semestre = Column(String(10))
    heures = Column(Integer)
    classe = Column(String(100))
    etablissement = Column(String(200))
    fichier_path = Column(String(300))
    responsable = Column(String(100))

class Tache(Base):
    __tablename__ = 'taches'
    id = Column(Integer, primary_key=True)
    tache = Column(String(200))
    categorie = Column(String(50))
    date_debut = Column(Date)
    date_fin = Column(Date)
    statut = Column(String(50))
    responsable = Column(String(100))

class Publication(Base):
    __tablename__ = 'publications'
    id = Column(Integer, primary_key=True)
    titre = Column(String(300))
    type = Column(String(50))
    conf_rev = Column(String(200))
    statut = Column(String(50))
    date_soumission = Column(Date)
    auteurs = Column(Text)
    lien = Column(String(500))

# Créer le moteur et la base
engine = create_engine('sqlite:///database.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- Configuration Streamlit ---
st.set_page_config(page_title="Suivi Académique", layout="wide")
st.title("🎓 Suivi des Projets et Tâches des Enseignants Universitaires")

# --- Fonction pour charger les données ---
def load_data():
    session = Session()
    # Cours
    cours_db = session.query(Cours).all()
    df_cours = pd.DataFrame([{
        "id": c.id,
        "Nom": c.nom,
        "Type": c.type,
        "Description": c.description,
        "Année Universitaire": c.annee_univ,
        "Semestre": c.semestre,
        "Heures": c.heures,
        "Classe": c.classe,
        "Établissement": c.etablissement,
        "Offre de formation": c.fichier_path,
        "Responsable": c.responsable
    } for c in cours_db])

    # Tâches
    taches_db = session.query(Tache).all()
    df_taches = pd.DataFrame([{
        "id": t.id,
        "Tâche": t.tache,
        "Catégorie": t.categorie,
        "Date Début": t.date_debut,
        "Date Fin": t.date_fin,
        "Statut": t.statut,
        "Responsable": t.responsable
    } for t in taches_db])

    # Publications
    pubs_db = session.query(Publication).all()
    df_pubs = pd.DataFrame([{
        "id": p.id,
        "Titre": p.titre,
        "Type": p.type,
        "Conf/Rev": p.conf_rev,
        "Statut": p.statut,
        "Date Soumission": p.date_soumission,
        "Auteurs": p.auteurs,
        "Lien": p.lien
    } for p in pubs_db])

    session.close()
    return df_cours, df_taches, df_pubs

# --- Fonction lien de téléchargement ---
def make_download_link(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        filename = os.path.basename(path)
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">📎 Télécharger</a>'
    return "–"

# --- Onglets ---
tab1, tab2, tab3, tab4 = st.tabs(["📚 Cours & TP/TD", "✅ Tâches", "📄 Publications", "📈 Dashboard & Calendrier"])

# Charger les données
df_cours, df_taches, df_pubs = load_data()

# --- 1. Gestion des Cours ---
with tab1:
    st.header("Gestion des Cours, TD et TP")

    with st.expander("➕ Ajouter un cours/TP/TD"):
        with st.form("form_cours"):
            nom = st.text_input("Nom du cours")
            type_cours = st.selectbox("Type", ["Cours", "TD", "TP"])
            description = st.text_area("Description")
            annee_univ = st.text_input("Année universitaire", value="2024-2025")
            semestre = st.selectbox("Semestre", ["S1", "S2", "S3", "S4", "S5", "S6"])
            heures = st.number_input("Nombre d'heures", min_value=1, value=2)
            classe = st.text_input("Classe des étudiants")
            etablissement = st.text_input("Établissement")
            responsable = st.text_input("Responsable")
            uploaded_file = st.file_uploader("Offre de formation (PDF/DOC)", type=["pdf", "doc", "docx"])

            if st.form_submit_button("Ajouter"):
                fichier_path = None
                if uploaded_file is not None:
                    os.makedirs("uploads", exist_ok=True)
                    fichier_path = os.path.join("uploads", f"{uuid.uuid4().hex}_{uploaded_file.name}")
                    with open(fichier_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                session = Session()
                session.add(Cours(
                    nom=nom, type=type_cours, description=description,
                    annee_univ=annee_univ, semestre=semestre, heures=heures,
                    classe=classe, etablissement=etablissement,
                    fichier_path=fichier_path, responsable=responsable
                ))
                session.commit()
                session.close()
                st.success("✅ Cours ajouté !")
                st.rerun()

    # Affichage des cours
    if not df_cours.empty:
        st.subheader("Liste des Cours")
        df_display = df_cours.copy()
        df_display["Offre de formation"] = df_display["Offre de formation"].apply(make_download_link)

        for idx, row in df_cours.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                col1.write(f"**{row['Nom']}** ({row['Type']}) - {row['Classe']}")
                if col2.button("✏️", key=f"edit_c_{row['id']}"):
                    st.session_state.edit_cours = row.to_dict()
                if col3.button("🗑️", key=f"del_c_{row['id']}"):
                    session = Session()
                    c = session.query(Cours).filter(Cours.id == row['id']).first()
                    if c and c.fichier_path and os.path.exists(c.fichier_path):
                        os.remove(c.fichier_path)
                    session.delete(c)
                    session.commit()
                    session.close()
                    st.rerun()
                col4.write(f"📅 {row['Semestre']} | {row['Heures']}h")
    else:
        st.info("Aucun cours ajouté.")

# --- 2. Gestion des Tâches ---
with tab2:
    st.header("Gestion des Tâches Académiques")

    with st.expander("➕ Ajouter une tâche"):
        with st.form("form_tache"):
            tache = st.text_input("Nom de la tâche")
            categorie = st.selectbox("Catégorie", ["Cours", "Recherche", "Administration", "Encadrement", "Autre"])
            debut = st.date_input("Date de début")
            fin = st.date_input("Date de fin")
            statut = st.selectbox("Statut", ["À faire", "En cours", "Terminé", "Reporté"])
            responsable = st.text_input("Responsable")
            if st.form_submit_button("Ajouter"):
                session = Session()
                session.add(Tache(
                    tache=tache, categorie=categorie,
                    date_debut=debut, date_fin=fin,
                    statut=statut, responsable=responsable
                ))
                session.commit()
                session.close()
                st.success("✅ Tâche ajoutée !")
                st.rerun()

    # Affichage des tâches
    if not df_taches.empty:
        for idx, row in df_taches.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                col1.write(f"**{row['Tâche']}** - {row['Catégorie']}")
                if col2.button("✏️", key=f"edit_t_{row['id']}"):
                    st.session_state.edit_tache = row.to_dict()
                if col3.button("🗑️", key=f"del_t_{row['id']}"):
                    session = Session()
                    session.query(Tache).filter(Tache.id == row['id']).delete()
                    session.commit()
                    session.close()
                    st.rerun()
                col4.write(f"🟢 {row['Statut']}")
    else:
        st.info("Aucune tâche.")

# --- 3. Gestion des Publications ---
with tab3:
    st.header("Publications Scientifiques")

    with st.expander("➕ Ajouter une publication"):
        with st.form("form_publi"):
            titre = st.text_input("Titre")
            type_p = st.selectbox("Type", ["Article de conférence", "Article de revue"])
            conf_rev = st.text_input("Conférence ou Revue")
            statut = st.selectbox("Statut", ["En rédaction", "Soumis", "Accepté", "Publié", "Refusé"])
            date = st.date_input("Date de soumission")
            auteurs = st.text_area("Auteurs", "Nom1, Nom2")
            lien = st.text_input("Lien (DOI, HAL, etc.)")
            if st.form_submit_button("Ajouter"):
                session = Session()
                session.add(Publication(
                    titre=titre, type=type_p, conf_rev=conf_rev,
                    statut=statut, date_soumission=date,
                    auteurs=auteurs, lien=lien
                ))
                session.commit()
                session.close()
                st.success("✅ Publication ajoutée !")
                st.rerun()

    # Affichage
    if not df_pubs.empty:
        for idx, row in df_pubs.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**{row['Titre']}** - {row['Type']}")
                if col2.button("✏️", key=f"edit_p_{row['id']}"):
                    st.session_state.edit_pub = row.to_dict()
                if col3.button("🗑️", key=f"del_p_{row['id']}"):
                    session = Session()
                    session.query(Publication).filter(Publication.id == row['id']).delete()
                    session.commit()
                    session.close()
                    st.rerun()
    else:
        st.info("Aucune publication.")

# --- 4. Dashboard & Calendrier ---
with tab4:
    st.header("📊 Tableau de Bord & 🗓️ Calendrier")

    df_cours, df_taches, df_pubs = load_data()  # Recharger

    col1, col2, col3 = st.columns(3)
    col1.metric("Cours", len(df_cours))
    col2.metric("Tâches", len(df_taches))
    col3.metric("Publications", len(df_pubs))

    if not df_taches.empty:
        fig = px.pie(df_taches, names="Statut", title="Répartition des Tâches")
        st.plotly_chart(fig, use_container_width=True)

    # 🗓️ Calendrier
    st.subheader("Calendrier des Tâches")
    events = []
    for _, row in df_taches.iterrows():
        events.append({
            "title": f"{row['Tâche']} ({row['Statut']})",
            "start": str(row["Date Début"]),
            "end": str(row["Date Fin"]),
            "color": {
                "À faire": "#d32f2f", "En cours": "#1976d2",
                "Terminé": "#388e3c", "Reporté": "#f57c00"
            }.get(row["Statut"], "#757575")
        })

    options = {
        "editable": "true",
        "selectable": "true",
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "dayGridMonth"
    }

    st_calendar.calendar(events=events, options=options)

    # Export iCal
    if st.button("Exporter le calendrier en .ics"):
        cal = Calendar()
        for _, row in df_taches.iterrows():
            ev = Event()
            ev.add('summary', row['Tâche'])
            ev.add('dtstart', datetime.combine(row['Date Début'], datetime.min.time()))
            ev.add('dtend', datetime.combine(row['Date Fin'], datetime.max.time()))
            ev.add('description', f"Statut: {row['Statut']}, Catégorie: {row['Catégorie']}, Responsable: {row['Responsable']}")
            cal.add_component(ev)
        ics_b64 = base64.b64encode(cal.to_ical()).decode()
        href = f'<a href="data:text/calendar;base64,{ics_b64}" download="taches.ics">📥 Télécharger .ics</a>'
        st.markdown(href, unsafe_allow_html=True)

# --- Modification des cours ---
if 'edit_cours' in st.session_state:
    st.sidebar.subheader("✏️ Modifier un cours")
    c = st.session_state.edit_cours
    with st.sidebar.form("modif_cours"):
        new_nom = st.text_input("Nom", c['Nom'])
        new_type = st.selectbox("Type", ["Cours", "TD", "TP"], index=["Cours", "TD", "TP"].index(c['Type']))
        new_desc = st.text_area("Description", c['Description'])
        new_annee = st.text_input("Année universitaire", c['Année Universitaire'])
        new_semestre = st.selectbox("Semestre", ["S1", "S2", "S3", "S4", "S5", "S6"], index=["S1", "S2", "S3", "S4", "S5", "S6"].index(c['Semestre']))
        new_heures = st.number_input("Heures", min_value=1, value=c['Heures'])
        new_classe = st.text_input("Classe", c['Classe'])
        new_etab = st.text_input("Établissement", c['Établissement'])
        new_resp = st.text_input("Responsable", c['Responsable'])

        st.write("Offre de formation")
        uploaded_file = st.file_uploader("Remplacer le fichier", type=["pdf", "doc", "docx"], key="upload_modif_cours")

        if st.form_submit_button("Mettre à jour"):
            session = Session()
            cours_db = session.query(Cours).filter(Cours.id == c['id']).first()

            # Gérer le nouveau fichier
            old_path = cours_db.fichier_path
            new_file_path = old_path

            if uploaded_file is not None:
                if old_path and os.path.exists(old_path):
                    os.remove(old_path)
                os.makedirs("uploads", exist_ok=True)
                new_file_path = os.path.join("uploads", f"{uuid.uuid4().hex}_{uploaded_file.name}")
                with open(new_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Mise à jour
            cours_db.nom = new_nom
            cours_db.type = new_type
            cours_db.description = new_desc
            cours_db.annee_univ = new_annee
            cours_db.semestre = new_semestre
            cours_db.heures = new_heures
            cours_db.classe = new_classe
            cours_db.etablissement = new_etab
            cours_db.fichier_path = new_file_path
            cours_db.responsable = new_resp

            session.commit()
            session.close()
            st.success("✅ Cours mis à jour !")
            st.session_state.pop('edit_cours')
            st.rerun()

# --- Modification des tâches ---
if 'edit_tache' in st.session_state:
    st.sidebar.subheader("✏️ Modifier une tâche")
    t = st.session_state.edit_tache
    with st.sidebar.form("modif_tache"):
        new_tache = st.text_input("Tâche", t['Tâche'])
        new_cat = st.selectbox("Catégorie", ["Cours", "Recherche", "Administration", "Encadrement", "Autre"], index=["Cours", "Recherche", "Administration", "Encadrement", "Autre"].index(t['Catégorie']))
        new_debut = st.date_input("Date début", t['Date Début'])
        new_fin = st.date_input("Date fin", t['Date Fin'])
        new_statut = st.selectbox("Statut", ["À faire", "En cours", "Terminé", "Reporté"], index=["À faire", "En cours", "Terminé", "Reporté"].index(t['Statut']))
        new_resp = st.text_input("Responsable", t['Responsable'])
        if st.form_submit_button("Mettre à jour"):
            session = Session()
            session.query(Tache).filter(Tache.id == t['id']).update({
                'tache': new_tache, 'categorie': new_cat, 'date_debut': new_debut,
                'date_fin': new_fin, 'statut': new_statut, 'responsable': new_resp
            })
            session.commit()
            session.close()
            st.session_state.pop('edit_tache')
            st.rerun()

# --- Modification des publications ---
if 'edit_pub' in st.session_state:
    st.sidebar.subheader("✏️ Modifier une publication")
    p = st.session_state.edit_pub
    with st.sidebar.form("modif_pub"):
        new_titre = st.text_input("Titre", p['Titre'])
        new_type = st.selectbox("Type", ["Article de conférence", "Article de revue"], index=0 if p['Type']=="Article de conférence" else 1)
        new_conf = st.text_input("Conférence/Revue", p['Conf/Rev'])
        new_statut = st.selectbox("Statut", ["En rédaction", "Soumis", "Accepté", "Publié", "Refusé"], index=["En rédaction", "Soumis", "Accepté", "Publié", "Refusé"].index(p['Statut']))
        new_date = st.date_input("Date soumission", p['Date Soumission'])
        new_auteurs = st.text_area("Auteurs", p['Auteurs'])
        new_lien = st.text_input("Lien", p['Lien'])
        if st.form_submit_button("Mettre à jour"):
            session = Session()
            session.query(Publication).filter(Publication.id == p['id']).update({
                'titre': new_titre, 'type': new_type, 'conf_rev': new_conf,
                'statut': new_statut, 'date_soumission': new_date,
                'auteurs': new_auteurs, 'lien': new_lien
            })
            session.commit()
            session.close()
            st.session_state.pop('edit_pub')
            st.rerun()

# --- Footer ---
st.markdown("---")
st.caption("© 2025 – Application de suivi académique pour enseignants universitaires")