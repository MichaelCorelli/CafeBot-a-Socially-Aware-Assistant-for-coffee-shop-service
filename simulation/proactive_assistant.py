import time
import numpy as np
from threading import Thread, Lock, Event
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json

class InteractionPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class User:
    id: str
    position: Tuple[float, float]
    first_seen: float
    last_seen: float
    current_zone: Optional[str]
    dwell_time: float
    assisted: bool
    interaction_count: int
    behavior_pattern: str  #'browsing', 'waiting', 'confused', 'leaving'
    
@dataclass
class Intervention:
    user_id: str
    zone: str
    position: Tuple[float, float]
    dwell_time: float
    priority: InteractionPriority
    message: str
    timestamp: float
    reason: str

class ProactiveAssistant:
    
    def __init__(self, perception_module, robot_position_callback):
        self.perception = perception_module
        self.get_robot_position = robot_position_callback
        self.monitoring_active = False
        self.monitor_thread = None
        self.stop_event = Event()
        self.users: Dict[str, User] = {}
        self.user_id_counter = 0
        
        self.interaction_zones = {
            'menu_area': {
                'center': (-6, 0),
                'radius': 2.0,
                'dwell_threshold': 15,
                'priority': InteractionPriority.MEDIUM,
                'max_interventions': 2
            },
            'counter': {
                'center': (-6, 0),
                'radius': 1.5,
                'dwell_threshold': 10,
                'priority': InteractionPriority.HIGH,
                'max_interventions': 3
            },
            'table_area': {
                'center': (0, 0),
                'radius': 5.0,
                'dwell_threshold': 60,
                'priority': InteractionPriority.LOW,
                'max_interventions': 1
            },
            'entrance': {
                'center': (8, 0),
                'radius': 2.0,
                'dwell_threshold': 5,
                'priority': InteractionPriority.HIGH,
                'max_interventions': 1
            },
            'waiting_area': {
                'center': (4, 4),
                'radius': 2.0,
                'dwell_threshold': 30,
                'priority': InteractionPriority.MEDIUM,
                'max_interventions': 1
            }
        }
        self.pending_interventions: List[Intervention] = []
        self.completed_interventions: List[Intervention] = []
        self._lock = Lock()
        self.behavior_thresholds = {
            'movement_threshold': 0.5,
            'confusion_dwell': 20,
            'leaving_speed': 1.0
        }
        self.stats = {
            'total_users_tracked': 0,
            'interventions_triggered': 0,
            'successful_interventions': 0,
            'average_dwell_time': 0.0
        }
        
        logging.basicConfig(level=logging.INFO)
    
    def start_monitoring(self, pepper):
        if not self.monitoring_active:
            self.monitoring_active = True
            self.stop_event.clear()
            self.monitor_thread = Thread(
                target=self._monitoring_loop,
                args=(pepper,),
                daemon=True
            )
            self.monitor_thread.start()
            logging.info("Proactive monitoring system activated")
    
    def stop_monitoring(self):
        if self.monitoring_active:
            self.monitoring_active = False
            self.stop_event.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=3)
            logging.info(f"Monitoring stopped. Stats: {json.dumps(self.stats, indent=2)}")
    
    def _monitoring_loop(self, pepper):
        while self.monitoring_active and not self.stop_event.is_set():
            try:
                self.perception.update_semantic_map(pepper)
                detected_humans = self._detect_humans()
                self._update_user_tracking(detected_humans)
                self._analyze_user_behaviors()
                self._check_intervention_triggers()
                self._cleanup_old_data()
                self._update_statistics()
                
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"Monitoring error: {e}", exc_info=True)
                time.sleep(2)
    
    def _detect_humans(self) -> List[Dict]:
        semantic_map = self.perception.get_dynamic_semantic_map()
        humans = []
        human_labels = ['person', 'human', 'customer', 'user', 'visitor']
        
        for item in semantic_map:
            label, x, y, z = item
            if any(h_label in label.lower() for h_label in human_labels):
                humans.append({
                    'position': (x, y),
                    'height': z,
                    'timestamp': time.time(),
                    'confidence': 0.9
                })
        
        return humans
    
    def _update_user_tracking(self, current_humans: List[Dict]):
        current_time = time.time()
        association_threshold = 1.5
        matched_detections = []
        for user_id, user in list(self.users.items()):
            if hasattr(user, 'velocity'):
                predicted_pos = (
                    user.position[0] + user.velocity[0] * 0.5,
                    user.position[1] + user.velocity[1] * 0.5
                )
            else:
                predicted_pos = user.position
            best_match = None
            best_distance = association_threshold
            
            for idx, human in enumerate(current_humans):
                if idx not in matched_detections:
                    dist = np.linalg.norm(
                        np.array(human['position']) - np.array(predicted_pos)
                    )
                    if dist < best_distance:
                        best_match = idx
                        best_distance = dist
            
            if best_match is not None:
                new_pos = current_humans[best_match]['position']
                time_diff = current_time - user.last_seen
                if time_diff > 0:
                    velocity = (
                        (new_pos[0] - user.position[0]) / time_diff,
                        (new_pos[1] - user.position[1]) / time_diff
                    )
                    user.velocity = velocity
                user.position = new_pos
                user.last_seen = current_time
                user.dwell_time = current_time - user.first_seen
                user.current_zone = self._get_current_zone(new_pos)
                
                matched_detections.append(best_match)
            else:
                if current_time - user.last_seen > 10:
                    del self.users[user_id]
                    logging.info(f"User {user_id} left the environment")

        for idx, human in enumerate(current_humans):
            if idx not in matched_detections:
                self.user_id_counter += 1
                new_id = f"user_{self.user_id_counter:04d}"
                
                self.users[new_id] = User(
                    id=new_id,
                    position=human['position'],
                    first_seen=current_time,
                    last_seen=current_time,
                    current_zone=self._get_current_zone(human['position']),
                    dwell_time=0.0,
                    assisted=False,
                    interaction_count=0,
                    behavior_pattern='browsing'
                )
                
                self.stats['total_users_tracked'] += 1
                logging.info(f"New user {new_id} detected at {human['position']}")
    
    def _get_current_zone(self, position: Tuple[float, float]) -> Optional[str]:
        for zone_name, zone_data in self.interaction_zones.items():
            distance = np.linalg.norm(
                np.array(position) - np.array(zone_data['center'])
            )
            if distance <= zone_data['radius']:
                return zone_name
        return None
    
    def _analyze_user_behaviors(self):
        current_time = time.time()
        
        for user in self.users.values():
            if current_time - user.last_seen > 5:
                continue

            if hasattr(user, 'velocity'):
                speed = np.linalg.norm(user.velocity)
                if speed < 0.1 and user.dwell_time > 20:
                    if user.current_zone == 'menu_area':
                        user.behavior_pattern = 'confused'
                    else:
                        user.behavior_pattern = 'waiting'
                elif speed > self.behavior_thresholds['leaving_speed']:
                    exit_pos = self.interaction_zones['entrance']['center']
                    to_exit = np.array(exit_pos) - np.array(user.position)
                    if np.dot(user.velocity, to_exit) > 0:
                        user.behavior_pattern = 'leaving'
                else:
                    user.behavior_pattern = 'browsing'
            if (user.current_zone == 'menu_area' and 
                user.dwell_time > self.behavior_thresholds['confusion_dwell']):
                user.behavior_pattern = 'confused'
    
    def _check_intervention_triggers(self):
        current_time = time.time()
        
        with self._lock:
            for user in self.users.values():
                if user.assisted and (current_time - user.last_seen) < 60:
                    continue
                
                if user.behavior_pattern == 'leaving':
                    continue
                
                if user.current_zone:
                    zone_data = self.interaction_zones[user.current_zone]
                    
                    trigger = False
                    priority = zone_data['priority']
                    reason = ""
                    
                    if user.dwell_time > zone_data['dwell_threshold']:
                        trigger = True
                        reason = f"Extended dwell time ({user.dwell_time:.0f}s)"
                    
                    if user.behavior_pattern == 'confused':
                        trigger = True
                        priority = InteractionPriority.HIGH
                        reason = "User appears confused"
                    
                    if (user.current_zone == 'entrance' and 
                        user.interaction_count == 0 and
                        user.dwell_time > 3):
                        trigger = True
                        priority = InteractionPriority.URGENT
                        reason = "New visitor at entrance"
                    
                    if trigger:
                        zone_interventions = sum(
                            1 for i in self.completed_interventions
                            if i.user_id == user.id and i.zone == user.current_zone
                        )
                        
                        if zone_interventions < zone_data['max_interventions']:
                            message = self._generate_contextual_message(
                                user, reason
                            )
                            
                            intervention = Intervention(
                                user_id=user.id,
                                zone=user.current_zone,
                                position=user.position,
                                dwell_time=user.dwell_time,
                                priority=priority,
                                message=message,
                                timestamp=current_time,
                                reason=reason
                            )
                            
                            self._add_intervention(intervention)
                            user.assisted = True
                            user.interaction_count += 1
    
    def _generate_contextual_message(self, user: User, reason: str) -> str:
        zone = user.current_zone
        behavior = user.behavior_pattern
        messages = {
            ('menu_area', 'confused'): [
                "I see you're looking at our menu. Can I explain our specialties?",
                "Need help choosing? Our cappuccino is very popular today!",
                "Would you like me to recommend something based on your preferences?"
            ],
            ('menu_area', 'browsing'): [
                "Take your time browsing. I'm here if you need any information.",
                "Our special today is the cornetto with cappuccino combo."
            ],
            ('counter', 'waiting'): [
                "Thank you for waiting. Someone will be with you shortly.",
                "While you wait, would you like to hear about our loyalty program?"
            ],
            ('entrance', 'browsing'): [
                "Welcome! Would you like a table or will this be takeaway?",
                "Good morning! First time here? Let me show you our menu.",
                "Welcome to CaféBot Café! How can I make your day better?"
            ],
            ('table_area', 'waiting'): [
                "Is everything alright with your experience so far?",
                "Can I get you anything else while you enjoy your time here?",
                "I hope you're enjoying your visit. Let me know if you need anything."
            ]
        }
        
        key = (zone, behavior)
        if key in messages:
            options = messages[key]
        elif zone in ['menu_area', 'counter', 'entrance', 'table_area']:
            options = messages.get(
                (zone, 'browsing'),
                ["Hello! How can I assist you today?"]
            )
        else:
            options = ["Is there anything I can help you with?"]
        idx = min(user.interaction_count, len(options) - 1)
        return options[idx]
    
    def _add_intervention(self, intervention: Intervention):

        self.pending_interventions.append(intervention)
        self.pending_interventions.sort(
            key=lambda x: (-x.priority.value, x.timestamp)
        )
        
        self.stats['interventions_triggered'] += 1
        logging.info(
            f"Intervention queued: {intervention.reason} "
            f"for {intervention.user_id} (Priority: {intervention.priority.name})"
        )
    
    def get_next_intervention(self) -> Optional[Intervention]:
        with self._lock:
            if self.pending_interventions:
                intervention = self.pending_interventions.pop(0)
                self.completed_interventions.append(intervention)
                return intervention
        return None
    
    def _cleanup_old_data(self):
        current_time = time.time()
        to_remove = [
            uid for uid, user in self.users.items()
            if current_time - user.last_seen > 60
        ]
        for uid in to_remove:
            del self.users[uid]
        if len(self.completed_interventions) > 100:
            self.completed_interventions = self.completed_interventions[-100:]
    
    def _update_statistics(self):
        if self.users:
            dwell_times = [u.dwell_time for u in self.users.values()]
            self.stats['average_dwell_time'] = np.mean(dwell_times)
    
    def get_environment_status(self) -> Dict:
        with self._lock:
            return {
                'active_users': len(self.users),
                'pending_interventions': len(self.pending_interventions),
                'user_zones': {
                    zone: sum(1 for u in self.users.values() 
                             if u.current_zone == zone)
                    for zone in self.interaction_zones.keys()
                },
                'behavior_distribution': {
                    behavior: sum(1 for u in self.users.values()
                                 if u.behavior_pattern == behavior)
                    for behavior in ['browsing', 'waiting', 'confused', 'leaving']
                },
                'statistics': self.stats
            }