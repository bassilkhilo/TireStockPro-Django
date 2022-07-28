import csv
import ftplib
import threading
import uuid

from django.db.models import Sum, Avg
from pytz import utc

from stockupdater.models import ScriptLogs, TireStock, AveragedTireProductData
from datetime import date, datetime
from io import BytesIO


def execute_script(data_source):
    print('Executing command: ' + data_source)
    # Initialize unique script ID to be used to track progress of script while its running in a thread
    unique = False
    script_id = ''
    while not unique:
        script_id = ('{}-{}-{}'.format(str(uuid.uuid4().int)[:17][:3], str(uuid.uuid4().int)[:17][3:10],
                                       str(uuid.uuid4().int)[:17][10:17]))
        script_id_queryset = ScriptLogs.objects.filter(script_id=script_id).count()
        if script_id_queryset == 0 and script_id != '':
            unique = True
    ScriptLogs(script_id=script_id, name='update_original_data_with_external_sources(' + data_source + ')',
               status='started', ).save()
    update_data_from_external_source(data_source, script_id)


def update_data_from_external_source(data_source, script_id):
    UpdateDataFromExternalSourcesThread(data_source, script_id).start()


class UpdateDataFromExternalSourcesThread(threading.Thread):
    def __init__(self, data_source, script_id):
        self.data_source = data_source
        self.script_id = script_id
        threading.Thread.__init__(self)

    def run(self):
        data_source = self.data_source
        script_id = self.script_id
        if data_source == 'update_stock':
            script_log = ScriptLogs.objects.get(script_id=script_id)

            if update_stock_data():
                script_log.status = 'completed'
                script_log.is_complete = True
                script_log.time_completed = datetime.now(tz=utc)
            else:
                script_log.status = 'error'
                script_log.is_complete = True
                script_log.time_completed = datetime.now(tz=utc)
            script_log.save()


def update_stock_data():
    try:

        update_data_bool = True
        update_averages_bool = True

        if update_data_bool:
            print('Updating tire stock data...')

            print('Accessing FTP...')

            ftp_host = "ftp.tiretutor.com"
            ftp_user = "tiretest"
            ftp_pass = "2u39E16i"

            ftp = ftplib.FTP(ftp_host, ftp_user, ftp_pass)
            ftp.encoding = "utf-8"

            # Get directory of the ftp to get all file names
            print('Retrieving FTP directory...')
            files = []
            try:
                files = ftp.nlst()
            except Exception as e:
                print(e)

            ftp.quit()

            print('Files in directory:', files)

            # Determine the labels similar in all stock lists for all the critical data required (Brand name, product code, available stock and price)
            # Purpose of this is to not have to hard code each stock list, rather, use these labels to identify their index dynamically to enter data to db accordingly
            brand_name_labels = ['brand name', 'manufacturer', 'make']
            product_code_labels = ['manufacturer part #', 'product code', 'manufacturercode']
            available_stock_labels = ['qty', 'stock']
            price_labels = ['price', 'cost']

            # Check if file names were retrieved, if len is 0, directory is empty
            files = []
            if len(files) > 0:
                for file_name in files:

                    if not file_name is None:
                        # retrieve client_id
                        client_id = file_name.replace('.csv', '').strip()
                        print('Updating stock list for client_id', client_id, '...')

                        # Data label index lists
                        brand_name_index = None
                        product_code_index = None
                        available_stock_index_list = []
                        price_index = None

                        ftp = ftplib.FTP(ftp_host, ftp_user, ftp_pass)
                        ftp.encoding = "utf-8"
                        bytes_io = BytesIO()
                        ftp.retrbinary('RETR ' + file_name, bytes_io.write)
                        bytes_io.seek(0)

                        csv_reader = csv.reader(bytes_io.read().decode("utf-8").splitlines(), delimiter=';')
                        ftp.quit()

                        line_counter = 0
                        for row in csv_reader:
                            if line_counter >= 0:
                                try:
                                    # Identify index for the following: brand name, product code, available quantity and price
                                    if line_counter == 0:
                                        labels = row
                                        # print(labels)
                                        labels_index_counter = 0
                                        for label in labels:
                                            label_name = label.lower().strip()

                                            # Get index for brand name
                                            for brand_label in brand_name_labels:
                                                if brand_label == label_name:
                                                    brand_name_index = labels_index_counter
                                                    break

                                            # Get index for product code
                                            for product_code_label in product_code_labels:
                                                if product_code_label == label_name:
                                                    product_code_index = labels_index_counter
                                                    break

                                            # Get index for all quantity locations
                                            for available_stock_label in available_stock_labels:
                                                if available_stock_label in label_name:
                                                    available_stock_index_list.append(labels_index_counter)
                                                    break

                                            # Get index for price
                                            for price_label in price_labels:
                                                if price_label == label_name:
                                                    price_index = labels_index_counter
                                                    break

                                            labels_index_counter += 1

                                        # Verify all index of required labels are found correctly
                                        # print(brand_name_index, product_code_index, available_stock_index_list, price_index)
                                    else:
                                        # Index of required data have been retrieved, time to populate the data into the stock model
                                        brand_name = row[brand_name_index]
                                        product_code = row[product_code_index]
                                        # If there are more than 1 locations for stock, we will split using a comma ,
                                        available_quantity = 0
                                        available_quantity_by_location = ''
                                        for stock_index in available_stock_index_list:
                                            try:
                                                stock = row[stock_index]
                                                if not stock is None and stock != '':
                                                    available_quantity += int(stock)
                                                    available_quantity_by_location += stock + ','
                                            except Exception as e:
                                                print(e)

                                        price = 0
                                        try:
                                            price = float(row[price_index])
                                        except Exception as e:
                                            print(e)

                                        last_updated = datetime.now(tz=utc)

                                        # Enter data into database
                                        # Check if the product already exists for the same client, if yes update stock/price, if not add to database
                                        if TireStock.objects.filter(client_id__iexact=client_id,
                                                                    brand_name__iexact=brand_name,
                                                                    product_code__iexact=product_code).count() == 0:
                                            TireStock(client_id=client_id, brand_name=brand_name,
                                                      product_code=product_code,
                                                      available_quantity=available_quantity,
                                                      available_quantity_by_location=available_quantity_by_location,
                                                      price_in_usd=price,
                                                      last_updated=last_updated).save()
                                        else:
                                            try:
                                                product = TireStock.objects.get(client_id__iexact=client_id,
                                                                                brand_name__iexact=brand_name,
                                                                                product_code__iexact=product_code)
                                                product.available_quantity = available_quantity
                                                product.available_quantity_by_location = available_quantity_by_location
                                                product.price_in_usd = price
                                                product.last_updated = last_updated
                                                product.save()
                                            except Exception as e:
                                                print(e)
                                        # print(client_id, brand_name, product_code, available_quantity,available_quantity_by_location, price)

                                except Exception as e:
                                    print(e)
                            line_counter += 1
                        print('Stock for client_id', client_id, 'has been updated...')
            print('Stock has been updated...')

        if update_averages_bool:
            print('Calculating averaged data...')

            # Get unique brand name and product code as a combination
            brand_name_and_brand_code_set = set()
            for tire_stock in TireStock.objects.all():
                brand_name = tire_stock.brand_name
                product_code = tire_stock.product_code
                if not brand_name is None and not product_code is None:
                    brand_name_and_brand_code_set.add(brand_name.lower() + '|' + product_code.lower())

            for bnpc_set in brand_name_and_brand_code_set:
                brand_name = bnpc_set.split('|')[0]
                product_code = bnpc_set.split('|')[1]
                try:
                    product_obj = TireStock.objects.filter(brand_name__iexact=brand_name,
                                                           product_code__iexact=product_code)
                    if product_obj.count() > 0:
                        total_available_quantity = product_obj.aggregate(Sum('available_quantity'))[
                            'available_quantity__sum']
                        average_price_in_usd = round(product_obj.aggregate(Avg('price_in_usd'))['price_in_usd__avg'], 2)

                        print(total_available_quantity, average_price_in_usd)
                        last_updated = datetime.now(tz=utc)

                        # Check if data exists already in AveragedTireProductData
                        if AveragedTireProductData.objects.filter(brand_name__iexact=brand_name,
                                                                  product_code__iexact=product_code).count() == 0:
                            AveragedTireProductData(brand_name=brand_name, product_code=product_code,
                                                    total_available_quantity=total_available_quantity,
                                                    average_price_in_usd=average_price_in_usd,
                                                    last_updated=last_updated).save()
                        else:
                            averaged_tire_product_obj = AveragedTireProductData.objects.get(
                                brand_name__iexact=brand_name, product_code__iexact=product_code)
                            averaged_tire_product_obj.total_available_quantity = total_available_quantity
                            averaged_tire_product_obj.average_price_in_usd = average_price_in_usd
                            averaged_tire_product_obj.last_updated = last_updated
                            averaged_tire_product_obj.save()

                except Exception as e:
                    print(e)

            print('Finished updating averaged data...')

        return True
    except Exception as e:
        print(e)
        return False
