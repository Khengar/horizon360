import math
from typing import List, Dict, Any
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class AttributionCalculator:
    """
    Multi-Touch Attribution Engine.
    Evaluates customer journeys across outbound & inbound channels and computes
    proportional revenue attribution across 5 standard models:
    - First Touch: 100% to first channel exposure
    - Last Touch: 100% to final interaction before conversion
    - Linear: Equal distribution across all touchpoints
    - Time Decay: Exponential decay with 7-day half-life
    - Position Based (U-Shaped): 40% First, 40% Last, 20% Middle
    """

    @classmethod
    def calculate_attribution_weights(cls, touchpoints: List[Any], total_revenue: Decimal = Decimal('0.00')) -> List[Dict[str, Any]]:
        """
        Takes a chronologically ordered list of AttributionTouchpoint records
        for a customer/deal and computes model weights.
        """
        n = len(touchpoints)
        if n == 0:
            return []

        revenue_val = float(total_revenue or 0.0)
        results = []

        if n == 1:
            tp = touchpoints[0]
            tp.first_touch_weight = 1.0
            tp.last_touch_weight = 1.0
            tp.linear_weight = 1.0
            tp.time_decay_weight = 1.0
            tp.position_based_weight = 1.0
            tp.attributed_revenue = Decimal(str(round(revenue_val, 2)))
            tp.save()
            return [tp]

        # 1. Linear weight
        linear_val = 1.0 / n

        # 2. Time decay setup (relative to last touchpoint)
        last_time = touchpoints[-1].occurred_at
        decay_factors = []
        for tp in touchpoints:
            diff_days = max(0.0, (last_time - tp.occurred_at).total_seconds() / 86400.0)
            # 7-day half life
            factor = math.pow(0.5, diff_days / 7.0)
            decay_factors.append(factor)
        sum_decay = sum(decay_factors) or 1.0

        for i, tp in enumerate(touchpoints):
            # First Touch
            first_w = 1.0 if i == 0 else 0.0

            # Last Touch
            last_w = 1.0 if i == (n - 1) else 0.0

            # Linear
            lin_w = linear_val

            # Time Decay
            time_w = decay_factors[i] / sum_decay

            # Position-based (40/40/20)
            if n == 2:
                pos_w = 0.5
            else:
                if i == 0:
                    pos_w = 0.40
                elif i == (n - 1):
                    pos_w = 0.40
                else:
                    middle_count = n - 2
                    pos_w = 0.20 / middle_count

            tp.first_touch_weight = round(first_w, 4)
            tp.last_touch_weight = round(last_w, 4)
            tp.linear_weight = round(lin_w, 4)
            tp.time_decay_weight = round(time_w, 4)
            tp.position_based_weight = round(pos_w, 4)

            # Assign linear attribution share to attributed_revenue by default
            tp.attributed_revenue = Decimal(str(round(revenue_val * lin_w, 2)))
            tp.save()
            results.append(tp)

        return results

    @classmethod
    def get_campaign_channel_breakdown(cls, campaign: Any) -> Dict[str, Any]:
        """
        Aggregates attributed metrics and channel efficiency for a given campaign.
        """
        touchpoints = list(campaign.touchpoints.all())
        channels = {}
        for tp in touchpoints:
            ch = tp.channel
            if ch not in channels:
                channels[ch] = {
                    'channel': ch,
                    'touchpoints_count': 0,
                    'first_touch_conversions': 0,
                    'last_touch_conversions': 0,
                    'linear_attributed_revenue': 0.0,
                    'time_decay_revenue': 0.0,
                }
            channels[ch]['touchpoints_count'] += 1
            if tp.first_touch_weight >= 0.99:
                channels[ch]['first_touch_conversions'] += 1
            if tp.last_touch_weight >= 0.99:
                channels[ch]['last_touch_conversions'] += 1
            channels[ch]['linear_attributed_revenue'] += float(tp.attributed_revenue or 0.0)

        return {
            'total_touchpoints': len(touchpoints),
            'channels': list(channels.values()),
        }
