from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.utils.formats import number_format


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=15, unique=True, db_column='nickname')
    birth = models.DateField()
    sex = models.CharField(max_length=7)
    interest = models.CharField(max_length=7)
    agree_terms = models.BooleanField(default=True)
    last_update_account = models.DateTimeField(default=timezone.now)
    profile_bio = models.TextField(max_length=256, blank=True)
    profile_cover = models.CharField(max_length=450, blank=True)
    profile_cover_file = models.FileField(blank=True, upload_to='static')
    profile_avatar = models.CharField(max_length=450, blank=True)
    profile_avatar_file = models.FileField(default='default.png', upload_to='static')
    user_verified = models.BooleanField(default=False)
    user_creator = models.BooleanField(default=False)
    folder_videos = models.CharField(max_length=50, blank=True)
    folder_videos_id = models.CharField(max_length=100, blank=True)
    customer_id = models.CharField(max_length=100, blank=True)
    account_connect_id = models.CharField(max_length=100, blank=True)
    dark_theme = models.BooleanField(default=False)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    suspended = models.BooleanField(default=False, db_column='suspended')

    def __str__(self):
        s = 'USER_ID:' + str(self.user_id) + ' - NICKNAME:' + str(self.nickname)
        return s


class CreatorsRequest(models.Model):
    profile_creator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    doc_official_file = models.FileField(upload_to='static/documentation/')
    doc_official_url = models.URLField(max_length=600, blank=True)
    doc_official_file_front_id = models.CharField(max_length=100, blank=True)
    doc_official_file_back_id = models.CharField(max_length=100, blank=True)
    doc_address_file = models.FileField(upload_to='static/documentation/')
    doc_address_url = models.URLField(max_length=600, blank=True)
    doc_selfie_file = models.FileField(upload_to='static/documentation/')
    doc_selfie_url = models.URLField(max_length=600, blank=True)
    cpf = models.CharField(max_length=11)
    full_name = models.CharField(max_length=75)
    birth_day = models.IntegerField()
    birth_month = models.IntegerField()
    birth_year = models.IntegerField()
    phone = models.CharField(max_length=15)
    full_address = models.CharField(max_length=100)
    complement = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    cep_address = models.CharField(max_length=10)
    country = models.CharField(max_length=5, default='BR')
    bank_agency = models.CharField(default=0, max_length=5)
    bank_account = models.CharField(default=0, max_length=15)
    bank = models.CharField(max_length=10, default=0)
    value_month = models.FloatField(default=0)
    value_year = models.FloatField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    details = models.TextField(max_length=256, blank=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    political_exposure = models.CharField(max_length=4, default='no')
    attempts = models.IntegerField(default=0)
    status = models.CharField(max_length=10, default='pending')

    def __str__(self):
        s = (str(self.updated_at) + ' - CREATOR_NICK:' + str(self.profile_creator.nickname)
             + ' - STATUS: ' + str(self.status))
        return s


class FeedUser(models.Model):
    profile_creator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now, blank=True)
    media_url = models.CharField(max_length=600, blank=True)
    file = models.FileField(default='default.png', upload_to='post_users')
    subtitles = models.TextField(max_length=400, blank=True)
    media_free = models.BooleanField(default=True)
    media_premium = models.BooleanField(default=False)
    media_relevance = models.IntegerField(default=1)
    media_type = models.CharField(max_length=8, default='IMAGE')
    video_id = models.CharField(max_length=100, blank=True)
    post_hidden = models.BooleanField(default=False)
    post_deleted = models.BooleanField(default=False)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = 'POST_ID:' + str(self.id) + ' - USER_ID:' + str(self.profile_creator.user.id) + ' - CREATED:' + str(self.created_at) + ' - RELEVANCE:' + str(self.media_relevance) + ' - TYPE:' + str(self.media_type)
        return s


class CommentPost(models.Model):
    post = models.ForeignKey(FeedUser, on_delete=models.CASCADE)
    profile_creator = models.IntegerField()
    profile_fan = models.ForeignKey(Profile, on_delete=models.CASCADE)
    fan_nickname = models.CharField(max_length=15)
    date_interaction = models.DateTimeField(default=timezone.now)
    fan_comment = models.TextField(max_length=400)
    comment_deleted = models.BooleanField(default=False)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = 'POST_ID:' + str(self.post.id) + ' - FAN_NICK:' + str(self.fan_nickname) + ' COMMENT:' + str(self.fan_comment)
        return s


class LikedPost(models.Model):
    post = models.ForeignKey(FeedUser, on_delete=models.CASCADE)
    profile_creator = models.IntegerField()
    profile_fan = models.ForeignKey(Profile, on_delete=models.CASCADE)
    fan_nickname = models.CharField(max_length=15)
    date_interaction = models.DateTimeField(default=timezone.now)
    updated_interaction = models.DateTimeField(default=timezone.now)
    fan_liked = models.BooleanField(default=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = 'USER_ID:' + str(self.profile_fan.user.id) + ' - NICKNAME:' + str(self.fan_nickname)
        return s


class LikeInComment(models.Model):
    comment = models.ForeignKey(CommentPost, on_delete=models.CASCADE)
    post = models.ForeignKey(FeedUser, on_delete=models.CASCADE)
    user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    user_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = 'COMMENT_ID:' + str(self.comment.id) + ' - POST_ID:' + str(self.post.id) + ' - CREATED:' + str(self.created_at)
        return s


class Product(models.Model):
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    product_id = models.CharField(max_length=100)
    value = models.FloatField()
    recurrence = models.CharField(default='month', max_length=5)
    active = models.BooleanField(default=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = (str(self.updated_at) + ' - CREATOR: '
             + str(self.creator.nickname) + ' - ' + str(self.recurrence) + ' - ' + str(self.active))
        return s


class Subscriber(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    subscription_id = models.CharField(max_length=100)
    suspended = models.BooleanField(default=False)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = (str(self.created_at) + ' - SUB:' + str(self.subscriber.nickname)
             + ' - CREATOR ID:' + str(self.creator) + ' - SUSPENDED:' + str(self.suspended))
        return s


class Invoice(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    fan = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    subscription_id = models.CharField(max_length=100)
    invoice_id = models.CharField(max_length=100)
    invoice_url = models.URLField()
    charge_id = models.CharField(max_length=100, blank=True)
    value = models.FloatField()
    status = models.CharField(max_length=10)

    def __str__(self):
        s = (str(self.created_at) + ' - CREATOR_ID:' + str(self.creator)
             + ' - FAN:' + str(self.fan.nickname) + ' : ' + str(self.status))
        return s


class TransferToConnectAccount(models.Model):
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    account_connect_id = models.CharField(max_length=100, blank=True)
    invoice_id = models.CharField(max_length=100)
    value = models.FloatField()
    status = models.CharField(max_length=10)
    transfer_stripe_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        s = str(self.transfer_stripe_id) + ' - R$ ' + str(self.value) + ' - ' + str(self.created_at)
        return s


class DisputeChargeback(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    dispute_id = models.CharField(max_length=100)
    charge_id = models.CharField(max_length=100)
    value = models.FloatField()
    currency = models.CharField(max_length=5, default='BRL')
    reason = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=25)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        s = str(self.dispute_id) + ' - R$ ' + str(self.value) + ' - ' + str(self.status)
        return s



class Payout(models.Model):
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    account_connect_id = models.CharField(max_length=100, blank=True)
    invoices_ids = models.TextField()
    total_amount_payout = models.FloatField()
    status = models.CharField(max_length=10)
    details = models.TextField(blank=True)
    payout_id = models.CharField(blank=True, max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        s = (str(self.payout_id) + ' - R$ ' + str(self.total_amount_payout)
             + ' - ' + str(self.status) + ' | ' + str(self.created_at))
        return s

class Webhook(models.Model):
    received_at = models.DateTimeField(default=timezone.now)
    webhook_type = models.CharField(max_length=25)
    webhook = models.TextField()

    def __str__(self):
        s = str(self.received_at) + ' - ' + str(self.webhook_type)
        return s


class Follower(models.Model):
    creator = models.IntegerField(default=0)
    follower = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        s = str(self.created_at) + ' - FOLLOWER:' + str(self.follower.nickname) + ' - CREATOR ID:' + str(self.creator)
        return s


class Notification(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    profile_from = models.ForeignKey(Profile, on_delete=models.CASCADE)
    profile_to = models.IntegerField()
    viewed = models.BooleanField(default=False)
    context_msg = models.CharField(max_length=100, blank=True)
    context_link = models.CharField(max_length=100, blank=True)

    def __str__(self):
        s = str(self.created_at) + '| FROM:' + str(self.profile_from) + ' > TO:' + str(self.profile_to) + ' - VIEWED: ' + str(self.viewed)
        return s