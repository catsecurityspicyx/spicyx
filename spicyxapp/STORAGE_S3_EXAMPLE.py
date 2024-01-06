from storages.backends.s3boto3 import S3Boto3Storage


class StaticBucket(S3Boto3Storage):
    location = ''
    default_acl = ''
    file_overwrite = ''
    bucket_name = ''
    region_name = ''


class PrivateBucket(S3Boto3Storage):
    default_acl = ''
    file_overwrite = ''
    bucket_name = ''
