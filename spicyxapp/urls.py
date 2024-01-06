from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth_views

from .views import start
from .views import home
from .views import myprofile
from .views import userprofile
from .views import registration
from .views import logout_view
from .views import editprofile
from .views import saveComment
from .views import saveLike
from .views import saveLikeinComment
from .views import deleteComment
from .views import deletePost
from .views import changePostHidden
from .views import changePostPremium
from .views import explorer
from .views import uploadVideoForPanda
from .views import uploadImage
from .views import viewedNotification
from .views import onlyPost
from .views import searchUsers
from .views import terms
from .views import privacity
from .views import followView
from .views import desactiveSignatureFan
from .views import loadMorePosts
from .views import myfollowers
from .views import mysettings
from .views import stripeCheckoutView
from .views import webhooks
from .views import creatorRequestStart
from .views import adminDocumentation
from .views import financesView
from .views import adminPayouts

urlpatterns = [
    path('', start, name='start'),
    path('m/home/', home, name='home'),
    path('m/explorer/', explorer, name='explorer'),
    path('', include('django.contrib.auth.urls')),
    path('m/logout/', logout_view, name='logout'),
    path('cadastro/', registration, name='cadastro'),
    path('termos/', terms, name='termos'),
    path('privacidade/', privacity, name='privacidade'),
    path('m/me/', myprofile, name='me'),
    path('m/settings/', mysettings, name='settings'),
    path('m/editprofile/', editprofile, name='editprofile'),
    path('m/savecomment/', saveComment, name='savecomment'),
    path('m/likepost/', saveLike, name='likepost'),
    path('m/likecomment/', saveLikeinComment, name='likecomment'),
    path('m/deletecomment/', deleteComment, name='deletecomment'),
    path('m/deletepost/', deletePost, name='deletepost'),
    path('m/uploadvideo/', uploadVideoForPanda, name='uploadvideo'),
    path('m/clearnotification/', viewedNotification, name='clearnotification'),
    path('m/uploadimage/', uploadImage, name='uploadimage'),
    path('m/changehidden/', changePostHidden, name='changehidden'),
    path('m/changepremium/', changePostPremium, name='changepremium'),
    path('m/<str:nickname>', userprofile, name='user'),
    path('m/post/<str:nickname>/<int:id>/', onlyPost, name='onlypost'),
    path('m/search/', searchUsers, name='search'),
    path('m/follow/', followView, name='follow'),
    path('m/myfollowers/', myfollowers, name='myfollowers'),

    path('i6z7Q2iNki8/painel/docs/', adminDocumentation, name='docs'),
    path('i6z7Q2iNki8/painel/payouts/', adminPayouts, name='payouts'),

    path('m/desactive/signature/', desactiveSignatureFan, name='desactivesignature'),
    path('m/sendreqcreator/', creatorRequestStart, name='creatorrequeststart'),
    path('m/finances/', financesView, name='finances'),

    path('m/<str:nickname>/checkout/', stripeCheckoutView, name='checkout'),
    path('webhooks/C7SWQA7b2n9ijrnxcrW5G/', webhooks, name='webhooks'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('m/api/load_more_posts/<int:start_index>/<str:origin>/', loadMorePosts, name='load_more_posts'),
]

