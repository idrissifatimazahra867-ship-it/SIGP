import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigp_backend.settings')
django.setup()

from api.models import Employe, Department, LeaveType, Pointage, Conge, Avertissement
from datetime import date, time, timedelta

# ── 1. Départements ──
print("Création des départements...")
dept_info, _      = Department.objects.get_or_create(name="Informatique")
dept_rh, _        = Department.objects.get_or_create(name="Ressources Humaines")
dept_compta, _    = Department.objects.get_or_create(name="Comptabilité")
dept_marketing, _ = Department.objects.get_or_create(name="Marketing")
dept_direction, _ = Department.objects.get_or_create(name="Direction")
dept_finance, _   = Department.objects.get_or_create(name="Finance")
dept_logistique, _= Department.objects.get_or_create(name="Logistique")

# ── 2. Types de congés ──
print("Création des types de congés...")
LeaveType.objects.get_or_create(name="Congé Annuel",       defaults={"max_days": 30, "is_paid": True,  "requires_document": False, "is_active": True})
LeaveType.objects.get_or_create(name="Maladie",            defaults={"max_days": 15, "is_paid": True,  "requires_document": True,  "is_active": True})
LeaveType.objects.get_or_create(name="Maternité",          defaults={"max_days": 90, "is_paid": True,  "requires_document": True,  "is_active": True})
LeaveType.objects.get_or_create(name="Sans Solde",         defaults={"max_days": 30, "is_paid": False, "requires_document": False, "is_active": True})
LeaveType.objects.get_or_create(name="Événement Familial", defaults={"max_days": 5,  "is_paid": True,  "requires_document": False, "is_active": True})



# ── 4. Employés ──
print("Création des employés...")

employes = [
    # ADMIN
    {
        "email": "admin@sigp.ma",
        "nom": "Benali",
        "prenom": "Youssef",
        "mot_de_passe": "admin1234",
        "telephone": "0661234567",
        "poste": "Directeur RH",
        "genre": "M",
        "date_naissance": date(1980, 5, 15),
        "date_embauche": date(2015, 1, 10),
        "departement": dept_direction,
        "is_admin": True,
        "statut": "actif",
    },
    # INFORMATIQUE
    {
        "email": "omar.filali@sigp.ma",
        "nom": "Filali",
        "prenom": "Omar",
        "mot_de_passe": "employe1234",
        "telephone": "0663456789",
        "poste": "Développeur Frontend",
        "genre": "M",
        "date_naissance": date(1997, 7, 10),
        "date_embauche": date(2022, 9, 1),
        "departement": dept_info,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "karim.mansouri@sigp.ma",
        "nom": "Mansouri",
        "prenom": "Karim",
        "mot_de_passe": "employe1234",
        "telephone": "0667890123",
        "poste": "Chef de Projet",
        "genre": "M",
        "date_naissance": date(1988, 4, 3),
        "date_embauche": date(2019, 5, 20),
        "departement": dept_info,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "yasmine.alaoui@sigp.ma",
        "nom": "Alaoui",
        "prenom": "Yasmine",
        "mot_de_passe": "employe1234",
        "telephone": "0661112233",
        "poste": "Développeuse Mobile",
        "genre": "F",
        "date_naissance": date(1999, 2, 18),
        "date_embauche": date(2023, 3, 1),
        "departement": dept_info,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "mehdi.rahimi@sigp.ma",
        "nom": "Rahimi",
        "prenom": "Mehdi",
        "mot_de_passe": "employe1234",
        "telephone": "0662223344",
        "poste": "Administrateur Système",
        "genre": "M",
        "date_naissance": date(1991, 9, 25),
        "date_embauche": date(2018, 7, 15),
        "departement": dept_info,
        "is_admin": False,
        "statut": "actif",
    },
    # RESSOURCES HUMAINES
    {
        "email": "salma.idrissi@sigp.ma",
        "nom": "Idrissi",
        "prenom": "Salma",
        "mot_de_passe": "employe1234",
        "telephone": "0664567890",
        "poste": "Responsable RH",
        "genre": "F",
        "date_naissance": date(1990, 11, 5),
        "date_embauche": date(2018, 3, 15),
        "departement": dept_rh,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "fatima.ouali@sigp.ma",
        "nom": "Ouali",
        "prenom": "Fatima",
        "mot_de_passe": "employe1234",
        "telephone": "0660123456",
        "poste": "Assistante RH",
        "genre": "F",
        "date_naissance": date(1996, 1, 14),
        "date_embauche": date(2023, 2, 1),
        "departement": dept_rh,
        "is_admin": False,
        "statut": "actif",
    },
    # COMPTABILITÉ
    {
        "email": "amine.cherkaoui@sigp.ma",
        "nom": "Cherkaoui",
        "prenom": "Amine",
        "mot_de_passe": "employe1234",
        "telephone": "0665678901",
        "poste": "Comptable Senior",
        "genre": "M",
        "date_naissance": date(1985, 2, 28),
        "date_embauche": date(2016, 6, 1),
        "departement": dept_compta,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "hiba.lahlou@sigp.ma",
        "nom": "Lahlou",
        "prenom": "Hiba",
        "mot_de_passe": "employe1234",
        "telephone": "0668901234",
        "poste": "Assistante Comptable",
        "genre": "F",
        "date_naissance": date(1995, 12, 9),
        "date_embauche": date(2021, 10, 1),
        "departement": dept_compta,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "rachid.benomar@sigp.ma",
        "nom": "Benomar",
        "prenom": "Rachid",
        "mot_de_passe": "employe1234",
        "telephone": "0663334455",
        "poste": "Auditeur Interne",
        "genre": "M",
        "date_naissance": date(1983, 6, 12),
        "date_embauche": date(2014, 4, 10),
        "departement": dept_compta,
        "is_admin": False,
        "statut": "actif",
    },
    # MARKETING
    {
        "email": "nadia.tazi@sigp.ma",
        "nom": "Tazi",
        "prenom": "Nadia",
        "mot_de_passe": "employe1234",
        "telephone": "0666789012",
        "poste": "Chargée de Communication",
        "genre": "F",
        "date_naissance": date(1993, 8, 17),
        "date_embauche": date(2020, 1, 15),
        "departement": dept_marketing,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "tariq.benjelloun@sigp.ma",
        "nom": "Benjelloun",
        "prenom": "Tariq",
        "mot_de_passe": "employe1234",
        "telephone": "0669012345",
        "poste": "Responsable Marketing",
        "genre": "M",
        "date_naissance": date(1987, 6, 25),
        "date_embauche": date(2017, 9, 10),
        "departement": dept_marketing,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "sara.kettani@sigp.ma",
        "nom": "Kettani",
        "prenom": "Sara",
        "mot_de_passe": "employe1234",
        "telephone": "0664445566",
        "poste": "Graphiste",
        "genre": "F",
        "date_naissance": date(1994, 3, 30),
        "date_embauche": date(2021, 6, 1),
        "departement": dept_marketing,
        "is_admin": False,
        "statut": "actif",
    },
    # FINANCE
    {
        "email": "adam.sqalli@sigp.ma",
        "nom": "Sqalli",
        "prenom": "Adam",
        "mot_de_passe": "employe1234",
        "telephone": "0665556677",
        "poste": "Analyste Financier",
        "genre": "M",
        "date_naissance": date(1989, 10, 8),
        "date_embauche": date(2017, 2, 20),
        "departement": dept_finance,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "rania.fassi@sigp.ma",
        "nom": "Fassi",
        "prenom": "Rania",
        "mot_de_passe": "employe1234",
        "telephone": "0666667788",
        "poste": "Contrôleuse de Gestion",
        "genre": "F",
        "date_naissance": date(1992, 7, 22),
        "date_embauche": date(2019, 11, 5),
        "departement": dept_finance,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "hamza.ziani@sigp.ma",
        "nom": "Ziani",
        "prenom": "Hamza",
        "mot_de_passe": "employe1234",
        "telephone": "0667778899",
        "poste": "Trésorier",
        "genre": "M",
        "date_naissance": date(1986, 4, 15),
        "date_embauche": date(2015, 8, 1),
        "departement": dept_finance,
        "is_admin": False,
        "statut": "actif",
    },
    # LOGISTIQUE
    {
        "email": "imane.berrada@sigp.ma",
        "nom": "Berrada",
        "prenom": "Imane",
        "mot_de_passe": "employe1234",
        "telephone": "0668889900",
        "poste": "Responsable Logistique",
        "genre": "F",
        "date_naissance": date(1988, 11, 3),
        "date_embauche": date(2016, 3, 15),
        "departement": dept_logistique,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "yassir.amrani@sigp.ma",
        "nom": "Amrani",
        "prenom": "Yassir",
        "mot_de_passe": "employe1234",
        "telephone": "0669990011",
        "poste": "Agent Logistique",
        "genre": "M",
        "date_naissance": date(1995, 5, 20),
        "date_embauche": date(2022, 1, 10),
        "departement": dept_logistique,
        "is_admin": False,
        "statut": "actif",
    },
    {
        "email": "loubna.tahiri@sigp.ma",
        "nom": "Tahiri",
        "prenom": "Loubna",
        "mot_de_passe": "employe1234",
        "telephone": "0660001122",
        "poste": "Coordinatrice Supply Chain",
        "genre": "F",
        "date_naissance": date(1991, 8, 14),
        "date_embauche": date(2018, 9, 1),
        "departement": dept_logistique,
        "is_admin": False,
        "statut": "actif",
    },
    # DIRECTION
    {
        "email": "khalid.naciri@sigp.ma",
        "nom": "Naciri",
        "prenom": "Khalid",
        "mot_de_passe": "employe1234",
        "telephone": "0661112233",
        "poste": "Directeur Général Adjoint",
        "genre": "M",
        "date_naissance": date(1975, 3, 10),
        "date_embauche": date(2010, 6, 1),
        "departement": dept_direction,
        "is_admin": False,
        "statut": "actif",
    },
]

created_employees = []

for data in employes:
    if not Employe.objects.filter(email=data["email"]).exists():
        emp = Employe.objects.create_user(
            email=data["email"],
            nom=data["nom"],
            prenom=data["prenom"],
            mot_de_passe=data["mot_de_passe"],
            telephone=data["telephone"],
            poste=data["poste"],
            genre=data["genre"],
            date_naissance=data["date_naissance"],
            date_embauche=data["date_embauche"],
            departement=data["departement"],
            is_admin=data["is_admin"],
            statut=data["statut"],
        )
        role = "ADMIN" if emp.is_admin else "Employé"
        print(f"  ✅ [{role}] {emp.prenom} {emp.nom} — {emp.poste}")
        created_employees.append(emp)
    else:
        print(f"  ⚠️  {data['email']} existe déjà, ignoré")
        created_employees.append(Employe.objects.get(email=data["email"]))

print("\n✅ Seed terminé !")
print(f"   7 départements | 5 types de congés | 1 planning | {len(employes)} employés")
print("\n🔑 Admin   : admin@sigp.ma / admin1234")
print("🔑 Employé : omar.filali@sigp.ma / employe1234")