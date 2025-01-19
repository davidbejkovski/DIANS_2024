from django.db import models

class StockData(models.Model):
    date = models.DateField()
    last_transaction_price = models.FloatField()
    min_price = models.FloatField()
    max_price = models.FloatField()
    avg_price = models.FloatField()
    promil = models.FloatField()
    quantity = models.IntegerField()
    best_turnover = models.FloatField()
    total_turnover = models.FloatField()
    company_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.company_name} - {self.date}"
