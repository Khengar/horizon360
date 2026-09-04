import json
from django.core.management.base import BaseCommand
from django.test.client import RequestFactory
from cdp_core.models import Company, Customer, RawEvent, EventSchema, UserProfile
from cdp_core.tasks import process_event_task
from cdp_core.unification import build_all_unified_profiles
from cdp_core.enrichment import enrich_all_profiles
from cdp_core.identity_batch import run_batch_identity_resolution
from cdp_core.views import CDPPipelineView
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model()
        user, _ = User.objects.get_or_create(username='testadmin4', email='admin4@horizon360.com')
        company, _ = Company.objects.get_or_create(name='Horizon Test Inc 4')
        
        up, _ = UserProfile.objects.get_or_create(user=user, defaults={'company': company})
        up.company = company
        up.save()
        
        events = [
            {"email": "mark.twain@example.com", "phone": "5552223333", "firstName": "Mark", "lastName": "Twain"},
            {"email": "mark.twainn@example.com", "phone": "5552223399", "firstName": "Mar", "lastName": "Twain"},
        ]
        
        for e in events:
            raw = RawEvent.objects.create(
                company=company, 
                event_name='page_view', 
                raw_payload=e, 
                processed=False
            )
            process_event_task(raw.id)
            
        print(f"Created {Customer.objects.filter(company=company).count()} customers deterministically.")
        
        build_all_unified_profiles(company)
        enrich_all_profiles(company)
        
        res = run_batch_identity_resolution(company.id)
        print(f"ML Batch results: {res}")
        
        factory = RequestFactory()
        request = factory.get('/api/cdp/pipeline/')
        request.user = user
        view = CDPPipelineView.as_view()
        response = view(request)
        print("\nAPI Response Summary:")
        data = response.data
        print(f"Total Unified Profiles: {data['pipeline']['data_unification']['unified_profiles']}")
        print(f"Merge Suggestions Pending: {len(data['merge_suggestions'])}")
        if len(data['merge_suggestions']) > 0:
            print(f"Suggestion Confidence: {data['merge_suggestions'][0]['confidence_score']*100:.2f}%")
            print(f"Match Reasons: {data['merge_suggestions'][0]['match_reasons']}")
        
