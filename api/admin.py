from django.contrib import admin
from .models import Employe, Pointage, Conge, Rapport


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display  = ('email', 'nom', 'prenom', 'poste', 'statut', 'is_admin')
    list_filter   = ('is_admin', 'statut')
    search_fields = ('email', 'nom', 'prenom')
    ordering      = ('nom',)
    fields        = ('email', 'nom', 'prenom', 'telephone', 'poste', 'date_embauche', 'statut', 'is_admin', 'is_active', 'password')


@admin.register(Pointage)
class PointageAdmin(admin.ModelAdmin):
    list_display  = ('employe', 'date', 'heure_entree', 'heure_sortie', 'heure_travaille')
    list_filter   = ('date',)
    search_fields = ('employe__nom', 'employe__prenom')
    date_hierarchy = 'date'


@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display  = ('employe', 'typeConge', 'date_debut', 'date_fin', 'statut', 'traite_par')
    list_filter   = ('statut', 'typeConge')
    search_fields = ('employe__nom', 'employe__prenom')


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display  = ('TypeRapport', 'Date_generation', 'periode', 'genere_par')
    list_filter   = ('TypeRapport',)