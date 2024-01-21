from spicyxapp import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
from datetime import date
from django.conf import settings
import boto3
from botocore.client import Config
from django.utils.html import escape
import re


def Check_force_password(email, password, fullname):
    fullname = fullname.lower().replace(" ", "")
    password = str(password)
    special_chars = ['#', '!', '$', '%', '*', '&', '-', '_', '(', ')']
    pass_contains_special_chars = False
    for i in special_chars:
        if i in password:
            pass_contains_special_chars = True
            break

    mynumbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    pass_contains_numbers = False
    for n in mynumbers:
        if n in password:
            pass_contains_numbers = True
            break

    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
                'V', 'W', 'X', 'Y', 'Z', 'Á', 'Â', 'Ã', 'À', 'É', 'Ê', 'Í', 'Ó', 'Ô', 'Õ', 'Ú', 'Ç']
    pass_upercase_letters = False
    for l in alphabet:
        if l in password:
            pass_upercase_letters = True
            break

    pass_min_length = False
    if int(len(password)) >= 6:
        pass_min_length = True

    pass_contains_fullname = False
    if password not in fullname:
        pass_contains_fullname = True

    pass_contains_email = False
    if password not in email:
        pass_contains_email = True

    if (pass_contains_special_chars and pass_contains_numbers and pass_upercase_letters and
            pass_min_length and pass_contains_fullname and pass_contains_email):
        return True
    else:
        return False


def Post_create_profile_link(subtitles):
    if subtitles != '':
        # check user exist
        users_found = re.findall(r'@[A-Za-z0-9_-]+', subtitles)
        users_exist = []
        try:
            for user in users_found:
                nickname = escape(user).replace("@", "")
                user_exist = models.Profile.objects.filter(nickname=nickname).exists()
                if user_exist:
                    users_exist.append(user)
        except Exception as e:
            print('Error in search user post. ' + str(e))
            pass

        # replace exists user found for profile link
        new_subtitle = subtitles
        try:
            for i in list(set(users_exist[:])):
                nickname = escape(i).replace("@", "")
                pattern = r'\B' + str(i) + r'\b'
                profile_link = '<a href="/m/@' + nickname + '" target="_blank">' + i + '</a>'
                new_subtitle = re.sub(pattern, profile_link, new_subtitle)
        except Exception as err:
            print('Error in replace @user for a profile. ' + str(err))
            pass

        return new_subtitle


def CheckVerifyUser(profile):
    try:
        v = models.Profile.objects.get(user_id=profile.user.id)
        v.user_verified = True
        v.user_creator = True
        v.last_update_account = timezone.now()
        v.save()
    except Exception as e:
        print('Error on verify user: ' + str(e))
        return None
    return {'status': 'success'}


def ApproveDocumentation(profile):
    try:
        doc = models.CreatorsRequest.objects.get(profile_creator=profile)
        doc.status = 'approved'
        doc.updated_at = timezone.now()
        doc.save()
    except Exception as e:
        print('Error on approve documentation: ' + str(e))
        return None
    return {'status': 'success'}


def addFanSignature(creator_user_id, fa_profile):
    try:
        s = models.Subscriber.objects.create(creator=creator_user_id,
                                             subscriber=fa_profile)
    except Exception as e:
        print('Error on add fan signature: ' + str(e))
        return None
    return {'status': 'success'}


def EditProfile(target, newData, user, userId):
    try:
        if target == 'cover':
            bucket_name = settings.BUCKET_NAME
            t = models.Profile.objects.get(user_id=userId)
            t.profile_cover_file = newData
            t.last_update_account = timezone.now()
            t.save()
            create_URL_temp = createPresignedUrl(bucket_name, str(t.profile_cover_file))
            if create_URL_temp:
                n_cov = models.Profile.objects.get(user_id=userId)
                n_cov.profile_cover = create_URL_temp
                n_cov.save()

        elif target == 'avatar':

            bucket_name = settings.BUCKET_NAME
            t = models.Profile.objects.get(user_id=userId)
            t.profile_avatar_file = newData
            t.last_update_account = timezone.now()
            t.save()
            create_URL_temp = createPresignedUrl(bucket_name, str(t.profile_avatar_file))
            if create_URL_temp:
                n_ava = models.Profile.objects.get(user_id=userId)
                n_ava.profile_avatar = create_URL_temp
                n_ava.save()

        elif target == 'name':
            t = User.objects.get(username=user)
            t.first_name = newData['first_name']
            t.last_name = newData['last_name']
            p = models.Profile.objects.get(user_id=userId)
            p.last_update_account = timezone.now()
            t.save()
            p.save()

        elif target == 'bio':
            t = models.Profile.objects.get(user_id=userId)
            t.profile_bio = newData
            t.last_update_account = timezone.now()
            t.save()
        else:
            status = False
            return status
    except:
        status = False
        return status

    status = True
    return status


def createPresignedUrl(bucket_name, object_name, expiration=86400):
    s3Client = boto3.client(
        's3',
        config=Config(signature_version='s3v4'),
        region_name='us-east-2',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    try:
        response = s3Client.generate_presigned_url("get_object", Params={'Bucket': bucket_name,
                                                                         'Key': object_name},
                                                   ExpiresIn=expiration)
    except Exception as err:
        print('Error in Create Presigned URL.')
        print(err)
        return None
    return response


def generateNewsPresignedUrls():
    posts_image = models.FeedUser.objects.filter(media_type='IMAGE', post_deleted=False)
    today = date.today()
    bucket_name = settings.BUCKET_NAME
    for post in posts_image:
        date_format = datetime.fromisoformat(str(post.updated_at))
        date_formated = date_format.date()
        if date_formated != today:
            try:
                newPresignedUrl = createPresignedUrl(bucket_name, str(post.file))
                if newPresignedUrl:
                    b = models.FeedUser.objects.get(file=post.file)
                    b.media_url = newPresignedUrl
                    b.updated_at = timezone.now()
                    b.save()
            except:
                print('Erro ao atualizar URL de post ID: ' + post.id)
                pass
    return


def generateNewsPresignedUrlsForProfiles():
    profiles = models.Profile.objects.all()
    today = date.today()
    bucket_name = settings.BUCKET_NAME
    for profile in profiles:
        date_format = datetime.fromisoformat(str(profile.last_update_account))
        date_formated = date_format.date()
        if date_formated != today:
            try:
                newPresignedUrlAvatar = createPresignedUrl(bucket_name, str(profile.profile_avatar_file))
                newPresignedUrlCover = createPresignedUrl(bucket_name, str(profile.profile_cover_file))
                if newPresignedUrlAvatar and newPresignedUrlCover:
                    b = models.Profile.objects.get(profile_avatar_file=profile.profile_avatar_file, profile_cover_file=profile.profile_cover_file)
                    b.profile_avatar = newPresignedUrlAvatar
                    b.profile_cover = newPresignedUrlCover
                    b.save()
            except:
                print('Erro ao atualizar perfil nickname: ' + profile.nickname)
                pass
    return


def checkUploadVideoLimite(userProfile, upload_limit):
    if userProfile.user_creator == True:
        return True
    else:
        fan_limite = upload_limit
        user_uploads = models.FeedUser.objects.filter(profile_creator=userProfile, media_type='VIDEO', post_deleted=False).count()
        if user_uploads <= fan_limite - 1:
            return True
        else:
            return False


def checkUploadImageLimite(userProfile, upload_limit):
    if userProfile.user_creator == True:
        return True
    else:
        fan_limite = upload_limit
        user_uploads = models.FeedUser.objects.filter(profile_creator=userProfile, media_type='IMAGE', post_deleted=False).count()
        if user_uploads <= fan_limite - 1:
            return True
        else:
            return False