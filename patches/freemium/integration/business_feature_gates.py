"""Pemetaan delapan subfitur Business ke layar, controller, dan jalur upstream."""
BUSINESS_GATE_TARGETS = {
    "Location": ("ui/Business/LocationActivity.java",),
    "Opening Hours": ("ui/Business/OpeningHoursActivity.java", "ui/Business/OpeningHoursDayActivity.java"),
    "Quick Replies": ("ui/Business/QuickRepliesActivity.java", "ui/Business/QuickRepliesController.java", "ui/Business/ChatAttachAlertQuickRepliesLayout.java"),
    "Greeting Messages": ("ui/Business/GreetMessagesActivity.java",),
    "Away Messages": ("ui/Business/AwayMessagesActivity.java",),
    "Links to Chat": ("ui/Business/BusinessLinksActivity.java", "ui/Business/BusinessLinksController.java"),
    "Start Page": ("ui/Business/BusinessIntroActivity.java",),
    "Chatbots": ("ui/Business/ChatbotsActivity.java", "ui/Business/BusinessChatbotController.java", "ui/Business/ChatbotSheet.java"),
}

BUSINESS_SOURCE_FILES = tuple(dict.fromkeys(
    path for paths in BUSINESS_GATE_TARGETS.values() for path in paths
))
