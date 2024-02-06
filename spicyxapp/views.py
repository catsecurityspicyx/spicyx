from django.shortcuts import render
from spicyxapp import models
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import logout
from datetime import datetime
from django.contrib.auth import authenticate, login
from django.core.cache import cache
from .functions import EditProfile
from .functions import createPresignedUrl
from .functions import generateNewsPresignedUrls
from .functions import generateNewsPresignedUrlsForProfiles
from .functions import checkUploadVideoLimite
from .functions import checkUploadImageLimite
from .functions import CheckVerifyUser
from .functions import ApproveDocumentation
from .functions import Post_create_profile_link
#from .functions import Check_force_password
import base64
import requests
import random
import json
import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from .models import User, Profile
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from django.template.loader import render_to_string
from django_ratelimit.decorators import ratelimit
import stripe
from .stripe_functions import createProduct
from .stripe_functions import createRecurringSignature
from .stripe_functions import webhookReceived
from .stripe_functions import cancelSubscription
from .stripe_functions import docs_generateNewsPresignedUrls
from .stripe_functions import saveWebhookBD
from .stripe_functions import updateProduct
import time
import io
from PIL import Image
from PIL import ImageOps
stripe.api_key = settings.STRIPE_SECRET_API_KEY


@ratelimit(key='ip', rate='200/5m', block=True)
@csrf_protect
def searchUsers(request):
    if request.user.is_authenticated:
        if request.GET:
            try:
                query = escape(request.GET.get('q'))
                query = query.replace("@", "")
                if query:
                    searchResult = list(Profile.objects.filter(
                        Q(nickname__icontains=query)
                    ).values())
                else:
                    searchResult = list(User.objects.all().values())

                return JsonResponse({'searchResult': searchResult}, safe=True)
            except Exception as e:
                error = 'Erro ao buscar usuário.'
                return HttpResponseRedirect("/m/explorer/?status=error&info=" + error)
        else:
            return HttpResponseRedirect('/m/explorer/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def start(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/m/home/")
    else:
        if request.POST:
            username = escape(request.POST['username'])
            password = escape(request.POST['password'])

            if settings.USE_RECAPTCHA_V2:
                recaptcha_response = request.POST.get('g-recaptcha-response')
                captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V2,
                               'response': recaptcha_response,
                               'remoteip': request.headers.get('CF-Connecting-IP') or request.headers.get(
                                   'X-Forwarded-For') or request.META.get('REMOTE_ADDR')}
                req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
                result = req.json()
                if result['success']:
                    pass
                else:
                    return HttpResponseRedirect("/")

            authLogin = authenticate(request, username=username, password=password)
            if authLogin is not None:
                login(request, authLogin)

                generateNewsPresignedUrls()
                generateNewsPresignedUrlsForProfiles()

                return HttpResponseRedirect("/m/home/")
            else:
                err_msg = '?status=error&info=E-mail ou senha incorreto.'
                return HttpResponseRedirect("/" + err_msg)

        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V2
        try:
            admin_profile = models.User.objects.get(username='spicyx').profile

            if cache.get('index_lastposts'):
                last_six_posts = cache.get('index_lastposts')
            else:
                last_six_posts = models.FeedUser.objects.filter(profile_creator=admin_profile,
                                                                post_deleted=False,
                                                                post_hidden=False,
                                                                media_premium=False,
                                                                media_free=True).order_by('-created_at')[:6]
                cache.set('index_lastposts', last_six_posts, timeout=3600)

        except Exception as e:
            return render(request, 'registration/login.html', {'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
        return render(request, 'registration/login.html',
                      {'last_posts': last_six_posts, 'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})


@ratelimit(key='ip', rate='100/5m', block=True)
def terms(request):
    return render(request, 'registration/terms.html')


@ratelimit(key='ip', rate='100/5m', block=True)
def privacity(request):
    return render(request, 'registration/privacity.html')


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def myPaaswordReset(request):
    GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V2

    if request.POST:
        if settings.USE_RECAPTCHA_V2:
            recaptcha_response = request.POST.get('g-recaptcha-response')
            captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V2,
                           'response': recaptcha_response}
            req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
            result = req.json()
            if result['success']:
                pass
            else:
                return HttpResponseRedirect("/password_reset/")

        return render(request, 'registration/password_reset_form.html', {'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})

    return render(request, 'registration/password_reset_form.html', {'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def registration(request):
    GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V2

    try:
        admin_profile = models.User.objects.get(username='spicyx').profile
        last_six_posts = models.FeedUser.objects.filter(profile_creator=admin_profile,
                                                        post_deleted=False,
                                                        post_hidden=False,
                                                        media_premium=False,
                                                        media_free=True).order_by('-created_at')[:6]
    except Exception as e:
        print(e)
        last_six_posts = {}
        pass

    if request.POST:
        if settings.USE_RECAPTCHA_V2:
            recaptcha_response = request.POST.get('g-recaptcha-response')
            captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V2,
                           'response': recaptcha_response}
            req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
            result = req.json()
            if result['success']:
                pass
            else:
                return HttpResponseRedirect("/cadastro/")

        birth = escape(request.POST['birth'])
        sex = escape(request.POST['sex'])
        interest = escape(request.POST['interest'])
        email = escape(request.POST['username'])
        username = escape(request.POST['username'])
        password = escape(request.POST['password'])
        first_name = escape(request.POST['first_name'])
        last_name = escape(request.POST['last_name'])

        f_name = first_name.replace(" ", "")
        l_name = last_name.replace(" ", "")
        nick = f_name + l_name
        nick = nick.lower()

        # pass_err = ('?status=error&info=Senha muito fraca, senha deve conter caracteres especiais, números, '
        #             'letras maiúsculas e ter no mínimo 6 caracteres.')
        # password_is_ok = Check_force_password(email, password, nick)
        # if not password_is_ok:
        #     return HttpResponseRedirect("/cadastro/" + pass_err)

        url = "https://api-v2.pandavideo.com.br/folders"
        headers = {
            'Authorization': settings.PANDA_VIDEO_API_KEY,
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        try:
            newUser = User.objects.create_user(username=username,
                                               email=email,
                                               password=password,
                                               first_name=first_name,
                                               last_name=last_name,
                                               is_staff=False,
                                               is_active=True,
                                               is_superuser=False,
                                               date_joined=timezone.now())

            if newUser.id:
                u_id = newUser.id
                t_now = timezone.now()
                t_timestamp = time.mktime(t_now.timetuple())
                folder_name = str(nick) + '_' + str(u_id) + '_' + str(t_timestamp)
                payload = {'name': folder_name}

                check_exist_nick = models.Profile.objects.filter(nickname=nick).exists()
                if check_exist_nick:
                    r1 = random.randint(1, 100)
                    r2 = random.randint(2, 99)
                    r3 = random.randint(1, 100)
                    nick = nick + str(r1) + str(newUser.id) + str(r2) + str(r3)
                    models.Profile.objects.create(user_id=newUser.id,
                                                  nickname=nick,
                                                  birth=birth,
                                                  sex=sex,
                                                  interest=interest,
                                                  user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'),
                                                  folder_videos=folder_name)
                elif not check_exist_nick:
                    models.Profile.objects.create(user_id=newUser.id,
                                                  nickname=nick,
                                                  birth=birth,
                                                  sex=sex,
                                                  interest=interest,
                                                  user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'),
                                                  folder_videos=folder_name)

                response = requests.request("POST", url, json=payload, headers=headers)
                dict_resp = json.loads(response.text)

                a = models.Profile.objects.get(nickname=nick)
                a.folder_videos_id = dict_resp['id']
                a.save()

                success = '?status=success&info=Cadastro realizado com sucesso!'
                return HttpResponseRedirect("/" + success)
        except:
            err = 'E-mail já cadastrado.'
            return render(request, 'registration/cadastro.html', {'err': err, 'last_posts': last_six_posts,
                                                                  'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})

    return render(request, 'registration/cadastro.html', {'last_posts': last_six_posts, 'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def saveComment(request):
    if request.user.is_authenticated:
        if request.POST:
            action = escape(request.POST['action'])
            returnTo = escape(request.POST['page'])
            iam = request.user.profile
            err_msg = ''

            try:
                if action == 'comment':
                    comment = escape(request.POST['comment'])
                    post_id = models.FeedUser.objects.get(id=escape(request.POST["post"]))
                    creator_post = escape(request.POST['creator'])
                    fan = models.Profile.objects.get(user=request.user.id)
                    fan_nick = escape(request.POST['fan_nick'])
                    models.CommentPost.objects.create(post=post_id, profile_creator=creator_post, profile_fan=fan,
                                                      fan_nickname=fan_nick, fan_comment=comment,
                                                      user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'))

                    creator_nick = models.User.objects.get(id=creator_post).profile.nickname
                    link_to = f'/m/post/{creator_nick}/{escape(request.POST["post"])}/'
                    msg_to = 'Comentou em seu post!'
                    models.Notification.objects.create(profile_from=iam, profile_to=creator_post, context_msg=msg_to,
                                                       context_link=link_to)
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu ao comentar.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect(link_to + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect(link_to + err_msg)
            elif returnTo == 'profile':
                return HttpResponseRedirect(link_to + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect(link_to + err_msg)
            elif returnTo == 'post':
                post_user_nick = escape(request.POST['creator_nickname'])
                p_id = int(escape(request.POST["post"]))
                return HttpResponseRedirect(f'/m/post/{post_user_nick}/{p_id}/' + err_msg)
        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def saveLike(request):
    if request.user.is_authenticated:
        if request.POST:
            action = escape(request.POST['action'])
            returnTo = escape(request.POST['page'])
            iam = request.user.profile
            err_msg = ''

            try:
                if action == 'like':
                    post_id = models.FeedUser.objects.get(id=escape(request.POST["post"]))
                    creator_post = escape(request.POST['creator'])
                    fan = models.Profile.objects.get(user=escape(request.POST['fan_id']))
                    fan_nick = escape(request.POST['fan_nick'])
                    models.LikedPost.objects.create(post=post_id, profile_creator=creator_post, profile_fan=fan,
                                                    fan_nickname=fan_nick,
                                                    user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'))

                    creator_nick = models.User.objects.get(id=creator_post).profile.nickname
                    link_to = f'/m/post/{creator_nick}/{escape(request.POST["post"])}/'
                    msg_to = 'Gostou do seu post!'
                    models.Notification.objects.create(profile_from=iam, profile_to=creator_post, context_msg=msg_to,
                                                       context_link=link_to)

                elif action == 'deslike':
                    post_id = models.FeedUser.objects.get(id=escape(request.POST["post"]))
                    fan = models.Profile.objects.get(user=escape(request.POST['fan_id']))
                    d = models.LikedPost.objects.get(post=post_id, profile_fan=fan)
                    d.delete()

                    creator_nick = models.FeedUser.objects.get(id=escape(request.POST["post"])).profile_creator.nickname
                    link_to = f'/m/post/{creator_nick}/{escape(request.POST["post"])}/'
                    msg_to = 'Removeu o GOSTEI do seu post.'
                    models.Notification.objects.create(profile_from=iam, profile_to=post_id.profile_creator.user_id,
                                                       context_msg=msg_to, context_link=link_to)
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'profile':
                url_nick = '/m/@' + str(escape(request.POST['url_nick']))
                return HttpResponseRedirect(url_nick + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)
            elif returnTo == 'post':
                post_user_nick = escape(request.POST['creator_nickname'])
                p_id = int(escape(request.POST["post"]))
                return HttpResponseRedirect(f'/m/post/{post_user_nick}/{p_id}/' + err_msg)
        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def saveLikeinComment(request):
    if request.user.is_authenticated:
        if request.POST:
            action = escape(request.POST['action'])
            returnTo = escape(request.POST['page'])
            iam = request.user.profile
            err_msg = ''

            try:
                if action == 'like':
                    comment_id = models.CommentPost.objects.get(id=escape(request.POST['comment']))
                    post_id = models.FeedUser.objects.get(id=escape(request.POST["post"]))
                    user_profile = models.Profile.objects.get(user=escape(request.POST['user_id']))
                    models.LikeInComment.objects.create(comment=comment_id, post=post_id, user_profile=user_profile,
                                                        user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'))

                    fan_nick = post_id.profile_creator.nickname
                    link_to = f'/m/post/{fan_nick}/{escape(request.POST["post"])}/'
                    msg_to = 'Gostou do seu comentário!'
                    models.Notification.objects.create(profile_from=iam, profile_to=comment_id.profile_fan.user.id,
                                                       context_msg=msg_to, context_link=link_to)

                elif action == 'deslike':
                    comment_id = models.CommentPost.objects.get(id=escape(request.POST['comment']))
                    post_id = models.FeedUser.objects.get(id=escape(request.POST["post"]))
                    user_profile = models.Profile.objects.get(user=escape(request.POST['user_id']))
                    d = models.LikeInComment.objects.get(comment=comment_id, post=post_id, user_profile=user_profile)
                    d.delete()

                    fan_nick = post_id.profile_creator.nickname
                    link_to = f'/m/post/{fan_nick}/{escape(request.POST["post"])}/'
                    msg_to = 'Removeu o GOSTEI do seu comentário!'
                    models.Notification.objects.create(profile_from=iam, profile_to=comment_id.profile_fan.user.id,
                                                       context_msg=msg_to, context_link=link_to)
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'profile':
                url_nick = '/m/@' + str(escape(request.POST['url_nick']))
                return HttpResponseRedirect(url_nick + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)
            elif returnTo == 'post':
                post_user_nick = escape(request.POST['creator_nickname'])
                p_id = int(escape(request.POST["post"]))
                return HttpResponseRedirect(f'/m/post/{post_user_nick}/{p_id}/' + err_msg)
        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def changePostHidden(request):
    if request.user.is_authenticated:
        if request.POST:
            post_id = escape(request.POST["post"])
            returnTo = escape(request.POST['page'])
            action = escape(request.POST['action'])
            user_profile = models.Profile.objects.get(user=request.user.id)
            err_msg = ''

            try:
                if action == 'hidden':
                    h = models.FeedUser.objects.get(id=post_id, profile_creator=user_profile)
                    h.post_hidden = True
                    h.save()
                elif action == 'visible':
                    h = models.FeedUser.objects.get(id=post_id, profile_creator=user_profile)
                    h.post_hidden = False
                    h.save()
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)
            elif returnTo == 'post':
                return HttpResponseRedirect('/m/me/' + err_msg)
        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def viewedNotification(request):
    if request.user.is_authenticated:
        if request.POST:
            returnTo = escape(request.POST['page'])
            target = escape(request.POST['target'])

            if target == 'all':
                my_notifications = models.Notification.objects.filter(profile_to=request.user.id, viewed=False)
                for notification in my_notifications:
                    try:
                        n = models.Notification.objects.get(id=notification.id, profile_to=request.user.id,
                                                            viewed=False)
                        n.viewed = True
                        n.save()
                    except:
                        pass
            if target == 'only':
                notification_id = escape(request.POST['noti_id'])
                try:
                    n = models.Notification.objects.get(id=notification_id, profile_to=request.user.id, viewed=False)
                    n.viewed = True
                    n.save()
                except:
                    pass

            if returnTo == '/m/home/':
                return HttpResponseRedirect('/m/home/')
            elif returnTo == '/m/me/':
                return HttpResponseRedirect('/m/me/')
            elif returnTo == '/m/explorer/':
                return HttpResponseRedirect('/m/explorer/')
            elif 'post' in returnTo:
                return HttpResponseRedirect(returnTo)
        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def changePostPremium(request):
    if request.user.is_authenticated:
        if request.POST:
            post_id = escape(request.POST["post"])
            returnTo = escape(request.POST['page'])
            action = escape(request.POST['action'])
            user_profile = models.Profile.objects.get(user=request.user.id)
            err_msg = ''

            try:
                if action == 'premium':
                    p = models.FeedUser.objects.get(id=post_id, profile_creator=user_profile)
                    p.media_premium = True
                    p.media_free = False
                    p.media_relevance = 5
                    p.save()
                elif action == 'free':
                    p = models.FeedUser.objects.get(id=post_id, profile_creator=user_profile)
                    p.media_premium = False
                    p.media_free = True
                    p.media_relevance = 1
                    p.save()
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu.'
                pass

            if returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)

        return HttpResponseRedirect('/m/me/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def deletePost(request):
    if request.user.is_authenticated:
        if request.POST:
            post_id = escape(request.POST["post"])
            returnTo = escape(request.POST['page'])
            err_msg = ''

            try:
                user_profile = models.Profile.objects.get(user=request.user.id)

                d = models.FeedUser.objects.get(id=post_id, profile_creator=user_profile)
                d.user_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR')
                d.post_deleted = True
                d.save()
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu ao deletar post.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)
            elif returnTo == 'post':
                return HttpResponseRedirect('/m/me/' + err_msg)
            if returnTo == '/m/home/':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == '/m/explorer/':
                return HttpResponseRedirect('/m/explorer/' + err_msg)

        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def deleteComment(request):
    if request.user.is_authenticated:
        if request.POST:
            returnTo = escape(request.POST['page'])
            comment_id = escape(request.POST['comment'])
            err_msg = ''

            try:
                post_id = models.FeedUser.objects.get(id=escape(request.POST["post"]))
                user_profile = models.Profile.objects.get(user=request.user.id)

                d = models.CommentPost.objects.get(id=comment_id, post=post_id, profile_fan=user_profile)
                d.delete()
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu ao deletar comentário.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'profile':
                url_nick = '/m/@' + str(escape(request.POST['url_nick']))
                return HttpResponseRedirect(url_nick + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)
            elif returnTo == 'post':
                post_user_nick = escape(request.POST['creator_nickname'])
                p_id = int(escape(request.POST["post"]))
                return HttpResponseRedirect(f'/m/post/{post_user_nick}/{p_id}/' + err_msg)
        return HttpResponseRedirect('/m/home/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def uploadImage(request):
    if request.user.is_authenticated:
        if request.POST:
            if settings.USE_RECAPTCHA_V3:
                recaptcha_response = request.POST.get('g-recaptcha-response')
                captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                               'response': recaptcha_response}
                req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
                result = req.json()
                if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                    pass
                else:
                    return HttpResponseRedirect("/m/logout/")

            bucket_name = settings.BUCKET_NAME
            returnTo = escape(request.POST['page'])
            err_msg = ''

            if 'post-image' not in request.FILES:
                error = 'Nenhuma imagem foi selecionada.'
                return HttpResponseRedirect("/m/home/?status=error&info=" + error)

            try:
                limit_account_fan = 20
                upload_authorization = checkUploadImageLimite(request.user.profile, limit_account_fan)
                if not upload_authorization:
                    error = f'Contas de fans podem upar somente {limit_account_fan} imagens.'
                    return HttpResponseRedirect("/m/home/?status=error&info=" + error)
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu.'
                pass

            post_image_file = request.FILES['post-image']
            new_name = 'spicyx_' + str(request.user.profile.nickname) + str(time.time()).replace(".", "") + '.'
            try:
                if post_image_file.size > settings.IMAGE_SIZE_LIMIT_POST:
                    error = 'Limite excedido: Tamanho limite para imagem é 100Mb.'
                    return HttpResponseRedirect("/m/home/?status=error&info=" + error)

                post_subtitles = str(escape(request.POST['subtitles']))
                post_status = escape(request.POST['media-status'])
                free = False
                premium = False
                relevance = 1
                if post_status == 'free':
                    free = True
                elif post_status == 'premium':
                    premium = True
                    relevance = 5
                extension = ''
                extensions_allowed = settings.ALLOWED_EXTENSIONS_IMAGES

                for namefile, extension in request.FILES.items():
                    namefile = post_image_file.name
                    extension = namefile.split('.')[1]

                if extension in extensions_allowed:
                    # compression post image to 60% quality
                    new_name = new_name + extension

                    img_compress = Image.open(post_image_file)
                    img_compress = ImageOps.exif_transpose(img_compress)

                    output = io.BytesIO()
                    check_format = 'JPEG' if extension.lower() == 'jpg' else extension.upper()
                    img_compress.save(output, format=check_format, quality=60)
                    output.seek(0)
                    post_image_file = ContentFile(output.getvalue(), name=new_name)

                    save_BD = models.FeedUser.objects.create(profile_creator=request.user.profile,
                                                             subtitles=post_subtitles,
                                                             file=post_image_file,
                                                             media_free=free,
                                                             media_premium=premium,
                                                             media_relevance=relevance,
                                                             user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'))

                    create_URL_temp = createPresignedUrl(bucket_name, str(save_BD.file))
                    if create_URL_temp:
                        t = models.FeedUser.objects.get(file=save_BD.file, profile_creator=request.user.profile)
                        t.media_url = create_URL_temp
                        t.save()
                else:
                    error = 'Extensão inválida.'
                    return HttpResponseRedirect("/m/home/?status=error&info=" + error)

                if returnTo == 'home':
                    cache.delete('home_feed')
                    cache.delete('explorer_feed')
                    return HttpResponseRedirect('/m/home/?status=success')
                elif returnTo == 'me':
                    cache.delete('home_feed')
                    cache.delete('explorer_feed')
                    return HttpResponseRedirect('/m/me/?status=success')
                elif returnTo == 'explorer':
                    cache.delete('home_feed')
                    cache.delete('explorer_feed')
                    return HttpResponseRedirect('/m/explorer/?status=success')

            except Exception as e:
                print(e)
                err_msg = '?status=error&info=Algo de errado ocorreu com o upload.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)
        return HttpResponseRedirect("/m/home/")
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def uploadVideoForPanda(request):
    if request.user.is_authenticated:
        if request.POST:
            if settings.USE_RECAPTCHA_V3:
                recaptcha_response = request.POST.get('g-recaptcha-response')
                captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                               'response': recaptcha_response}
                req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
                result = req.json()
                if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                    pass
                else:
                    return HttpResponseRedirect("/m/logout/")

            returnTo = escape(request.POST['page'])
            err_msg = ''

            if 'post-video' not in request.FILES:
                error = 'Nenhum vídeo foi selecionado.'
                return HttpResponseRedirect("/m/home/?status=error&info=" + error)

            try:
                limit_account_fan = 2
                upload_authorization = checkUploadVideoLimite(request.user.profile, limit_account_fan)
                if upload_authorization == False:
                    error = f'Contas de fans podem upar somente {limit_account_fan} vídeos.'
                    return HttpResponseRedirect("/m/home/?status=error&info=" + error)

                payload = request.FILES['post-video']
                v_subtitles = escape(request.POST['subtitles'])

                if payload.size > settings.VIDEO_SIZE_LIMITE:
                    error = 'Limite excedido: Tamanho limite para vídeo é 1Gb.'
                    return HttpResponseRedirect("/m/home/?status=error&info=" + error)

                extension = ''
                extensions_allowed = settings.ALLOWED_EXTENSIONS_VIDEOS

                for namefile, extension in request.FILES.items():
                    namefile = payload.name
                    extension = namefile.split('.')[1]
                if extension not in extensions_allowed:
                    error = 'Extensão não permitida. Utilize vídeos: .mp4, .avi, .3gp'
                    return HttpResponseRedirect("/m/home/?status=error&info=" + error)

                a = settings.PANDA_VIDEO_API_KEY
                a2 = base64.b64encode(a.encode())
                b = request.user.profile.folder_videos_id
                b2 = base64.b64encode(b.encode())
                r1 = random.randint(2, 98)
                r2 = random.randint(1, 100)
                hj1 = timezone.now()
                hj2 = hj1.strftime("%Y/%m/%d, %H:%M:%S")
                posted_date = (str(base64.b64encode(hj2.encode())).replace('=', '').replace("'", "").replace('"', ''))
                c = 'spicyx_' + str(r1) + str(request.user.profile.nickname) + posted_date + str(r2)
                c2 = base64.b64encode(c.encode())
                d = str(uuid.uuid4())
                d2 = base64.b64encode(d.encode())

                url = "https://uploader-fr01.pandavideo.com.br/files"
                up_met = 'authorization ' + a2.decode('utf-8') + ', folder_id ' + b2.decode(
                    'utf-8') + ', filename ' + c2.decode('utf-8') + ', video_id ' + d2.decode('utf-8')
                headers = {
                    'Tus-Resumable': '1.0.0',
                    'Upload-Length': str(payload.size),
                    'Content-Type': 'application/offset+octet-stream',
                    'Upload-Metadata': up_met
                }
                response = requests.post(url, headers=headers, data=payload)

                if str(response.status_code) == '201':
                    url2 = f'https://api-v2.pandavideo.com.br/videos/{d}'
                    headers2 = {
                        'accept': 'application/json',
                        'Authorization': a
                    }

                    for i in range(1, 7):
                        resp2 = requests.get(url2, headers=headers2)
                        dados = json.loads(resp2.text)
                        time.sleep(5)
                        if str(resp2.status_code) == '200':
                            video_id = dados['video_external_id']
                            free = ''
                            premium = ''
                            relevance = 1
                            if escape(request.POST['media-status']) == 'free':
                                free = True
                                premium = False

                            elif escape(request.POST['media-status']) == 'premium':
                                free = False
                                premium = True
                                relevance = 5

                            p_creator = request.user.profile
                            models.FeedUser.objects.create(profile_creator=p_creator,
                                                           media_url=video_id,
                                                           subtitles=v_subtitles,
                                                           media_free=free,
                                                           media_premium=premium,
                                                           media_relevance=relevance,
                                                           media_type='VIDEO',
                                                           user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'))
                            break

                if returnTo == 'home':
                    cache.delete('home_feed')
                    cache.delete('explorer_feed')
                    return HttpResponseRedirect('/m/home/?status=success')
                elif returnTo == 'me':
                    cache.delete('home_feed')
                    cache.delete('explorer_feed')
                    return HttpResponseRedirect('/m/me/?status=success')
                elif returnTo == 'explorer':
                    cache.delete('home_feed')
                    cache.delete('explorer_feed')
                    return HttpResponseRedirect('/m/explorer/?status=success')
            except Exception as err:
                err_msg = '?status=error&info=Algo de errado ocorreu com o upload.'
                pass

            if returnTo == 'home':
                return HttpResponseRedirect('/m/home/' + err_msg)
            elif returnTo == 'me':
                return HttpResponseRedirect('/m/me/' + err_msg)
            elif returnTo == 'explorer':
                return HttpResponseRedirect('/m/explorer/' + err_msg)

        return HttpResponseRedirect("/m/home/")
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def home(request):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        mySession = User.objects.get(username=request.user)
        userData = User.objects.all()
        profileData = models.Profile.objects.all()
        comments = models.CommentPost.objects.all().order_by('-date_interaction')

        likes = models.LikedPost.objects.all()
        liked_post_ids = [like.post.id for like in likes if like.profile_fan == mySession.profile]

        likes_comment = models.LikeInComment.objects.all()
        liked_comment_ids = [like_comment.comment.id for like_comment in likes_comment if
                             like_comment.user_profile == mySession.profile]

        signatures = models.Subscriber.objects.all()
        subscribe = [sub.creator.id for sub in signatures if
                     sub.subscriber == mySession.profile and sub.suspended == False]

        followers = models.Follower.objects.all()
        follower = [follow.creator for follow in followers if follow.follower == mySession.profile]

        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')

        upload_authorization = checkUploadVideoLimite(mySession.profile, 2)

        if cache.get('home_feed'):
            feedPosts_q_original = models.FeedUser.objects.filter(
                Q(profile_creator__user__id=mySession.id) | \
                (Q(profile_creator__user__id__in=follower) & Q(media_premium=False)) | \
                Q(profile_creator__user__id__in=subscribe)
                & Q(post_hidden=False) & Q(post_deleted=False)).order_by('-media_relevance',
                                                                         '-created_at')[:25]
            query_list = list(feedPosts_q_original)
            if query_list == list(cache.get('home_feed')):
                feedPosts_q = cache.get('home_feed')
            else:
                feedPosts_q = feedPosts_q_original
                cache.set('home_feed', feedPosts_q_original, timeout=3600)
        else:
            feedPosts_q = models.FeedUser.objects.filter(
                Q(profile_creator__user__id=mySession.id) | \
                (Q(profile_creator__user__id__in=follower) & Q(media_premium=False)) | \
                Q(profile_creator__user__id__in=subscribe)
                & Q(post_hidden=False) & Q(post_deleted=False)).order_by('-media_relevance',
                                                                         '-created_at')[:25]
            cache.set('home_feed', feedPosts_q, timeout=3600)

        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3

        for newpost in feedPosts_q:
            if newpost.subtitles != '':
                newpost.subtitles = Post_create_profile_link(newpost.subtitles)

        return render(request, 'members/home.html', {'userData': userData,
                                                     'profile': profileData, 'feed': feedPosts_q,
                                                     'comments': comments, 'liked_post_ids': liked_post_ids,
                                                     'mySession': mySession, 'liked_comment_ids': liked_comment_ids,
                                                     'subscribe': subscribe, 'countNotifications': countNotifications,
                                                     'notifications': notifications, 'follower': follower,
                                                     'darktheme': darktheme,
                                                     'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='200/5m', block=True)
@csrf_protect
def explorer(request):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        mySession = User.objects.get(username=request.user)
        userData = User.objects.all()
        profileData = models.Profile.objects.all()

        if mySession.profile.interest == 'all':
            query2 = (Q(post_hidden=False) & Q(post_deleted=False) & Q(
                media_premium=False) & Q(media_free=True))
        else:
            query2 = (Q(profile_creator__sex=mySession.profile.interest) & Q(post_hidden=False) & Q(post_deleted=False) & Q(
                media_premium=False) & Q(media_free=True))

        if cache.get('explorer_feed'):
            feedPosts_original = models.FeedUser.objects.filter(query2).order_by('-media_relevance',
                                                                                 '-created_at')[:25]
            query_list = list(feedPosts_original)
            if query_list == list(cache.get('explorer_feed')):
                feedPosts = cache.get('explorer_feed')
            else:
                feedPosts = feedPosts_original
                cache.set('explorer_feed', feedPosts_original, timeout=3600)
        else:
            feedPosts = models.FeedUser.objects.filter(query2).order_by('-media_relevance',
                                                                        '-created_at')[:25]
            cache.set('explorer_feed', feedPosts, timeout=3600)

        for newpost in feedPosts:
            if newpost.subtitles != '':
                newpost.subtitles = Post_create_profile_link(newpost.subtitles)

        comments = models.CommentPost.objects.all().order_by('-date_interaction')

        likes = models.LikedPost.objects.all()
        liked_post_ids = [like.post.id for like in likes if like.profile_fan == mySession.profile]

        likes_comment = models.LikeInComment.objects.all()
        liked_comment_ids = [like_comment.comment.id for like_comment in likes_comment if
                             like_comment.user_profile == mySession.profile]

        signatures = models.Subscriber.objects.all()
        subscribe = [sub.creator.id for sub in signatures if
                     sub.subscriber == mySession.profile and sub.suspended == False]

        followers = models.Follower.objects.all()
        follower = [follow.creator for follow in followers if follow.follower == mySession.profile]

        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')
        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3

        return render(request, 'members/explorer.html', {'userData': userData,
                                                         'profile': profileData, 'feed': feedPosts,
                                                         'comments': comments, 'liked_post_ids': liked_post_ids,
                                                         'mySession': mySession, 'liked_comment_ids': liked_comment_ids,
                                                         'subscribe': subscribe,
                                                         'countNotifications': countNotifications,
                                                         'notifications': notifications, 'follower': follower,
                                                         'darktheme': darktheme,
                                                         'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def myfollowers(request):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        mySession = User.objects.get(username=request.user)

        subscribers = models.Subscriber.objects.filter(creator=mySession.id, suspended=False)
        countSubscribers = models.Subscriber.objects.filter(creator=mySession.id, suspended=False).count()

        followers = models.Follower.objects.filter(creator=mySession.id)
        countFollowers = models.Follower.objects.filter(creator=mySession.id).count()

        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')

        return render(request, 'members/myfollowers.html',
                      {'mySession': mySession, 'countSubscribers': countSubscribers,
                       'countFollowers': countFollowers, 'subscribers': subscribers, 'followers': followers,
                       'darktheme': darktheme, 'countNotifications': countNotifications, 'notifications': notifications})

    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def myprofile(request):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        userData = User.objects.get(username=request.user)
        profileData = models.Profile.objects.get(user_id=request.user.id)
        mySession = User.objects.get(username=request.user)
        feedPosts = models.FeedUser.objects.all().order_by('-created_at')
        comments = models.CommentPost.objects.all().order_by('-date_interaction')
        countFreePosts = models.FeedUser.objects.filter(media_free=True, profile_creator=profileData,
                                                        post_deleted=False).count()
        countPremiumPosts = models.FeedUser.objects.filter(media_premium=True, profile_creator=profileData,
                                                           post_deleted=False).count()
        countImagePosts = models.FeedUser.objects.filter(media_type='IMAGE', profile_creator=profileData,
                                                         post_hidden=False, post_deleted=False).count()
        countVideoPosts = models.FeedUser.objects.filter(media_type='VIDEO', profile_creator=profileData,
                                                         post_hidden=False, post_deleted=False).count()
        countSubscribers = models.Subscriber.objects.filter(creator=userData.id, suspended=False).count()

        likes = models.LikedPost.objects.all()
        liked_post_ids = [like.post.id for like in likes if like.profile_fan == mySession.profile]

        likes_comment = models.LikeInComment.objects.all()
        liked_comment_ids = [like_comment.comment.id for like_comment in likes_comment if
                             like_comment.user_profile == mySession.profile]

        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')

        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3
        return render(request, 'members/myprofile.html', {'userData': userData, 'profile': profileData,
                                                          'feed': feedPosts, 'comments': comments,
                                                          'liked_post_ids': liked_post_ids,
                                                          'mySession': mySession,
                                                          'liked_comment_ids': liked_comment_ids,
                                                          'countFreePosts': countFreePosts,
                                                          'countPremiumPosts': countPremiumPosts,
                                                          'countImages': countImagePosts,
                                                          'countVideos': countVideoPosts,
                                                          'countSubscribers': countSubscribers,
                                                          'countNotifications': countNotifications,
                                                          'notifications': notifications, 'darktheme': darktheme,
                                                          'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def editprofile(request):
    if request.user.is_authenticated:
        if request.POST:
            target = escape(request.POST['target'])
            extension = ''
            extensions_allowed = settings.ALLOWED_EXTENSIONS_IMAGES

            try:
                if target == 'bio':
                    newData = escape(request.POST['bio'])
                    EditProfile(target, newData, request.user, request.user.id)
                if target == 'name':
                    newData = {'first_name': escape(request.POST['first_name']),
                               'last_name': escape(request.POST['last_name'])}
                    EditProfile(target, newData, request.user, request.user.id)

                if target == 'avatar':
                    cropped_image_b64 = escape(request.POST['cropped_file_avatar'])
                    format, imgstr = cropped_image_b64.split(';base64,')
                    ext = format.split('/')[-1]
                    r1 = random.randint(2, 98)
                    cropped_image = ContentFile(base64.b64decode(imgstr), name='spicx' + str(r1) + '_.' + ext)
                    if cropped_image:
                        new_avatar_file = cropped_image
                    else:
                        new_avatar_file = escape(request.FILES['fileavatar'])

                    if new_avatar_file.size > settings.IMAGE_SIZE_LIMIT_AVATAR:
                        error = 'Limite excedido: Tamanho limite para avatar é 10Mb.'
                        return HttpResponseRedirect("/m/home/?status=error&info=" + error)
                    for namefile, extension in request.FILES.items():
                        namefile = new_avatar_file.name
                        extension = namefile.split('.')[1]

                    if extension in extensions_allowed:
                        # compress img to 50% quality
                        img_compress = Image.open(cropped_image)
                        output = io.BytesIO()
                        img_compress.save(output, format=str(extension), quality=50)
                        output.seek(0)
                        new_avatar_file = ContentFile(output.getvalue(), name=namefile)

                        newData = new_avatar_file
                        EditProfile(target, newData, request.user, request.user.id)

                if target == 'cover':
                    cropped_image_b64 = escape(request.POST['cropped_file_cover'])
                    format, imgstr = cropped_image_b64.split(';base64,')
                    ext = format.split('/')[-1]
                    r1 = random.randint(2, 98)
                    cropped_image = ContentFile(base64.b64decode(imgstr), name='spicx' + str(r1) + '_.' + ext)
                    if cropped_image:
                        new_cover_file = cropped_image
                    else:
                        new_cover_file = escape(request.FILES['filecover'])

                    if new_cover_file.size > settings.IMAGE_SIZE_LIMIT_COVER:
                        error = 'Limite excedido: Tamanho limite para capa é 10Mb.'
                        return HttpResponseRedirect("/m/home/?status=error&info=" + error)
                    for namefile, extension in request.FILES.items():
                        namefile = new_cover_file.name
                        extension = namefile.split('.')[1]

                    if extension in extensions_allowed:
                        # compress img to 60% quality
                        img_compress = Image.open(cropped_image)
                        output = io.BytesIO()
                        img_compress.save(output, format=str(extension), quality=60)
                        output.seek(0)
                        new_cover_file = ContentFile(output.getvalue(), name=namefile)

                        newData = new_cover_file
                        EditProfile(target, newData, request.user, request.user.id)
            except:
                err_msg = '?status=error&info=Algo de errado ocorreu ao editar perfil.'
                return HttpResponseRedirect('/m/me/' + err_msg)

        return HttpResponseRedirect('/m/me/')
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def mysettings(request):
    if request.user.is_authenticated:
        if request.POST:
            if settings.USE_RECAPTCHA_V3:
                recaptcha_response = request.POST.get('g-recaptcha-response')
                captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                               'response': recaptcha_response}
                req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
                result = req.json()
                if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                    pass
                else:
                    return HttpResponseRedirect("/m/logout/")

            action = escape(request.POST['action'])
            if action == 'darkmode':
                if 'darkmode' in request.POST:
                    dark = models.Profile.objects.get(user=request.user)
                    dark.dark_theme = True
                    dark.save()
                    return HttpResponseRedirect('/m/settings/?status=success&info=Dark mode on')
                else:
                    dark = models.Profile.objects.get(user=request.user)
                    dark.dark_theme = False
                    dark.save()
                    return HttpResponseRedirect('/m/settings/?status=success&info=Dark mode off')
            if action == 'gender':
                try:
                    newSex = escape(request.POST['sex'])
                    me = models.Profile.objects.get(user=request.user)
                    me.sex = newSex
                    me.save()
                    return HttpResponseRedirect('/m/settings/?status=success&info=Gênero atualizado.')
                except:
                    err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                    return HttpResponseRedirect('/m/settings/' + err_msg)
            if action == 'interest':
                try:
                    newInterest = escape(request.POST['interest'])
                    me = models.Profile.objects.get(user=request.user)
                    me.interest = newInterest
                    me.save()
                    return HttpResponseRedirect('/m/settings/?status=success&info=Preferência atualizada.')
                except:
                    err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                    return HttpResponseRedirect('/m/settings/' + err_msg)
            if action == 'birth':
                try:
                    newBirth = escape(request.POST['birth'])
                    me = models.Profile.objects.get(user=request.user)
                    me.birth = newBirth
                    me.save()
                    return HttpResponseRedirect('/m/settings/?status=success&info=Data de nascimento atualizada.')
                except:
                    err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                    return HttpResponseRedirect('/m/settings/' + err_msg)
            if action == 'updateproduct':
                try:
                    prod_creator_userID1 = escape(request.POST['creator_month'])
                    prod_creator_userID2 = escape(request.POST['creator_year'])
                    creatorProfile_session = models.Profile.objects.get(user_id=request.user.id)
                    newprice_month = escape(request.POST['newprice_month'])
                    newprice_month = float(newprice_month.replace(",", "."))
                    newprice_year = escape(request.POST['newprice_year'])
                    newprice_year = float(newprice_year.replace(",", "."))
                    prodID_month = escape(request.POST['prod_id_month'])
                    prodID_year = escape(request.POST['prod_id_year'])

                    if prod_creator_userID1 == prod_creator_userID2 and prod_creator_userID1 == str(request.user.id):
                        checkModifyMonth = models.Product.objects.filter(creator=creatorProfile_session,
                                                                         product_id=prodID_month,
                                                                         recurrence='month',
                                                                         value=newprice_month).exists()
                        checkModifyYear = models.Product.objects.filter(creator=creatorProfile_session,
                                                                        product_id=prodID_year,
                                                                        recurrence='year',
                                                                        value=newprice_year).exists()
                        if not checkModifyMonth:
                            updatePriceMonth = updateProduct(newprice_month, prodID_month)
                        else:
                            updateProdBDMonth = models.Product.objects.get(product_id=prodID_month)
                            updateProdBDMonth.updated_at = timezone.now()
                            updateProdBDMonth.save()
                        if not checkModifyYear:
                            updatePriceYear = updateProduct(newprice_year, prodID_year)
                        else:
                            updateProdBDYear = models.Product.objects.get(product_id=prodID_year)
                            updateProdBDYear.updated_at = timezone.now()
                            updateProdBDYear.save()

                        successmsg = '?status=success&info=Preços atualizados com sucesso.'
                        return HttpResponseRedirect('/m/settings/' + successmsg)
                    else:
                        err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                        return HttpResponseRedirect('/m/settings/' + err_msg)

                except Exception as e:
                    print(e)
                    err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                    return HttpResponseRedirect('/m/settings/' + err_msg)


        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        userData = User.objects.get(username=request.user)
        profileData = models.Profile.objects.get(user_id=request.user.id)
        mySession = User.objects.get(username=request.user)
        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')
        products = models.Product.objects.filter(creator=profileData)

        statusCreatorRequest = {}
        authUpdatePriceProducts = False
        try:
            statusCreatorRequest = models.CreatorsRequest.objects.get(profile_creator=request.user.profile)

            checkLastUpdateProduct = models.Product.objects.get(creator=profileData, recurrence='month').updated_at
            lastUpdate = datetime.fromisoformat(str(checkLastUpdateProduct))
            today = datetime.fromisoformat(str(timezone.now()))
            if (today - lastUpdate) > timedelta(days=30):
                authUpdatePriceProducts = True
        except:
            pass

        birth_origin = models.Profile.objects.get(user=request.user).birth
        birth = birth_origin.strftime('%Y-%m-%d')
        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3
        return render(request, 'members/mysettings.html', {'profile': profileData, 'mySession': mySession, 'darktheme': darktheme,
                                                           'countNotifications': countNotifications, 'notifications': notifications, 'birth': birth,
                                                           'statusCreatorRequest': statusCreatorRequest, 'products': products,
                                                           'authUpdatePriceProducts': authUpdatePriceProducts,
                                                           'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        HttpResponseRedirect('/')


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def userprofile(request, nickname):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        nickname = escape(nickname).replace("@", "")
        if nickname:
            try:
                profileData = models.Profile.objects.get(nickname=nickname)
                userData = User.objects.get(id=profileData.user_id)
                mySession = User.objects.get(username=request.user)
                feedPosts = models.FeedUser.objects.all().order_by('-created_at')
                comments = models.CommentPost.objects.all().order_by('-date_interaction')
                countImagePosts = models.FeedUser.objects.filter(media_type='IMAGE', profile_creator=profileData,
                                                                 post_hidden=False, post_deleted=False).count()
                countVideoPosts = models.FeedUser.objects.filter(media_type='VIDEO', profile_creator=profileData,
                                                                 post_hidden=False, post_deleted=False).count()
                countFreePosts = models.FeedUser.objects.filter(media_free=True, profile_creator=profileData,
                                                                post_hidden=False, post_deleted=False).count()
                countPremiumPosts = models.FeedUser.objects.filter(media_premium=True, profile_creator=profileData,
                                                                   post_hidden=False, post_deleted=False).count()
                countSubscribers = models.Subscriber.objects.filter(creator=profileData.user.id,
                                                                    suspended=False).count()
                subscriber = models.Subscriber.objects.filter(creator=profileData.user.id, subscriber=mySession.profile,
                                                              suspended=False).exists()
                follower = models.Follower.objects.filter(creator=profileData.user.id,
                                                          follower=mySession.profile).exists()

                likes = models.LikedPost.objects.all()
                liked_post_ids = [like.post.id for like in likes if like.profile_fan == mySession.profile]

                likes_comment = models.LikeInComment.objects.all()
                liked_comment_ids = [like_comment.comment.id for like_comment in likes_comment if
                                     like_comment.user_profile == mySession.profile]

                countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
                notifications = models.Notification.objects.all().order_by('-created_at')

                product = {}
                if profileData.user_creator:
                    try:
                        product = models.Product.objects.get(creator=profileData, recurrence='month', active=True)
                    except:
                        product = {}

                return render(request, 'members/profile.html', {'userData': userData, 'profile': profileData,
                                                                'feed': feedPosts, 'comments': comments,
                                                                'liked_post_ids': liked_post_ids,
                                                                'mySession': mySession,
                                                                'liked_comment_ids': liked_comment_ids,
                                                                'countImages': countImagePosts,
                                                                'countVideos': countVideoPosts,
                                                                'countFree': countFreePosts,
                                                                'countPremium': countPremiumPosts,
                                                                'subscriber': subscriber,
                                                                'countSubscribers': countSubscribers,
                                                                'countNotifications': countNotifications,
                                                                'notifications': notifications,
                                                                'follower': follower, 'darktheme': darktheme,
                                                                'product': product})
            except Exception as err:
                print(err)
                err_msg = '?status=error&info=Usuário não encontrado.'
                return HttpResponseRedirect("/m/home/" + err_msg)
        else:
            return HttpResponseRedirect("/m/home/")
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def onlyPost(request, nickname, id):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        nickname = escape(nickname).replace("@", "")
        mySession = User.objects.get(username=request.user)

        signatures = models.Subscriber.objects.all()
        subscribe = [sub.creator.id for sub in signatures if
                     sub.subscriber == mySession.profile and sub.suspended == False]

        followers = models.Follower.objects.all()
        follower = [follow.creator for follow in followers if follow.follower == mySession.profile]

        comments = models.CommentPost.objects.all().order_by('-date_interaction')

        likes = models.LikedPost.objects.all()
        liked_post_ids = [like.post.id for like in likes if like.profile_fan == mySession.profile]

        likes_comment = models.LikeInComment.objects.all()
        liked_comment_ids = [like_comment.comment.id for like_comment in likes_comment if
                             like_comment.user_profile == mySession.profile]

        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')

        if nickname and id:
            profile_creator = models.Profile.objects.get(nickname=nickname)
            post = models.FeedUser.objects.filter(profile_creator=profile_creator, id=escape(id))

            return render(request, 'members/post.html', {'found': post, 'subscribe': subscribe, 'mySession': mySession,
                                                         'comments': comments, 'liked_post_ids': liked_post_ids,
                                                         'liked_comment_ids': liked_comment_ids,
                                                         'countNotifications': countNotifications,
                                                         'notifications': notifications,
                                                         'follower': follower, 'darktheme': darktheme})
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='50/5m', block=True)
@csrf_protect
def followView(request):
    if request.user.is_authenticated:
        if request.POST:
            action = escape(request.POST['action'])
            creator = escape(request.POST['creator'])
            creator_nick = escape(request.POST['creator_nick'])
            my_profile = request.user.profile
            err_msg = ''

            if action == 'follow':
                try:
                    found = models.Follower.objects.filter(creator=creator, follower=my_profile).exists()
                except:
                    err_msg = '?status=error&info=Algo de errado ocorreu.'
                    return HttpResponseRedirect("/m/@" + creator_nick + err_msg)

                if not found:
                    try:
                        models.Follower.objects.create(creator=creator, follower=my_profile,
                                                       user_ip=request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR'))

                        link_to = f'/m/@' + my_profile.nickname
                        msg_to = 'Começou a te seguir.'
                        models.Notification.objects.create(profile_from=my_profile, profile_to=creator,
                                                           context_msg=msg_to, context_link=link_to)
                    except:
                        pass
                return HttpResponseRedirect('/m/@' + creator_nick + '?status=success&info=Seguindo.')

            if action == 'unfollow':
                try:
                    d = models.Follower.objects.get(creator=creator, follower=my_profile)
                    d.delete()

                    link_to = f'/m/@' + my_profile.nickname
                    msg_to = 'Deixou de te seguir.'
                    models.Notification.objects.create(profile_from=my_profile, profile_to=creator,
                                                       context_msg=msg_to, context_link=link_to)
                except:
                    err_msg = '?status=error&info=Algo de errado ocorreu ao deixar de seguir.'
                    return HttpResponseRedirect("/m/@" + creator_nick + err_msg)
                return HttpResponseRedirect('/m/@' + creator_nick + '?status=success&info=Deixado de seguir.')

        else:
            return HttpResponseRedirect("/m/explorer/")
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def desactiveSignatureFan(request):
    if request.user.is_authenticated:
        if request.POST:
            me = request.user.profile
            creator_id = escape(request.POST['creator'])
            creator_nick = escape(request.POST['creator_nick'])
            err_msg = ''

            try:
                search_exist_subscribe = models.Subscriber.objects.filter(creator=creator_id, subscriber=me,
                                                                          suspended=False).exists()
            except Exception as error:
                print(error)
                err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                return HttpResponseRedirect("/m/@" + creator_nick + err_msg)

            if search_exist_subscribe:
                try:
                    subFound = models.Subscriber.objects.get(creator=creator_id, subscriber=me, suspended=False)
                    cancel_sub = cancelSubscription(subFound.subscription_id)
                except Exception as err:
                    print(err)
                    err_msg = '?status=error&info=Algo deu errado, tente novamente mais tarde.'
                    return HttpResponseRedirect("/m/@" + creator_nick + err_msg)

                if escape(request.POST['page']):
                    returnTo = escape(request.POST['page'])
                    if returnTo == 'home':
                        return HttpResponseRedirect(
                            '/m/home/' + '?status=success&info=Assinatura desativada com sucesso.')
                    elif returnTo == 'explorer':
                        return HttpResponseRedirect(
                            '/m/explorer/' + '?status=success&info=Assinatura desativada com sucesso.')

                return HttpResponseRedirect(
                    "/m/@" + creator_nick + '?status=success&info=Assinatura desativada com sucesso.')

        return HttpResponseRedirect("/m/me/?status=error")

    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def loadMorePosts(request, start_index, origin):
    if request.user.is_authenticated:
        mySession = User.objects.get(username=request.user)
        userData = User.objects.all()
        profileData = models.Profile.objects.all()
        comments = models.CommentPost.objects.all().order_by('-date_interaction')

        likes = models.LikedPost.objects.all()
        liked_post_ids = [like.post.id for like in likes if like.profile_fan == mySession.profile]

        likes_comment = models.LikeInComment.objects.all()
        liked_comment_ids = [like_comment.comment.id for like_comment in likes_comment if
                             like_comment.user_profile == mySession.profile]

        start = int(escape(start_index))
        origin = escape(origin)
        feedPosts_q = {}

        signatures = models.Subscriber.objects.all()
        subscribe = [sub.creator.id for sub in signatures if
                     sub.subscriber == mySession.profile and sub.suspended == False]

        followers = models.Follower.objects.all()
        follower = [follow.creator for follow in followers if follow.follower == mySession.profile]

        query = (Q(profile_creator__user__id=mySession.id) |
                 (Q(profile_creator__user__id__in=follower) & Q(media_premium=False)) |
                 Q(profile_creator__user__id__in=subscribe)) & Q(post_hidden=False) & Q(post_deleted=False)

        if mySession.profile.interest == 'all':
            query2 = (Q(post_hidden=False) & Q(post_deleted=False) & Q(
                media_premium=False) & Q(media_free=True))
        else:
            query2 = (Q(profile_creator__sex=mySession.profile.interest) & Q(post_hidden=False) & Q(
                post_deleted=False) & Q(
                media_premium=False) & Q(media_free=True))

        limit_posts_count = len(list(models.FeedUser.objects.filter(query).values()[0:]))
        limit_posts_count_explorer = models.FeedUser.objects.filter(query2).count()

        limit = start + 25
        has_more = True
        try:
            if origin == 'home':
                if start >= limit_posts_count:
                    has_more = False
                    response = {'feed': [], 'has_more': has_more}
                    return JsonResponse(response)

                feedPosts_q = models.FeedUser.objects.filter(query).order_by('-media_relevance',
                                                                             '-created_at')[start:limit]

            elif origin == 'explorer':
                if start >= limit_posts_count_explorer:
                    has_more = False
                    response = {'feed': [], 'has_more': has_more}
                    return JsonResponse(response)

                feedPosts_q = models.FeedUser.objects.filter(query2).order_by('-media_relevance',
                                                                              '-created_at')[start:limit]

            html_post = render_to_string('members/post_structure.html', {'userData': userData,
                                                                         'profile': profileData, 'feed': feedPosts_q,
                                                                         'comments': comments, 'has_more': has_more,
                                                                         'liked_post_ids': liked_post_ids,
                                                                         'mySession': mySession,
                                                                         'liked_comment_ids': liked_comment_ids,
                                                                         'subscribe': subscribe,
                                                                         'follower': follower}, request=request)

            return HttpResponse(html_post, content_type='text/html')

        except Exception as err:
            print(err)
            return

    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def creatorRequestStart(request):
    if request.user.is_authenticated:
        if request.POST:
            user_id = escape(request.POST['userid'])
            if int(user_id) != request.user.id:
                return HttpResponseRedirect("/m/settings/?status=error&info=Algo deu errado.")

            for filea in ['doc_official', 'doc_address', 'selfie']:
                if filea not in request.FILES:
                    error = 'Carregue todos os arquivos solicitados.'
                    return HttpResponseRedirect("/m/settings/?status=error&info=" + error)

            doc_official = request.FILES['doc_official']
            doc_address = request.FILES['doc_address']
            doc_selfie = request.FILES['selfie']

            extension = ''
            extensions_allowed = settings.ALLOWED_DOCS_CREATORS_EXTENSIONS
            for sendfile in [doc_official, doc_address, doc_selfie]:
                for namefile, extension in request.FILES.items():
                    namefile = sendfile.name
                    extension = namefile.split('.')[1]

                    if extension not in extensions_allowed:
                        error = 'Extensão inválida.'
                        return HttpResponseRedirect("/m/settings/?status=error&info=" + error)

            for filec in [doc_official, doc_address, doc_selfie]:
                if filec.size > settings.DOCS_CREATORS_SIZE_LIMIT:
                    error = 'Limite excedido: Tamanho máximo para arquivos é 50Mb.'
                    return HttpResponseRedirect("/m/settings/?status=error&info=" + error)

            phone = escape(request.POST['phone'])
            full_name = escape(request.POST['full_name'])
            day = escape(request.POST['day'])
            month = escape(request.POST['month'])
            year = escape(request.POST['year'])
            address = escape(request.POST['full_address'])
            complement = escape(request.POST['line2'])
            city = escape(request.POST['city'])
            state = escape(request.POST['state'])
            cep = escape(request.POST['cep'])
            country = escape(request.POST['country'])
            ag = escape(request.POST['ag'])
            cc = escape(request.POST['cc'])
            value_month = escape(request.POST['plan_month'])
            value_year = escape(request.POST['plan_year'])
            bankname = escape(request.POST['bankname'])
            user_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR')
            political_exposure = escape(request.POST['political'])
            old_cpf = escape(request.POST['cpf'])
            cpf = old_cpf.replace(".", "").replace("-", "")
            limit_attemps = 3

            try:
                checkLastCreatorRequest = models.CreatorsRequest.objects.filter(profile_creator=request.user.profile).exists()
                if not checkLastCreatorRequest:
                    models.CreatorsRequest.objects.create(profile_creator=request.user.profile,
                                                          attempts=+1,
                                                          user_ip=user_ip,
                                                          cpf=cpf,
                                                          political_exposure=political_exposure,
                                                          doc_official_file=doc_official,
                                                          doc_address_file=doc_address,
                                                          doc_selfie_file=doc_selfie,
                                                          full_name=full_name,
                                                          birth_day=day,
                                                          birth_month=month,
                                                          birth_year=year,
                                                          phone=phone,
                                                          full_address=address,
                                                          complement=complement,
                                                          city=city,
                                                          state=state,
                                                          cep_address=cep,
                                                          country=country,
                                                          bank_agency=ag,
                                                          bank_account=cc,
                                                          bank=bankname,
                                                          value_month=value_month,
                                                          value_year=value_year)
                else:
                    updateCreatorRequest = models.CreatorsRequest.objects.get(profile_creator=request.user.profile)
                    if updateCreatorRequest.attempts >= limit_attemps:
                        return HttpResponseRedirect("/m/settings/")
                    else:
                        updateCreatorRequest.attempts += 1
                        updateCreatorRequest.status = 'pending'
                        updateCreatorRequest.user_ip = user_ip
                        updateCreatorRequest.cpf = cpf
                        updateCreatorRequest.political_exposure = political_exposure
                        updateCreatorRequest.doc_official_file = doc_official
                        updateCreatorRequest.doc_address_file = doc_address
                        updateCreatorRequest.doc_selfie_file = doc_selfie
                        updateCreatorRequest.full_name = full_name
                        updateCreatorRequest.birth_day = day
                        updateCreatorRequest.birth_month = month
                        updateCreatorRequest.birth_year = year
                        updateCreatorRequest.phone = phone
                        updateCreatorRequest.full_address = address
                        updateCreatorRequest.complement = complement
                        updateCreatorRequest.city = city
                        updateCreatorRequest.state = state
                        updateCreatorRequest.cep_address = cep
                        updateCreatorRequest.country = country
                        updateCreatorRequest.bank_agency = ag
                        updateCreatorRequest.bank_account = cc
                        updateCreatorRequest.bank = bankname
                        updateCreatorRequest.value_month = value_month
                        updateCreatorRequest.value_year = value_year
                        updateCreatorRequest.save()

                return HttpResponseRedirect("/m/settings/")
            except Exception as e:
                print('Error in CreatorsRequest: ' + str(e))
            return HttpResponseRedirect("/m/settings/")

        else:
            return HttpResponseRedirect("/m/settings/")

    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='100/5m', block=True)
@csrf_protect
def stripeCheckoutView(request, nickname):
    if request.user.is_authenticated:
        if request.method == 'POST':
            creator = escape(request.POST['creator'])
            fan = escape(request.POST['fan'])
            plan = escape(request.POST['plan'])
            try:
                creator_profile = models.Profile.objects.get(nickname=creator)
                fan_profile = models.Profile.objects.get(nickname=fan)
                get_prod_id = models.Product.objects.get(creator=creator_profile, recurrence=plan, active=True)
                newSignature = createRecurringSignature(get_prod_id.product_id, creator_profile.user.id, request.user.id)

                url = "/m/@" + creator + '/checkout/?status=success&info=Fatura criada com sucesso.'
                return HttpResponseRedirect(url)

            except Exception as e:
                print('Error in checkout view: ' + str(e))
                return HttpResponseRedirect("/m/@" + creator)

        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        nickname = escape(nickname).replace("@", "")
        if nickname:
            try:
                profileData = models.Profile.objects.get(nickname=nickname)
                if not profileData.user_creator:
                    return HttpResponseRedirect("/m/@" + str(nickname) + '?status=error&info=Usuário não é um criador '
                                                                         'de conteúdos.')
                userData = User.objects.get(id=profileData.user_id)
                mySession = User.objects.get(username=request.user)
                countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
                notifications = models.Notification.objects.all().order_by('-created_at')
                product = models.Product.objects.filter(creator=profileData, active=True)

                currentInvoice = {}
                checkInvoiceExist = models.Invoice.objects.filter(creator=profileData.user.id, fan=request.user.profile, status='pending').exists()
                if checkInvoiceExist:
                    currentInvoice = models.Invoice.objects.get(creator=profileData.user.id, fan=request.user.profile, status='pending')

                subscriber = {}
                subscribeExist = models.Subscriber.objects.filter(creator=profileData.user.id, subscriber=request.user.profile, suspended=False).exists()
                if subscribeExist:
                    subscriber = models.Subscriber.objects.get(creator=profileData.user.id, subscriber=request.user.profile, suspended=False)

                return render(request, 'members/payments/checkout.html',
                              {'userData': userData, 'profile': profileData,
                               'countNotifications': countNotifications, 'notifications': notifications,
                               'darktheme': darktheme, 'mySession': mySession,
                               'product': product, 'currentInvoice': currentInvoice,
                               'subscriber': subscriber})

            except Exception as err:
                print('Error in stripeCheckoutView: ' + str(err))
                return HttpResponseRedirect("/m/@" + str(nickname))

        else:
            return HttpResponseRedirect("/m/home/")
    else:
        return HttpResponseRedirect("/")


@csrf_exempt
def webhooks(request):
    if request.method == 'POST':
        # Check authorized ips
        whitelist_ips_webhooks = [
            '3.18.12.63', '3.130.192.231',
            '13.235.14.237', '13.235.122.149',
            '18.211.135.69', '35.154.171.200',
            '52.15.183.38', '54.88.130.119',
            '54.88.130.237', '54.187.174.169',
            '54.187.205.235', '54.187.216.72',
        ]
        if request.META['REMOTE_ADDR'] not in whitelist_ips_webhooks:
            return HttpResponse(status=403)

        event = None
        payload = request.body
        sig_header = request.headers['Stripe-Signature']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
            data = event['data']
        except ValueError as e:
            print('ValueError in stripeWebhook: ' + str(e))
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            print('SignatureVerificationError in stripeWebhook: ' + str(e))
            return HttpResponse(status=401)

        event_type = event['type']
        webhook_full = json.loads(request.body)
        if event_type == 'checkout.session.completed':
            print('Payment Success')
        elif event_type == 'invoice.payment_succeeded':
            print('Payment Success')
            webhookReceived(webhook_full, data['object'], event_type)
        elif event_type == 'customer.subscription.created':
            print('Subscription Created')
        elif event_type == 'customer.subscription.updated':
            print('Subscription updated')
            webhookReceived(webhook_full, data['object'], event_type)
        elif event_type == 'customer.subscription.deleted':
            print('Subscription canceled')
            webhookReceived(webhook_full, data['object'], event_type)
        elif event_type == 'product.created':
            print('Product created')
            webhookReceived(webhook_full, data['object'], event_type)
        elif event_type == 'charge.refunded':
            print('Charge refunded')
            webhookReceived(webhook_full, data['object'], event_type)
        elif event_type == 'invoice.created':
            print('New invoice created')
            webhookReceived(webhook_full, data['object'], event_type)
        elif event_type == 'charge.dispute.created':
            print('New dispute/chargeback created')
            webhookReceived(webhook_full, data['object'], event_type)
        else:
            print('Webhook unknown: ' + str(event_type))
            saveWebhookBD(event_type, webhook_full)

        return HttpResponse(status=200)

    else:
        return HttpResponse(status=401)


def financesView(request):
    if request.user.is_authenticated:
        darktheme = models.Profile.objects.get(user=request.user).dark_theme
        userData = User.objects.get(username=request.user)
        profileData = models.Profile.objects.get(user_id=request.user.id)
        mySession = User.objects.get(username=request.user)
        countNotifications = models.Notification.objects.filter(profile_to=mySession.id, viewed=False).count()
        notifications = models.Notification.objects.all().order_by('-created_at')
        invoices = models.Invoice.objects.filter(fan=profileData).order_by('-created_at')
        payouts = models.Payout.objects.filter(creator=profileData, status='success').order_by('-created_at')

        subscriptions = models.Subscriber.objects.filter(
            subscriber=profileData, suspended=False).order_by('-created_at')

        disputes = models.DisputeChargeback.objects.filter(creator=userData)
        refunds = models.Invoice.objects.filter(creator=userData, status='refunded')

        return render(request, "members/finances.html",
                      {'profile': profileData, 'mySession': mySession, 'darktheme': darktheme,
                       'countNotifications': countNotifications, 'notifications': notifications,
                       'invoices': invoices, 'subscriptions': subscriptions, 'payouts': payouts,
                       'disputes': disputes, 'refunds': refunds})
    else:
        return HttpResponseRedirect("/")


def adminPayouts(request):
    if request.user.is_staff and request.user.is_authenticated:
        # if request.method == 'POST':
        #     payouts = createPayout()
        #     return HttpResponseRedirect(
        #         '/7j3k2b9QVYQf4XNg89qAthG/painel/payouts/?status=success&info=Saques efetuados.')

        if request.method == 'POST':
            recaptcha_response = request.POST.get('g-recaptcha-response')
            captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                           'response': recaptcha_response}
            req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
            result = req.json()
            if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                pass
            else:
                return HttpResponseRedirect("/m/logout/")

        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3
        return render(request, 'painel/payouts.html', {'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})

    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='25/5m', block=True)
@csrf_protect
def adminDocumentation(request):
    if request.user.is_staff and request.user.is_authenticated:
        if request.method == 'POST':
            recaptcha_response = request.POST.get('g-recaptcha-response')
            captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                           'response': recaptcha_response}
            req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
            result = req.json()
            if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                pass
            else:
                return HttpResponseRedirect("/m/logout/")

            if 'new_urls' in request.POST:
                if escape(request.POST['new_urls']) == 'generate':
                    docs_generateNewsPresignedUrls()
                    return HttpResponseRedirect(
                        '/7j3k2b9QVYQf4XNg89qAthG/painel/docs/?filter=pending&status=success&info=URLs geradas.')

            if 'actiondocreview' in request.POST:
                status = escape(request.POST['status'])
                creatorID = escape(request.POST['creatorID'])
                if status == '' or creatorID == '':
                    return HttpResponseRedirect(
                        '/7j3k2b9QVYQf4XNg89qAthG/painel/docs/?filter=pending&status=error&info=Informações faltantes.')

                creatorProfile = models.User.objects.get(id=creatorID).profile

                checkStatus = models.CreatorsRequest.objects.get(profile_creator=creatorProfile)
                if status == checkStatus.status:
                    return HttpResponseRedirect(
                        '/7j3k2b9QVYQf4XNg89qAthG/painel/docs/?filter=pending&status=error&info=Documentação já está nesta situação.')

                if status == 'approved':
                    verifyUser = CheckVerifyUser(request.user.profile)

                    if verifyUser['status'] == 'success':
                        p_nick = str(request.user.profile.nickname)
                        req_prod_data = models.CreatorsRequest.objects.get(profile_creator=creatorProfile)
                        product_name = '@' + p_nick + '_plan_month'
                        product_name_year = '@' + p_nick + '_plan_year'
                        newProduct = createProduct(product_name, float(req_prod_data.value_month),
                                                   'Assinatura de conteúdo premium de @' + p_nick, request.user.profile,
                                                   product_name_year, float(req_prod_data.value_year))

                        if newProduct['status'] == 'success':
                            approveDoc = ApproveDocumentation(request.user.profile)
                            return HttpResponseRedirect(
                                '/7j3k2b9QVYQf4XNg89qAthG/painel/docs/?filter=pending&status=success&info=Documentação aprovada.')

                if status == 'refused':
                    req_creator_data = models.CreatorsRequest.objects.get(profile_creator=creatorProfile)
                    req_creator_data.status = 'refused'
                    req_creator_data.save()
                    return HttpResponseRedirect(
                        '/7j3k2b9QVYQf4XNg89qAthG/painel/docs/?filter=pending&status=success&info=Documentação recusada.')

        documentations = models.CreatorsRequest.objects.all()
        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3

        return render(request, 'painel/documentation.html', {'documentations': documentations,
                                                             'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return HttpResponseRedirect("/")
    

@ratelimit(key='ip', rate='25/5m', block=True)
@csrf_protect
def adminProducts(request):
    if request.user.is_staff and request.user.is_authenticated:
        if request.method == 'POST':
            recaptcha_response = request.POST.get('g-recaptcha-response')
            captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                           'response': recaptcha_response}
            req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
            result = req.json()
            if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                pass
            else:
                return HttpResponseRedirect("/m/logout/")

            prodID = escape(request.POST['prod_id'])
            newValue = escape(request.POST['new_value'])
            newValue = float(newValue.replace(",", "."))

            try:
                getProductBD = models.Product.objects.get(product_id=prodID)
                update_Product = updateProduct(newValue, getProductBD.product_id)
                return HttpResponseRedirect(
                    '/7j3k2b9QVYQf4XNg89qAthG/painel/products/?status=success&info=Preço atualizado.')
            except:
                return HttpResponseRedirect(
                    '/7j3k2b9QVYQf4XNg89qAthG/painel/products/?status=error&info=Algo deu errado ao atualizar preço.')

        products = models.Product.objects.all()
        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3

        return render(request, 'painel/products.html', {'products': products,
                                                        'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return HttpResponseRedirect("/")


@ratelimit(key='ip', rate='25/5m', block=True)
@csrf_protect
def adminNotifications(request):
    if request.user.is_staff and request.user.is_authenticated:
        if request.method == 'POST':
            recaptcha_response = request.POST.get('g-recaptcha-response')
            captchaData = {'secret': settings.RECAPTCHA_PRIVATE_KEY_V3,
                           'response': recaptcha_response}
            req = requests.post('https://www.google.com/recaptcha/api/siteverify', data=captchaData)
            result = req.json()
            if result['success'] and float(result['score']) >= settings.RECAPTCHA_ALLOWED_SCORE:
                pass
            else:
                return HttpResponseRedirect("/m/logout/")

            if 'action_notification' in request.POST:
                select_target = escape(request.POST['select_target_notify'])
                notification_message = escape(request.POST['text_notify'])
                link_to = '/m/@equipespicyx'
                profile_spicyx = models.Profile.objects.get(nickname='equipespicyx')
                if select_target == 'all':
                    all_users_profiles = models.Profile.objects.all()
                    notify_fails = 0
                    for profile in all_users_profiles:
                        try:
                            models.Notification.objects.create(
                                profile_from=profile_spicyx,
                                profile_to=profile.user.id,
                                context_msg=notification_message,
                                context_link=link_to
                            )
                            return HttpResponseRedirect(
                                '/7j3k2b9QVYQf4XNg89qAthG/painel/notifications/?status=success&info=Notificações '
                                'enviadas. Falhas: ' + str(notify_fails))
                        except Exception as e:
                            notify_fails += 1
                            pass
                else:
                    only_user_target = escape(request.POST['specify_user'])
                    print(only_user_target)
                    profile_to = models.Profile.objects.get(nickname=only_user_target)
                    try:
                        models.Notification.objects.create(
                            profile_from=profile_spicyx,
                            profile_to=profile_to.user.id,
                            context_msg=notification_message,
                            context_link=link_to
                        )
                        return HttpResponseRedirect(
                            '/7j3k2b9QVYQf4XNg89qAthG/painel/notifications/?status=success&info=Notificação enviada.')
                    except Exception as err:
                        return HttpResponseRedirect(
                            '/7j3k2b9QVYQf4XNg89qAthG/painel/notifications/?status=error&info=Não foi possível enviar '
                            'notificação para o usuário informado.')

        GOOGLE_RECAPTCHA_SITE_KEY = settings.RECAPTCHA_PUBLIC_KEY_V3
        return render(request, 'painel/send_notification.html', {'recaptcha_site_key': GOOGLE_RECAPTCHA_SITE_KEY})
    else:
        return HttpResponseRedirect("/")

