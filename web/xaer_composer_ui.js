import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_TARGETS = {
    XaerPonyPromptComposer: "pony",
    XaerZImagePromptComposer: "zimage",
    XaerMiniMaxH3PromptComposer: "minimaxh3",
};

const NODE_MAX_CHARS = {
    pony: 3,
    zimage: 6,
    minimaxh3: 6,
};

const CATEGORY_DEFS = [
    { key: "prefix", label: "PREFIX (Global Lead-in)", badge: "P", color: "#2c4c6e" },
    { key: "character", label: "CHARACTER (Rolled Per Character)", badge: "C", color: "#4e2c6e" },
    { key: "action", label: "ACTION (Pose / Choreography)", badge: "A", color: "#6e472c" },
    { key: "location", label: "LOCATION (Environment)", badge: "L", color: "#2c6e49" },
    { key: "suffix", label: "SUFFIX (Global Closer)", badge: "S", color: "#6e2c3e" },
    { key: "unassigned", label: "UNASSIGNED POOL (Inactive)", badge: "U", color: "#3a3a3a" },
];

const PROTECTED_BULK_CATS = new Set(["prefix", "location", "suffix", "unassigned"]);

function syncCharacterSlotVisibility(node, maxChars) {
    const countWidget = node.widgets?.find((w) => w.name === "character_count");
    const count = countWidget ? Math.min(maxChars, Math.max(1, Number(countWidget.value))) : 1;

    for (let i = 1; i <= maxChars; i++) {
        const w = node.widgets?.find((widget) => widget.name === `character_${i}`);
        if (!w) continue;
        if (!w._origType) {
            w._origType = w.type;
            w._origComputeSize = w.computeSize;
        }
        if (i <= count) {
            w.type = w._origType;
            w.computeSize = w._origComputeSize;
        } else {
            w.type = "converted-widget";
            w.computeSize = () => [0, -4];
            if (!w.value || !w.options?.values?.includes(w.value)) {
                w.value = "Random (Unique)";
            }
        }
    }
    node.setDirtyCanvas(true, true);
}

function collectNodeParams(node) {
    const params = {};
    for (const w of node.widgets || []) {
        if (w.name && w.name !== "xaer_category_containers") {
            params[w.name] = w.value;
        }
    }
    return params;
}

function buildContainerDOM(node, targetNode, layoutWidget) {
    const root = document.createElement("div");
    root.style.cssText = `
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 6px;
        background: #18181b;
        border: 1px solid #333;
        border-radius: 6px;
        font-family: sans-serif;
        font-size: 11px;
        color: #e4e4e7;
        max-height: 540px;
        overflow-y: auto;
        box-sizing: border-box;
    `;

    // Live Prompt Preview Panel
    const previewWrapper = document.createElement("div");
    previewWrapper.style.cssText = `
        display: flex;
        flex-direction: column;
        gap: 4px;
        background: #121215;
        border: 1px solid #3f3f46;
        border-radius: 5px;
        padding: 5px 6px;
    `;

    const previewHeader = document.createElement("div");
    previewHeader.style.cssText = "display:flex; justify-content:space-between; align-items:center;";

    const previewTitle = document.createElement("span");
    previewTitle.textContent = "LIVE PROMPT PREVIEW";
    previewTitle.style.cssText = "font-size:10px; font-weight:bold; color:#a1a1aa; letter-spacing:0.4px;";

    const previewBtns = document.createElement("div");
    previewBtns.style.cssText = "display:flex; gap:4px;";

    const btnPreview = document.createElement("button");
    btnPreview.textContent = "👁 Preview";
    btnPreview.title = "Generate live preview of the prompt line with current seed & toggles";
    btnPreview.style.cssText = "background:#27272a; color:#93c5fd; border:1px solid #3b82f6; border-radius:3px; padding:2px 6px; cursor:pointer; font-size:10px;";

    const btnCopy = document.createElement("button");
    btnCopy.textContent = "📋 Copy";
    btnCopy.title = "Copy preview prompt to clipboard";
    btnCopy.style.cssText = "background:#27272a; color:#e4e4e7; border:1px solid #52525b; border-radius:3px; padding:2px 6px; cursor:pointer; font-size:10px;";

    previewBtns.appendChild(btnPreview);
    previewBtns.appendChild(btnCopy);
    previewHeader.appendChild(previewTitle);
    previewHeader.appendChild(previewBtns);

    const previewBox = document.createElement("div");
    previewBox.textContent = "Click '👁 Preview' or run queue to see the generated line...";
    previewBox.style.cssText = `
        font-family: monospace;
        font-size: 10.5px;
        line-height: 1.35;
        color: #d4d4d8;
        background: #09090b;
        border: 1px solid #27272a;
        border-radius: 4px;
        padding: 5px 6px;
        max-height: 92px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-word;
        user-select: text;
    `;

    previewWrapper.appendChild(previewHeader);
    previewWrapper.appendChild(previewBox);
    root.appendChild(previewWrapper);

    node._updateXaerPreviewText = (text) => {
        previewBox.textContent = text || "(Empty prompt — enable at least one preset or wildcard)";
    };

    async function fetchLivePreview() {
        btnPreview.textContent = "⏳...";
        try {
            const resp = await api.fetchApi("/xaer_composer/preview_prompt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target_node: targetNode,
                    params: collectNodeParams(node),
                }),
            });
            const data = await resp.json();
            if (data.status === "ok") {
                node._updateXaerPreviewText(data.prompt);
            }
        } catch (err) {
            previewBox.textContent = `Preview error: ${err}`;
        } finally {
            btnPreview.textContent = "👁 Preview";
        }
    }

    node._triggerXaerLivePreview = fetchLivePreview;
    btnPreview.onclick = fetchLivePreview;

    btnCopy.onclick = async () => {
        try {
            await navigator.clipboard.writeText(previewBox.textContent || "");
            btnCopy.textContent = "✓ Copied";
            setTimeout(() => {
                btnCopy.textContent = "📋 Copy";
            }, 1200);
        } catch {
            btnCopy.textContent = "Failed";
        }
    };

    // Toolbar
    const toolbar = document.createElement("div");
    toolbar.style.cssText = "display:flex; flex-wrap:wrap; gap:4px; justify-content:space-between; align-items:center;";

    const btnRefresh = document.createElement("button");
    btnRefresh.textContent = "↻ Scan";
    btnRefresh.title = "Scan wildcard directory for new files";
    btnRefresh.style.cssText = "background:#27272a; color:#e4e4e7; border:1px solid #444; border-radius:4px; padding:3px 6px; cursor:pointer; font-size:10px;";

    const btnAllOn = document.createElement("button");
    btnAllOn.textContent = "☑ All On (Char/Act)";
    btnAllOn.title = "Enable all Character and Action wildcards (leaves Prefix, Location, and Suffix untouched)";
    btnAllOn.style.cssText = "background:#253d2c; color:#d4f7dc; border:1px solid #3b6e49; border-radius:4px; padding:3px 6px; cursor:pointer; font-size:10px;";

    const btnAllOff = document.createElement("button");
    btnAllOff.textContent = "☐ All Off (Char/Act)";
    btnAllOff.title = "Disable all Character and Action wildcards (leaves Prefix, Location, and Suffix untouched)";
    btnAllOff.style.cssText = "background:#3d2529; color:#f7d4d9; border:1px solid #6e3b44; border-radius:4px; padding:3px 6px; cursor:pointer; font-size:10px;";

    const btnSave = document.createElement("button");
    btnSave.textContent = "💾 Save";
    btnSave.title = "Save current layout & toggles as default in node_config.json";
    btnSave.style.cssText = "background:#1e3a5f; color:#fff; border:1px solid #3b82f6; border-radius:4px; padding:3px 6px; cursor:pointer; font-size:10px;";

    toolbar.appendChild(btnRefresh);
    toolbar.appendChild(btnAllOn);
    toolbar.appendChild(btnAllOff);
    toolbar.appendChild(btnSave);
    root.appendChild(toolbar);

    const containersWrapper = document.createElement("div");
    containersWrapper.style.cssText = "display:flex; flex-direction:column; gap:6px;";
    root.appendChild(containersWrapper);

    let state = {};
    function loadStateFromWidget() {
        try {
            state = JSON.parse(layoutWidget.value || "{}");
        } catch {
            state = {};
        }
        for (const c of CATEGORY_DEFS) {
            if (!Array.isArray(state[c.key])) state[c.key] = [];
        }
    }
    loadStateFromWidget();
    node._reloadXaerContainerState = () => {
        loadStateFromWidget();
        render();
    };

    let dragPayload = null;

    function commitState() {
        layoutWidget.value = JSON.stringify(state);
        if (layoutWidget.callback) layoutWidget.callback(layoutWidget.value);
        render();
        fetchLivePreview();
    }

    function setBulkNonProtected(enabledVal) {
        for (const catDef of CATEGORY_DEFS) {
            if (PROTECTED_BULK_CATS.has(catDef.key)) continue;
            for (const item of state[catDef.key] || []) {
                item.enabled = enabledVal;
            }
        }
        commitState();
    }

    btnAllOn.onclick = () => setBulkNonProtected(true);
    btnAllOff.onclick = () => setBulkNonProtected(false);

    function moveItem(fromCat, index, toCat, targetIndex = null) {
        if (!state[fromCat] || !state[fromCat][index]) return;
        const [item] = state[fromCat].splice(index, 1);
        if (targetIndex === null || targetIndex < 0 || targetIndex > state[toCat].length) {
            state[toCat].push(item);
        } else {
            state[toCat].splice(targetIndex, 0, item);
        }
        commitState();
    }

    function render() {
        containersWrapper.innerHTML = "";

        for (const catDef of CATEGORY_DEFS) {
            const box = document.createElement("div");
            box.style.cssText = `
                background: #202024;
                border: 1px solid ${catDef.color};
                border-radius: 5px;
                padding: 4px 6px;
            `;

            box.addEventListener("dragover", (e) => {
                e.preventDefault();
                box.style.background = "#2a2a32";
            });
            box.addEventListener("dragleave", () => {
                box.style.background = "#202024";
            });
            box.addEventListener("drop", (e) => {
                e.preventDefault();
                box.style.background = "#202024";
                if (dragPayload) {
                    moveItem(dragPayload.cat, dragPayload.idx, catDef.key);
                    dragPayload = null;
                }
            });

            const header = document.createElement("div");
            header.style.cssText = `
                font-weight: bold;
                font-size: 10px;
                letter-spacing: 0.4px;
                color: #f4f4f5;
                background: ${catDef.color};
                padding: 2px 6px;
                border-radius: 3px;
                margin-bottom: 4px;
                display: flex;
                justify-content: space-between;
            `;
            const items = state[catDef.key] || [];
            const enabledCount = items.filter((i) => i.enabled).length;
            header.innerHTML = `<span>${catDef.label}</span><span>${enabledCount}/${items.length}</span>`;
            box.appendChild(header);

            const listEl = document.createElement("div");
            listEl.style.cssText = "display:flex; flex-direction:column; gap:3px; min-height:18px;";

            if (items.length === 0) {
                const emptyHint = document.createElement("div");
                emptyHint.textContent = "Drop wildcard here...";
                emptyHint.style.cssText = "color:#71717a; font-style:italic; font-size:10px; padding:2px 4px;";
                listEl.appendChild(emptyHint);
            }

            items.forEach((item, idx) => {
                const row = document.createElement("div");
                row.draggable = true;
                row.style.cssText = `
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 4px;
                    background: ${item.enabled ? "#27272a" : "#1c1c1f"};
                    border: 1px solid ${item.enabled ? "#52525b" : "#2e2e32"};
                    border-radius: 3px;
                    padding: 2px 5px;
                    cursor: grab;
                    opacity: ${item.enabled ? "1" : "0.65"};
                `;

                row.addEventListener("dragstart", (e) => {
                    dragPayload = { cat: catDef.key, idx };
                    e.dataTransfer.effectAllowed = "move";
                });

                row.addEventListener("dragover", (e) => {
                    e.preventDefault();
                });

                row.addEventListener("drop", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (dragPayload) {
                        moveItem(dragPayload.cat, dragPayload.idx, catDef.key, idx);
                        dragPayload = null;
                    }
                });

                const left = document.createElement("label");
                left.style.cssText = "display:flex; align-items:center; gap:5px; cursor:pointer; flex:1; overflow:hidden;";

                const cb = document.createElement("input");
                cb.type = "checkbox";
                cb.checked = !!item.enabled;
                cb.addEventListener("change", () => {
                    item.enabled = cb.checked;
                    commitState();
                });

                const nameSpan = document.createElement("span");
                nameSpan.textContent = item.file.replace(/\.txt$/i, "");
                nameSpan.title = item.file;
                nameSpan.style.cssText = "white-space:nowrap; overflow:hidden; text-overflow:ellipsis;";

                left.appendChild(cb);
                left.appendChild(nameSpan);

                const actions = document.createElement("div");
                actions.style.cssText = "display:flex; gap:2px; flex-shrink:0;";

                const upBtn = document.createElement("button");
                upBtn.textContent = "↑";
                upBtn.title = "Move Up";
                upBtn.style.cssText = "background:#333; color:#ddd; border:none; border-radius:2px; padding:0 4px; cursor:pointer; font-size:10px;";
                upBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (idx > 0) moveItem(catDef.key, idx, catDef.key, idx - 1);
                };

                const downBtn = document.createElement("button");
                downBtn.textContent = "↓";
                downBtn.title = "Move Down";
                downBtn.style.cssText = "background:#333; color:#ddd; border:none; border-radius:2px; padding:0 4px; cursor:pointer; font-size:10px;";
                downBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (idx < items.length - 1) moveItem(catDef.key, idx, catDef.key, idx + 1);
                };

                actions.appendChild(upBtn);
                actions.appendChild(downBtn);

                for (const targetCat of CATEGORY_DEFS) {
                    if (targetCat.key === catDef.key || targetCat.key === "unassigned") continue;
                    const qBtn = document.createElement("button");
                    qBtn.textContent = targetCat.badge;
                    qBtn.title = `Move to ${targetCat.label}`;
                    qBtn.style.cssText = `background:${targetCat.color}; color:#fff; border:none; border-radius:2px; padding:0 4px; cursor:pointer; font-size:9px;`;
                    qBtn.onclick = (e) => {
                        e.stopPropagation();
                        moveItem(catDef.key, idx, targetCat.key);
                    };
                    actions.appendChild(qBtn);
                }

                row.appendChild(left);
                row.appendChild(actions);
                listEl.appendChild(row);
            });

            box.appendChild(listEl);
            containersWrapper.appendChild(box);
        }
    }

    btnRefresh.onclick = async () => {
        const dirWidget = node.widgets?.find((w) => w.name === "wildcard_dir");
        const wildcardDir = dirWidget ? dirWidget.value : "";
        const resp = await api.fetchApi("/xaer_composer/get_layout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ wildcard_dir: wildcardDir, target_node: targetNode }),
        });
        const data = await resp.json();
        if (data.status === "ok" && data.layout) {
            state = data.layout;
            commitState();
        }
    };

    btnSave.onclick = async () => {
        const dirWidget = node.widgets?.find((w) => w.name === "wildcard_dir");
        const wildcardDir = dirWidget ? dirWidget.value : "";
        const resp = await api.fetchApi("/xaer_composer/save_layout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                wildcard_dir: wildcardDir,
                target_node: targetNode,
                layout: state,
            }),
        });
        const data = await resp.json();
        btnSave.textContent = data.status === "ok" ? "✓ Saved" : "Error";
        setTimeout(() => {
            btnSave.textContent = "💾 Save";
        }, 1500);
    };

    render();
    setTimeout(fetchLivePreview, 150);
    return root;
}

app.registerExtension({
    name: "Xaer.WildcardComposer.UI",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        const targetNode = NODE_TARGETS[nodeData.name];
        if (!targetNode) return;
        const maxChars = NODE_MAX_CHARS[targetNode] || 6;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (onNodeCreated) onNodeCreated.apply(this, arguments);

            const layoutWidget = this.widgets?.find((w) => w.name === "category_layout_json");
            if (layoutWidget) {
                layoutWidget.type = "converted-widget";
                layoutWidget.computeSize = () => [0, -4];

                const domEl = buildContainerDOM(this, targetNode, layoutWidget);
                this.addDOMWidget("xaer_category_containers", "custom", domEl, {
                    serialize: false,
                });
            }

            for (const w of this.widgets || []) {
                if (w.name === "category_layout_json" || w.name === "xaer_category_containers") continue;
                const origCb = w.callback;
                w.callback = (val) => {
                    if (origCb) origCb.call(w, val);
                    if (w.name === "character_count") {
                        syncCharacterSlotVisibility(this, maxChars);
                    }
                    if (this._triggerXaerLivePreview) {
                        this._triggerXaerLivePreview();
                    }
                };
            }

            syncCharacterSlotVisibility(this, maxChars);
            this.setSize([420, 860]);
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            if (onConfigure) onConfigure.apply(this, arguments);

            const layoutWidget = this.widgets?.find((w) => w.name === "category_layout_json");
            if (layoutWidget) {
                layoutWidget.type = "converted-widget";
                layoutWidget.computeSize = () => [0, -4];
            }

            const countW = this.widgets?.find((w) => w.name === "character_count");
            if (countW && Number(countW.value) > maxChars) {
                countW.value = maxChars;
            }

            const actionW = this.widgets?.find((w) => w.name === "action_scope");
            if (actionW && !actionW.options?.values?.includes(actionW.value)) {
                actionW.value = "per_character";
            }

            const bulkW = this.widgets?.find((w) => w.name === "wildcard_bulk_override");
            if (bulkW && !bulkW.options?.values?.includes(bulkW.value)) {
                bulkW.value = "Use Individual Toggles";
            }

            const presetW = this.widgets?.find(
                (w) => w.name === "quality_preset" || w.name === "style_preset" || w.name === "camera_preset"
            );
            if (presetW) {
                if (typeof presetW.value === "string" && presetW.value.trim().startsWith("{") && layoutWidget) {
                    layoutWidget.value = presetW.value;
                }
                if (!presetW.options?.values?.includes(presetW.value)) {
                    presetW.value = "None";
                }
            }

            const customTextW = this.widgets?.find(
                (w) => w.name === "custom_quality_tags" || w.name === "custom_style_prefix" || w.name === "custom_camera_direction"
            );
            if (customTextW && typeof customTextW.value === "string" && customTextW.value.trim().startsWith("{")) {
                if (layoutWidget && (!layoutWidget.value || layoutWidget.value === "{}")) {
                    layoutWidget.value = customTextW.value;
                }
                customTextW.value = "";
            }

            if (typeof layoutWidget?.value === "string" && !layoutWidget.value.trim().startsWith("{")) {
                layoutWidget.value = "{}";
            }

            syncCharacterSlotVisibility(this, maxChars);
            if (this._reloadXaerContainerState) {
                this._reloadXaerContainerState();
            }
            if (this._triggerXaerLivePreview) {
                this._triggerXaerLivePreview();
            }
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            if (onExecuted) onExecuted.apply(this, arguments);
            if (message?.preview_text?.[0] && this._updateXaerPreviewText) {
                this._updateXaerPreviewText(message.preview_text[0]);
            }
        };
    },
});