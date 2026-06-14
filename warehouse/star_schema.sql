-- ===========================================================================
-- DATA WAREHOUSE ENSA KÉNITRA — Schéma en Étoile (Star Schema)
-- Architecture BI Sécurisée — Équipe : AFTYSS, ABDELMOUMEN, BENHADDANE
-- Année universitaire 2024-2025
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- 1. DIMENSIONS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_time (
    time_id          SERIAL PRIMARY KEY,
    annee_universitaire VARCHAR(10) NOT NULL,
    annee            INTEGER NOT NULL,
    semestre         INTEGER NOT NULL CHECK (semestre IN (1, 2)),
    periode          VARCHAR(20),  -- ex: "S1 2022-2023"
    UNIQUE (annee_universitaire, semestre)
);

CREATE TABLE IF NOT EXISTS dim_filiere (
    filiere_id       INTEGER PRIMARY KEY,
    nom              VARCHAR(50)  NOT NULL,
    description      TEXT,
    departement      VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS dim_student (
    student_id       INTEGER PRIMARY KEY,
    nom              VARCHAR(100) NOT NULL,
    prenom           VARCHAR(100) NOT NULL,
    sexe             CHAR(1),
    date_naissance   DATE,
    email            VARCHAR(150),
    filiere_id       INTEGER REFERENCES dim_filiere(filiere_id),
    annee_entree     INTEGER,
    ville_origine    VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_course (
    course_id        INTEGER PRIMARY KEY,
    nom              VARCHAR(200) NOT NULL,
    filiere_id       INTEGER REFERENCES dim_filiere(filiere_id),
    semestre_label   VARCHAR(5),
    credits          INTEGER
);

CREATE TABLE IF NOT EXISTS dim_teacher (
    teacher_id       INTEGER PRIMARY KEY,
    nom              VARCHAR(100) NOT NULL,
    prenom           VARCHAR(100) NOT NULL,
    departement      VARCHAR(150),
    grade            VARCHAR(100),
    salaire          NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS dim_room (
    room_id          INTEGER PRIMARY KEY,
    nom              VARCHAR(100),
    capacite         INTEGER,
    type             VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS dim_department (
    department_id    SERIAL PRIMARY KEY,
    nom              VARCHAR(150) NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------------
-- 2. TABLES DE FAITS
-- ---------------------------------------------------------------------------

-- FACT_GRADES : notes par étudiant × cours × période
CREATE TABLE IF NOT EXISTS fact_grades (
    grade_id         SERIAL PRIMARY KEY,
    student_id       INTEGER NOT NULL REFERENCES dim_student(student_id),
    course_id        INTEGER NOT NULL REFERENCES dim_course(course_id),
    time_id          INTEGER NOT NULL REFERENCES dim_time(time_id),
    note             NUMERIC(5, 2),
    note_status      VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN note IS NULL          THEN 'manquante'
            WHEN note >= 16            THEN 'très_bien'
            WHEN note >= 14            THEN 'bien'
            WHEN note >= 12            THEN 'assez_bien'
            WHEN note >= 10            THEN 'passable'
            ELSE                            'insuffisant'
        END
    ) STORED
);

-- FACT_ENROLLMENTS : inscriptions par étudiant × filière × période
CREATE TABLE IF NOT EXISTS fact_enrollments (
    enrollment_id    SERIAL PRIMARY KEY,
    student_id       INTEGER NOT NULL REFERENCES dim_student(student_id),
    filiere_id       INTEGER NOT NULL REFERENCES dim_filiere(filiere_id),
    time_id          INTEGER NOT NULL REFERENCES dim_time(time_id),
    statut           VARCHAR(20),
    annee_cursus     INTEGER,
    is_abandon       BOOLEAN GENERATED ALWAYS AS (statut = 'abandonné') STORED,
    is_diplome       BOOLEAN GENERATED ALWAYS AS (statut = 'diplômé')   STORED
);

-- FACT_FINANCE : budget et dépenses par département × période
CREATE TABLE IF NOT EXISTS fact_finance (
    finance_id       SERIAL PRIMARY KEY,
    department_id    INTEGER NOT NULL REFERENCES dim_department(department_id),
    time_id          INTEGER NOT NULL REFERENCES dim_time(time_id),
    budget           NUMERIC(14, 2),
    depenses         NUMERIC(14, 2),
    taux_execution   NUMERIC(6, 2),
    anomalie_budget  BOOLEAN DEFAULT FALSE
);

-- FACT_TEACHING : charge enseignants × cours × période
CREATE TABLE IF NOT EXISTS fact_teaching (
    teaching_id      SERIAL PRIMARY KEY,
    teacher_id       INTEGER NOT NULL REFERENCES dim_teacher(teacher_id),
    course_id        INTEGER NOT NULL REFERENCES dim_course(course_id),
    heures           INTEGER
);

-- FACT_SCHEDULE : occupation salles × cours × période
CREATE TABLE IF NOT EXISTS fact_schedule (
    schedule_id      SERIAL PRIMARY KEY,
    course_id        INTEGER NOT NULL REFERENCES dim_course(course_id),
    room_id          INTEGER NOT NULL REFERENCES dim_room(room_id),
    time_id          INTEGER NOT NULL REFERENCES dim_time(time_id),
    date_session     DATE,
    heure            VARCHAR(8)
);

-- ---------------------------------------------------------------------------
-- 3. INDEX ANALYTIQUES
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_fact_grades_student   ON fact_grades(student_id);
CREATE INDEX IF NOT EXISTS idx_fact_grades_course    ON fact_grades(course_id);
CREATE INDEX IF NOT EXISTS idx_fact_grades_time      ON fact_grades(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_grades_note      ON fact_grades(note);

CREATE INDEX IF NOT EXISTS idx_fact_enr_student      ON fact_enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_fact_enr_filiere      ON fact_enrollments(filiere_id);
CREATE INDEX IF NOT EXISTS idx_fact_enr_time         ON fact_enrollments(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_enr_statut       ON fact_enrollments(statut);

CREATE INDEX IF NOT EXISTS idx_fact_fin_dept         ON fact_finance(department_id);
CREATE INDEX IF NOT EXISTS idx_fact_fin_time         ON fact_finance(time_id);

CREATE INDEX IF NOT EXISTS idx_dim_student_filiere   ON dim_student(filiere_id);
CREATE INDEX IF NOT EXISTS idx_dim_course_filiere    ON dim_course(filiere_id);

-- ---------------------------------------------------------------------------
-- 4. VUES ANALYTIQUES (OLAP)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW olap_performance_par_filiere AS
SELECT
    df.nom                          AS filiere,
    dt.annee_universitaire,
    dt.semestre,
    COUNT(fg.grade_id)              AS nb_notes,
    ROUND(AVG(fg.note)::NUMERIC, 2) AS moyenne,
    ROUND(
        SUM(CASE WHEN fg.note >= 10 THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(fg.grade_id), 0) * 100, 2
    )                               AS taux_reussite_pct,
    ROUND(
        SUM(CASE WHEN fg.note < 10  THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(fg.grade_id), 0) * 100, 2
    )                               AS taux_echec_pct
FROM fact_grades        fg
JOIN dim_student        ds ON fg.student_id  = ds.student_id
JOIN dim_filiere        df ON ds.filiere_id  = df.filiere_id
JOIN dim_time           dt ON fg.time_id     = dt.time_id
WHERE fg.note IS NOT NULL
GROUP BY df.nom, dt.annee_universitaire, dt.semestre
ORDER BY dt.annee_universitaire, dt.semestre, df.nom;


CREATE OR REPLACE VIEW olap_inscriptions AS
SELECT
    df.nom                          AS filiere,
    dt.annee_universitaire,
    COUNT(fe.enrollment_id)         AS total,
    SUM(CASE WHEN fe.statut = 'inscrit'    THEN 1 ELSE 0 END) AS inscrits,
    SUM(CASE WHEN fe.statut = 'abandonné'  THEN 1 ELSE 0 END) AS abandonnes,
    SUM(CASE WHEN fe.statut = 'diplômé'    THEN 1 ELSE 0 END) AS diplomes,
    ROUND(SUM(fe.is_abandon::int)::NUMERIC / NULLIF(COUNT(*),0) * 100, 2) AS taux_abandon_pct,
    ROUND(SUM(fe.is_diplome::int)::NUMERIC / NULLIF(COUNT(*),0) * 100, 2) AS taux_diplome_pct
FROM fact_enrollments fe
JOIN dim_filiere      df ON fe.filiere_id = df.filiere_id
JOIN dim_time         dt ON fe.time_id    = dt.time_id
GROUP BY df.nom, dt.annee_universitaire
ORDER BY dt.annee_universitaire, df.nom;


CREATE OR REPLACE VIEW olap_budget_execution AS
SELECT
    dd.nom                          AS departement,
    dt.annee_universitaire,
    SUM(ff.budget)                  AS budget_total,
    SUM(ff.depenses)                AS depenses_total,
    ROUND(SUM(ff.depenses) / NULLIF(SUM(ff.budget), 0) * 100, 2) AS taux_execution_pct,
    SUM(CASE WHEN ff.anomalie_budget THEN 1 ELSE 0 END) AS nb_anomalies
FROM fact_finance    ff
JOIN dim_department  dd ON ff.department_id = dd.department_id
JOIN dim_time        dt ON ff.time_id       = dt.time_id
GROUP BY dd.nom, dt.annee_universitaire
ORDER BY dt.annee_universitaire, dd.nom;


CREATE OR REPLACE VIEW olap_charge_enseignants AS
SELECT
    dt_t.nom        AS departement,
    dt_t.prenom || ' ' || dt_t.nom AS enseignant,
    COUNT(ft.course_id)             AS nb_cours,
    SUM(ft.heures)                  AS total_heures,
    ROUND(AVG(ft.heures), 1)        AS moy_heures_par_cours
FROM fact_teaching ft
JOIN dim_teacher   dt_t ON ft.teacher_id = dt_t.teacher_id
GROUP BY dt_t.departement, dt_t.nom, dt_t.prenom
ORDER BY total_heures DESC;


CREATE OR REPLACE VIEW olap_occupation_salles AS
SELECT
    dr.nom                          AS salle,
    dr.type,
    dr.capacite,
    dt.annee_universitaire,
    COUNT(fs.schedule_id)           AS nb_sessions,
    ROUND(
        COUNT(fs.schedule_id)::NUMERIC
        / NULLIF(MAX(COUNT(fs.schedule_id)) OVER (PARTITION BY dt.annee_universitaire), 0) * 100,
    1)                              AS taux_occupation_relatif_pct
FROM fact_schedule  fs
JOIN dim_room       dr ON fs.room_id  = dr.room_id
JOIN dim_time       dt ON fs.time_id  = dt.time_id
GROUP BY dr.nom, dr.type, dr.capacite, dt.annee_universitaire
ORDER BY dt.annee_universitaire, nb_sessions DESC;
