from .models import SystemLogo, Visitor, TemplateConfig

def active_logos(request):
    return {
        'active_logos': SystemLogo.objects.filter(is_active=True).order_by('created_at')
    }

def visitor_count(request):
    # 1. Skip counting authenticated staff/admin users
    if request.user and request.user.is_authenticated:
        return {
            'visitor_count': Visitor.objects.count()
        }

    # 2. Skip counting bots, crawlers, and script engines
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    bot_keywords = ['bot', 'spider', 'crawler', 'slurp', 'curl', 'wget', 'python', 'http-client', 'postman', 'headless']
    if any(keyword in user_agent for keyword in bot_keywords):
        return {
            'visitor_count': Visitor.objects.count()
        }

    # 3. Extract real client IP, resolving proxies if any
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    # 4. Filter out private/local loopback IPs (e.g. Render internal routing)
    is_private = False
    if ip:
        if ip in ['127.0.0.1', '::1', 'localhost']:
            is_private = True
        elif ip.startswith('10.') or ip.startswith('192.168.'):
            is_private = True
        elif ip.startswith('172.'):
            try:
                parts = ip.split('.')
                if len(parts) == 4:
                    second_octet = int(parts[1])
                    if 16 <= second_octet <= 31:
                        is_private = True
            except ValueError:
                pass

    # 5. Only create a new visitor record if this browser session hasn't been counted yet
    if ip and not is_private:
        if not request.session.get('has_counted_visit'):
            try:
                # We removed unique=True constraint, so each unique browser gets its own row.
                Visitor.objects.create(ip_address=ip)
                request.session['has_counted_visit'] = True
            except Exception:
                pass
            
    return {
        'visitor_count': Visitor.objects.count()
    }

def template_config(request):
    return {
        'template_config': TemplateConfig.get_solo()
    }
