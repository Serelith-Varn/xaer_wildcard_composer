from .nodesh3 import (
    XaerMiniMaxH3PromptComposer,
    XaerMiniMaxH3Ref2VADirector,
    XaerPonyPromptComposer,
    XaerZImagePromptComposer,
)

NODE_CLASS_MAPPINGS = {
    "XaerPonyPromptComposer": XaerPonyPromptComposer,
    "XaerZImagePromptComposer": XaerZImagePromptComposer,
    "XaerMiniMaxH3PromptComposer": XaerMiniMaxH3PromptComposer,
    "XaerMiniMaxH3Ref2VADirector": XaerMiniMaxH3Ref2VADirector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XaerPonyPromptComposer": "Xaer Wildcard Composer (Pony XL)",
    "XaerZImagePromptComposer": "Xaer Wildcard Composer (Z-Image)",
    "XaerMiniMaxH3PromptComposer": "Xaer MiniMax H3 Prompt Composer (9-Slot Ref2VA)",
    "XaerMiniMaxH3Ref2VADirector": "Xaer MiniMax H3 Ref2VA 9-Slot Director",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
