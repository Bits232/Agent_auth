
# Agent_auth_app/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .security_checker import SecurityChecker

def landing(request):
    """Beautiful landing page"""
    return render(request, 'landing.html')

def demo(request):
    """Security demo page"""
    return render(request, 'demo.html')

@csrf_exempt
def live_security_analysis(request):
    """AJAX endpoint for live security analysis"""
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('input', '')
        
        # Analyze ANY input, not just passwords
        threats = SecurityChecker.check_input(user_input)
        
        response_data = {
            'input': user_input,
            'threats': threats,
            'threat_count': len(threats),
            'systems_active': ['pg_textsearch BM25', 'AI Security Agent']
        }
        
        return JsonResponse(response_data)