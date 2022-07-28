from django.core.serializers import json

from django.contrib.auth.models import User
from django.db.models import Avg, Sum, Q
from django.http import JsonResponse
import ftplib
from datetime import datetime

# Create your views here.
from rest_framework.decorators import action

from stockupdater.models import TireStock, AveragedTireProductData
from stockupdater.scripts import update_data_from_external_source, execute_script
from rest_framework import viewsets, status

from stockupdater.serializers import TireStockSerializer, UserSerializer, AveragedTireStockSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AveragedTireStockViewSet(viewsets.ModelViewSet):
    queryset = AveragedTireProductData.objects.all()
    serializer_class = AveragedTireStockSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)  # IsAuthenticated

    @action(detail=False, methods=['POST'])
    def get_average_price_and_stock_availability(self, request):
        if 'search_query' in request.data:
            search_query = request.data['search_query']

            search_query_split = search_query.split(' ')

            brand_name = ''
            product_code = ''

            try:
                brand_name = search_query.split(' ')[0]
            except:
                pass
            try:
                product_code = search_query.split(' ')[1]
            except:
                pass

            if brand_name != '':
                related_search_result = AveragedTireProductData.objects \
                    .filter(brand_name__icontains=brand_name,
                            product_code__icontains=product_code)

                # In case the brand name has a space such as Mickey Thompson
                if related_search_result.count() == 0:

                    try:
                        brand_name = search_query.split(' ')[0] + ' ' + search_query.split(' ')[1]
                        related_search_result = AveragedTireProductData.objects.filter(brand_name__icontains=brand_name)
                    except:
                        pass
                    try:
                        product_code = search_query.split(' ')[2]
                        related_search_result = related_search_result.filter(product_code__icontains=product_code)
                    except:
                        pass

                related_search_result = related_search_result.order_by('id')[:10]

                serializer = AveragedTireStockSerializer(related_search_result, many=True)

                response = serializer.data
                return Response(response, status=status.HTTP_200_OK)
            else:
                return JsonResponse({}, status=status.HTTP_200_OK)

        else:
            response = {'result': 'Please provide the brand name and product code'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def get_brand_and_product_code(self, request):
        if 'average_obj_pk' in request.data:
            try:
                average_obj_pk = int(request.data['average_obj_pk'])
                average_obj = AveragedTireProductData.objects.get(pk=average_obj_pk)

                brand_name = average_obj.brand_name
                product_code = average_obj.product_code
                response = {'brand_name': brand_name, 'product_code': product_code}
                return Response(response, status=status.HTTP_200_OK)
            except:
                return JsonResponse({}, status=status.HTTP_200_OK)


        else:
            response = {'result': 'Please provide the averaged object pk'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'])
    def get_detailed_quantity_price_list(self, request):
        if 'average_obj_pk' in request.data:

            try:
                average_obj_pk = int(request.data['average_obj_pk'])
                average_obj = AveragedTireProductData.objects.get(pk=average_obj_pk)

                brand_name = average_obj.brand_name
                product_code = average_obj.product_code

                detailed_quantity_price_queryset = TireStock.objects.filter(brand_name__iexact=brand_name,
                                                                            product_code__iexact=product_code)

                serializer = TireStockSerializer(detailed_quantity_price_queryset, many=True)

                response = serializer.data
                return Response(response, status=status.HTTP_200_OK)
            except:
                return JsonResponse({}, status=status.HTTP_200_OK)


        else:
            response = {'result': 'Please provide the averaged object pk'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # Prevent crud functionality for this viewset
    def update(self, request, *args, **kwargs):
        response = {'message': 'Cannot update data this way...'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        response = {'message': 'Cannot create data this way...'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        response = {'message': 'Cannot delete data this way...'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TireStockViewSet(viewsets.ModelViewSet):
    queryset = TireStock.objects.all()
    serializer_class = TireStockSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)  # IsAuthenticated

    @action(detail=False, methods=['POST'])
    def get_average_price_and_stock_availability(self, request):
        if 'brand_name' in request.data and 'product_code' in request.data:
            brand_name = request.data['brand_name']
            product_code = request.data['product_code']
            average_price_in_usd = TireStock.objects.filter(brand_name__iexact=brand_name,
                                                            product_code__iexact=product_code).aggregate(
                Avg('price_in_usd'))
            total_available_stock = TireStock.objects.filter(brand_name__iexact=brand_name,
                                                             product_code__iexact=product_code).aggregate(
                Sum('available_quantity'))
            print(brand_name, product_code, average_price_in_usd, total_available_stock)
            response = {'average_price_in_usd': average_price_in_usd, 'total_available_stock': total_available_stock}
            return Response(response, status=status.HTTP_200_OK)
        else:
            response = {'message': 'Please provide the brand name and product code'}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    # Prevent crud functionality for this viewset
    def update(self, request, *args, **kwargs):
        response = {'message': 'Cannot update data this way...'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        response = {'message': 'Cannot create data this way...'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        response = {'message': 'Cannot delete data this way...'}
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


def initiate_scripts_execution(request):
    # Credentials to access this end point
    endpoint_authentication_token = 'VUYVBU789y23@4534454'

    try:
        request_auth_token = request.GET.get('auth_token')

        if request_auth_token == endpoint_authentication_token:
            execute_script('update_stock')
            return JsonResponse({'result': 'success'})
        else:
            return JsonResponse({'result': 'Unauthorized'})
    except Exception as e:
        print(e)
        return JsonResponse({'result': 'error'})
