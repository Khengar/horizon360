from rest_framework import serializers
from .models import Project, Task

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
