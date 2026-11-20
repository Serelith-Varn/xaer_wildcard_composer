import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const TARGET_NODES = {
  XaerPonyPromptComposer: { target: "pony", maxChars: 3 },
  XaerZImagePromptComposer: { target: "zimage", maxChars: 6 },
  XaerMiniMaxH3PromptComposer: { target: "minimaxh3", maxChars: 6 },
};

const CATEGORIES = [
    { key: "prefix",               label: "PREFIX" },
    { key: "character_head",       label: "CHARACTER HEAD (Per Subject)" },
    { key: "character_torso",      label: "CHARACTER TORSO (Per Subject)" },
    { key: "character_lower_body", label: "CHARACTER LOWER BODY (Per Subject)" },
    { key: "character_wearables",  label: "CHARACTER WEARABLES (Per Subject)" },
    { key: "action",               label: "ACTION" },
    { key: "location",             label: "LOCATION" },
    { key: "suffix",               label: "SUFFIX" },
    { key: "unassigned",           label: "UNASSIGNED" },
];

function emptyLayout() {
  return {
    prefix: [],
    character: [],
    action: [],
    location: [],
    suffix: [],
    unassigned: [],
  };
}

function normalizeLayout(raw) {
  const out = emptyLayout();
  if (!raw || typeof raw !== "object") return out;
  for (const cat of CATEGORIES) {
    const arr = Array.isArray(raw[cat.key]) ? raw[cat.key] : [];
    out[cat.key] = arr
      .filter((x) => x && typeof x.file === "string")
      .map((x) => ({ file: x.file, enabled: Boolean(x.enabled) }));
  }
  return out;
}

function injectStyles() {
  if (document.getElementById("xaer-composer-styles")) return;
  const style = document.createElement("style");
  style.id = "xaer-composer-styles";
  style.textContent = `
    .xaer-panel {
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding: 6px;
      background: #18181f;
      border: 1px solid #303040;
      border-radius: 6px;
      font-family: Inter, Segoe UI, sans-serif;
      font-size: 11px;
      color: #e4e4ec;
      box-sizing: border-box;
      overflow-y: auto;
    }
    .xaer-toolbar {
      display: flex;
      gap: 6px;
      align-items: center;
      justify-content: space-between;
    }
    .xaer-btn {
      background: #282836;
      color: #e4e4ec;
      border: 1px solid #424258;
      border-radius: 4px;
      padding: 3px 8px;
      font-size: 11px;
      cursor: pointer;
    }
    .xaer-btn:hover { background: #343448; }
    .xaer-btn-primary {
      background: #4e3678;
      border-color: #7452ad;
    }
    .xaer-btn-primary:hover { background: #5e4290; }
    .xaer-status {
      font-size: 10px;
      color: #9e9eb8;
      margin-left: auto;
    }
    .xaer-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }
    .xaer-bucket {
      background: #20202a;
      border: 1px solid #343446;
      border-radius: 5px;
      padding: 4px;
      min-height: 54px;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .xaer-bucket.drag-over {
      border-color: #9d6bff;
      background: #272236;
    }
    .xaer-bucket-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 10px;
      font-weight: 700;
      color: #b5a6d6;
      padding-bottom: 2px;
      border-bottom: 1px solid #2e2e3e;
    }
    .xaer-bucket-actions button {
      background: transparent;
      border: none;
      color: #8f8fa8;
      font-size: 9px;
      cursor: pointer;
      padding: 0 3px;
    }
    .xaer-bucket-actions button:hover { color: #ffffff; }
    .xaer-item {
      display: flex;
      align-items: center;
      gap: 5px;
      background: #292936;
      border: 1px solid #3a3a4c;
      border-radius: 4px;
      padding: 2px 5px;
      cursor: grab;
      user-select: none;
    }
    .xaer-item:hover { border-color: #6d5b94; }
    .xaer-item input[type="checkbox"] {
      margin: 0;
      cursor: pointer;
    }
    .xaer-item-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
      font-size: 10.5px;
    }
    .xaer-preview-box {
      background: #121218;
      border: 1px solid #2c2c3c;
      border-radius: 4px;
      padding: 5px;
      font-family: Consolas, monospace;
      font-size: 10.5px;
      color: #cfcfe2;
      max-height: 92px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }
  `;
  document.head.appendChild(style);
}

app.registerExtension({
  name: "Xaer.WildcardCategoryComposer",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    const meta = TARGET_NODES[nodeData.name];
    if (!meta) return;

    injectStyles();

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      if (onNodeCreated) onNodeCreated.apply(this, arguments);

      const node = this;
      const layoutWidget = node.widgets?.find((w) => w.name === "category_layout_json");
      const dirWidget = node.widgets?.find((w) => w.name === "wildcard_dir");
      const countWidget = node.widgets?.find((w) => w.name === "character_count");

      if (layoutWidget) {
        layoutWidget.type = "hidden";
        layoutWidget.computeSize = () => [0, -4];
      }

      let layoutState = emptyLayout();
      try {
        if (layoutWidget?.value) {
          layoutState = normalizeLayout(JSON.parse(layoutWidget.value));
        }
      } catch (_) {
        layoutState = emptyLayout();
      }

      const container = document.createElement("div");
      container.className = "xaer-panel";

      const toolbar = document.createElement("div");
      toolbar.className = "xaer-toolbar";

      const scanBtn = document.createElement("button");
      scanBtn.className = "xaer-btn";
      scanBtn.textContent = "↻ Scan";

      const saveBtn = document.createElement("button");
      saveBtn.className = "xaer-btn xaer-btn-primary";
      saveBtn.textContent = "💾 Save";

      const previewBtn = document.createElement("button");
      previewBtn.className = "xaer-btn";
      previewBtn.textContent = "👁 Preview";

      const statusSpan = document.createElement("span");
      statusSpan.className = "xaer-status";
      statusSpan.textContent = "Ready";

      toolbar.append(scanBtn, saveBtn, previewBtn, statusSpan);

      const grid = document.createElement("div");
      grid.className = "xaer-grid";

      const previewBox = document.createElement("div");
      previewBox.className = "xaer-preview-box";
      previewBox.textContent = "Prompt preview will appear here...";

      container.append(toolbar, grid, previewBox);

      const syncJson = () => {
        if (layoutWidget) {
          layoutWidget.value = JSON.stringify(layoutState);
        }
      };

      const updateCharacterSlotVisibility = () => {
        const activeCount = Number(countWidget?.value || 1);
        for (let i = 1; i <= meta.maxChars; i++) {
          const w = node.widgets?.find((x) => x.name === `character_${i}`);
          if (!w) continue;
          if (i <= activeCount) {
            if (w._origType) w.type = w._origType;
            if (w._origComputeSize) w.computeSize = w._origComputeSize;
          } else {
            if (!w._origType) w._origType = w.type;
            if (!w._origComputeSize) w._origComputeSize = w.computeSize;
            w.type = "hidden";
            w.computeSize = () => [0, -4];
          }
        }
        node.setDirtyCanvas(true, true);
      };

      if (countWidget) {
        const origCb = countWidget.callback;
        countWidget.callback = function () {
          if (origCb) origCb.apply(this, arguments);
          updateCharacterSlotVisibility();
        };
      }

      let dragPayload = null;

      const renderBuckets = () => {
        grid.innerHTML = "";
        for (const cat of CATEGORIES) {
          const bucket = document.createElement("div");
          bucket.className = "xaer-bucket";

          bucket.addEventListener("dragover", (e) => {
            e.preventDefault();
            bucket.classList.add("drag-over");
          });
          bucket.addEventListener("dragleave", () => {
            bucket.classList.remove("drag-over");
          });
          bucket.addEventListener("drop", (e) => {
            e.preventDefault();
            bucket.classList.remove("drag-over");
            if (!dragPayload) return;
            const { fromCat, index } = dragPayload;
            const [moved] = layoutState[fromCat].splice(index, 1);
            if (moved) {
              layoutState[cat.key].push(moved);
              syncJson();
              renderBuckets();
            }
            dragPayload = null;
          });

          const header = document.createElement("div");
          header.className = "xaer-bucket-header";
          const title = document.createElement("span");
          title.textContent = `${cat.label} (${layoutState[cat.key].length})`;

          const actions = document.createElement("div");
          actions.className = "xaer-bucket-actions";

          const allBtn = document.createElement("button");
          allBtn.textContent = "All";
          allBtn.onclick = () => {
            layoutState[cat.key].forEach((x) => (x.enabled = true));
            syncJson();
            renderBuckets();
          };

          const noneBtn = document.createElement("button");
          noneBtn.textContent = "None";
          noneBtn.onclick = () => {
            layoutState[cat.key].forEach((x) => (x.enabled = false));
            syncJson();
            renderBuckets();
          };

          actions.append(allBtn, noneBtn);
          header.append(title, actions);
          bucket.appendChild(header);

          layoutState[cat.key].forEach((entry, idx) => {
            const row = document.createElement("div");
            row.className = "xaer-item";
            row.draggable = true;

            row.addEventListener("dragstart", () => {
              dragPayload = { fromCat: cat.key, index: idx };
            });

            const cb = document.createElement("input");
            cb.type = "checkbox";
            cb.checked = entry.enabled;
            cb.onchange = () => {
              entry.enabled = cb.checked;
              syncJson();
            };

            const lbl = document.createElement("span");
            lbl.className = "xaer-item-label";
            lbl.textContent = entry.file.replace(/\.txt$/i, "");
            lbl.title = entry.file;

            row.append(cb, lbl);
            bucket.appendChild(row);
          });

          grid.appendChild(bucket);
        }
      };

      const fetchLayout = async () => {
        statusSpan.textContent = "Scanning...";
        try {
          const resp = await api.fetchApi("/xaer_composer/get_layout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              wildcard_dir: dirWidget?.value || "",
              target_node: meta.target,
            }),
          });
          const data = await resp.json();
          if (data.status === "ok" && data.layout) {
            layoutState = normalizeLayout(data.layout);
            syncJson();
            renderBuckets();
            statusSpan.textContent = "Synced";
          }
        } catch (err) {
          statusSpan.textContent = "Scan error";
        }
      };

      scanBtn.onclick = fetchLayout;

      saveBtn.onclick = async () => {
        statusSpan.textContent = "Saving...";
        try {
          const resp = await api.fetchApi("/xaer_composer/save_layout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              wildcard_dir: dirWidget?.value || "",
              target_node: meta.target,
              layout: layoutState,
            }),
          });
          const data = await resp.json();
          statusSpan.textContent = data.status === "ok" ? "Saved" : "Save error";
        } catch (_) {
          statusSpan.textContent = "Save error";
        }
      };

      previewBtn.onclick = async () => {
        statusSpan.textContent = "Rolling...";
        const params = {};
        for (const w of node.widgets || []) {
          if (w.name) params[w.name] = w.value;
        }
        try {
          const resp = await api.fetchApi("/xaer_composer/preview_prompt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              target_node: meta.target,
              params,
            }),
          });
          const data = await resp.json();
          if (data.status === "ok") {
            previewBox.textContent = data.prompt || "(empty)";
            statusSpan.textContent = "Previewed";
          }
        } catch (_) {
          statusSpan.textContent = "Preview error";
        }
      };

      const domWidget = node.addDOMWidget("xaer_category_ui", "custom", container, {
        serialize: false,
      });
      domWidget.computeSize = (width) => [Math.max(width, 460), 420];

      const origExecuted = node.onExecuted;
      node.onExecuted = function (output) {
        if (origExecuted) origExecuted.apply(this, arguments);
        if (output?.preview_text?.[0]) {
          previewBox.textContent = output.preview_text[0];
        }
      };

      renderBuckets();
      updateCharacterSlotVisibility();
      if (Object.values(layoutState).every((arr) => arr.length === 0)) {
        fetchLayout();
      }
    };
  },
});