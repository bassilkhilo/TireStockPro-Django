from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from stockupdater.models import TireStock, AveragedTireProductData


class TireStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = TireStock
        fields = (
            'id', 'client_id', 'brand_name', 'product_code', 'available_quantity', 'available_quantity_by_location',
            'price_in_usd', 'last_updated')


class AveragedTireStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AveragedTireProductData
        fields = (
            'id', 'brand_name', 'product_code', 'total_available_quantity', 'average_price_in_usd', 'last_updated')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {"password": {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user
