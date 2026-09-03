from rest_framework import serializers
from .models import Project, Task, Target
from finance.models import Transaction
from django.db.models import Sum

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'customer' in data and data['customer'] and data['customer'].company != company:
            raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

        return data

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        
    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'project' in data and data['project'] and data['project'].company != company:
            raise serializers.ValidationError({"project": "Project does not belong to this company."})

        return data

class TargetSerializer(serializers.ModelSerializer):
    current_progress = serializers.SerializerMethodField()

    class Meta:
        model = Target
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def get_current_progress(self, obj):
        # Calculate money made or spent between start_date and deadline
        if obj.metric_type == 'revenue':
            total = Transaction.objects.filter(
                company=obj.company,
                transaction_type='earn',
                date__gte=obj.start_date,
                date__lte=obj.deadline
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            return float(total)
        elif obj.metric_type == 'expense':
            total = Transaction.objects.filter(
                company=obj.company,
                transaction_type='loss',
                date__gte=obj.start_date,
                date__lte=obj.deadline
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            return float(total)
        return 0
