import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PropensityScorer:
    """
    Predictive Propensity & Send-Time Optimization Engine.
    Uses ONNX Runtime when a compiled model is available, with a deterministic
    Universal Data Model (UDM) feature extraction and scoring engine as fallback.
    """

    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'propensity_model.onnx')

    def __init__(self):
        self._session = None
        self._initialized = False

    def _ensure_session(self):
        if self._initialized:
            return self._session

        self._initialized = True
        if os.path.exists(self.MODEL_PATH):
            try:
                import onnxruntime as ort
                self._session = ort.InferenceSession(self.MODEL_PATH)
                logger.info("ONNX Runtime session initialized for propensity scoring.")
            except Exception as e:
                logger.warning(f"Could not load ONNX model at {self.MODEL_PATH}: {e}. Using UDM heuristic engine.")
                self._session = None
        else:
            self._session = None
        return self._session

    def extract_features(self, customer: Any, campaign: Any) -> Dict[str, Any]:
        """
        Extracts multi-touchpoint behavioral and firmographic feature representations
        from the Universal Data Model (UDM).
        """
        profile = getattr(customer, 'unified_profile', None)
        account = getattr(customer, 'account', None)
        timeline = getattr(customer, 'timeline', []) or []

        # 1. Timeline event frequency and recency
        total_events = len(timeline)
        event_hours = []
        for ev in timeline:
            if isinstance(ev, dict) and 'timestamp' in ev:
                try:
                    dt = datetime.fromisoformat(ev['timestamp'].replace('Z', '+00:00'))
                    event_hours.append(dt.hour)
                except Exception:
                    pass

        # Most frequent activity hour or default to 10 AM
        if event_hours:
            optimal_hour = max(set(event_hours), key=event_hours.count)
        else:
            optimal_hour = 10

        # 2. Deals aggregation
        deals = list(customer.deals.all()) if hasattr(customer, 'deals') else []
        won_deals = [d for d in deals if getattr(d, 'stage', '') == 'won']
        total_won_val = sum(float(getattr(d, 'value', 0) or 0) for d in won_deals)

        # 3. Profile metrics
        eng_score = float(getattr(profile, 'engagement_score', 0.0) or 0.0) if profile else 20.0
        eng_tier = getattr(profile, 'engagement_tier', 'cold') if profile else 'cold'
        lifecycle = getattr(profile, 'lifecycle_stage', 'known') if profile else 'known'
        has_consent = bool(getattr(profile, 'marketing_consent', False)) if profile else True

        return {
            'engagement_score': eng_score,
            'engagement_tier': eng_tier,
            'lifecycle_stage': lifecycle,
            'has_consent': has_consent,
            'total_timeline_events': total_events,
            'deals_count': len(deals),
            'won_deals_count': len(won_deals),
            'won_revenue': total_won_val,
            'account_tier': getattr(account, 'tier', 'standard') if account else 'standard',
            'optimal_hour': optimal_hour,
        }

    def score_customer(self, customer: Any, campaign: Any) -> Dict[str, Any]:
        """
        Evaluates conversion probability, churn risk, and optimal delivery hour.
        """
        features = self.extract_features(customer, campaign)
        session = self._ensure_session()

        if session:
            try:
                # ONNX Inference path
                import numpy as np
                feature_vector = np.array([[
                    features['engagement_score'],
                    features['total_timeline_events'],
                    features['deals_count'],
                    features['won_deals_count'],
                    features['won_revenue'],
                ]], dtype=np.float32)

                input_name = session.get_inputs()[0].name
                outputs = session.run(None, {input_name: feature_vector})
                conv_prob = float(outputs[0][0][0])
                churn_prob = float(outputs[0][0][1]) if outputs[0].shape[1] > 1 else 0.1
                
                return {
                    'conversion_probability': round(min(1.0, max(0.0, conv_prob)), 3),
                    'churn_probability': round(min(1.0, max(0.0, churn_prob)), 3),
                    'optimal_send_hour': features['optimal_hour'],
                    'model_version': 'onnx-v1',
                    'features_snapshot': features,
                }
            except Exception as e:
                logger.warning(f"ONNX inference failed: {e}. Falling back to heuristic.")

        # Deterministic UDM Heuristic Path
        return self._heuristic_score(features)

    def _heuristic_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        # Base conversion probability from engagement score
        eng_factor = features['engagement_score'] / 100.0
        
        tier_boost = {
            'on_fire': 0.35,
            'hot': 0.25,
            'warm': 0.10,
            'cold': -0.05
        }.get(features['engagement_tier'], 0.0)

        deals_boost = min(0.20, features['won_deals_count'] * 0.05)
        timeline_boost = min(0.15, features['total_timeline_events'] * 0.02)

        raw_conv = 0.20 + (eng_factor * 0.35) + tier_boost + deals_boost + timeline_boost
        if not features['has_consent']:
            raw_conv = 0.0

        conv_probability = round(min(0.99, max(0.05, raw_conv)), 3)

        # Churn probability estimation
        churn_risk = False
        raw_churn = 0.10
        if features['lifecycle_stage'] in ['churned', 'dormant']:
            raw_churn = 0.85
            churn_risk = True
        elif features['engagement_tier'] == 'cold' and features['total_timeline_events'] > 2:
            raw_churn = 0.55
            churn_risk = True
        elif features['engagement_score'] < 15:
            raw_churn = 0.40

        churn_probability = round(min(0.95, max(0.02, raw_churn)), 3)

        return {
            'conversion_probability': conv_probability,
            'churn_probability': churn_probability,
            'churn_risk': churn_risk,
            'optimal_send_hour': features['optimal_hour'],
            'model_version': 'udm-heuristic-v1',
            'features_snapshot': features,
        }
