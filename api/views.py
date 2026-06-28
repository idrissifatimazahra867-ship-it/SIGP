from datetime import date
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.db.models import Count
from datetime import date, time
from django.contrib import messages
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect


from datetime import date
from .models import Employe, Pointage, Conge, Rapport, Department, LeaveType,Avertissement
from .serializers import (
    EmployeSerializer, EmployeCreateSerializer,
    PointageSerializer, CongeSerializer, RapportSerializer
)
from .permissions import IsAdminRH




from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_POST
def envoyer_avertissement(request):
    data        = json.loads(request.body)
    employee_id = data.get('employee_id')
    motif       = data.get('motif')
    message     = data.get('message')

    try:
        employe = Employe.objects.get(idEmploye=employee_id)  # ← idEmploye au lieu de id
        Avertissement.objects.create(
            employee=employe,
            envoye_par=request.user,
            motif=motif,
            message=message
        )
        return JsonResponse({'status': 'ok'})
    except Employe.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Employé introuvable'}, status=404)
def soumettre_justification(request):
    avert_id = request.POST.get('avertissement_id')
    message  = request.POST.get('message', '')
    document = request.FILES.get('document')

    try:
        avert = Avertissement.objects.get(id=avert_id, employee=request.user)
        avert.justification_message = message
        if document:
            avert.justification_document = document
        avert.justification_date = timezone.now()
        avert.save()
        return JsonResponse({'status': 'ok'})
    except Avertissement.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
    


def traiter_justification(request):
    data = json.loads(request.body)
    avert_id = data.get('avert_id')
    action   = data.get('action')  # 'accepter' ou 'refuser'
    motif    = data.get('motif', '')

    try:
        avert = Avertissement.objects.get(id=avert_id)
        if action == 'accepter':
            avert.justification_statut = 'acceptee'
            avert.justification_refus_motif = None
        elif action == 'refuser':
            avert.justification_statut = 'refusee'
            avert.justification_refus_motif = motif
            # Remettre la justification à zéro pour que l'employé puisse renvoyer
            avert.justification_message  = None
            avert.justification_document = None
            avert.justification_date     = None
        avert.save()
        return JsonResponse({'status': 'ok'})
    except Avertissement.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)
# ─── JWT Login personnalisé ────────────────────────────────────────────────────

class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email']    = user.email
        token['nom']      = user.nom
        token['prenom']   = user.prenom
        token['is_admin'] = user.is_admin
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['employe'] = {
            'id':       self.user.idEmploye,
            'nom':      self.user.nom,
            'prenom':   self.user.prenom,
            'email':    self.user.email,
            'is_admin': self.user.is_admin,
        }
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class   = CustomTokenSerializer


# ─── Vue Login HTML (formulaire → session Django) ─────────────────────────────

class LoginHTMLView(View):
    """
    Gère la page de connexion HTML.
    GET  → affiche login.html
    POST → appelle l'API JWT, stocke les tokens en session, redirige
    """

    def get(self, request):
        # Si déjà connecté, rediriger directement
        if request.session.get('access_token'):
            user = request.session.get('user', {})
            if user.get('is_admin'):
                return redirect('/dashboard/')
            return redirect('/dashboard/employee/')
        return render(request, 'login.html')

    def post(self, request):
        import requests as http_requests

        email    = request.POST.get('username')   # champ name="username" dans le HTML
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Veuillez remplir tous les champs.')
            return render(request, 'login.html')

        try:
            response = http_requests.post(
                request.build_absolute_uri('/api/token/'),
                json={'email': email, 'password': password},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                # ── Stocker les tokens et infos user en session ──
                request.session['access_token']  = data['access']
                request.session['refresh_token'] = data['refresh']
                request.session['user']          = data['employe']

                # ── Redirection selon le rôle ──
                if data['employe']['is_admin']:
                    return redirect('/dashboard/')
                else:
                    return redirect('/dashboard/employee/')

            elif response.status_code == 401:
                messages.error(request, 'Email ou mot de passe incorrect.')
            else:
                messages.error(request, 'Erreur lors de la connexion. Réessayez.')

        except Exception as e:
            messages.error(request, 'Impossible de joindre le serveur. Vérifiez votre connexion.')

        return render(request, 'login.html')


# ─── Vue Déconnexion ──────────────────────────────────────────────────────────

class LogoutView(View):
    """
    Supprime la session et redirige vers la page de login.
    Appel : GET /logout/
    """
    def get(self, request):
        request.session.flush()
        return redirect('/')

def admin_dashboard(request):

    total_employes = Employe.objects.count()

    presents = Pointage.objects.filter(
        date=date.today(),
        heure_entree__isnull=False
    ).count()

    conges_attente = Conge.objects.filter(
        statut='en_attente'
    ).count()

    retards = 0
    pointages_jour = Pointage.objects.filter(date=date.today())

    for p in pointages_jour:
        if p.verifier_retard():
            retards += 1

    context = {
        'total_employes': total_employes,
        'presents': presents,
        'conges_attente': conges_attente,
        'retards': retards,
        'pointages_jour': pointages_jour[:5],
        'conges': Conge.objects.select_related('employe')[:5]
    }

    return render(
        request,
        'dashboard/admin_dashboard.html',
        context
    )

# ─── Employe ViewSet ──────────────────────────────────────────────────────────

class EmployeViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les employés.
    Seul l'admin RH peut créer / modifier / supprimer.
    Un employé peut voir et modifier son propre profil.
    """
    queryset         = Employe.objects.filter(is_active=True)
    serializer_class = EmployeSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeCreateSerializer
        return EmployeSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminRH()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if not self.request.user.is_admin:
            return Employe.objects.filter(pk=self.request.user.pk)
        return Employe.objects.filter(is_active=True)

    @action(detail=False, methods=['get'], url_path='me')
    def mon_profil(self, request):
        """GET /api/employes/me/ → profil de l'utilisateur connecté."""
        serializer = EmployeSerializer(request.user)
        return Response(serializer.data)

def employees_list(request):
    employees = Employe.objects.all()
    departments = Department.objects.all()

    departments_count = Department.objects.count()
    actifs = Employe.objects.filter(statut='actif').count()
    inactifs = Employe.objects.exclude(statut='actif').count()

    dept = request.GET.get("departement")
    statut = request.GET.get("statut")

    if dept:
        employees = employees.filter(departement_id=dept)

    if statut:
        employees = employees.filter(statut=statut)

    return render(request, 'employees/list.html', {
        'employees': employees,
        'departments': departments,
        'departments_count': departments_count,
        'actifs': actifs,
        'inactifs': inactifs,
        'selected_dept': dept,
        'selected_statut': statut,
    })

def add_employee(request):

    if request.method == "POST":

        departement = Department.objects.get(
            id=request.POST.get("departement")
        )

        Employe.objects.create_user(
            email=request.POST.get("email"),
            nom=request.POST.get("nom"),
            prenom=request.POST.get("prenom"),
            mot_de_passe=request.POST.get("mot_de_passe"),
            telephone=request.POST.get("telephone"),
            poste=request.POST.get("poste"),
            genre=request.POST.get("genre"),
            date_naissance=request.POST.get("date_naissance"),
            departement=departement,
            date_embauche=request.POST.get("date_embauche"),
            statut=request.POST.get("statut")
        )

        return redirect('/employees/')

    departements = Department.objects.all()
    return render(
        request,
        'employees/add.html',
        {'departments': Department.objects.all()}  # ← departments sans e
)

def edit_employee(request, id):

    employee = get_object_or_404(Employe, idEmploye=id)

    if request.method == "POST":
        employee.prenom = request.POST.get("prenom")
        employee.nom = request.POST.get("nom")
        employee.email = request.POST.get("email")
        employee.telephone = request.POST.get("telephone")
        employee.genre = request.POST.get("genre")
        employee.date_naissance = request.POST.get("date_naissance")
        employee.departement_id = request.POST.get("departement")
        employee.date_embauche = request.POST.get("date_embauche")
        employee.poste = request.POST.get("poste")
        employee.statut = request.POST.get("statut")

        # ── Mot de passe — uniquement si rempli ──
        nouveau_mdp = request.POST.get("mot_de_passe")
        if nouveau_mdp:
            employee.set_password(nouveau_mdp)

        employee.save()
        return redirect('employees-list')

    return render(request, 'employees/edit.html', {
        'departments': Department.objects.all(),
        'employee': employee
    })

# ─── Pointage ViewSet ─────────────────────────────────────────────────────────

class PointageViewSet(viewsets.ModelViewSet):
    serializer_class   = PointageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            qs = Pointage.objects.select_related('employe').all()
            employe_id = self.request.query_params.get('employe')
            date_param = self.request.query_params.get('date')
            if employe_id:
                qs = qs.filter(employe_id=employe_id)
            if date_param:
                qs = qs.filter(date=date_param)
            return qs
        return Pointage.objects.filter(employe=self.request.user)

    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            serializer.save(employe=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['post'], url_path='entree')
    def pointer_entree(self, request):
        """POST /api/pointages/entree/ → enregistre l'heure d'arrivée."""
        from datetime import datetime
        aujourd_hui = date.today()
        pointage, created = Pointage.objects.get_or_create(
            employe=request.user, date=aujourd_hui,
            defaults={'heure_entree': datetime.now().time()}
        )
        if not created and pointage.heure_entree:
            return Response(
                {'detail': "Entrée déjà enregistrée aujourd'hui."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not created:
            pointage.heure_entree = datetime.now().time()
            pointage.save()
        return Response(PointageSerializer(pointage).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='sortie')
    def pointer_sortie(self, request):
        """POST /api/pointages/sortie/ → enregistre l'heure de départ."""
        from datetime import datetime
        try:
            pointage = Pointage.objects.get(employe=request.user, date=date.today())
        except Pointage.DoesNotExist:
            return Response(
                {'detail': "Aucune entrée enregistrée aujourd'hui."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if pointage.heure_sortie:
            return Response(
                {'detail': 'Sortie déjà enregistrée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        pointage.heure_sortie = datetime.now().time()
        pointage.calculer_heures()
        pointage.save()
        return Response(PointageSerializer(pointage).data)

    @action(detail=False, methods=['get'], url_path='historique')
    def historique(self, request):
        """GET /api/pointages/historique/ → historique des pointages."""
        qs = self.get_queryset()
        return Response(PointageSerializer(qs, many=True).data)


def pointage_home(request):
    today = date.today()

    date_filter = request.GET.get("date")
    dept_filter = request.GET.get("departement")
    statut_filter = request.GET.get("statut")
    search = request.GET.get("search")
    selected_date = date_filter if date_filter else str(today)


    # IDs employés en congé aujourd'hui (pour le statut dans le tableau)
    employes_en_conge = set(
        Conge.objects.filter(
            statut='valide',
            date_debut__lte=today,
            date_fin__gte=today
        ).values_list('employe_id', flat=True)
    )

    # Compteur : tous les congés validés sans condition de date
    conges_count = Conge.objects.filter(statut='valide').count()

    # POINTAGES
    pointages = Pointage.objects.filter(
        date=date_filter if date_filter else today
    )

    pointage_map = {p.employe_id: p for p in pointages}

    # EMPLOYES
    employees = Employe.objects.all()

    # FILTRE DEPARTEMENT
    if dept_filter:
        employees = employees.filter(departement_id=dept_filter)

    data = []
    present_count = 0
    absent_count = 0
    late_count = 0

    for emp in employees:

        # SEARCH
        if search:
            full_name = f"{emp.prenom} {emp.nom}".lower()
            if search.lower() not in full_name:
                continue

        p = pointage_map.get(emp.idEmploye)

        # STATUS — congé en priorité
        if emp.idEmploye in employes_en_conge:
            status = "leave"
        elif p and p.heure_entree:
            if p.verifier_retard():
                status = "late"
            else:
                status = "present"
        else:
            status = "absent"

        # FILTRE STATUT
        if statut_filter and statut_filter != status:
            continue

        # COUNTING
        if status == "present":
            present_count += 1
        elif status == "absent":
            absent_count += 1
        elif status == "late":
            late_count += 1

        data.append({
            "employee": emp,
            "pointage": p,
            "status": status
        })

    context = {
        "data": data,
        "today": selected_date,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "conges_count": conges_count,
        "departments": Department.objects.all(),
        "selected_dept": dept_filter,
        "selected_status": statut_filter,
    }

    return render(request, "pointage/home.html", context)
# ─── Conge ViewSet ────────────────────────────────────────────────────────────

class CongeViewSet(viewsets.ModelViewSet):
    serializer_class   = CongeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            qs = Conge.objects.select_related('employe', 'traite_par').all()
            statut = self.request.query_params.get('statut')
            if statut:
                qs = qs.filter(statut=statut)
            return qs
        return Conge.objects.filter(employe=self.request.user)

    def perform_create(self, serializer):
        serializer.save(employe=self.request.user, statut='en_attente')

    def update(self, request, *args, **kwargs):
        conge = self.get_object()
        if not request.user.is_admin:
            if conge.employe != request.user or conge.statut != 'en_attente':
                return Response(
                    {'detail': 'Modification impossible.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='valider', permission_classes=[IsAdminRH])
    def valider(self, request, pk=None):
        conge = self.get_object()
        conge.statut = 'valide'
        conge.traite_par = request.user
        conge.save()
        return Response(CongeSerializer(conge).data)

    @action(detail=True, methods=['post'], url_path='refuser', permission_classes=[IsAdminRH])
    def refuser(self, request, pk=None):
        conge = self.get_object()
        conge.statut = 'refuse'
        conge.traite_par = request.user
        conge.save()
        return Response(CongeSerializer(conge).data)

    @action(detail=True, methods=['post'], url_path='annuler')
    def annuler(self, request, pk=None):
        conge = self.get_object()
        if not request.user.is_admin and conge.employe != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if conge.statut != 'en_attente':
            return Response(
                {'detail': 'Seules les demandes en attente peuvent être annulées.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        conge.statut = 'annule'
        conge.save()
        return Response(CongeSerializer(conge).data)


def conges_home(request):

    type_filter = request.GET.get("type")
    statut_filter = request.GET.get("statut")
    search = request.GET.get("search")

    conges = Conge.objects.all()

    # 🔹 filtre type
    if type_filter:
        conges = conges.filter(typeConge__id=type_filter)  # ← corrigé

    # 🔹 filtre statut
    if statut_filter:
        conges = conges.filter(statut=statut_filter)

    # 🔹 recherche
    if search:
        conges = conges.filter(
            Q(employe__nom__icontains=search) |
            Q(employe__prenom__icontains=search) |
            Q(motif__icontains=search)
        )

    # 🔹 stats
    attente_count = Conge.objects.filter(statut="en_attente").count()
    valide_count = Conge.objects.filter(statut="valide").count()
    refuse_count = Conge.objects.filter(statut="refuse").count()
    total_count = Conge.objects.count()

    leave_types = LeaveType.objects.filter(is_active=True)  # ← ajouté

    return render(request, "leaves/home.html", {
        "conges": conges,
        "attente_count": attente_count,
        "valide_count": valide_count,
        "refuse_count": refuse_count,
        "total_count": total_count,
        "leave_types": leave_types,  # ← ajouté
    })
def valider_conge(request, id):
    conge = get_object_or_404(Conge, idConge=id)
    conge.statut = "valide"
    conge.save()
    return redirect("/leaves/")
def refuser_conge(request, id):
    conge = get_object_or_404(Conge, idConge=id)
    conge.statut = "refuse"
    conge.save()
    return redirect("/leaves/")
# ─── Rapport ViewSet ──────────────────────────────────────────────────────────

class RapportViewSet(viewsets.ModelViewSet):
    serializer_class   = RapportSerializer
    permission_classes = [IsAdminRH]
    queryset           = Rapport.objects.all()

    def perform_create(self, serializer):
        serializer.save(genere_par=self.request.user)

    @action(detail=False, methods=['post'], url_path='journalier')
    def rapport_journalier(self, request):
        date_param = request.data.get('date', date.today().isoformat())
        pointages  = Pointage.objects.filter(date=date_param).select_related('employe')
        donnees = {
            'date':           date_param,
            'total_employes': pointages.count(),
            'total_heures':   pointages.aggregate(t=Sum('heure_travaille'))['t'] or 0,
            'details':        PointageSerializer(pointages, many=True).data,
        }
        rapport = Rapport.objects.create(
            TypeRapport='journalier', periode=date_param,
            genere_par=request.user, donnees=donnees
        )
        return Response(RapportSerializer(rapport).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='mensuel')
    def rapport_mensuel(self, request):
        mois = request.data.get('mois', date.today().strftime('%Y-%m'))
        annee, num_mois = map(int, mois.split('-'))
        pointages = Pointage.objects.filter(
            date__year=annee, date__month=num_mois
        ).select_related('employe')
        conges = Conge.objects.filter(
            date_debut__year=annee, date_debut__month=num_mois
        ).select_related('employe')
        donnees = {
            'periode':        mois,
            'total_heures':   pointages.aggregate(t=Sum('heure_travaille'))['t'] or 0,
            'total_conges':   conges.count(),
            'conges_valides': conges.filter(statut='valide').count(),
        }
        rapport = Rapport.objects.create(
            TypeRapport='mensuel', periode=mois,
            genere_par=request.user, donnees=donnees
        )
        return Response(RapportSerializer(rapport).data, status=status.HTTP_201_CREATED)
    
def rapports_view(request):

    today = date.today()

    presences = Pointage.objects.filter(date__month=today.month).count()
    retards = Pointage.objects.filter(heure_entree__gt=time(8, 0)).count()
    conges = Conge.objects.filter(statut="valide").count()
    employes = Employe.objects.filter(is_active=True).count()

    context = {
        "today": today,
        "stats": {
            "presences": presences,
            "retards": retards,
            "conges": conges,
            "employes": employes,
        },
        # ✅ Ajoute cette ligne
        "departments": Department.objects.all(),
    }

    return render(request, "dashboard/rapports.html", context)

def rapport_presences_pdf(request):
    selected_date = request.GET.get('date', str(timezone.now().date()))
    statut_filter = request.GET.get('statut')

    pointages_jour = Pointage.objects.filter(
        date=selected_date
    ).select_related('employe', 'employe__departement')

    pointage_map = {p.employe_id: p for p in pointages_jour}

    employees = Employe.objects.filter(is_admin=False).select_related('departement')

    data = []
    for emp in employees:
        p = pointage_map.get(emp.idEmploye)

        if p:
            status = p.get_status()
        else:
            status = 'absent'

        if statut_filter and statut_filter != status:
            continue

        data.append({
            'employe': emp,                                    # ← employé direct
            'date': selected_date,
            'heure_entree': p.heure_entree if p else None,
            'heure_sortie': p.heure_sortie if p else None,
            'status': status,
        })

    html = render_to_string('dashboard/pdf_presences.html', {
        'data': data,
        'selected_date': selected_date,
        'generated_at': timezone.now(),
    })
    return _make_pdf(html, f'presences_{selected_date}.pdf')


def rapport_conges_pdf(request):

    date_debut = request.GET.get(
        'date_debut',
        str(timezone.now().date().replace(day=1))
    )

    date_fin = request.GET.get('date_fin') or str(timezone.now().date())

    statut = request.GET.get("statut")

    conges = Conge.objects.select_related(
        "employe",
        "typeConge"
    ).filter(
        date_debut__gte=date_debut,
        date_debut__lte=date_fin
    )

    if statut:
        conges = conges.filter(statut=statut)

    html = render_to_string(
        'dashboard/pdf_conges.html',
        {
            'conges': conges,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'generated_at': timezone.now(),
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="conges_{date_debut}.pdf"'
    )

    pisa.CreatePDF(html, dest=response)

    return response


def _make_pdf(html, filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    pisa.CreatePDF(html, dest=response)
    return response


def rapport_employes_pdf(request):
    employes = Employe.objects.select_related('departement').all()
    statut = request.GET.get("statut")
    departement = request.GET.get("departement")

    if statut == "active":
        employes = employes.filter(statut="actif")
    elif statut == "inactive":
        employes = employes.exclude(statut="actif")

    if departement:
        employes = employes.filter(departement_id=departement)

    html = render_to_string(
        'dashboard/pdf_employes.html',
        {
            'employes': employes,
            'generated_at': timezone.now(),
        }
    )

    return _make_pdf(html, 'employes.pdf')

def parametres_view(request):
    leave_types = LeaveType.objects.all()
    avertissements = Avertissement.objects.select_related('employee', 'envoye_par').order_by('-date_envoi')

    context = {
        "leave_types": leave_types,
        "avertissements": avertissements,

    }


    return render(request, "dashboard/parametres.html", context)


def add_leave_type(request):
        if request.method == "POST":
            LeaveType.objects.create(
                name=request.POST["name"],
                max_days=request.POST["max_days"],
                is_paid=request.POST["is_paid"] == "1",
                requires_document=request.POST["requires_document"] == "1",
            )
        messages.success(request, "Type de congé ajouté !")
        return redirect("parametres")
def edit_leave_type(request, id):
    lt = get_object_or_404(LeaveType, id=id)

    if request.method == "POST":
        lt.name = request.POST.get("name")
        lt.max_days = request.POST.get("max_days")
        lt.is_paid = request.POST.get("is_paid") == "1"
        lt.requires_document = request.POST.get("requires_document") == "1"
        lt.is_active = request.POST.get("is_active") == "1"
        lt.save()

        messages.success(request, "Type de congé modifié !")
        return redirect("parametres")

    return render(request, "dashboard/edit_leave_type.html", {"lt": lt})
def delete_leave_type(request, id):
    lt = get_object_or_404(LeaveType, id=id)
    lt.delete()
    messages.success(request, "Type de congé supprimé !")
    return redirect("parametres")
    

    



from django.http import JsonResponse
import json

def employee_dashboard(request):
    from datetime import date
    employe = request.user
    today = date.today()
    avertissements = request.user.avertissements.filter(justification_date__isnull=True)
    nb_non_lus = avertissements.filter(lu=False).count()  # ← compter d'abord

    
    # Marquer comme lus automatiquement après affichage
    avertissements.filter(lu=False).update(lu=True)

    # Pointage du jour
    pointage_today = Pointage.objects.filter(
        employe=employe, date=today
    ).first()

    # Stats du mois
    employee_presences = Pointage.objects.filter(
        employe=employe,
        date__month=today.month,
        date__year=today.year,
        heure_entree__isnull=False
    ).count()

    employee_retards = Pointage.objects.filter(
        employe=employe,
        date__month=today.month,
        date__year=today.year,
    )
    retards_count = sum(1 for p in employee_retards if p.verifier_retard())

    employee_conges = Conge.objects.filter(
        employe=employe,
        statut='valide',
        date_debut__year=today.year
    ).count()

    # Historique récent 7 jours
    recent_pointages = Pointage.objects.filter(
        employe=employe
    ).order_by('-date')[:7]

    # Congés récents
    recent_leaves = Conge.objects.filter(
        employe=employe
    ).order_by('-date_debut')[:5]

    return render(request, 'dashboard/employee_dashboard.html', {
        'pointage_today': pointage_today,
        'recent_pointages': recent_pointages,
        'recent_leaves': recent_leaves,
        'employee_presences': employee_presences,
        'employee_retards': retards_count,
        'employee_conges': employee_conges,
        'avertissements': avertissements,
        'nb_non_lus': nb_non_lus,     })


def pointage_employee(request):
    from datetime import date
    pointage = Pointage.objects.filter(
        employe=request.user, date=date.today()
    ).first()
    return render(request, 'pointage/employee.html', {
        'pointage': pointage
    })


def enregistrer_pointage(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    from datetime import date, datetime
    data = json.loads(request.body)
    type_pointage = data.get('type')
    now_time = datetime.now().time()
    today = date.today()

    pointage, _ = Pointage.objects.get_or_create(
        employe=request.user, date=today
    )

    if type_pointage == 'arrivee':
        if pointage.heure_entree:
            return JsonResponse({'status': 'already'})
        pointage.heure_entree = now_time

    elif type_pointage == 'depart_pause':
        if not pointage.heure_entree:
            return JsonResponse({'status': 'error', 'msg': 'Pas encore arrivé'})
        pointage.debut_pause = now_time

    elif type_pointage == 'retour_pause':
        if not pointage.debut_pause:
            return JsonResponse({'status': 'error', 'msg': 'Pas de départ pause'})
        pointage.retour_pause = now_time

    elif type_pointage == 'depart_final':
        if not pointage.retour_pause:
            return JsonResponse({'status': 'error', 'msg': 'Pas de retour pause'})
        pointage.heure_sortie = now_time
        pointage.calculer_heures()

    pointage.save()
    return JsonResponse({'status': 'ok'})


def mes_conges(request):
    statut_filter = request.GET.get("statut")
    conges = Conge.objects.filter(employe=request.user).order_by('-date_debut')

    if statut_filter:
        conges = conges.filter(statut=statut_filter)

    return render(request, 'leaves/mes_conges.html', {
        'conges': conges,
        'attente_count': Conge.objects.filter(employe=request.user, statut='en_attente').count(),
        'valide_count':  Conge.objects.filter(employe=request.user, statut='valide').count(),
        'refuse_count':  Conge.objects.filter(employe=request.user, statut='refuse').count(),
        'total_count':   Conge.objects.filter(employe=request.user).count(),
    })

def annuler_conge_employe(request, id):
    conge = get_object_or_404(Conge, idConge=id, employe=request.user)
    if conge.statut == 'en_attente':
        conge.statut = 'annule'
        conge.save()
    return redirect('employee-leaves')
def nouvelle_demande_conge(request):
    from datetime import date as date_type
    leave_types = LeaveType.objects.filter(is_active=True)

    stats = {
        'approved': Conge.objects.filter(employe=request.user, statut='valide').count(),
        'pending': Conge.objects.filter(employe=request.user, statut='en_attente').count(),
    }

    if request.method == 'POST':
        leave_type_id = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')

        leave_type = get_object_or_404(LeaveType, id=leave_type_id)

        # ── Validation du nombre de jours ──
        d1 = date_type.fromisoformat(start_date)
        d2 = date_type.fromisoformat(end_date)
        nb_jours = (d2 - d1).days + 1

        if d2 < d1:
            messages.error(request, 'La date de fin doit être après la date de début.')
            return render(request, 'leaves/new.html', {'leave_types': leave_types, 'stats': stats})

        if nb_jours > leave_type.max_days:
            messages.error(request, f'La durée demandée ({nb_jours} jours) dépasse le maximum autorisé ({leave_type.max_days} jours) pour ce type de congé.')
            return render(request, 'leaves/new.html', {'leave_types': leave_types, 'stats': stats})

        Conge.objects.create(
            employe=request.user,
            typeConge=leave_type,
            date_debut=start_date,
            date_fin=end_date,
            motif=reason,
            statut='en_attente'
        )
        messages.success(request, 'Demande envoyée avec succès !')
        return redirect('employee-leaves')

    return render(request, 'leaves/new.html', {
        'leave_types': leave_types,
        'stats': stats,
    })

def historique_pointage(request):
    from datetime import datetime, date as date_type, timedelta

    today = date_type.today()
    periode = request.GET.get('periode', 'mois')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    # ── Calcul période ──
    if date_debut and date_fin:
        date_debut = date_type.fromisoformat(date_debut)
        date_fin = date_type.fromisoformat(date_fin)
    elif periode == 'mois_dernier':
        first_day = today.replace(day=1)
        date_fin = first_day - timedelta(days=1)
        date_debut = date_fin.replace(day=1)
    elif periode == '3mois':
        date_fin = today
        date_debut = today - timedelta(days=90)
    else:  # ce mois
        date_debut = today.replace(day=1)
        date_fin = today

    pointages = Pointage.objects.filter(
        employe=request.user,
        date__gte=date_debut,
        date__lte=date_fin
    ).order_by('-date')

    data = []
    for p in pointages:
        heures_str = None
        if p.heure_entree and p.heure_sortie:
            debut = datetime.combine(date_type.today(), p.heure_entree)
            fin   = datetime.combine(date_type.today(), p.heure_sortie)
            delta = fin - debut
            total_minutes = int(delta.seconds / 60)
            h = total_minutes // 60
            m = total_minutes % 60
            heures_str = f"{h}h {m:02d}min"

        data.append({
            'date': p.date,
            'arrivee': p.heure_entree,
            'depart_pause': p.debut_pause,
            'retour_pause': p.retour_pause,
            'depart_final': p.heure_sortie,
            'total_hours': heures_str,
            'status': p.get_status(),
        })

    return render(request, 'pointage/history.html', {
        'pointages': data,
        'periode': periode,
        'date_debut': date_debut,
        'date_fin': date_fin,
    })

    return render(request, 'pointage/history.html', {'pointages': data})