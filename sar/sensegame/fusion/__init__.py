"""SenseCrew fusion hint layer (registry 2370/2371, provisional). Clean-room; synthetic fixtures only.

Fusion never changes POA; only sensegame.search_core.CleanScorer.update does.
Decision B (Discussion #28 comment 19445708): M1_W_KM is None until a cited W exists.
Fusion does not read a numeric M1 width, does not treat a geometric swath as that
width, and does not score M1 through pod, pos, optimal, or update.
The exponential coverage fallback, if used at all, is the labelled model in
GDD v0.5 §4 / §4a and is not M1 detection.
"""
