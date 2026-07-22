from .models import SystemLogo, Visitor, TemplateConfig

def active_logos(request):
    return {
        'active_logos': SystemLogo.objects.filter(is_active=True).order_by('created_at')
    }

def visitor_count(request):
    # Extract real client IP, resolving proxies if any
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    if ip:
        try:
            Visitor.objects.get_or_create(ip_address=ip)
        except Exception:
            pass
            
    return {
        'visitor_count': Visitor.objects.count()
    }

def template_config(request):
    return {
        'template_config': TemplateConfig.get_solo()
    }
