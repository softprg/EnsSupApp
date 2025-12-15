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
from sqlalchemy import Boolean
# Base de données
from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import streamlit_calendar as st_calendar
import random
# --- Style CSS pour les post-it ---

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
    notes = Column(Text)  # Champ notes

class Tache(Base):
    __tablename__ = 'taches'
    id = Column(Integer, primary_key=True)
    tache = Column(String(200))
    categorie = Column(String(50))
    date_debut = Column(Date)
    date_fin = Column(Date)
    statut = Column(String(50))
    responsable = Column(String(100))
    notes = Column(Text)

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
    notes = Column(Text)

class TacheDev(Base):
    __tablename__ = 'taches_dev'
    id = Column(Integer, primary_key=True)
    nom = Column(String(200))
    description = Column(Text)
    priorite = Column(String(20))  # Faible, Moyenne, Élevée
    date_echeance = Column(Date)
    statut = Column(String(50))  # À faire, En cours, En test, Terminé
    responsable = Column(String(100))
    notes = Column(Text)
class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    titre = Column(String(100), default="Note")
    contenu = Column(Text)
    couleur = Column(String(20), default="yellow")  # yellow, pink, blue, green, gray
    est_archivee = Column(Boolean, default=False)
    date_creation = Column(Date, default=datetime.now)
# Créer le moteur et la base
engine = create_engine('sqlite:///database1.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- Configuration Streamlit ---
st.set_page_config(page_title="Suivi Académique", layout="wide")
st.title("🎓 Suivi des Projets et Tâches des Enseignants Universitaires")

# --- Fonction pour charger les données ---
def load_notes(archivees=False):
    session = Session()
    notes_db = session.query(Note).filter(Note.est_archivee == archivees).all()
    session.close()
    return notes_db
def afficher_notesold(archivees=False):
    notes = load_notes(archivees)
    couleur_map = {
        "yellow": "#fff9c4",   # Jaune clair
        "pink": "#f8bbd0",     # Rose
        "blue": "#bbdefb",     # Bleu
        "green": "#c8e6c9",    # Vert
        "gray": "#eeeeee"      # Gris
    }

    if not notes:
        st.info("Aucune note." if not archivees else "Aucune note archivée.")
        return

    for note in notes:
        bg = couleur_map.get(note.couleur, "#fff9c4")
        with st.container():
            st.markdown(f"<div class='postit' style='background-color: {bg};'>", unsafe_allow_html=True)

            # Titre (modifiable)
            nouveau_titre = st.text_input("Titre", value=note.titre, key=f"titre_{note.id}")

            # Contenu (modifiable)
            nouveau_contenu = st.text_area("Contenu", value=note.contenu, key=f"contenu_{note.id}", height=80)

            # Actions : Sauvegarder / Archiver / Supprimer
            col1, col2, col3 = st.columns([1, 1, 1])
            if col1.button("💾", key=f"save_{note.id}"):
                session = Session()
                n = session.query(Note).filter(Note.id == note.id).first()
                n.titre = nouveau_titre
                n.contenu = nouveau_contenu
                session.commit()
                session.close()
                st.rerun()

            if not archivees:
                if col2.button("📦", key=f"arch_{note.id}"):
                    session = Session()
                    n = session.query(Note).filter(Note.id == note.id).first()
                    n.est_archivee = True
                    session.commit()
                    session.close()
                    st.rerun()
            else:
                if col2.button("📤", key=f"unarch_{note.id}"):
                    session = Session()
                    n = session.query(Note).filter(Note.id == note.id).first()
                    n.est_archivee = False
                    session.commit()
                    session.close()
                    st.rerun()

            if col3.button("🗑️", key=f"del_{note.id}"):
                session = Session()
                session.query(Note).filter(Note.id == note.id).delete()
                session.commit()
                session.close()
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
import random  # Assurez-vous que cet import est en haut de votre fichier
def afficher_notes(archivees=False):
    notes = load_notes(archivees)
    
    # Couleurs en format Streamlit natif (pas de CSS)
    couleur_map = {
        "yellow": "warning",   # Jaune
        "pink": "error",       # Rose
        "blue": "info",        # Bleu
        "green": "success",    # Vert
        "gray": "secondary"    # Gris
    }
    
    # Messages d'information si aucune note
    if not notes:
        if archivees:
            st.info("📭 Aucune note archivée pour le moment")
        else:
            st.info("📭 Aucune note active. Utilisez 'Ajouter une note' pour créer votre première note !")
        return

    # Déterminer le nombre de colonnes (1 à 4 selon le nombre de notes)
    num_cols = min(4, max(1, len(notes)))
    cols = st.columns(num_cols)
    
    # Fonction pour créer une note Post-it
    def creer_note(col, note, bg_color):
        with col:
            # Container avec couleur de fond native de Streamlit
            with st.container(border=True):
                # Titre de la note (modifiable)
                st.subheader(note.titre)
                
                # Contenu de la note (modifiable)
                nouveau_contenu = st.text_area(
                    "Contenu", 
                    value=note.contenu, 
                    key=f"contenu_{note.id}",
                    height=100,
                    label_visibility="collapsed"
                )
                
                # Boutons d'action
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾", key=f"save_{note.id}", help="Sauvegarder"):
                        session = Session()
                        try:
                            n = session.query(Note).filter(Note.id == note.id).first()
                            if n:
                                n.contenu = nouveau_contenu
                                session.commit()
                                st.toast("Note sauvegardée !", icon="✅")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Erreur : {str(e)}")
                        finally:
                            session.close()
                        st.rerun()
                
                with col2:
                    if not archivees:
                        if st.button("📦", key=f"arch_{note.id}", help="Archiver"):
                            session = Session()
                            try:
                                n = session.query(Note).filter(Note.id == note.id).first()
                                if n:
                                    n.est_archivee = True
                                    session.commit()
                                    st.toast("Note archivée !", icon="📦")
                            except Exception as e:
                                session.rollback()
                            finally:
                                session.close()
                            st.rerun()
                    else:
                        if st.button("📤", key=f"unarch_{note.id}", help="Restaurer"):
                            session = Session()
                            try:
                                n = session.query(Note).filter(Note.id == note.id).first()
                                if n:
                                    n.est_archivee = False
                                    session.commit()
                                    st.toast("Note restaurée !", icon="📤")
                            except Exception as e:
                                session.rollback()
                            finally:
                                session.close()
                            st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"del_{note.id}", help="Supprimer", type="secondary"):
                        session = Session()
                        try:
                            session.query(Note).filter(Note.id == note.id).delete()
                            session.commit()
                            st.toast("Note supprimée !", icon="🗑️")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Erreur : {str(e)}")
                        finally:
                            session.close()
                        st.rerun()

    # Placer les notes dans la grille
    for i, note in enumerate(notes):
        bg_color = couleur_map.get(note.couleur, "warning")
        col = cols[i % num_cols]
        creer_note(col, note, bg_color)
           

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
        "Responsable": c.responsable,
        "Notes": c.notes
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
        "Responsable": t.responsable,
        "Notes": t.notes
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
        "Lien": p.lien,
        "Notes": p.notes
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
        return f'<a href="application/octet-stream;base64,{b64}" download="{filename}">📎 Télécharger</a>'
    return "–"

# --- Fonction d'alertes ---
def get_alerts():
    alerts = []
    today = datetime.now().date()
    _, df_taches, df_pubs = load_data()

    session = Session()
    dev_tasks = session.query(TacheDev).all()
    session.close()

    # Alertes Tâches
    if not df_taches.empty:
        for _, t in df_taches.iterrows():
            if t["Statut"] != "Terminé" and isinstance(t["Date Fin"], datetime):
                days_left = (t["Date Fin"].date() - today).days
                if 0 <= days_left <= 7:
                    alerts.append({
                        "type": "⚠️ Tâche",
                        "text": f"**{t['Tâche']}** arrive à échéance dans {days_left} jour(s)",
                        "color": "red" if days_left <= 3 else "orange"
                    })

    # Alertes Publications
    if not df_pubs.empty:
        for _, p in df_pubs.iterrows():
            if p["Statut"] in ["En rédaction", "Soumis"] and isinstance(p["Date Soumission"], datetime):
                days_left = (p["Date Soumission"].date() - today).days
                if 0 <= days_left <= 7:
                    alerts.append({
                        "type": "📢 Publication",
                        "text": f"Soumission de **{p['Titre']}** dans {days_left} jour(s)",
                        "color": "red" if days_left <= 3 else "orange"
                    })

    # Alertes Développement
    for t in dev_tasks:
        if t.statut != "Terminé" and t.date_echeance:
            days_left = (t.date_echeance - today).days
            if 0 <= days_left <= 7:
                alerts.append({
                    "type": "⚙️ Dév",
                    "text": f"Tâche dev **{t.nom}** échéance dans {days_left} jour(s)",
                    "color": "red" if days_left <= 3 else "orange"
                })

    return alerts

# --- Affichage des alertes ---
alerts = get_alerts()
if alerts:
    st.markdown("### 🔔 **Alertes d'échéance**")
    for a in alerts:
        icon = "🔴" if a["color"] == "red" else "🟠"
        st.markdown(f"{icon} {a['type']} : {a['text']}")
    st.markdown("---")

# --- Onglets ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📚 Cours & TP/TD", "✅ Tâches", "📄 Publications",
    "📈 Dashboard & Calendrier", "⚙️ Développement", "📌 Notes"
])

# Charger les données
df_cours, df_taches, df_pubs = load_data()

# --- 1. Cours ---
with tab1:
    st.header("Gestion des Cours, TD et TP")
    with st.expander("➕ Ajouter un cours/TP/TD"):
        with st.form("form_cours"):
            nom = st.text_input("Nom du cours")
            type_cours = st.selectbox("Type", ["Cours", "TD", "TP"])
            description = st.text_area("Description")
            annee_univ = st.text_input("Année universitaire", value="2024-2025")
            semestre = st.selectbox("Semestre", ["S1", "S2", "S3", "S4", "S5", "S6"])
            heures = st.number_input("Heures", min_value=1, value=2)
            classe = st.text_input("Classe")
            etablissement = st.text_input("Établissement")
            responsable = st.text_input("Responsable")
            uploaded_file = st.file_uploader("Offre de formation", type=["pdf", "doc", "docx"])
            notes = st.text_area("Notes personnelles")
            if st.form_submit_button("Ajouter"):
                fichier_path = None
                if uploaded_file:
                    os.makedirs("uploads", exist_ok=True)
                    fichier_path = os.path.join("uploads", f"{uuid.uuid4().hex}_{uploaded_file.name}")
                    with open(fichier_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                session = Session()
                session.add(Cours(nom=nom, type=type_cours, description=description,
                                  annee_univ=annee_univ, semestre=semestre, heures=heures,
                                  classe=classe, etablissement=etablissement,
                                  fichier_path=fichier_path, responsable=responsable,
                                  notes=notes))
                session.commit()
                session.close()
                st.success("✅ Ajouté !")
                st.rerun()
    if not df_cours.empty:
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
                col4.write(f"📅 {row['Semestre']}")

# --- 2. Tâches ---
with tab2:
    st.header("Gestion des Tâches")
    with st.expander("➕ Ajouter"):
        with st.form("form_tache"):
            tache = st.text_input("Nom")
            categorie = st.selectbox("Catégorie", ["Cours", "Recherche", "Administration", "Encadrement", "Autre"])
            debut = st.date_input("Début")
            fin = st.date_input("Fin")
            statut = st.selectbox("Statut", ["À faire", "En cours", "Terminé", "Reporté"])
            responsable = st.text_input("Responsable")
            notes = st.text_area("Notes")
            if st.form_submit_button("Ajouter"):
                session = Session()
                session.add(Tache(tache=tache, categorie=categorie, date_debut=debut,
                                  date_fin=fin, statut=statut, responsable=responsable,
                                  notes=notes))
                session.commit()
                session.close()
                st.success("✅ Ajoutée !")
                st.rerun()
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

# --- 3. Publications ---
with tab3:
    st.header("Publications")
    with st.expander("➕ Ajouter"):
        with st.form("form_publi"):
            titre = st.text_input("Titre")
            type_p = st.selectbox("Type", ["Article de conférence", "Article de revue"])
            conf_rev = st.text_input("Conférence/Revue")
            statut = st.selectbox("Statut", ["En rédaction", "Soumis", "Accepté", "Publié", "Refusé"])
            date = st.date_input("Date soumission")
            auteurs = st.text_area("Auteurs", "Nom1, Nom2")
            lien = st.text_input("Lien")
            notes = st.text_area("Notes")
            if st.form_submit_button("Ajouter"):
                session = Session()
                session.add(Publication(titre=titre, type=type_p, conf_rev=conf_rev,
                                        statut=statut, date_soumission=date,
                                        auteurs=auteurs, lien=lien, notes=notes))
                session.commit()
                session.close()
                st.success("✅ Ajoutée !")
                st.rerun()
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

# --- 4. Dashboard & Calendrier ---
with tab4:
    st.header("📊 Dashboard & 🗓️ Calendrier")

    df_cours, df_taches, df_pubs = load_data()

    # KPIs Académiques
    col1, col2, col3 = st.columns(3)
    col1.metric("Cours", len(df_cours))
    col2.metric("Tâches", len(df_taches))
    col3.metric("Publications", len(df_pubs))

    # Graphique Tâches
    if not df_taches.empty:
        fig_tache = px.pie(df_taches, names="Statut", title="Statut des tâches académiques")
        st.plotly_chart(fig_tache, use_container_width=True)

    # === MÉTRIQUES DÉVELOPPEMENT ===
    session = Session()
    dev_tasks = session.query(TacheDev).all()
    session.close()

    df_dev = pd.DataFrame([{
        "id": t.id, "Nom": t.nom, "Priorité": t.priorite,
        "Échéance": t.date_echeance, "Statut": t.statut,
        "Responsable": t.responsable, "Notes": t.notes
    } for t in dev_tasks])

    if not df_dev.empty:
        col4, col5, col6 = st.columns(3)
        total = len(df_dev)
        terminees = len(df_dev[df_dev["Statut"] == "Terminé"])
        en_cours = len(df_dev[df_dev["Statut"].isin(["En cours", "En test"])])
        col4.metric("Tâches Dev", total)
        col5.metric("Terminées", terminees, f"{round(100*terminees/total)}%" if total else "0%")
        col6.metric("En cours", en_cours)

        fig_dev = px.bar(df_dev.groupby("Statut").size().reset_index(name="Nombre"),
                         x="Statut", y="Nombre", color="Statut",
                         title="Tâches de Développement par Statut")
        st.plotly_chart(fig_dev, use_container_width=True)
    else:
        st.info("Aucune tâche de développement enregistrée.")
    # === CALENDRIER ===
    events = []
    for _, row in df_taches.iterrows():
        events.append({
            "title": f"✅ {row['Tâche']}",
            "start": str(row["Date Début"]),
            "end": str(row["Date Fin"]),
            "color": {"À faire": "#d32f2f", "En cours": "#1976d2", "Terminé": "#388e3c"}.get(row["Statut"], "#757575")
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
# --- 5. Tâches de Développement ---
with tab5:
    st.header("⚙️ Suivi des Tâches de Développement")
    with st.expander("➕ Ajouter une tâche"):
        with st.form("form_dev"):
            nom = st.text_input("Nom")
            desc = st.text_area("Description")
            priorite = st.selectbox("Priorité", ["Faible", "Moyenne", "Élevée"])
            echeance = st.date_input("Échéance")
            statut = st.selectbox("Statut", ["À faire", "En cours", "En test", "Terminé"])
            responsable = st.text_input("Responsable")
            notes = st.text_area("Notes")
            if st.form_submit_button("Ajouter"):
                session = Session()
                session.add(TacheDev(nom=nom, description=desc, priorite=priorite,
                                     date_echeance=echeance, statut=statut,
                                     responsable=responsable, notes=notes))
                session.commit()
                session.close()
                st.success("✅ Ajoutée !")
                st.rerun()
    session = Session()
    dev_tasks = session.query(TacheDev).all()
    session.close()
    if dev_tasks:
        for t in dev_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                col1.write(f"**{t.nom}** - {t.priorite}")
                if col2.button("✏️", key=f"edit_dev_{t.id}"):
                    st.session_state.edit_dev = t
                if col3.button("🗑️", key=f"del_dev_{t.id}"):
                    session = Session()
                    session.delete(session.query(TacheDev).filter(TacheDev.id == t.id).first())
                    session.commit()
                    session.close()
                    st.rerun()
                col4.write(f"📅 {t.date_echeance} | {t.statut}")


with tab6:
    st.header("📌 Notes visuelles (Post-it)")

    # Ajouter une nouvelle note
    with st.expander("➕ Ajouter une note"):
        with st.form("form_note"):
            titre = st.text_input("Titre", "Nouvelle note")
            contenu = st.text_area("Contenu")
            couleur = st.selectbox("Couleur", ["yellow", "pink", "blue", "green", "gray"])
            if st.form_submit_button("Créer"):
                session = Session()
                session.add(Note(titre=titre, contenu=contenu, couleur=couleur))
                session.commit()
                session.close()
                st.rerun()

    st.subheader("📝 Notes actives")
    afficher_notes(archivees=False)

    st.subheader("📦 Notes archivées")
    afficher_notes(archivees=True)
# --- Modifications ---
if 'edit_cours' in st.session_state:
    st.sidebar.subheader("✏️ Modifier Cours")
    c = st.session_state.edit_cours
    with st.sidebar.form("modif_cours"):
        new_nom = st.text_input("Nom", c['Nom'])
        new_type = st.selectbox("Type", ["Cours", "TD", "TP"], index=["Cours", "TD", "TP"].index(c['Type']))
        new_desc = st.text_area("Description", c['Description'])
        new_annee = st.text_input("Année", c['Année Universitaire'])
        new_semestre = st.selectbox("Semestre", ["S1", "S2", "S3", "S4", "S5", "S6"], index=["S1", "S2", "S3", "S4", "S5", "S6"].index(c['Semestre']))
        new_heures = st.number_input("Heures", min_value=1, value=c['Heures'])
        new_classe = st.text_input("Classe", c['Classe'])
        new_etab = st.text_input("Étab", c['Établissement'])
        new_resp = st.text_input("Resp", c['Responsable'])
        new_notes = st.text_area("Notes", c['Notes'])
        uploaded_file = st.file_uploader("Remplacer fichier", type=["pdf", "doc", "docx"])
        if st.form_submit_button("Mettre à jour"):
            session = Session()
            db = session.query(Cours).filter(Cours.id == c['id']).first()
            old = db.fichier_path
            path = old
            if uploaded_file:
                if old and os.path.exists(old): os.remove(old)
                os.makedirs("uploads", exist_ok=True)
                path = os.path.join("uploads", f"{uuid.uuid4().hex}_{uploaded_file.name}")
                with open(path, "wb") as f: f.write(uploaded_file.getbuffer())
            db.nom, db.type, db.description, db.annee_univ = new_nom, new_type, new_desc, new_annee
            db.semestre, db.heures, db.classe, db.etablissement = new_semestre, new_heures, new_classe, new_etab
            db.fichier_path, db.responsable, db.notes = path, new_resp, new_notes
            session.commit()
            session.close()
            st.session_state.pop('edit_cours')
            st.rerun()

# (Idem pour edit_tache, edit_pub, edit_dev — gardés concis ici)
# --- Modification Tâche Académique ---
if 'edit_tache' in st.session_state:
    st.sidebar.subheader("✏️ Modifier une tâche")
    t = st.session_state.edit_tache
    with st.sidebar.form("modif_tache"):
        new_tache = st.text_input("Nom", t['Tâche'])
        new_cat = st.selectbox("Catégorie", ["Cours", "Recherche", "Administration", "Encadrement", "Autre"],
                               index=["Cours", "Recherche", "Administration", "Encadrement", "Autre"].index(t['Catégorie']))
        new_debut = st.date_input("Date début", t['Date Début'])
        new_fin = st.date_input("Date fin", t['Date Fin'])
        new_statut = st.selectbox("Statut", ["À faire", "En cours", "Terminé", "Reporté"],
                                  index=["À faire", "En cours", "Terminé", "Reporté"].index(t['Statut']))
        new_resp = st.text_input("Responsable", t['Responsable'])
        new_notes = st.text_area("Notes", t['Notes'])

        if st.form_submit_button("Mettre à jour"):
            session = Session()
            session.query(Tache).filter(Tache.id == t['id']).update({
                'tache': new_tache,
                'categorie': new_cat,
                'date_debut': new_debut,
                'date_fin': new_fin,
                'statut': new_statut,
                'responsable': new_resp,
                'notes': new_notes
            })
            session.commit()
            session.close()
            st.session_state.pop('edit_tache')
            st.success("✅ Tâche mise à jour !")
            st.rerun()
# --- Modification Tâche de Développement ---
if 'edit_dev' in st.session_state:
    st.sidebar.subheader("✏️ Modifier tâche de développement")
    t = st.session_state.edit_dev
    with st.sidebar.form("modif_dev"):
        new_nom = st.text_input("Nom", t.nom)
        new_desc = st.text_area("Description", t.description)
        new_prio = st.selectbox("Priorité", ["Faible", "Moyenne", "Élevée"],
                                index=["Faible", "Moyenne", "Élevée"].index(t.priorite))
        new_echeance = st.date_input("Échéance", t.date_echeance)
        new_statut = st.selectbox("Statut", ["À faire", "En cours", "En test", "Terminé"],
                                  index=["À faire", "En cours", "En test", "Terminé"].index(t.statut))
        new_resp = st.text_input("Responsable", t.responsable)
        new_notes = st.text_area("Notes", t.notes)

        if st.form_submit_button("Mettre à jour"):
            session = Session()
            session.query(TacheDev).filter(TacheDev.id == t.id).update({
                'nom': new_nom,
                'description': new_desc,
                'priorite': new_prio,
                'date_echeance': new_echeance,
                'statut': new_statut,
                'responsable': new_resp,
                'notes': new_notes
            })
            session.commit()
            session.close()
            st.session_state.pop('edit_dev')
            st.success("✅ Tâche de développement mise à jour !")
            st.rerun()
# --- Footer ---
st.markdown("---")
st.caption("© 2025 – Application de suivi académique complète")