from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Destination(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    carbon_score = models.IntegerField(help_text='Lower is greener', default=50)
    transport_options = models.CharField(max_length=200, blank=True, help_text='Comma-separated transports: train,bus,bike')
    tags = models.CharField(max_length=200, blank=True, help_text='Comma-separated tags: nature,city,coast')

    def transports(self):
        return [t.strip() for t in self.transport_options.split(',') if t.strip()]

    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def __str__(self):
        return f"{self.name} ({self.country})"


class TravelRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    distance_km = models.FloatField()
    passenger_count = models.IntegerField(default=1)
    selected_travel_type = models.CharField(max_length=50, blank=True)
    recommended_transport = models.CharField(max_length=50)
    co2_estimated_kg = models.FloatField()
    co2_saved_kg = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source}→{self.destination} ({self.distance_km} km)"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    preferred_contact = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)


class LoginAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150)
    success = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=50, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username} - {status} ({self.timestamp})"

    class Meta:
        ordering = ['-timestamp']
