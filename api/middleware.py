from django.shortcuts import redirect
from api.models import Employe

# Pages publiques — jamais bloquées
PAGES_PUBLIQUES = ['/', '/logout/']
PREFIXES_PUBLICS = ['/api/', '/admin/', '/static/', '/media/']

# Pages réservées aux admins SEULEMENT
# (ne pas mettre /dashboard/ seul car /dashboard/employee/ en fait partie)
PAGES_ADMIN = [
    '/dashboard/parametres/',
    '/dashboard/rapports/',
    '/dashboard/pdf_',
    '/employees/',
    '/pointage/',        # pointage admin
    '/conges/',
    '/leaves/',
]

# Pages employé — accessibles aux non-admins
PAGES_EMPLOYE_OK = [
    '/dashboard/employee/',
    '/pointage/employee/',
    '/pointage/enregistrer/',
    '/pointage/history/',
    '/leaves/new/',
    '/leaves/mes-conges/',
]

# Toutes les pages qui nécessitent une connexion
PAGES_PROTEGEES = [
    '/dashboard/',
    '/employees/',
    '/leaves/',
    '/pointage/',
    '/conges/',
]


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ── 1. Pages publiques — laisser passer ──
        if path in PAGES_PUBLIQUES:
            return self.get_response(request)
        if any(path.startswith(p) for p in PREFIXES_PUBLICS):
            return self.get_response(request)

        # ── 2. Injecter request.user depuis la session ──
        user_data = request.session.get('user')
        if user_data:
            try:
                request.user = Employe.objects.get(idEmploye=user_data['id'])
            except Employe.DoesNotExist:
                pass

        # ── 3. Vérifier connexion ──
        if any(path.startswith(p) for p in PAGES_PROTEGEES):
            if not request.session.get('access_token'):
                return redirect('/')

        # ── 4. Vérifier admin pour pages admin ──
        # Exception : pages employé sont accessibles aux non-admins
        is_employe_page = any(path.startswith(p) for p in PAGES_EMPLOYE_OK)

        if not is_employe_page:
            if any(path.startswith(p) for p in PAGES_ADMIN):
                user = request.session.get('user', {})
                if not user.get('is_admin'):
                    return redirect('/dashboard/employee/')

        return self.get_response(request)