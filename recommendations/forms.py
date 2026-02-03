from django import forms
from .models import Profile

TRANSPORT_CHOICES = [
    ('', 'Any'),
    ('train', 'Train'),
    ('bus', 'Bus'),
    ('bike', 'Bike'),
    ('walk', 'Walk'),
]

class RecommendationForm(forms.Form):
    max_carbon = forms.IntegerField(required=False, min_value=0, label='Maximum carbon score')
    transport = forms.ChoiceField(choices=TRANSPORT_CHOICES, required=False)
    tags = forms.CharField(required=False, help_text='Comma-separated tags')


TRAVEL_TYPE_CHOICES = [
    ('', 'Unknown/Other'),
    ('car', 'Car'),
    ('flight', 'Flight'),
    ('train', 'Train'),
    ('bus', 'Bus'),
    ('ev', 'Electric Vehicle'),
    ('bike', 'Bike / Walk'),
]


class TravelInputForm(forms.Form):
    """Form for Green Travel Recommendation using Google Maps API"""
    source = forms.CharField(
        max_length=200, 
        label='Source Location',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Delhi, DL',
            'class': 'form-control'
        })
    )
    destination = forms.CharField(
        max_length=200, 
        label='Destination Location',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Delhi, Mumbai',
            'class': 'form-control'
        })
    )
    travel_type = forms.ChoiceField(
        choices=TRAVEL_TYPE_CHOICES, 
        required=False, 
        label='Your Current Travel Type (optional)',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    passenger_count = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=20,
        initial=1,
        label='Passengers',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of passengers'})
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone', 'address', 'city', 'country', 'birth_date', 'bio', 'preferred_contact']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_contact': forms.TextInput(attrs={'class': 'form-control'}),
        }
