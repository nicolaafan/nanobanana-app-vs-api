"""Turn-by-turn comparison widget: Gemini app outputs vs Interactions API outputs."""

import base64
import io
import json
import uuid
from pathlib import Path

from IPython.display import HTML
from PIL import Image

_TEMPLATE = """
<div id="__UID__" style="max-width:__WIDTH__px;font-family:system-ui,sans-serif">
  <div style="display:flex;align-items:center;gap:14px;margin:4px 0 2px">
    <input data-role="turn" type="range" min="0" value="0" step="1" style="flex:0 0 240px">
    <strong data-role="title" style="font-size:14px"></strong>
  </div>
  <div data-role="caption" style="font-size:12.5px;color:#666;margin:2px 0 8px;min-height:3.2em"></div>
  <div data-role="stage" style="position:relative;line-height:0;user-select:none;cursor:col-resize;touch-action:none">
    <img data-role="app" style="width:100%;display:block">
    <div data-role="clip" style="position:absolute;inset:0;overflow:hidden">
      <img data-role="api" style="width:100%;display:block">
    </div>
    <div data-role="line" style="position:absolute;top:0;bottom:0;width:2px;background:#fff;box-shadow:0 0 5px rgba(0,0,0,.8);pointer-events:none"></div>
    <span style="position:absolute;top:8px;left:8px;background:rgba(0,0,0,.55);color:#fff;padding:2px 8px;font-size:12px;border-radius:3px;line-height:1.4">Gemini app</span>
    <span style="position:absolute;top:8px;right:8px;background:rgba(0,0,0,.55);color:#fff;padding:2px 8px;font-size:12px;border-radius:3px;line-height:1.4">API</span>
  </div>
</div>
<script>
(function () {
  const data = __DATA__;
  const root = document.getElementById("__UID__");
  const el = (role) => root.querySelector('[data-role="' + role + '"]');
  const turn = el("turn"), stage = el("stage");
  turn.max = data.app.length - 1;

  function setWipe(pct) {
    pct = Math.max(0, Math.min(100, pct));
    el("clip").style.clipPath = "inset(0 0 0 " + pct + "%)";
    el("line").style.left = "calc(" + pct + "% - 1px)";
  }

  function render() {
    const t = +turn.value;
    el("app").src = "data:image/jpeg;base64," + data.app[t];
    el("api").src = "data:image/jpeg;base64," + data.api[t];
    el("title").textContent = "Turn " + t + " / " + turn.max;
    el("caption").textContent = data.captions[t];
  }

  const pctAt = (e) => {
    const r = stage.getBoundingClientRect();
    return ((e.clientX - r.left) / r.width) * 100;
  };
  let dragging = false;
  stage.addEventListener("pointerdown", (e) => {
    dragging = true;
    stage.setPointerCapture(e.pointerId);
    setWipe(pctAt(e));
  });
  stage.addEventListener("pointermove", (e) => { if (dragging) setWipe(pctAt(e)); });
  stage.addEventListener("pointerup", () => { dragging = false; });
  turn.addEventListener("input", render);

  setWipe(50);
  render();
})();
</script>
"""


def _encode(path: Path, width: int) -> str:
    image = Image.open(path)
    image.thumbnail((width, width))
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, "JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode()


def comparison(app_dir, api_dir, edits, width=1200):
    """Turn slider + wipe slider over the image (left: Gemini app, right: API).

    Expects `0.jpeg` (shared starting image) through `N.jpeg` in both directories.
    """
    app_dir, api_dir = Path(app_dir), Path(api_dir)
    turns = range(len(edits) + 1)
    data = {
        "app": [_encode(app_dir / f"{t}.jpeg", width) for t in turns],
        "api": [_encode(api_dir / f"{t}.jpeg", width) for t in turns],
        "captions": ["Shared starting image."]
        + [f"Edit {t}: {prompt}" for t, prompt in enumerate(edits, 1)],
    }
    uid = f"cmp-{uuid.uuid4().hex[:8]}"
    html = (
        _TEMPLATE.replace("__UID__", uid)
        .replace("__WIDTH__", str(width))
        .replace("__DATA__", json.dumps(data))
    )
    return HTML(html)
