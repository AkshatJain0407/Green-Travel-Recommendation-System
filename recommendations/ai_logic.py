"""
AI Logic Module for Green Travel Recommendations
Rule-based intelligent decision-making system for eco-friendly transport selection
"""

class TransportOption:
    """Represents a transport option with emissions and green score"""
    def __init__(self, name, emission_factor, base_score):
        self.name = name
        self.emission_factor = emission_factor  # kg CO2 per km
        self.base_score = base_score  # base green score 0-100
    
    def calculate_emission(self, distance_km):
        """Calculate CO2 emission for given distance"""
        return round(self.emission_factor * distance_km, 2)
    
    def calculate_green_score(self, distance_km):
        """Calculate green score (0-100, higher is greener)"""
        return self.base_score


class GreenTravelAI:
    """
    AI Decision Logic Engine for Green Travel Recommendations
    Uses rule-based intelligence to recommend eco-friendly options
    """
    
    # Transport options with emission factors and green scores
    TRANSPORTS = {
        'bus': TransportOption('Bus', 0.105, 90),
        'train': TransportOption('Train', 0.041, 85),
        'ev': TransportOption('Electric Vehicle', 0.075, 80),
        'car': TransportOption('Car (Petrol)', 0.192, 45),
        'flight': TransportOption('Flight', 0.255, 30),
        'bike': TransportOption('Bike/Walk', 0.08, 100),
    }
    
    # Cost estimates in INR per km (rough averages)
    COST_PER_KM_INR = {
         'bus': 6.0,
    'train': 3.0,
    'ev': 1.5,
    'car': 10.0,
    'flight': 20.0,
    'bike': 2.5
    }

    # Average speeds (km/h) used to estimate duration when Google duration isn't provided
    AVERAGE_SPEED_KMH = {
        'bus': 50,
        'train': 80,
        'ev': 60,
        'car': 60,
        'flight': 800,
        'bike': 50,
    }

    @staticmethod
    def get_transport_options(distance_km):
        """
        AI Decision Rules:
        - Short distance (<= 100 km): Bike, Bus, Train, Car, EV
        - Medium distance (101-300 km): Train, EV, Bus, Car, Flight
        - Long distance (> 300 km): Flight, Train, EV, Car
        """
        options = {}

        if distance_km <= 100:
            # SHORT DISTANCE: Prioritize public transport & bikes
            suitable = ['bike', 'bus', 'train', 'car', 'ev']
        elif distance_km <= 300:
            # MEDIUM DISTANCE: Train and EV are optimal
            suitable = ['train', 'ev', 'bus', 'car', 'flight']
        else:
            # LONG DISTANCE: Flight or train
            suitable = ['flight', 'train', 'ev', 'car']

        for transport in suitable:
            if transport in GreenTravelAI.TRANSPORTS:
                options[transport] = GreenTravelAI.TRANSPORTS[transport]

        return options
    
    @staticmethod
    def calculate_recommendations(distance_km, google_durations=None, passengers=1):
        """
        Calculate emissions and green scores for all transport options
        Returns sorted list by green score (highest first)
        """
        options = GreenTravelAI.get_transport_options(distance_km)
        results = []
        
        for name, transport in options.items():
            emission = transport.calculate_emission(distance_km)
            green_score = transport.calculate_green_score(distance_km)

            # Adjust green score based on distance suitability
            adjusted_score = green_score
            if distance_km < 300 and name in ['bus', 'bike']:
                adjusted_score = min(100, green_score + 10)
            elif 300 <= distance_km < 700 and name in ['train', 'ev']:
                adjusted_score = min(100, green_score + 5)

            # Cost in INR (rounded)
            cost_per_km = GreenTravelAI.COST_PER_KM_INR.get(name, 0.0)
            cost_inr = round(cost_per_km * distance_km, 2)

            # Duration estimation: prefer Google-provided per-mode durations when available
            preferred_mode = None
            if name in ['car', 'ev']:
                preferred_mode = 'driving'
            elif name in ['bus', 'train']:
                preferred_mode = 'transit'
            elif name == 'bike':
                preferred_mode = 'bicycling'
            elif name == 'flight':
                preferred_mode = None

            duration_seconds = None
            if google_durations and preferred_mode and preferred_mode in google_durations:
                try:
                    duration_seconds = int(google_durations[preferred_mode])
                except Exception:
                    duration_seconds = None

            if duration_seconds is None:
                # fallback to speed-based estimate
                base_speed = GreenTravelAI.AVERAGE_SPEED_KMH.get(name, 50)
                # Adjust speeds for city vs highway based on distance
                if distance_km < 50:
                    # City speeds for short distances
                    if name in ['car', 'ev']:
                        speed = 40.0  # km/h
                    elif name in ['bus', 'train']:
                        speed = 50.0  # km/h
                    elif name == 'bike':
                        speed = 15.0  # km/h
                    else:
                        speed = base_speed
                else:
                    # Highway speeds for longer distances
                    speed = base_speed
                duration_hours = distance_km / max(1e-6, speed)
                duration_seconds = int(duration_hours * 3600)

            # For flights, use flight-specific speed if no Google duration
            if name == 'flight' and (not google_durations or 'flight' not in google_durations):
                speed = GreenTravelAI.AVERAGE_SPEED_KMH.get('flight', 800)
                duration_hours = distance_km / max(1e-6, speed)
                duration_seconds = int(duration_hours * 3600)

            # Human-friendly duration text
            hrs = duration_seconds // 3600
            mins = (duration_seconds % 3600) // 60
            if hrs:
                duration_text = f"{hrs}h {mins}m"
            else:
                duration_text = f"{mins}m"

            # divide costs/emissions per passenger when relevant
            per_person_cost = round(cost_inr / max(1, passengers), 2)
            per_person_emission = round(emission / max(1, passengers), 2)

            results.append({
                'transport': name,
                'emission_kg': emission,
                'emission_per_person_kg': per_person_emission,
                'green_score': adjusted_score,
                'cost_inr': cost_inr,
                'cost_per_person_inr': per_person_cost,
                'duration_seconds': duration_seconds,
                'duration_text': duration_text,
            })
        
        # Sort by green score (highest first)
        results.sort(key=lambda x: (-x['green_score'], x['emission_kg']))
        return results
    
    @staticmethod
    def get_best_recommendation(distance_km, google_durations=None, passengers=1):
        """Get the single best recommendation"""
        recommendations = GreenTravelAI.calculate_recommendations(distance_km, google_durations, passengers)
        if recommendations:
            return recommendations[0]
        return None
    
    @staticmethod
    def get_eco_message(green_score, transport_name, distance_km):
        """Generate eco-friendly message based on green score and distance"""
        if green_score >= 90:
            return f"🌱 Excellent choice! {transport_name.title()} is the greenest option for this {distance_km} km journey."
        elif green_score >= 75:
            return f"✅ Good choice! {transport_name.title()} is a sustainable option for this distance."
        elif green_score >= 50:
            return f"⚠️ Moderate option. Consider {transport_name.title()} but explore greener alternatives if possible."
        else:
            return f"❌ High emissions. {transport_name.title()} has significant environmental impact. Choose greener options."
    
    @staticmethod
    def compare_with_flight(best_option, distance_km):
        """Calculate CO2 saved compared to flight"""
        flight_emission = GreenTravelAI.TRANSPORTS['flight'].calculate_emission(distance_km)
        saved = round(flight_emission - best_option['emission_kg'], 2)
        return max(0, saved)

