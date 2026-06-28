from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings

# ─── Manager personnalisé pour Employe ────────────────────────────────────────

class EmployeManager(BaseUserManager):
    def create_user(self, email, nom, prenom, mot_de_passe, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, nom=nom, prenom=prenom, **extra_fields)
        user.set_password(mot_de_passe)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, prenom, mot_de_passe, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        return self.create_user(email, nom, prenom, mot_de_passe, **extra_fields)

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
# ─── Employe (utilisateur de base) ────────────────────────────────────────────

class Employe(AbstractBaseUser):
    """
    Correspond à la classe Employe du diagramme.
    Sert aussi de base pour l'Administrateur RH via le flag is_admin.
    """
    idEmploye   = models.AutoField(primary_key=True)
    nom         = models.CharField(max_length=100)
    prenom      = models.CharField(max_length=100)
    email       = models.EmailField(unique=True)
    telephone   = models.CharField(max_length=20, blank=True)
    poste       = models.CharField(max_length=100, blank=True)
    genre = models.CharField(
        max_length=10,
        choices=[
            ('M', 'Masculin'),
            ('F', 'Féminin')
        ],
        blank=True
    )

    date_naissance = models.DateField(null=True, blank=True)

    departement = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )   
    date_embauche = models.DateField(null=True, blank=True)
    statut      = models.CharField(max_length=50, default='actif')
    is_admin    = models.BooleanField(default=False)   # True → Administrateur RH

    objects = EmployeManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']

    # Champs requis par Django pour l'interface admin
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    class Meta:
        db_table = 'employe'
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'


# ─── Pointage ─────────────────────────────────────────────────────────────────

class Pointage(models.Model):
    """
    Classe Pointage du diagramme.
    Un employé peut avoir plusieurs pointages (relation 1..* ↔ 0..*).
    """
    idPointage     = models.AutoField(primary_key=True)
    employe        = models.ForeignKey(
        Employe, on_delete=models.CASCADE,
        related_name='pointages', db_column='idEmploye'
    )
    date           = models.DateField()
    heure_entree = models.TimeField(null=True, blank=True)
    debut_pause = models.TimeField(null=True, blank=True)
    retour_pause = models.TimeField(null=True, blank=True)
    heure_sortie = models.TimeField(null=True, blank=True)

    heure_travaille = models.FloatField(default=0.0)

    def calculer_heures(self):
        """Calcule automatiquement les heures travaillées."""
        if self.heure_entree and self.heure_sortie:
            from datetime import datetime, date
            debut = datetime.combine(date.today(), self.heure_entree)
            fin   = datetime.combine(date.today(), self.heure_sortie)
            delta = fin - debut
            self.heure_travaille = round(delta.seconds / 3600, 2)
        return self.heure_travaille

    def verifier_retard(self, heure_normale_debut='08:30'):
        """Retourne True si l'employé est arrivé en retard."""
        from datetime import time
        h, m = map(int, heure_normale_debut.split(':'))
        heure_ref = time(h, m)
        return self.heure_entree > heure_ref if self.heure_entree else False
    
    def get_status(self):
        if not self.heure_entree:
            return "absent"
        if self.verifier_retard():
            return "late"
        return "present"

    def __str__(self):
        return f"Pointage {self.employe} - {self.date}"

    class Meta:
        db_table = 'pointage'
        unique_together = ('employe', 'date')


# ─── Conge ────────────────────────────────────────────────────────────────────

class Conge(models.Model):
    """
    Classe Conge du diagramme.
    Un employé fait des demandes, l'admin valide ou refuse.
    """
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide',     'Validé'),
        ('refuse',     'Refusé'),
        ('annule',     'Annulé'),
    ]

    idConge      = models.AutoField(primary_key=True)
    employe      = models.ForeignKey(
        Employe, on_delete=models.CASCADE,
        related_name='conges', db_column='idEmploye'
    )
    typeConge = models.ForeignKey('LeaveType', on_delete=models.CASCADE, related_name='conges')  
    date_debut   = models.DateField()
    date_fin     = models.DateField()
    motif        = models.TextField(blank=True)
    statut       = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    traite_par   = models.ForeignKey(
        Employe, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conges_traites', db_column='idAdmin'
    )

    def __str__(self):
        return f"Congé {self.employe} ({self.typeConge}) - {self.statut}"

    class Meta:
        db_table = 'conge'
        verbose_name = 'Congé'
        verbose_name_plural = 'Congés'


# ─── Rapport ──────────────────────────────────────────────────────────────────

class Rapport(models.Model):
    """
    Classe Rapport du diagramme.
    Généré par l'Administrateur RH (relation consulte 1..0..*).
    """
    TYPE_CHOICES = [
        ('journalier', 'Rapport journalier'),
        ('mensuel',    'Rapport mensuel'),
        ('conge',      'Rapport congés'),
    ]

    idRapport        = models.AutoField(primary_key=True)
    TypeRapport      = models.CharField(max_length=50, choices=TYPE_CHOICES)
    Date_generation  = models.DateField(auto_now_add=True)
    periode          = models.CharField(max_length=100, blank=True)
    genere_par       = models.ForeignKey(
        Employe, on_delete=models.SET_NULL, null=True,
        related_name='rapports', db_column='idAdmin'
    )
    # Données du rapport stockées en JSON (flexible)
    donnees          = models.JSONField(default=dict, blank=True)
class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    max_days = models.IntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    




class Avertissement(models.Model):
    MOTIF_CHOICES = [
        ('absence_injustifiee', 'Absence injustifiée'),
        ('retard_repete',       'Retard répété'),
        ('retard_ponctuel',     'Retard ponctuel'),
        ('autre',               'Autre'),
    ]
    JUSTIF_STATUT_CHOICES = [
    ('en_attente', 'En attente'),
    ('acceptee',   'Acceptée'),
    ('refusee',    'Refusée'),
]
    employee    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avertissements')
    envoye_par  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='avertissements_envoyes')
    motif       = models.CharField(max_length=50, choices=MOTIF_CHOICES)
    message     = models.TextField()
    date_envoi  = models.DateTimeField(auto_now_add=True)
    lu          = models.BooleanField(default=False)  # pour marquer comme lu
    justification_message = models.TextField(blank=True, null=True)
    justification_document = models.FileField(upload_to='justifications/', blank=True, null=True)
    justification_date = models.DateTimeField(null=True, blank=True)
    justification_statut = models.CharField(max_length=20, choices=JUSTIF_STATUT_CHOICES, null=True, blank=True)
    justification_refus_motif = models.TextField(blank=True, null=True)  # motif du refus

    class Meta:
        ordering = ['-date_envoi']

    def __str__(self):
        return f"Avertissement → {self.employee} ({self.motif})"