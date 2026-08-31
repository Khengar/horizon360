from django.core.management.base import BaseCommand
from cdp_core.models import Company
from intelligence.agents import MeshRunner

class Command(BaseCommand):
    help = 'Executes the Multi-Agent Intelligence Mesh across all companies or a specific company.'

    def add_arguments(self, parser):
        parser.add_argument('--company-id', type=int, help='ID of specific company to run mesh for')

    def handle(self, *args, **options):
        company_id = options.get('company_id')
        if company_id:
            companies = Company.objects.filter(id=company_id)
        else:
            companies = Company.objects.filter(is_active=True)

        self.stdout.write(f"Executing Multi-Agent Intelligence Mesh across {companies.count()} companies...")

        total_insights = 0
        for comp in companies:
            res = MeshRunner.run_mesh_for_company(comp)
            total_insights += res['total_insights_generated']
            summaries = res.get('agent_summaries', {})
            details = ", ".join(f"{k}: {v}" for k, v in summaries.items())
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Company '{comp.name}' (ID: {comp.id}): "
                    f"{res['agents_executed']} agents executed ({details}), "
                    f"{res['total_insights_generated']} insights generated."
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Intelligence Mesh completed! Total insights generated: {total_insights}"))
