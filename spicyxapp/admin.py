from django.contrib import admin

from spicyxapp import models

admin.site.register(models.Profile)
admin.site.register(models.FeedUser)
admin.site.register(models.LikedPost)
admin.site.register(models.CommentPost)
admin.site.register(models.LikeInComment)
admin.site.register(models.Subscriber)
admin.site.register(models.Notification)
admin.site.register(models.Follower)
admin.site.register(models.Product)
admin.site.register(models.CreatorsRequest)
admin.site.register(models.Invoice)
admin.site.register(models.Webhook)
admin.site.register(models.TransferToConnectAccount)
admin.site.register(models.Payout)
admin.site.register(models.DisputeChargeback)
admin.site.register(models.HttpError)
