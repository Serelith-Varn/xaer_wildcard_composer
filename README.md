# Xaer Wildcard Composer for ComfyUI

A multi-model ComfyUI custom node suite designed to dynamically compose prompts from `.txt` wildcard collections for **Pony XL**, **Z-Image Turbo**, and **MiniMax H3**.

## Features

* **Three Dedicated Model Nodes (`Xaer'Thalassor/Prompting`):**
  * **Xaer Wildcard Composer (Pony XL):** Quality/score presets or custom tags, tag deduplication, automatic subject count tags (`1girl`, `2girls`, `1person`), and `BREAK` separators between characters.
  * **Xaer Wildcard Composer (Z-Image Turbo):** Natural-language descriptive prose with built-in or custom camera/lighting lead-ins and clean subject grouping.
  * **Xaer Wildcard Composer (MiniMax H3):** Multi-section cinematic prompts (`[Subject 1]`, `[Subject 2]`, `[Environment & Atmosphere]`, `[Camera & Cinematography]`) to prevent character drift in video generation.
* **Interactive In-Node Category Containers:** Drag-and-drop wildcards between `PREFIX`, `CHARACTER`, `ACTION`, `LOCATION`, `SUFFIX`, and `UNASSIGNED POOL`, reorder within containers, toggle bulk `All On / All Off (Char/Act)` without touching `Prefix`, `Location`, or `Suffix`, and save defaults to `node_config.json`.
* **Live Prompt Preview:** Built-in preview console inside each node with instant updates and one-click clipboard copy.
* **Unique Multi-Character Roster (`xaer_characters.txt`):** Supports `1` to `6` character slots with zero-duplicate `Random (Unique)` sampling or explicit dropdown picks.
* **Dynamic Wildcard Syntax & Sanitization:** Recursively resolves `{option1|option2|option3}` and `{|optional}` brace syntax, strips structured armor/field labels, and normalizes weights.

## Installation

```bash
cd ComfyUI/custom_nodes
git clone [https://github.com/Serelith-Varn/xaer_wildcard_composer.git](https://github.com/Serelith-Varn/xaer_wildcard_composer.git)