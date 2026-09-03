from rest_framework import serializers
from .models import Invoice, Payment, JournalEntry, Expense, Product, LineItem, Transaction

class PaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_number', 'customer', 'amount', 'currency',
            'payment_method', 'transaction_id', 'status', 'paid_at', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'invoice', 'customer']


    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            company = request.user.profile.company
            if 'customer' in data and data['customer'].company != company:
                raise serializers.ValidationError({"customer": "Customer does not belong to this company."})
            if 'invoice' in data and data['invoice'] and data['invoice'].company != company:
                raise serializers.ValidationError({"invoice": "Invoice does not belong to this company."})
        return data


class JournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntry
        fields = [
            'id', 'entry_number', 'entry_type', 'account_code', 'amount',
            'currency', 'reference_type', 'reference_id', 'description', 'posted_at'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    balance_due = serializers.ReadOnlyField()
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['company', 'created_at', 'updated_at', 'amount_paid']

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            company = request.user.profile.company

            # Validate customer belongs to same company
            if 'customer' in data and data['customer'].company != company:
                raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

            # Validate deal belongs to same company and matches customer
            if 'deal' in data and data['deal']:
                if data['deal'].company != company:
                    raise serializers.ValidationError({"deal": "Deal does not belong to this company."})
                if data['deal'].customer != data.get('customer', self.instance.customer if self.instance else None):
                    raise serializers.ValidationError({"deal": "Deal customer does not match invoice customer."})
            
        return data

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

class LineItemSerializer(serializers.ModelSerializer):
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = LineItem
        fields = '__all__'
        read_only_fields = ['invoice']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
