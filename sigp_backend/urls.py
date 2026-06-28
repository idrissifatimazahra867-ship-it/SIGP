from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import admin_dashboard
from api.views import employees_list
from api.views import add_employee
from api.views import edit_employee
from api.views import pointage_home
from api.views import conges_home
from api.views import valider_conge
from api.views import refuser_conge
from api.views import rapports_view
from api.views import rapport_presences_pdf, rapport_conges_pdf, rapport_employes_pdf
from api.views import parametres_view, add_leave_type, edit_leave_type, delete_leave_type,envoyer_avertissement, soumettre_justification, traiter_justification
from api.views import (
    employee_dashboard, pointage_employee,
    enregistrer_pointage, mes_conges, annuler_conge_employe,
    nouvelle_demande_conge, historique_pointage
)
from api.views import LoginView, LoginHTMLView, LogoutView
from django.views.generic import TemplateView

urlpatterns = [

    # ── Django Admin ─────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── API JWT (tokens) ─────────────────────────────────────────────────────
    path('api/token/',         LoginView.as_view(),        name='token_obtain'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── API REST (employés, pointages, congés, rapports) ─────────────────────
    path('api/', include('api.urls')),

    # ── Authentification HTML ─────────────────────────────────────────────────
    path('',        LoginHTMLView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(),    name='logout'),

   # Dashboard
   path('dashboard/',admin_dashboard,name='dashboard'),
   path("dashboard/parametres/", parametres_view, name="parametres"),
   path("dashboard/parametres/conge/add/", add_leave_type),
   path('dashboard/parametres/conge/<int:id>/edit/', edit_leave_type, name='edit-leave-type'),
   path('dashboard/parametres/conge/<int:id>/delete/', delete_leave_type, name='delete-leave-type'),
   path("dashboard/rapports/", rapports_view, name="rapports"),
   path("dashboard/pdf_conges/", rapport_conges_pdf, name="rapport_conges_pdf"),
   path("dashboard/pdf_presences/", rapport_presences_pdf, name="rapport_presences_pdf"),
   path("dashboard/pdf_employes/", rapport_employes_pdf, name="rapport_employes_pdf"),
    # ── Employés ──────────────────────────────────────────────────────────────
    path('employees/', employees_list, name='employees-list'),   
    path('employees/add/',add_employee,name='employees-add'),    
    path('employees/edit/<int:id>/', edit_employee, name='employee-edit'),
    # ── Congés ────────────────────────────────────────────────────────────────
    path('leaves/', conges_home, name='leaves-home'),
    path('conges/<int:id>/valider/', valider_conge, name='conge-valider'),
    path('conges/<int:id>/refuser/', refuser_conge, name='conge-refuser'),
    path('conges/<int:id>/annuler/', annuler_conge_employe, name='conge-annuler'),


    # ── Pointage ──────────────────────────────────────────────────────────────

    path('pointage/', pointage_home, name='pointage-home'),
    path('pointage/avertissement/', envoyer_avertissement, name='envoyer_avertissement'),
    path('avertissement/justifier/', soumettre_justification, name='soumettre_justification'),
    path('avertissement/traiter/', traiter_justification, name='traiter_justification'),

    path('dashboard/employee/', employee_dashboard, name='dashboard-employee'),
    path('pointage/employee/', pointage_employee, name='pointage-employee'),
    path('pointage/enregistrer/', enregistrer_pointage, name='pointage-enregistrer'),
    path('pointage/history/', historique_pointage, name='pointage-history'),
    path('leaves/mes-conges/', mes_conges, name='employee-leaves'),
    path('leaves/new/', nouvelle_demande_conge, name='leaves-new'),

    # path('pointage/employee/', pointage_employee, name='pointage-employee'),

    # path('pointage/history/', pointage_history, name='pointage-history'),

]

# ── Fichiers media et static en mode DEBUG ────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
                          if settings.STATICFILES_DIRS else settings.STATIC_ROOT)