from django.db import models


# Create your models here.
class TireStock(models.Model):
    client_id = models.CharField(max_length=255, null=True, blank=True)
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    product_code = models.CharField(max_length=255, null=True, blank=True)
    available_quantity = models.IntegerField(null=True, blank=True, default=0)
    available_quantity_by_location = models.CharField(max_length=255, null=True, blank=True)
    price_in_usd = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.product_code


class AveragedTireProductData(models.Model):
    brand_name = models.CharField(max_length=255, null=True, blank=True)
    product_code = models.CharField(max_length=255, null=True, blank=True)
    total_available_quantity = models.IntegerField(null=True, blank=True, default=0)
    average_price_in_usd = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.product_code



class ScriptLogs(models.Model):
    script_id = models.CharField(max_length=255, unique=True)
    time_started = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=255, null=True)
    is_complete = models.BooleanField(default=False)
    time_completed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.script_id + ' | ' + str(self.time_started) + ' | ' + str(self.name)+ ' | ' + str(self.status)+ ' | ' + str(self.is_complete) + ' | ' + str(self.time_completed)
