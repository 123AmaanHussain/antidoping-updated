import random
import time
from datetime import datetime, timedelta
import threading
from flask_socketio import SocketIO

class FitnessSimulator:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.running = False
        self.thread = None
        self.athlete_data = {}  # Store simulated data for each athlete
        
        # Define activity patterns
        self.activity_patterns = {
            'resting': {'hr_range': (60, 75), 'steps_per_min': (0, 5)},
            'walking': {'hr_range': (75, 100), 'steps_per_min': (85, 110)},
            'running': {'hr_range': (140, 180), 'steps_per_min': (150, 180)},
            'workout': {'hr_range': (120, 160), 'steps_per_min': (30, 60)}
        }
        
        # Define risk scenarios
        self.risk_scenarios = [
            {
                'name': 'High Intensity Training',
                'condition': lambda hr, hrv: hr > 170 and hrv < 50,
                'message': 'Extended high-intensity activity detected. Monitor recovery.',
                'level': 'medium'
            },
            {
                'name': 'Overtraining Risk',
                'condition': lambda hr, hrv: hr > 150 and hrv < 40,
                'message': 'Potential overtraining detected. Rest recommended.',
                'level': 'high'
            },
            {
                'name': 'Poor Recovery',
                'condition': lambda hr, hrv: hr > 80 and hrv < 30,
                'message': 'Poor recovery indicators. Consider rest day.',
                'level': 'high'
            }
        ]
        
    def start_simulation(self, athlete_id):
        """Start simulation for a specific athlete"""
        if athlete_id not in self.athlete_data:
            self.athlete_data[athlete_id] = {
                'heart_rate': 70,
                'steps': 0,
                'sleep_hours': 0,
                'hrv': 65,
                'last_update': datetime.now(),
                'sleep_start': None,
                'is_sleeping': False,
                'current_activity': 'resting',
                'activity_duration': 0,
                'daily_workout_done': False,
                'calories_burned': 0,
                'stress_level': 50,  # 0-100 scale
                'recovery_score': 85,  # 0-100 scale
                'hydration_level': 100,  # 0-100 scale
                'last_meal_time': datetime.now() - timedelta(hours=2),
                'supplements_taken': []
            }
        
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._simulation_loop)
            self.thread.daemon = True
            self.thread.start()
    
    def _simulate_activity_change(self, data):
        """Simulate random activity pattern changes"""
        if random.random() < 0.1:  # 10% chance to change activity
            activities = list(self.activity_patterns.keys())
            return random.choice(activities)
        return data['current_activity']

    def _simulate_heart_rate(self, current_hr, activity, stress_level):
        """Simulate heart rate with random spikes"""
        hr_range = self.activity_patterns[activity]['hr_range']
        target_hr = random.uniform(*hr_range)
        
        # Random spikes for demo
        if random.random() < 0.05:  # 5% chance of spike
            target_hr += random.uniform(20, 40)
        
        # Add stress influence
        stress_factor = stress_level / 100 * 20
        target_hr += stress_factor
        
        # Gradual change towards target
        hr_change = (target_hr - current_hr) * 0.2
        hr_change += random.uniform(-5, 5)  # More variation
        
        new_hr = current_hr + hr_change
        return max(min(new_hr, 200), 45)

    def _simulate_steps(self, current_steps, activity, duration):
        """Simulate step count based on activity"""
        steps_range = self.activity_patterns[activity]['steps_per_min']
        steps_per_min = random.uniform(*steps_range)
        new_steps = current_steps + (steps_per_min * (duration / 60))
        return new_steps

    def _simulate_hrv(self, heart_rate, stress_level, sleep_hours):
        """Simulate Heart Rate Variability"""
        base_hrv = 100 - (heart_rate * 0.3)  # Lower HR generally means higher HRV
        stress_impact = stress_level * 0.2  # Higher stress reduces HRV
        sleep_impact = sleep_hours * 2  # More sleep improves HRV
        
        hrv = base_hrv - stress_impact + sleep_impact
        hrv += random.uniform(-5, 5)  # Add some variation
        
        return max(min(hrv, 100), 20)  # Keep within realistic bounds

    def _simulate_sleep(self, data):
        """Simulate sleep patterns"""
        current_time = datetime.now()
        hour = current_time.hour
        
        # Start sleep between 21:00 and 23:00
        if not data['is_sleeping'] and 21 <= hour <= 23 and random.random() < 0.3:
            data['is_sleeping'] = True
            data['sleep_start'] = current_time
        
        # Wake up between 6:00 and 8:00
        elif data['is_sleeping'] and 6 <= hour <= 8 and random.random() < 0.3:
            data['is_sleeping'] = False
            if data['sleep_start']:
                sleep_duration = (current_time - data['sleep_start']).total_seconds() / 3600
                data['sleep_hours'] = sleep_duration
                data['sleep_start'] = None

    def _simulate_stress(self, data):
        """Simulate stress levels"""
        base_stress = data['stress_level']
        activity_stress = {
            'resting': -5,
            'walking': 0,
            'running': 10,
            'workout': 15
        }
        
        stress_change = activity_stress[data['current_activity']]
        stress_change += random.uniform(-5, 5)
        
        # Recovery during sleep
        if data['is_sleeping']:
            stress_change -= 10
        
        new_stress = base_stress + (stress_change * 0.1)  # Gradual change
        return max(min(new_stress, 100), 0)

    def _calculate_recovery_score(self, data):
        """Calculate recovery score based on various metrics"""
        hrv_factor = data['hrv']
        sleep_factor = min(data['sleep_hours'] * 10, 80)  # Cap at 8 hours
        stress_factor = 100 - data['stress_level']
        
        recovery_score = (hrv_factor + sleep_factor + stress_factor) / 3
        recovery_score += random.uniform(-5, 5)  # Add variation
        
        return max(min(recovery_score, 100), 0)

    def _simulate_hydration(self, data):
        """Simulate hydration levels"""
        activity_dehydration = {
            'resting': 0.5,
            'walking': 1,
            'running': 3,
            'workout': 2.5
        }
        
        # Calculate time since last update
        time_diff = (datetime.now() - data['last_update']).total_seconds() / 3600
        dehydration_rate = activity_dehydration[data['current_activity']]
        
        # Random hydration events (drinking water)
        if random.random() < 0.1:  # 10% chance of drinking water
            hydration_gain = random.uniform(5, 15)
            data['hydration_level'] = min(100, data['hydration_level'] + hydration_gain)
        
        # Calculate dehydration
        hydration_loss = dehydration_rate * time_diff
        new_hydration = data['hydration_level'] - hydration_loss
        
        return max(min(new_hydration, 100), 0)

    def _simulation_loop(self):
        """Main simulation loop"""
        while self.running:
            current_time = datetime.now()
            
            for athlete_id, data in self.athlete_data.items():
                try:
                    # Calculate time difference since last update
                    time_diff = (current_time - data['last_update']).total_seconds()
                    
                    # Update activity
                    data['current_activity'] = self._simulate_activity_change(data)
                    data['activity_duration'] += time_diff
                    
                    # Update metrics
                    data['heart_rate'] = self._simulate_heart_rate(
                        data['heart_rate'],
                        data['current_activity'],
                        data['stress_level']
                    )
                    
                    data['steps'] = self._simulate_steps(
                        data['steps'],
                        data['current_activity'],
                        time_diff
                    )
                    
                    # Simulate sleep patterns
                    self._simulate_sleep(data)
                    
                    # Update stress levels
                    data['stress_level'] = self._simulate_stress(data)
                    
                    # Update HRV based on current conditions
                    data['hrv'] = self._simulate_hrv(
                        data['heart_rate'],
                        data['stress_level'],
                        data['sleep_hours']
                    )
                    
                    # Update recovery score
                    data['recovery_score'] = self._calculate_recovery_score(data)
                    
                    # Update hydration
                    data['hydration_level'] = self._simulate_hydration(data)
                    
                    # Calculate calories burned
                    met_values = {
                        'resting': 1.0,
                        'walking': 3.5,
                        'running': 8.0,
                        'workout': 6.0
                    }
                    calories_per_min = met_values[data['current_activity']] * 3.5 * 70 / 200
                    data['calories_burned'] += calories_per_min * (time_diff / 60)
                    
                    # Check for risk scenarios
                    risks = []
                    for scenario in self.risk_scenarios:
                        if scenario['condition'](data['heart_rate'], data['hrv']):
                            risks.append({
                                'name': scenario['name'],
                                'message': scenario['message'],
                                'level': scenario['level']
                            })
                    
                    # Emit data via Socket.IO
                    self.socketio.emit('athlete_update', {
                        'athlete_id': athlete_id,
                        'data': {
                            'heart_rate': round(data['heart_rate']),
                            'hrv': round(data['hrv']),
                            'steps': int(data['steps']),
                            'sleep_hours': round(data['sleep_hours'], 1),
                            'activity': data['current_activity'],
                            'calories_burned': int(data['calories_burned']),
                            'stress_level': round(data['stress_level']),
                            'recovery_score': round(data['recovery_score']),
                            'hydration_level': round(data['hydration_level']),
                            'is_sleeping': data['is_sleeping'],
                            'risks': risks
                        }
                    })
                    
                    # Update last update timestamp
                    data['last_update'] = current_time
                    
                except Exception as e:
                    print(f"Error in simulation loop for athlete {athlete_id}: {str(e)}")
            
            time.sleep(1)  # Update every second
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        if self.thread:
            self.thread.join()
