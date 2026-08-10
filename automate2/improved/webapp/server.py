"""
server.py - BOM UAT Automation Dashboard (Flask + SSE + Live View + Fast Interrupt)
"""
import sys, os, json, queue, threading, traceback, time, uuid, base64
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, Response, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright
from config import SCREENSHOT_DIR, REPORT_DIR, ROLE_CREDENTIALS
from loader import load_testcases, load_nav_matrix
from login import login
from verifiers import run_verification
from reporter import save_report

app  = Flask(__name__, static_folder="static", static_url_path="/static")
BASE = os.path.dirname(os.path.abspath(__file__))

# ── Global state ──────────────────────────────────────────────────────────────
_state = {
    "running": False,
    "stop":    False,
    "results": [],
    "total":   0,
    "done":    0,
    "pass":    0,
    "fail":    0,
    "skip":    0,
    "run_id":  None,
    "latest_ss": None,
}

_active_ctx = None
_active_page = None
_ctx_lock = threading.Lock()

_sse_queues: dict[str, queue.Queue] = {}
_sse_lock = threading.Lock()

try:
    load_testcases()
    load_nav_matrix()
except Exception as e:
    print(f"Loader cache pre-warm warning: {e}", sys.stderr)


def _broadcast(event_type: str, data: dict):
    payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
    with _sse_lock:
        for q in list(_sse_queues.values()):
            try:
                q.put(payload)
            except Exception:
                pass

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE, "static"), "index.html")

@app.route("/screenshots/<path:name>")
def serve_screenshot(name):
    return send_from_directory(SCREENSHOT_DIR, name)

@app.route("/api/testcases")
def api_testcases():
    try:
        perm  = request.args.getlist("type") or None
        roles = request.args.getlist("role") or None
        limit = request.args.get("limit", type=int, default=None)
        df    = load_testcases(permission_types=perm, roles=roles, limit=limit)
        df    = df.fillna("")
        cols  = [c for c in ["TC ID","Module","Function","Role","Permission Type","ขั้นตอนทดสอบ","ผลที่คาดหวัง"] if c in df.columns]
        rows  = df[cols].to_dict(orient="records")
        return jsonify({"total": len(rows), "rows": rows})
    except Exception as e:
        print(f"[API TESTCASES ERROR] {e}", sys.stderr)
        return jsonify({"error": str(e), "total": 0, "rows": []}), 500


@app.route("/api/state")
def api_state():
    return jsonify(_state)

@app.route("/api/run", methods=["POST"])
def api_run():
    if _state["running"]:
        return jsonify({"error": "Already running"}), 409
    body       = request.get_json(force=True)
    perm_types = body.get("types")   or None
    roles      = body.get("roles")   or None
    limit      = body.get("limit")   or None
    tc_ids     = body.get("tc_ids")  or None
    headless   = body.get("headless", True)
    retry_fail = body.get("retry_failed", False)
    proof_delay= float(body.get("proof_delay", 1.5)) # Hold proof screenshot delay (seconds)

    if retry_fail:
        tc_ids = [r["TC ID"] for r in _state["results"] if r.get("Status") == "Failed"]
        if not tc_ids:
            return jsonify({"error": "No failed tests to retry"}), 400
        perm_types = None; roles = None; limit = None

    _state.update(running=True, stop=False, results=[], total=0,
                  done=0, pass_=0, fail=0, skip=0, run_id=str(uuid.uuid4())[:8], latest_ss=None)
    _state["pass"] = 0

    threading.Thread(
        target=_run_worker, daemon=True,
        args=(perm_types, roles, limit, tc_ids, headless, proof_delay)
    ).start()
    return jsonify({"status": "started"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    global _active_ctx, _active_page
    _state["stop"] = True
    with _ctx_lock:
        if _active_ctx:
            try:
                _active_ctx.close()
            except Exception:
                pass
            _active_ctx = None
            _active_page = None
    _broadcast("run_stopped", {"done": _state["done"]})
    return jsonify({"status": "stopped_immediately"})

@app.route("/api/results")
def api_results():
    return jsonify(_state)

@app.route("/api/update_row", methods=["POST"])
def api_update_row():
    body  = request.get_json(force=True)
    tc_id = body.get("tc_id")
    role  = body.get("role")
    field = body.get("field")
    value = body.get("value")
    
    updated = False
    for r in _state.get("results", []):
        if r.get("TC ID") == tc_id and r.get("Role") == role:
            r[field] = value
            updated = True
            break
            
    if updated:
        try: save_report(_state["results"])
        except Exception: pass
        return jsonify({"status": "updated", "tc_id": tc_id, "field": field})
    return jsonify({"status": "not_found"}), 404

@app.route("/api/save_report", methods=["POST"])
def api_save_report():
    if _state.get("results"):
        save_report(_state["results"])
        return jsonify({"status": "saved", "count": len(_state["results"])})
    return jsonify({"status": "empty", "count": 0})


@app.route("/api/report")
def api_report():
    from config import REPORT_FILE
    if _state.get("results"):
        try: save_report(_state["results"])
        except Exception: pass
    if os.path.exists(REPORT_FILE):
        return send_from_directory(REPORT_DIR, os.path.basename(REPORT_FILE), as_attachment=True)
    return jsonify({"error": "No report"}), 404


@app.route("/api/events")
def api_events():
    client_id = str(uuid.uuid4())
    q = queue.Queue()
    with _sse_lock:
        _sse_queues[client_id] = q

    def stream():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'data': {'client_id': client_id}})}\n\n"
            while True:
                try:
                    payload = q.get(timeout=20)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            with _sse_lock:
                _sse_queues.pop(client_id, None)

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

_latest_live_frame = {"image": "", "tc_id": "", "label": "Idle", "ts": 0}

@app.route("/api/live_frame")
def api_live_frame():
    return jsonify(_latest_live_frame)

# ── Live screenshot capture helper ───────────────────────────────────────────
def _capture_live_frame(page, tc_id, label="live"):
    if not page:
        return
    try:
        ss_bytes = page.screenshot(type="jpeg", quality=45, timeout=1000)
        b64 = base64.b64encode(ss_bytes).decode("utf-8")
        img_url = f"data:image/jpeg;base64,{b64}"
        _latest_live_frame["image"] = img_url
        _latest_live_frame["tc_id"] = tc_id
        _latest_live_frame["label"] = label
        _latest_live_frame["ts"]    = time.time()
        _broadcast("live_frame", {"tc_id": tc_id, "label": label, "image": img_url})
    except Exception:
        pass


# ── Worker ────────────────────────────────────────────────────────────────────
def _run_worker(perm_types, roles, limit, tc_ids, headless, proof_delay):
    global _active_ctx, _active_page
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    try:
        df  = load_testcases(permission_types=perm_types, roles=roles, limit=limit)
        nav = load_nav_matrix()
        if tc_ids:
            df = df[df["TC ID"].isin(tc_ids)]

        total = len(df)
        _state["total"] = total
        _broadcast("run_start", {"total": total, "run_id": _state["run_id"]})

        results = []
        cur_role = None

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)

            for _, row in df.iterrows():
                if _state["stop"]:
                    break

                tc_id    = str(row["TC ID"]).strip() if pd.notna(row["TC ID"]) else ""
                role     = str(row["Role"]).strip() if pd.notna(row["Role"]) else ""
                func     = str(row["Function"]).strip() if pd.notna(row["Function"]) else ""
                ptype    = str(row["Permission Type"]).strip() if pd.notna(row["Permission Type"]) else ""
                expected = str(row.get("ผลที่คาดหวัง", "")).strip() if pd.notna(row.get("ผลที่คาดหวัง")) else ""
                step     = str(row.get("ขั้นตอนทดสอบ", "")).strip() if pd.notna(row.get("ขั้นตอนทดสอบ")) else ""

                nav_info = nav.get(func, {}) if isinstance(nav, dict) else {}
                app_name = nav_info.get("app", func) if isinstance(nav_info, dict) else func
                app_name_str = str(app_name or "")
                for key in ["Point of Sale","Sales","Accounting","Purchase",
                            "Inventory","Request","Fleet","MPOS","Contacts","Settings"]:
                    if key.lower() in app_name_str.lower():
                        app_name = key; break



                _broadcast("tc_start", {"tc_id": tc_id, "role": role,
                                        "function": func, "type": ptype,
                                        "step": step, "expected": expected})

                # Handle login if role changed
                if role != cur_role or _active_ctx is None:
                    with _ctx_lock:
                        if _active_ctx:
                            try: _active_ctx.close()
                            except: pass
                    try:
                        def make_cb(tc_id_val):
                            def cb(page, label):
                                _capture_live_frame(page, tc_id_val, label)
                            return cb

                        ctx, page_obj = login(browser, role, frame_cb=make_cb(tc_id))
                        with _ctx_lock:
                            _active_ctx = ctx
                            _active_page = page_obj
                        cur_role = role
                        _broadcast("login_ok", {"tc_id": tc_id, "role": role, "url": page_obj.url[:100]})
                        _capture_live_frame(page_obj, tc_id, label=f"Logged in as {role}")
                    except Exception as e:
                        if _state["stop"]: break
                        _broadcast("tc_done", {"tc_id": tc_id, "status": "Failed", "comment": f"Login: {e}"})
                        results.append({**row.to_dict(), "Status": "Failed",
                                        "Comments": str(e)[:100], "Screenshot": ""})
                        _state["done"] += 1; _state["fail"] += 1
                        _state["results"] = results
                        continue

                ss_name = f"{tc_id}_{role.replace(' ','_')}_{ptype[:6].replace(' ','_')}.png"
                ss_path = os.path.join(SCREENSHOT_DIR, ss_name)

                t0 = time.time()
                status = comment = ""

                # Live update frame before verification
                _capture_live_frame(_active_page, tc_id, label="Testing...")

                try:
                    if _state["stop"]: break
                    status, comment = run_verification(
                        _active_page, ptype, app_name, func, expected, role,
                        frame_cb=lambda page, label: _capture_live_frame(page, tc_id, label))

                except Exception as e:
                    if _state["stop"]: break
                    status  = "Failed"
                    comment = f"Error: {traceback.format_exc()[:200]}"

                elapsed = round(time.time() - t0, 1)

                # Capture final proof screenshot & broadcast immediately
                try:
                    if _active_page:
                        _active_page.screenshot(path=ss_path)
                        _capture_live_frame(_active_page, tc_id, label=f"PROOF [{status}]")
                except:
                    ss_name = ""

                # Proof freeze delay: keep broadcasting live frame so user sees proof picture hold
                if proof_delay > 0 and not _state["stop"]:
                    t_hold = time.time() + proof_delay
                    while time.time() < t_hold and not _state["stop"]:
                        _capture_live_frame(_active_page, tc_id, label=f"PROOF [{status}] (Hold)")
                        time.sleep(0.3)


                if _state["stop"]: break

                # Reset to dashboard
                try:
                    from config import DASHBOARD_URL
                    if _active_page:
                        _active_page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
                        _active_page.wait_for_timeout(400)
                except: pass

                if   status == "Passed":  _state["pass"] += 1
                elif status == "Failed":  _state["fail"] += 1
                else:                     _state["skip"] += 1

                _state["done"] += 1
                _state["latest_ss"] = ss_name
                result_row = {**row.to_dict(), "Status": status,
                              "Comments": comment, "Screenshot": ss_name,
                              "Elapsed": f"{elapsed}s", "App": app_name}
                results.append(result_row)
                _state["results"] = results

                _broadcast("tc_done", {
                    "tc_id": tc_id, "role": role, "function": func,
                    "type": ptype, "status": status, "comment": comment,
                    "done": _state["done"], "total": total, "elapsed": elapsed,
                    "pass": _state["pass"], "fail": _state["fail"],
                    "skip": _state["skip"], "screenshot": ss_name,
                })

            with _ctx_lock:
                if _active_ctx:
                    try: _active_ctx.close()
                    except: pass
                _active_ctx = None
                _active_page = None

            browser.close()

        if results:
            save_report(results)
            _broadcast("report_ready", {"pass": _state["pass"], "fail": _state["fail"]})
        
        if _state["stop"]:
            _broadcast("run_stopped", {"done": _state["done"]})
        else:
            _broadcast("run_complete", {"done": _state["done"], "total": total,
                                        "pass": _state["pass"], "fail": _state["fail"]})
    except Exception as e:
        _broadcast("run_error", {"error": traceback.format_exc()[:500]})
    finally:
        _state["running"] = False
        with _ctx_lock:
            _active_ctx = None
            _active_page = None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"BOM UAT Dashboard -> http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
