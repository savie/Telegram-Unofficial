"""Telegram Business: validasi source upstream untuk seluruh delapan subfitur."""
from ..integration.business_feature_gates import BUSINESS_GATE_TARGETS, BUSINESS_SOURCE_FILES

TARGETS = BUSINESS_SOURCE_FILES

# Seluruh operasi tetap memakai controller dan request Telegram upstream.
# Gate lokal membuka entry point; keputusan server tetap menjadi otoritas operasi.
SERVER_BACKED_FEATURES = tuple(BUSINESS_GATE_TARGETS)
