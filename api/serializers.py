from rest_framework import serializers
from .models import Employe, Pointage, Conge, Rapport


class EmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Employe
        fields = [
            'idEmploye', 'nom', 'prenom', 'email',
            'telephone', 'poste', 'date_embauche', 'statut', 'is_admin'
        ]
        read_only_fields = ['idEmploye']


class EmployeCreateSerializer(serializers.ModelSerializer):
    """Utilisé pour créer un employé avec mot de passe."""
    mot_de_passe = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = Employe
        fields = [
            'nom', 'prenom', 'email', 'mot_de_passe',
            'telephone', 'poste', 'date_embauche', 'statut', 'is_admin'
        ]

    def create(self, validated_data):
        mot_de_passe = validated_data.pop('mot_de_passe')
        employe = Employe(**validated_data)
        employe.set_password(mot_de_passe)
        employe.save()
        return employe


class PointageSerializer(serializers.ModelSerializer):
    employe_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Pointage
        fields = [
            'idPointage', 'employe', 'employe_nom',
            'date', 'heure_entree', 'heure_sortie', 'heure_travaille'
        ]
        read_only_fields = ['idPointage', 'heure_travaille']

    def get_employe_nom(self, obj):
        return str(obj.employe)

    def create(self, validated_data):
        pointage = Pointage(**validated_data)
        pointage.calculer_heures()
        pointage.save()
        return pointage

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.calculer_heures()
        instance.save()
        return instance


class CongeSerializer(serializers.ModelSerializer):
    employe_nom  = serializers.SerializerMethodField()
    traite_par_nom = serializers.SerializerMethodField()

    class Meta:
        model  = Conge
        fields = [
            'idConge', 'employe', 'employe_nom',
            'typeConge', 'date_debut', 'date_fin',
            'motif', 'statut', 'traite_par', 'traite_par_nom'
        ]
        read_only_fields = ['idConge', 'statut', 'traite_par','employe']

    def get_employe_nom(self, obj):
        return str(obj.employe)

    def get_traite_par_nom(self, obj):
        return str(obj.traite_par) if obj.traite_par else None


class RapportSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Rapport
        fields = [
            'idRapport', 'TypeRapport', 'Date_generation',
            'periode', 'genere_par', 'donnees'
        ]
        read_only_fields = ['idRapport', 'Date_generation']