from .nodes import (
    XaerMiniMaxH3PromptComposer,
    XaerPonyPromptComposer,
    XaerZImagePromptComposer,
)

NODE_CLASS_MAPPINGS = {
    "XaerPonyPromptComposer": XaerPonyPromptComposer,
    "XaerZImagePromptComposer": XaerZImagePromptComposer,
    "XaerMiniMaxH3PromptComposer": XaerMiniMaxH3PromptComposer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XaerPonyPromptComposer": "Xaer Wildcard Composer (Pony XL)",
    "XaerZImagePromptComposer": "Xaer Wildcard Composer (Z-Image)",
    "XaerMiniMaxH3PromptComposer": "Xaer Wildcard Composer (MiniMax H3)",
}

WEB_DIRECTORY = "./web"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]