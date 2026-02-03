from django.contrib import admin
from .models import Profile, LoginAttempt, TravelRecord


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'country')
    search_fields = ('user__username', 'full_name', 'city', 'country')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'success', 'timestamp', 'ip_address')
    search_fields = ('username', 'user__username')
    list_filter = ('success', 'timestamp')
    readonly_fields = ('username', 'user', 'success', 'ip_address', 'user_agent', 'timestamp')


@admin.register(TravelRecord)
class TravelRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'source', 'destination', 'distance_km', 'recommended_transport', 'co2_saved_kg', 'created_at')
    search_fields = ('user__username', 'source', 'destination')
    list_filter = ('recommended_transport', 'created_at')
    readonly_fields = ('user', 'source', 'destination', 'distance_km', 'passenger_count', 'selected_travel_type', 'recommended_transport', 'co2_estimated_kg', 'co2_saved_kg', 'created_at')
