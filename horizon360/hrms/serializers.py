from rest_framework import serializers
from .models import Department, Employee, LeaveRequest

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'department' in data and data['department'] and data['department'].company != company:
            raise serializers.ValidationError({"department": "Department does not belong to this company."})

        return data

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'employee' in data and data['employee'] and data['employee'].company != company:
            raise serializers.ValidationError({"employee": "Employee does not belong to this company."})

        return data
