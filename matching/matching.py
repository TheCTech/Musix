import logging
from rapidfuzz import fuzz

from matching.aliases import TrackAnswerAliases
from utils.utils import normalize

logger = logging.getLogger(__name__)

def analyze_guess(user_input: str, answer_aliases: TrackAnswerAliases):
    user_input = normalize(user_input)

    scores: list[tuple[str, float]] = []
    for artist in answer_aliases.artists:
        scores.append(("artist", fuzz.ratio(user_input, artist)))
    for title in answer_aliases.names:
        scores.append(("title", fuzz.ratio(user_input, title)))
    for both in answer_aliases.both:
        scores.append(("both", fuzz.ratio(user_input, both)))

    logger.debug(scores)

    best = max(scores, key=lambda x: x[1])

    best_type = best[0]
    best_score = best[1]

    if best_score >= 90:
        quality = "perfect"
    elif best_score >= 75:
        quality = "close"
    elif best_score >= 50:
        quality = "partial"
    else:
        quality = "bad"

    return {
        "match_type": best_type,
        "score": round(best_score, 2),
        "quality": quality
    }