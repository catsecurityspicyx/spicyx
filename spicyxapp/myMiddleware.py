from .models import HttpError


class CaptureErrorIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        white_list_status_code = [200]

        response = self.get_response(request)
        if response.status_code not in white_list_status_code:
            ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Forwarded-For') or request.META.get('REMOTE_ADDR')
            url = request.build_absolute_uri()
            status_code = response.status_code
            HttpError.objects.create(user_ip=ip, url=url, status_code=status_code)
        return response
