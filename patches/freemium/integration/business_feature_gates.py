"""Mapping subfitur Business ke source upstream; bukan grant terpisah."""
BUSINESS_GATE_TARGETS = {
    "Location": ("ui/Business/LocationActivity.java",),
    "Opening Hours": ("ui/Business/OpeningHoursActivity.java",),
    "Quick Replies": ("ui/Business/QuickRepliesActivity.java", "ui/Business/QuickRepliesController.java"),
    "Greeting Messages": ("ui/Business/GreetMessagesActivity.java",),
    "Away Messages": ("ui/Business/AwayMessagesActivity.java",),
    "Links to Chat": ("ui/Business/BusinessLinksActivity.java", "ui/Business/BusinessLinksController.java"),
    "Start Page": ("ui/Business/BusinessIntroActivity.java",),
    "Chatbots": ("ui/Business/ChatbotsActivity.java", "ui/Business/BusinessChatbotController.java"),
}
