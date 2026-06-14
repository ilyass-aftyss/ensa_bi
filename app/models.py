"""
SQLAlchemy ORM models — source tables (OLTP layer).
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Filiere(Base):
    __tablename__ = "filieres"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    students = relationship("Student", back_populates="filiere")


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    sexe = Column(String(1))
    date_naissance = Column(Date)
    email = Column(String(150), unique=True)
    filiere_id = Column(Integer, ForeignKey("filieres.id"))
    annee_cursus = Column(Integer)
    annee_entree = Column(Integer)
    ville_origine = Column(String(100))
    filiere = relationship("Filiere", back_populates="students")
    grades = relationship("Grade", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    filiere_id = Column(Integer, ForeignKey("filieres.id"))
    semestre = Column(String(5))
    credits = Column(Integer)
    grades = relationship("Grade", back_populates="course")
    teachings = relationship("Teaching", back_populates="course")


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    sexe = Column(String(1))
    departement = Column(String(150))
    grade = Column(String(100))
    salaire = Column(Numeric(10, 2))
    teachings = relationship("Teaching", back_populates="teacher")


class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    note = Column(Float)
    semestre = Column(Integer)
    annee_universitaire = Column(String(10))
    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")


class Teaching(Base):
    __tablename__ = "teaching"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    heures = Column(Integer)
    teacher = relationship("Teacher", back_populates="teachings")
    course = relationship("Course", back_populates="teachings")


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100))
    capacite = Column(Integer)
    type = Column(String(80))
    schedules = relationship("Schedule", back_populates="room")


class Schedule(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    date = Column(Date)
    heure = Column(String(8))
    annee_universitaire = Column(String(10))
    room = relationship("Room", back_populates="schedules")


class Finance(Base):
    __tablename__ = "finance"
    id = Column(Integer, primary_key=True, index=True)
    departement = Column(String(150))
    annee_universitaire = Column(String(10))
    budget = Column(Numeric(14, 2))
    depenses = Column(Numeric(14, 2))
    taux_execution_pct = Column(Float)
    anomalie_budget = Column(String(5), nullable=True)


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    annee_universitaire = Column(String(10))
    statut = Column(String(20))
    filiere_id = Column(Integer, ForeignKey("filieres.id"))
    annee_cursus = Column(Integer)
    student = relationship("Student", back_populates="enrollments")
