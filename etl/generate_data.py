"""
Générateur de données synthétiques ENSA Kénitra — version ETL.
Produit des fichiers CSV dans ./data/raw/ pour les étapes extract/transform/load.
"""
import csv
import random
import os
from datetime import date, timedelta

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
PRENOMS_M = [
    "Mohamed","Ahmed","Youssef","Omar","Ali","Hassan","Hamza","Anas","Ibrahim",
    "Karim","Saad","Tariq","Rachid","Nabil","Bilal","Mehdi","Younes","Adam",
    "Walid","Hicham","Othmane","Zakaria","Ilyass","Amine","Reda","Mounir",
    "Soufiane","Adnane","Khalid","Jamal","Mostafa","Ismail","Nassim","Sami",
    "Ayoub","Rayan","Samir","Marouane","Abdelkarim","Badr",
]
PRENOMS_F = [
    "Fatima","Khadija","Nadia","Sara","Leila","Amina","Zineb","Hajar","Meryem",
    "Houda","Hind","Imane","Sanaa","Loubna","Rim","Ghita","Yasmine","Chaima",
    "Hafsa","Manal","Siham","Wiam","Ikram","Oumaima","Nihal","Samira","Layla",
    "Rania","Nora","Asma","Dina","Soukaina","Narjiss","Jihane","Bouchra","Salma",
    "Nour","Hana","Kawtar","Lamia",
]
NOMS = [
    "Alaoui","Benali","Idrissi","El Amrani","Cherkaoui","Bouazza","Tazi",
    "El Filali","Benomar","Sabri","Nadori","El Hassani","Berrada","Squalli",
    "El Ouazzani","Ziani","Bensaid","El Yousfi","Moussaoui","El Khatib",
    "Lahlou","Bakkali","Chraibi","El Fathi","Taqi","Rahmouni","El Ghazi",
    "Mansouri","Bouzidi","Benkirane","El Baraka","Slaoui","Fennich",
    "El Hajji","Kettani","Lemrini","El Mernissi","Boudouma","Hilali",
    "El Mesaoudi","Tahiri","Ennaji","Benlahcen","Regragui","Afilal",
    "Benhaddane","Aftyss","Abdelmoumen","El Ansari","Boukhari","Zerrouq",
]
ANNEES = ["2020-2021","2021-2022","2022-2023","2023-2024","2024-2025"]
VILLES = ["Kénitra","Rabat","Casablanca","Salé","Fès","Meknès","Sidi Kacem","Larache","Tanger","Oujda"]

FILIERES = [
    (1,"GI-BD","Génie Informatique - Big Data & Data Science"),
    (2,"GI-GL","Génie Informatique - Génie Logiciel"),
    (3,"GSTR","Génie Électrique, Réseaux et Systèmes de Télécommunication"),
    (4,"GINDUS","Génie Industriel"),
    (5,"GEN","Enseignements Généraux"),
]
FILIERE_DIFFICULTY = {1:0.0, 2:0.0, 3:-1.5, 4:-1.0, 5:0.5}

COURSES = [
    (1,"Statistique Inférentielle",1,"S1",4),
    (2,"Complexité & Structures de Données",1,"S1",5),
    (3,"Réseaux Informatiques",1,"S1",5),
    (4,"Électronique Numérique",1,"S1",5),
    (5,"Systèmes d'Information & Bases de Données",1,"S1",5),
    (6,"Langues Étrangères",1,"S1",3),
    (7,"Digitalisation",1,"S1",3),
    (8,"Technologies Web",1,"S2",5),
    (9,"Modélisation & Simulation",1,"S2",5),
    (10,"Optimisation des Systèmes",1,"S2",5),
    (11,"Technologies de Communication",1,"S2",5),
    (12,"Programmation Objet",1,"S2",4),
    (13,"Droit, Civisme & Citoyenneté",1,"S2",3),
    (14,"Advanced Python",1,"S3",5),
    (15,"Systèmes d'Exploitation",1,"S3",5),
    (16,"Multimédia & Traitement d'Image",1,"S3",4),
    (17,"Ingénierie des Bases de Données",1,"S3",5),
    (18,"Programmation Java",1,"S3",5),
    (19,"Introduction à l'IA",1,"S3",3),
    (20,"Fondamentaux des Big Data",1,"S4",5),
    (21,"IA Avancée",1,"S4",5),
    (22,"Gouvernance & Données",1,"S4",5),
    (23,"Analyse & Visualisation",1,"S4",5),
    (24,"Cybersécurité",1,"S4",4),
    (25,"Big Data Avancée",1,"S5",5),
    (26,"Vision par Ordinateur & Deep Learning",1,"S5",5),
    (27,"Business Intelligence",1,"S5",5),
    (28,"Cloud & Virtualisation",1,"S5",4),
    (29,"Sécurité des Données",1,"S5",5),
    (30,"Développement Full Stack",2,"S4",5),
    (31,"Développement Mobile",2,"S4",5),
    (32,"UX/UI Design",2,"S4",4),
    (33,"Admin & Prog. Système",2,"S4",5),
    (34,"Datawarehouse & Datamining",2,"S4",5),
    (35,"Génie Logiciel & Architecture",2,"S5",5),
    (36,"Développement JEE",2,"S5",5),
    (37,"Design Patterns & Tests",2,"S5",5),
    (38,"BPM & CRM",2,"S5",4),
    (39,"DevOps",2,"S5",5),
    (40,"Maths pour Ingénieur 1",3,"S5",5),
    (41,"Ondes, Propagation & Antennes",3,"S5",5),
    (42,"Électronique Analogique",3,"S5",5),
    (43,"Circuits Électriques et Magnétiques",3,"S5",5),
    (44,"Capteurs et Actionneurs",3,"S6",5),
    (45,"Machines CC & Schémas Électrotechniques",3,"S6",5),
    (46,"Électronique Numérique Avancée",3,"S6",5),
    (47,"Électronique de Puissance 1",3,"S6",5),
    (48,"Asservissement Continu et Échantillonné",3,"S6",5),
    (49,"Informatique Industrielle",3,"S7",5),
    (50,"Machines Synchrones et Asynchrones",3,"S7",5),
    (51,"Transmission Numérique & Réseaux",3,"S7",5),
    (52,"Électronique de Puissance 2",3,"S7",5),
    (53,"Régulation Industrielle et Intelligente",3,"S7",5),
    (54,"Production d'Énergie Renouvelable",3,"S8",5),
    (55,"Informatique & Intelligence Embarquées",3,"S8",5),
    (56,"Réseaux Électriques",3,"S8",5),
    (57,"Systèmes Embarqués et Temps Réel",3,"S8",5),
    (58,"Transport Énergie et Stabilité Réseaux",3,"S9",5),
    (59,"Robotique Industrielle et Collaborative",3,"S9",5),
    (60,"Communication Industrielle et Supervision",3,"S9",5),
    (61,"Apprentissage Artificiel et Vision",3,"S9",5),
    (62,"Mobilité Verte",3,"S9",5),
    (63,"Internet des Objets et Systèmes Cyberphysiques",3,"S9",5),
    (64,"Optimisation et Systèmes Industriels",4,"S5",5),
    (65,"Développement WEB",4,"S6",5),
    (66,"Modélisation et Simulation Numérique",4,"S6",5),
    (67,"POO",4,"S6",4),
    (68,"Management de la Qualité",4,"S7",5),
    (69,"CFAO et Procédés Industriels",4,"S7",5),
    (70,"Gestion de la Production",4,"S7",5),
    (71,"SCM",4,"S7",5),
    (72,"Introduction à l'IA",4,"S7",3),
    (73,"IA for Industrial Business Process Management",4,"S8",5),
    (74,"Management de la Maintenance et SdF",4,"S8",5),
    (75,"Systèmes d'Informations Intégrés (ERP)",4,"S8",5),
    (76,"Ordonnancement",4,"S8",5),
    (77,"Automatisme et Robotique",4,"S8",4),
    (78,"Performance, Durabilité et Résilience",4,"S9",5),
    (79,"Industrial Data Driving et Prise de Décision",4,"S9",5),
    (80,"Analyse de Données Intelligente",4,"S9",5),
    (81,"Cloud et Cybersécurité",4,"S9",4),
    (82,"Mathématiques Appliquées",5,"S1",5),
    (83,"Physique Générale",5,"S1",5),
    (84,"Informatique & Algo",5,"S1",5),
    (85,"Communication & Expression",5,"S2",3),
    (86,"Thermodynamique",5,"S2",4),
    (87,"Mécanique Rationnelle",5,"S2",4),
]
COURSES_BY_FILIERE = {}
for c in COURSES:
    COURSES_BY_FILIERE.setdefault(c[2], []).append(c[0])

DEPTS_FINANCE = [
    "Informatique et Mathématiques","Génie Électrique et Réseaux","Génie Industriel",
    "Enseignements Généraux","Direction","Scolarité & Administration",
    "Ressources Humaines","Infrastructure et Maintenance",
    "Recherche et Innovation","Bibliothèque et Documentation",
]
BUDGET_BASE = {
    "Informatique et Mathématiques":850000,"Génie Électrique et Réseaux":920000,
    "Génie Industriel":880000,"Enseignements Généraux":650000,"Direction":1200000,
    "Scolarité & Administration":450000,"Ressources Humaines":380000,
    "Infrastructure et Maintenance":700000,"Recherche et Innovation":600000,
    "Bibliothèque et Documentation":200000,
}

def write_csv(path, rows, header):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  ✔ {os.path.basename(path)} ({len(rows)} lignes)")

def make_email(prenom, nom, used):
    tr = str.maketrans("àâäéèêëîïôöùûüçñ","aaaeeeeiioouuucn")
    p = prenom.lower().replace(" ","").replace("-","").replace("'","").translate(tr)
    n = nom.lower().replace(" ","").replace("-","").replace("'","").translate(tr)
    base = f"{p}.{n}"
    email = f"{base}@uit.ac.ma"
    i = 1
    while email in used:
        email = f"{base}{i}@uit.ac.ma"; i += 1
    used.add(email)
    return email

def gaussian_note(mean, std=3.2):
    n = random.gauss(mean, std)
    return round(max(0.0, min(20.0, n)), 2)

def generate_all():
    print("\n🔄 Génération des données ENSA Kénitra...")

    write_csv(os.path.join(RAW_DIR,"filieres.csv"), FILIERES,
              ["id","nom","description"])

    write_csv(os.path.join(RAW_DIR,"courses.csv"), COURSES,
              ["id","nom","filiere_id","semestre","credits"])

    # Teachers
    DEPT_BY_FILIERE = {
        1:"Informatique et Mathématiques", 2:"Informatique et Mathématiques",
        3:"Génie Électrique et Réseaux", 4:"Génie Industriel", 5:"Enseignements Généraux",
    }
    GRADES_ENS = ["Professeur","Professeur Habilité","Professeur Associé","Maître de Conférences","Enseignant-Chercheur"]
    teachers = []
    tid = 1
    dept_teachers = {}
    for fil_id, dept in DEPT_BY_FILIERE.items():
        for _ in range(random.randint(8,14)):
            sexe = "M" if random.random() < 0.65 else "F"
            prenom = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
            nom = random.choice(NOMS)
            grade = random.choice(GRADES_ENS)
            sal = round(random.gauss(12000,3000),2)
            sal = max(7500, min(sal,25000))
            if random.random() < 0.03: sal = ""
            teachers.append((tid,nom,prenom,sexe,dept,grade,sal))
            dept_teachers.setdefault(dept,[]).append(tid)
            tid += 1
    write_csv(os.path.join(RAW_DIR,"teachers.csv"), teachers,
              ["id","nom","prenom","sexe","departement","grade","salaire"])

    # Students
    FILIERE_SIZE = {1:260, 2:220, 3:300, 4:280, 5:140}
    students = []
    used_emails = set()
    sid = 1
    for fil_id, count in FILIERE_SIZE.items():
        for _ in range(count):
            sexe = "M" if random.random() < 0.62 else "F"
            prenom = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
            nom = random.choice(NOMS)
            email = make_email(prenom, nom, used_emails)
            weights = [0.14,0.17,0.25,0.24,0.20]
            annee_entree = random.choices([2020,2021,2022,2023,2024], weights=weights)[0]
            age_entree = random.randint(18,23)
            naissance = date(annee_entree - age_entree, random.randint(1,12), random.randint(1,28))
            ville = random.choice(VILLES)
            annee_cursus = min(5, 2025 - annee_entree + 1)
            if random.random() < 0.02: email = ""
            students.append((sid,nom,prenom,sexe,str(naissance),email,fil_id,annee_cursus,annee_entree,ville))
            sid += 1
    write_csv(os.path.join(RAW_DIR,"students.csv"), students,
              ["id","nom","prenom","sexe","date_naissance","email","filiere_id","annee_cursus","annee_entree","ville_origine"])

    # Grades
    LEVEL_BASE = {"bon":13.5,"moyen":11.0,"faible":8.5}
    profiles = {}
    for s in students:
        profiles[s[0]] = random.choices(["bon","moyen","faible"],[30,45,25])[0]
    grades = []
    gid = 1
    for s in students:
        sid2 = s[0]; fil_id = s[6]; annee_entree = s[8]
        base_mean = LEVEL_BASE[profiles[sid2]] + FILIERE_DIFFICULTY[fil_id]
        all_c = COURSES_BY_FILIERE.get(fil_id,[]) + (COURSES_BY_FILIERE.get(5,[]) if fil_id!=5 else [])
        n_courses = min(len(all_c), random.randint(6,12))
        selected = random.sample(all_c, n_courses)
        for cid in selected:
            for ay in ANNEES:
                yr = int(ay[:4])
                if yr < annee_entree or yr > annee_entree + 4: continue
                for sem in [1,2]:
                    note = "" if random.random() < 0.07 else gaussian_note(base_mean)
                    grades.append((gid, sid2, cid, note, sem, ay))
                    gid += 1
    write_csv(os.path.join(RAW_DIR,"grades.csv"), grades,
              ["id","student_id","course_id","note","semestre","annee_universitaire"])

    # Teaching
    DEPT_BY_FIL = {
        1:"Informatique et Mathématiques", 2:"Informatique et Mathématiques",
        3:"Génie Électrique et Réseaux", 4:"Génie Industriel", 5:"Enseignements Généraux",
    }
    teaching = []
    assigned = set()
    for c in COURSES:
        dept = DEPT_BY_FIL[c[2]]
        pool = dept_teachers.get(dept,[])
        if not pool: continue
        t = random.choice(pool)
        key = (t, c[0])
        if key not in assigned:
            teaching.append((t, c[0], random.choice([15,18,21,24,28,30])))
            assigned.add(key)
    write_csv(os.path.join(RAW_DIR,"teaching.csv"), teaching,
              ["teacher_id","course_id","heures"])

    # Rooms
    room_types = [
        ("Amphithéâtre",300),("Amphithéâtre",250),("Amphithéâtre",200),
        ("Salle de Cours",60),("Salle de Cours",60),("Salle de Cours",45),
        ("Salle de Cours",45),("Salle de Cours",40),("Salle de Cours",40),
        ("Salle TP Informatique",30),("Salle TP Informatique",30),
        ("Salle TP Informatique",25),("Salle TP Électronique",25),
        ("Salle TP Industriel",20),("Salle TP Industriel",20),
        ("Bibliothèque",80),("Salle de Séminaire",50),("Salle de Séminaire",35),
        ("Labo Réseaux",20),("Labo IA & Big Data",25),
    ]
    rooms = [(i+1, f"Salle {i+1:02d}", cap, rtype) for i,(rtype,cap) in enumerate(room_types)]
    write_csv(os.path.join(RAW_DIR,"rooms.csv"), rooms,
              ["id","nom","capacite","type"])

    # Schedule
    HEURE_SLOTS = ["08:00","10:00","12:00","14:00","16:00","18:00"]
    schedule = []
    sc_id = 1
    for ay in ANNEES:
        yr = int(ay[:4])
        for week in range(1,21):
            base = date(yr,9,1) + timedelta(weeks=week-1)
            for cid in random.sample([c[0] for c in COURSES], 30):
                day_offset = random.randint(0,4)
                sd = base + timedelta(days=day_offset)
                rm = random.choice(rooms)
                schedule.append((sc_id, cid, rm[0], str(sd), random.choice(HEURE_SLOTS), ay))
                sc_id += 1
    write_csv(os.path.join(RAW_DIR,"schedule.csv"), schedule,
              ["id","course_id","room_id","date","heure","annee_universitaire"])

    # Finance
    finance = []
    fid = 1
    for ay in ANNEES:
        yr = int(ay[:4])
        for dept in DEPTS_FINANCE:
            base = BUDGET_BASE[dept]
            growth = 1 + (yr-2020)*0.03 + random.gauss(0,0.02)
            budget = round(base * growth, 2)
            exec_rate = random.uniform(0.72,0.98)
            dep = round(budget * exec_rate, 2)
            if random.random() < 0.02:
                dep = round(budget * random.uniform(1.01,1.08), 2)
            finance.append((fid, dept, ay, budget, dep, round(dep/budget*100, 2)))
            fid += 1
    write_csv(os.path.join(RAW_DIR,"finance.csv"), finance,
              ["id","departement","annee_universitaire","budget","depenses","taux_execution_pct"])

    # Enrollments
    enrollments = []
    eid = 1
    for s in students:
        sid3 = s[0]; annee_entree = s[8]; fil_id = s[6]
        for ay in ANNEES:
            yr = int(ay[:4])
            if yr < annee_entree: continue
            years_in = yr - annee_entree
            if years_in > 5: continue
            if years_in >= 5:
                statut = "diplômé"
            elif years_in >= 3 and random.random() < 0.06:
                statut = "abandonné"
            elif years_in >= 1 and random.random() < 0.03:
                statut = "abandonné"
            else:
                statut = "inscrit"
            if random.random() < 0.04: statut = ""
            enrollments.append((eid, sid3, ay, statut, fil_id, years_in+1))
            eid += 1
    write_csv(os.path.join(RAW_DIR,"enrollments.csv"), enrollments,
              ["id","student_id","annee_universitaire","statut","filiere_id","annee_cursus"])

    print(f"\n✅ Données générées dans {RAW_DIR}")
    return {
        "students": len(students), "grades": len(grades),
        "teachers": len(teachers), "enrollments": len(enrollments),
    }

if __name__ == "__main__":
    stats = generate_all()
    print("\nRésumé :", stats)
