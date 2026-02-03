from django.shortcuts import render
from .models import Destination
from .forms import RecommendationForm
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib import messages
from .forms import TravelInputForm
from .models import TravelRecord
from django.utils import timezone
from django.conf import settings
from .ai_logic import GreenTravelAI

# googlemaps is optional at runtime; if it's not installed we fall back to the
# mock distance calculator below. This prevents an import-time crash.
try:
    import googlemaps as _googlemaps
except Exception:
    _googlemaps = None
# Try to import geopy for OpenStreetMap fallback
try:
    from geopy.geocoders import Nominatim as _Nominatim
    from geopy.distance import geodesic as _geodesic
    _geopy = True
except Exception:
    _Nominatim = None
    _geodesic = None
    _geopy = False
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .forms import ProfileForm
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse

def get_distance_from_api(source, destination):
    """
    Fetch distance and duration from Google Maps Distance Matrix API
    Returns dict {'distance_km': float, 'duration_text': str, 'duration_seconds': int}
    or None if API fails
    """
    try:
        api_key = settings.GOOGLE_MAPS_API_KEY
        # If Google Maps not available, try OpenStreetMap (Nominatim) fallback
        if not api_key or api_key == 'YOUR_GOOGLE_MAPS_API_KEY_HERE' or _googlemaps is None:
            # Use geopy + Nominatim to geocode and compute straight-line distance
            try:
                if _geopy and _Nominatim is not None and _geodesic is not None:
                    geolocator = _Nominatim(user_agent="greentravel_app")
                    src = geolocator.geocode(source, timeout=10)
                    dst = geolocator.geocode(destination, timeout=10)
                    if src and dst:
                        coords_1 = (src.latitude, src.longitude)
                        coords_2 = (dst.latitude, dst.longitude)
                        distance_km = round(_geodesic(coords_1, coords_2).km, 2)
                        durations = {}
                        # Adjust speeds for city vs highway based on distance
                        if distance_km < 50:
                            # City speeds for short distances
                            driving_speed = 40.0  # km/h
                            transit_speed = 50.0  # km/h
                        else:
                            # Highway speeds for longer distances
                            driving_speed = 60.0  # km/h
                            transit_speed = 70.0  # km/h
                        durations['driving'] = int((distance_km / driving_speed) * 3600)
                        durations['transit'] = int((distance_km / transit_speed) * 3600)
                        durations['bicycling'] = int((distance_km / 15.0) * 3600)
                        durations['walking'] = int((distance_km / 5.0) * 3600)
                        return {'distance_km': distance_km, 'durations': durations, 'fallback': 'osm'}
            except Exception:
                pass

            # If geopy/Nominatim not available or geocoding failed, use legacy mock
            info = mock_distance_calculation(source, destination)
            info['mock'] = True
            return info

        gmaps = _googlemaps.Client(key=api_key)

        # Get driving distance (canonical) and collect durations for several modes
        driving = gmaps.distance_matrix(origins=source, destinations=destination, mode='driving', units='metric')
        if not (driving and driving.get('status') == 'OK' and driving.get('rows')):
            return None

        elem = driving['rows'][0]['elements'][0]
        if not (elem and elem.get('status') == 'OK' and 'distance' in elem):
            return None

        distance_m = elem['distance']['value']
        distance_km = round(distance_m / 1000, 2)

        durations = {}
        if 'duration' in elem and elem['duration']:
            durations['driving'] = elem['duration']['value']
            durations['driving_text'] = elem['duration']['text']

        for mode in ['transit', 'bicycling', 'walking']:
            try:
                res = gmaps.distance_matrix(origins=source, destinations=destination, mode=mode, units='metric')
                if res and res.get('status') == 'OK' and res.get('rows'):
                    e = res['rows'][0]['elements'][0]
                    if e.get('status') == 'OK' and 'duration' in e and e['duration']:
                        durations[mode] = e['duration']['value']
                        durations[f'{mode}_text'] = e['duration']['text']
            except Exception:
                pass

        return {'distance_km': distance_km, 'durations': durations}
    except Exception as e:
        print(f"API Error: {e}")
    
    return None


def get_country_for_place(place):
    """Return country code (ISO short_name) for a place using Google Geocoding.
    Returns the two-letter country short name (e.g. 'IN') when available, else None.
    Falls back to None when geocode not available or API key missing.
    """
    try:
        api_key = settings.GOOGLE_MAPS_API_KEY
        # Prefer Google Geocoding when available
        if api_key and _googlemaps is not None and api_key != 'YOUR_GOOGLE_MAPS_API_KEY_HERE':
            try:
                gmaps = _googlemaps.Client(key=api_key)
                results = gmaps.geocode(place)
                if results:
                    for comp in results[0].get('address_components', []):
                        if 'country' in comp.get('types', []):
                            return comp.get('short_name')
            except Exception:
                pass

        # Fallback: use Nominatim (OpenStreetMap) via geopy when available
        if _geopy and _Nominatim is not None:
            try:
                geolocator = _Nominatim(user_agent="greentravel_app")
                res = geolocator.geocode(place, addressdetails=True, timeout=10)
                if res and getattr(res, 'raw', None):
                    adr = res.raw.get('address', {})
                    cc = adr.get('country_code')
                    if cc:
                        return cc.upper()
            except Exception:
                return None

    except Exception:
        return None
    return None


def is_within_india(source, destination):
    """Return True if both source and destination are within India.
    Uses Google Geocoding. Requires `GOOGLE_MAPS_API_KEY` and `googlemaps` installed.
    Returns False if geocoding is unavailable or either place is not in India.
    """
    # Use Google Geocoding only. If geocoding isn't available, we cannot reliably assert India membership.
    try:
        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key or _googlemaps is None:
            return False
        src_country = get_country_for_place(source)
        dst_country = get_country_for_place(destination)
        if not src_country or not dst_country:
            return False
        return str(src_country).upper() == 'IN' and str(dst_country).upper() == 'IN'
    except Exception:
        return False


def mock_distance_calculation(source, destination):
    """
    Mock distance calculation for demo when API key is not configured
    Demonstrates API functionality without actual API calls
    """
    # Simple hash-based mock distances for Indian cities
    location_pairs = {
        ('delhi', 'mumbai'): 1400,
        ('delhi', 'kolkata'): 1500,
        ('delhi', 'chennai'): 2200,
        ('delhi', 'bangalore'): 2100,
        ('delhi', 'ghaziabad'): 30,
        ('delhi', 'noida'): 25,
        ('delhi', 'gurgaon'): 30,
        ('mumbai', 'bangalore'): 980,
        ('mumbai', 'chennai'): 1330,
        ('mumbai', 'kolkata'): 1900,
        ('bangalore', 'chennai'): 350,
        ('bangalore', 'kolkata'): 1900,
        ('chennai', 'kolkata'): 1700,
        ('delhi', 'jaipur'): 280,
        ('mumbai', 'pune'): 150,
        ('bangalore', 'mysore'): 140,
        ('delhi', 'agra'): 200,
        ('mumbai', 'goa'): 580,
        ('delhi', 'rishikesh'): 240,
        ('delhi', 'srinagar'): 800,
    }

    src = source.lower().strip()
    dst = destination.lower().strip()

    for (s, d), dist in location_pairs.items():
        if (s in src and d in dst) or (d in src and s in dst):
            distance_km = dist
            durations = {}
            # Adjust speeds for city vs highway based on distance
            if distance_km < 50:
                # City speeds for short distances
                driving_speed = 40.0  # km/h
                transit_speed = 50.0  # km/h
            else:
                # Highway speeds for longer distances
                driving_speed = 60.0  # km/h
                transit_speed = 70.0  # km/h
            durations['driving'] = int((distance_km / driving_speed) * 3600)
            durations['transit'] = int((distance_km / transit_speed) * 3600)
            durations['bicycling'] = int((distance_km / 15.0) * 3600)
            durations['walking'] = int((distance_km / 5.0) * 3600)
            return {'distance_km': distance_km, 'durations': durations}

    # Default to a medium distance for demo (Indian context)
    distance_km = 500
    durations = {}
    durations['driving'] = int((distance_km / 60.0) * 3600)
    durations['transit'] = int((distance_km / 70.0) * 3600)
    durations['bicycling'] = int((distance_km / 15.0) * 3600)
    durations['walking'] = int((distance_km / 5.0) * 3600)
    return {'distance_km': distance_km, 'durations': durations}


def recommend(request):
    # Keep the old recommendation form support for destination browsing
    form = RecommendationForm(request.GET or None)
    recommendations = []
    if form.is_valid():
        max_carbon = form.cleaned_data.get('max_carbon')
        transport = form.cleaned_data.get('transport')
        tags_raw = form.cleaned_data.get('tags')
        tags = [t.strip().lower() for t in tags_raw.split(',')] if tags_raw else []

        qs = Destination.objects.all()
        if max_carbon is not None:
            qs = qs.filter(carbon_score__lte=max_carbon)
        results = []
        for d in qs:
            score = d.carbon_score
            transport_match = True
            tag_score = 0
            if transport:
                transport_match = transport in [t.lower() for t in d.transports()]
            if tags:
                for tag in tags:
                    if tag and tag in [t.lower() for t in d.tag_list()]:
                        tag_score += 1
            if transport and not transport_match:
                continue
            results.append((score - tag_score*5, tag_score, d))
        # sort by computed score (lower better) then tag_score desc
        results.sort(key=lambda x: (x[0], -x[1]))
        recommendations = [r[2] for r in results]

    # Travel input form with Google Maps API integration
    travel_form = TravelInputForm(request.POST or None)
    travel_result = None
    api_error = None
    api_info = None
    
    if request.method == 'POST' and travel_form.is_valid():
        # Require login to perform travel calculations
        if not request.user.is_authenticated:
            api_error = "Please log in to use the route finder."
        else:
            source = travel_form.cleaned_data['source']
            destination = travel_form.cleaned_data['destination']
            user_choice = travel_form.cleaned_data.get('travel_type')
            passenger_count = int(travel_form.cleaned_data.get('passenger_count') or 1)

            # Determine which backend to use: prefer Google Maps when key+client available,
            # otherwise attempt OpenStreetMap via geopy as a fallback and show clear admin guidance.
            distance_info = None
            api_key = settings.GOOGLE_MAPS_API_KEY
            can_use_google = bool(api_key) and api_key.strip() != '' and _googlemaps is not None

            if can_use_google:
                # Use Google Maps for geocoding and distance calculations
                if not is_within_india(source, destination):
                    api_error = "Route not found — the finder only supports routes within India (Google geocoding failed)."
                else:
                    distance_info = get_distance_from_api(source, destination)
                    if distance_info is None:
                        api_error = (
                            "Could not calculate distance using Google Maps. "
                            "Verify `GOOGLE_MAPS_API_KEY`, billing, and that the `googlemaps` package is installed."
                        )
            else:
                # Try geopy/OpenStreetMap fallback if available
                if _geopy:
                    # When Google is not available, we can't reliably assert India-membership.
                    # Use OSM geocoding/distance and warn the user about reduced coverage/accuracy.
                    distance_info = get_distance_from_api(source, destination)
                    if distance_info is None:
                        api_error = (
                            "Could not calculate distance using OpenStreetMap fallback. "
                            "For full India coverage and more accurate routing, set `GOOGLE_MAPS_API_KEY` and install `googlemaps`."
                        )
                    else:
                        # Inform admin/user that fallback was used (non-blocking)
                        if distance_info.get('fallback') == 'osm' or distance_info.get('mock'):
                            api_info = (
                                "Using OpenStreetMap fallback (geopy) — results may be less accurate than Google Maps. "
                                "To enable Google Maps routing across India, set `GOOGLE_MAPS_API_KEY` and install `googlemaps`."
                            )
                else:
                    # Neither Google nor geopy available: actionable admin message
                    api_error = (
                        "This route finder requires either a configured Google Maps API key with the `googlemaps` client, "
                        "or the `geopy` package for an OpenStreetMap fallback.\n\n"
                        "Please set `GOOGLE_MAPS_API_KEY` in settings (or as an environment variable) and install the dependencies:\n\n"
                        "pip install googlemaps geopy\n\n"
                        "Or set `GOOGLE_MAPS_API_KEY` only and install `googlemaps` for full routing coverage across India."
                    )

                if distance_info is None:
                    api_error = "Could not calculate distance. Please enter valid locations or check your Google Maps API key."
                else:
                    # Warn when using mock data (no Google API key or client)
                    if distance_info.get('mock'):
                        api_info = "Using mock distances (no Google Maps API key configured). Results may be inaccurate — set `GOOGLE_MAPS_API_KEY` in settings for accurate calculations."
                    distance_km = distance_info.get('distance_km')
                    google_durations = distance_info.get('durations') or {}
                    # Use AI Logic to get recommendations (pass Google per-mode durations)
                    best_option = GreenTravelAI.get_best_recommendation(distance_km, google_durations, passenger_count)
                    all_recommendations = GreenTravelAI.calculate_recommendations(distance_km, google_durations, passenger_count)

                    if best_option:
                        # Calculate CO2 saved compared to flight
                        co2_saved = GreenTravelAI.compare_with_flight(best_option, distance_km)

                        # Generate eco-friendly message
                        eco_message = GreenTravelAI.get_eco_message(
                            best_option['green_score'], 
                            best_option['transport'], 
                            distance_km
                        )

                        travel_result = {
                            'source': source,
                            'destination': destination,
                            'distance_km': distance_km,
                            'passenger_count': passenger_count,
                            'recommended': best_option['transport'],
                            'green_score': best_option['green_score'],
                            'co2_estimated_kg': best_option['emission_kg'],
                            'co2_per_person_kg': best_option.get('emission_per_person_kg'),
                            'co2_saved_kg': co2_saved,
                            'eco_message': eco_message,
                            'all_recommendations': all_recommendations,
                            'estimated_time': best_option.get('duration_text'),
                            'estimated_cost_inr': best_option.get('cost_inr'),
                            'cost_per_person_inr': best_option.get('cost_per_person_inr'),
                        }

                        # Store record in database
                        try:
                            rec = TravelRecord.objects.create(
                                user=request.user if request.user.is_authenticated else None,
                                source=source,
                                destination=destination,
                                distance_km=distance_km,
                                passenger_count=passenger_count,
                                selected_travel_type=user_choice or '',
                                recommended_transport=best_option['transport'],
                                co2_estimated_kg=best_option['emission_kg'],
                                co2_saved_kg=co2_saved,
                            )
                            rec.save()
                        except Exception as e:
                            # Don't block on DB errors
                            print(f"Database Error: {e}")
    
    context = {
        'form': form,
        'recommendations': recommendations,
        'travel_form': travel_form,
        'travel_result': travel_result,
        'api_error': api_error,
        'api_info': api_info,
    }
    
    return render(request, 'recommendations/index.html', context)


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created — you can now log in')
            return redirect('recommendations:login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def about(request):
    return render(request, 'recommendations/about.html')


@login_required
def history(request):
    # Show recent records for the logged-in user and total CO2 saved
    records = TravelRecord.objects.filter(user=request.user).order_by('-created_at')[:200]
    total_saved = records.aggregate(total=Sum('co2_saved_kg'))['total'] or 0.0
    total_emitted = records.aggregate(total=Sum('co2_estimated_kg'))['total'] or 0.0
    context = {
        'records': records,
        'total_saved_kg': round(total_saved, 2),
        'total_emitted_kg': round(total_emitted, 2),
    }
    return render(request, 'recommendations/history.html', context)


@login_required
def profile(request):
    # Edit or view personal profile information
    profile = None
    try:
        profile = request.user.profile
    except Exception:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated')
            return redirect('recommendations:profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'recommendations/profile.html', {'form': form})


def custom_logout(request):
    """Custom logout view that redirects to home immediately"""
    logout(request)
    return HttpResponseRedirect(reverse('recommendations:index'))
