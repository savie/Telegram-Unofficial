"""Stories: buka gate stealth, views kedaluwarsa, dan limit caption/expiry client-side."""
from ..integration.premium_feature_gates import patch_local_premium_checks

TARGETS = (
    "ui/Stories/StealthModeAlert.java",
    "ui/Stories/SelfStoryViewsPage.java",
    "ui/Stories/StoriesController.java",
    "ui/Stories/recorder/CaptionContainerView.java",
    "ui/Stories/recorder/CaptionStory.java",
)


def patch_stealth_mode(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))


def patch_expired_story_views(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))


def patch_stories_controller(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))



def patch_caption_container_view(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 2),
    ))



def patch_caption_story(source: str) -> str:
    return patch_local_premium_checks(source, (
        ("UserConfig.getInstance(currentAccount).isPremium()", "TeleBetaFreemium.hasAllAccess(currentAccount)", 1),
    ))
