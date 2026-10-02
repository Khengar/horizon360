import random
from typing import List, Dict, Any

class ThompsonSamplingBandit:
    """
    Contextual Multi-Armed Bandit using Thompson Sampling over Beta distributions.
    Replaces static A/B testing with continuous, real-time creative optimization.
    """

    def select_variant(self, contents: List[Any], exploration_rate: float = 0.05) -> Any:
        """
        Chooses which creative variant to send to a recipient.
        With probability `exploration_rate`, picks a random variant (epsilon-exploration).
        Otherwise samples from Beta(alpha, beta) for each arm (exploitation via probability matching).
        """
        if not contents:
            return None
        if len(contents) == 1:
            return contents[0]

        # Epsilon exploration check
        if exploration_rate > 0 and random.random() < exploration_rate:
            return random.choice(contents)

        best_sample = -1.0
        best_variant = contents[0]

        for variant in contents:
            alpha = max(1.0, float(getattr(variant, 'bandit_alpha', 1.0)))
            beta = max(1.0, float(getattr(variant, 'bandit_beta', 1.0)))
            try:
                sample = random.betavariate(alpha, beta)
            except Exception:
                sample = alpha / (alpha + beta)

            if sample > best_sample:
                best_sample = sample
                best_variant = variant

        return best_variant

    def record_feedback(self, variant: Any, reward: bool) -> None:
        """
        Updates the Beta distribution parameters for the specified variant based on observed outcome:
        - reward=True (e.g. open/click/conversion): alpha += 1
        - reward=False (e.g. bounce or unengaged after window): beta += 1
        """
        if not variant:
            return

        variant.impressions = (variant.impressions or 0) + 1
        if reward:
            variant.bandit_alpha = (variant.bandit_alpha or 1.0) + 1.0
            variant.successes = (variant.successes or 0) + 1
        else:
            variant.bandit_beta = (variant.bandit_beta or 1.0) + 1.0

        variant.save(update_fields=['bandit_alpha', 'bandit_beta', 'impressions', 'successes'])

    def get_distribution_stats(self, contents: List[Any]) -> List[Dict[str, Any]]:
        """
        Calculates win rates, expected values, and current dynamic traffic allocation.
        """
        stats = []
        total_samples = 1000
        win_counts = {c.id: 0 for c in contents}

        for _ in range(total_samples):
            best_id = None
            best_val = -1.0
            for c in contents:
                alpha = max(1.0, float(getattr(c, 'bandit_alpha', 1.0)))
                beta = max(1.0, float(getattr(c, 'bandit_beta', 1.0)))
                try:
                    val = random.betavariate(alpha, beta)
                except Exception:
                    val = alpha / (alpha + beta)
                if val > best_val:
                    best_val = val
                    best_id = c.id
            if best_id:
                win_counts[best_id] += 1

        for c in contents:
            imp = c.impressions or 0
            succ = c.successes or 0
            rate = round((succ / imp * 100), 2) if imp > 0 else 0.0
            allocated_weight = round((win_counts.get(c.id, 0) / total_samples) * 100, 1)

            stats.append({
                'id': c.id,
                'variant_name': c.variant_name,
                'impressions': imp,
                'successes': succ,
                'conversion_rate': rate,
                'traffic_weight': allocated_weight,
                'alpha': round(c.bandit_alpha, 1),
                'beta': round(c.bandit_beta, 1),
            })

        return stats
