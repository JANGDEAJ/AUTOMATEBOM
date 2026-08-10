"""
server.py - BOM UAT Automation Dashboard (Flask + SSE)
"""
import sys, os, json, queue, threading, traceback, time, uuid
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
}
_sse_queues: dict[str, queue.Queue] = {}   # client_id -> Queue
_sse_lock = threading.Lock()


def _broadcast(event_type: str, data: dict):
    payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
    with _sse_lock:
        for q in _sse_queues.values():
            q.put(payload)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(os.path.join(BASE, "static"), "index.html")

@app.route("/screenshots/<path:name>")
def serve_screenshot(name):
    return send_from_directory(SCREENSHOT_DIR, name)

@app.route("/api/testcases")
def api_testcases():
    perm  = request.args.getlist("type") or None
    roles = request.args.getlist("role") or None
    limit = request.args.get("limit", type=int, default=None)
    df    = load_testcases(permission_types=perm, roles=roles, limit=limit)
    rows  = df[["TC ID","Module","Function","Role","Permission Type",
                "ขั้นตอนทดสอบ","ผลที่คาดหวัง"]].to_dict(orient="records")
    return jsonify({"total": len(rows), "rows": rows})

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

    # If retry_failed, collect failed TC IDs
    if retry_fail:
        tc_ids = [r["TC ID"] for r in _state["results"] if r.get("Status") == "Failed"]
        if not tc_ids:
            return jsonify({"error": "No failed tests to retry"}), 400
        perm_types = None; roles = None; limit = None

    _state.update(running=True, stop=False, results=[], total=0,
                  done=0, pass_=0, fail=0, skip=0, run_id=str(uuid.uuid4())[:8])
    _state["pass"] = 0  # reset counters
    threading.Thread(
        target=_run_worker, daemon=True,
        args=(perm_types, roles, limit, tc_ids, headless)
    ).start()
    return jsonify({"status": "started"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    _state["stop"] = True
    return jsonify({"status": "stop_requested"})

@app.route("/api/results")
def api_results():
    return jsonify(_state)

@app.route("/api/report")
def api_report():
    from config import REPORT_FILE
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
                    payload = q.get(timeout=25)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            with _sse_lock:
                _sse_queues.pop(client_id, None)

    return Response(stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Worker ────────────────────────────────────────────────────────────────────
def _run_worker(perm_types, roles, limit, tc_ids, headless):
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
        ctx = page_obj = None

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)

            for _, row in df.iterrows():
                if _state["stop"]:
                    _broadcast("run_stopped", {"done": _state["done"]})
                    break

                tc_id    = row["TC ID"]
                role     = row["Role"]
                func     = row["Function"]
                ptype    = row["Permission Type"]
                expected = str(row.get("ผลที่คาดหวัง", "")).strip()
                step     = str(row.get("ขั้นตอนทดสอบ", "")).strip()

                nav_info = nav.get(func, {})
                app_name = nav_info.get("app", func)
                for key in ["Point of Sale","Sales","Accounting","Purchase",
                            "Inventory","Request","Fleet","MPOS","Contacts","Settings"]:
                    if key.lower() in app_name.lower():
                        app_name = key; break

                _broadcast("tc_start", {"tc_id": tc_id, "role": role,
                                        "function": func, "type": ptype,
                                        "step": step, "expected": expected})

                if role != cur_role:
                    if ctx:
                        try: ctx.close()
                        except: pass
                    try:
                        ctx, page_obj = login(browser, role)
                        cur_role = role
                        _broadcast("login_ok", {"tc_id": tc_id, "role": role,
                                                "url": page_obj.url[:100]})
                    except Exception as e:
                        _broadcast("tc_done", {"tc_id": tc_id, "status": "Failed",
                                               "comment": f"Login: {e}"})
                        results.append({**row.to_dict(), "Status": "Failed",
                                        "Comments": str(e)[:100], "Screenshot": ""})
                        _state["done"] += 1; _state["fail"] += 1
                        _state["results"] = results
                        continue

                ss_name = f"{tc_id}_{role.replace(' ','_')}_{ptype[:6].replace(' ','_')}.png"
                ss_path = os.path.join(SCREENSHOT_DIR, ss_name)

                t0 = time.time()
                status = comment = ""
                try:
                    status, comment = run_verification(
                        page_obj, ptype, app_name, func, expected, role)
                except Exception as e:
                    status  = "Failed"
                    comment = f"Error: {traceback.format_exc()[:200]}"

                elapsed = round(time.time() - t0, 1)

                try: page_obj.screenshot(path=ss_path)
                except: ss_name = ""

                try:
                    from config import DASHBOARD_URL
                    page_obj.goto(DASHBOARD_URL, wait_until="domcontentloaded")
                    page_obj.wait_for_timeout(600)
                except: pass

                if   status == "Passed":  _state["pass"] += 1
                elif status == "Failed":  _state["fail"] += 1
                else:                     _state["skip"] += 1

                _state["done"] += 1
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

            if ctx:
                try: ctx.close()
                except: pass
            browser.close()

        if results:
            save_report(results)
            _broadcast("report_ready", {"pass": _state["pass"], "fail": _state["fail"]})
        _broadcast("run_complete", {"done": _state["done"], "total": total,
                                    "pass": _state["pass"], "fail": _state["fail"]})
    except Exception as e:
        _broadcast("run_error", {"error": traceback.format_exc()[:500]})
    finally:
        _state["running"] = False


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"BOM UAT Dashboard -> http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
