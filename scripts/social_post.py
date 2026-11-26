"""Post the day's carousel (and Reel) to Instagram and the Facebook Page
using Meta's free Graph API. Runs inside GitHub Actions.

Reads public/social/<date>/post.json (written by the daily content task):
{
  "slug": "...",
  "images": ["https://blog.retirementplankaro.com/social/<date>/ig1.jpg", ...],
  "video": "https://blog.retirementplankaro.com/social/<date>/<name>.mp4",   (optional)
  "ig_caption": "...",
  "fb_message": "...",
  "reel_caption": "..."        (optional; posts the video as an IG + FB Reel)
}

Writes social-log/<date>.json with what was posted, so nothing is posted twice.
Needs secret META_PAGE_TOKEN (a non-expiring Page access token).
"""
import json
import os
import pathlib
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v27.0")
PAGE_ID = os.environ.get("FB_PAGE_ID", "1521147887744395")
TOKEN = os.environ.get("META_PAGE_TOKEN", "").strip()


def log(*a):
    print(*a, flush=True)


def api(method, path, **params):
    params["access_token"] = TOKEN
    for attempt in range(3):
        r = requests.request(method, f"{GRAPH}/{path}", data=params if method == "POST" else None,
                             params=params if method == "GET" else None, timeout=120)
        try:
            body = r.json()
        except ValueError:
            body = {"raw": r.text}
        if r.ok and "error" not in body:
            return body
        err = body.get("error", body)
        # transient errors: retry
        if isinstance(err, dict) and (err.get("is_transient") or err.get("code") in (1, 2, 4, 17, 341)):
            time.sleep(20 * (attempt + 1))
            continue
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(f"{path}: {msg}")
    raise RuntimeError(f"{path}: Meta busy, tried 3 times")


def wait_url(url, minutes=12):
    end = time.time() + minutes * 60
    while time.time() < end:
        try:
            r = requests.head(url, timeout=30, allow_redirects=True)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        log("waiting for blog deploy:", url)
        time.sleep(30)
    return False


def wait_container(cid, minutes=10):
    end = time.time() + minutes * 60
    while time.time() < end:
        st = api("GET", cid, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the media ({st})")
        time.sleep(10)
    raise RuntimeError("Instagram media processing timed out")


def ig_user_id():
    env = os.environ.get("IG_USER_ID", "").strip()
    if env:
        return env
    acc = api("GET", PAGE_ID, fields="instagram_business_account").get("instagram_business_account")
    if not acc:
        raise RuntimeError("Instagram account is not linked to the Facebook Page")
    return acc["id"]


def post_instagram_carousel(ig, images, caption):
    children = []
    for url in images[:10]:
        c = api("POST", f"{ig}/media", image_url=url, is_carousel_item="true")
        children.append(c["id"])
    for c in children:
        wait_container(c)
    car = api("POST", f"{ig}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)
    wait_container(car["id"])
    pub = api("POST", f"{ig}/media_publish", creation_id=car["id"])
    link = api("GET", pub["id"], fields="permalink").get("permalink")
    return {"id": pub["id"], "url": link or "https://www.instagram.com/retirementplankaro/"}


def post_instagram_reel(ig, video, caption):
    c = api("POST", f"{ig}/media", media_type="REELS", video_url=video, caption=caption, share_to_feed="true")
    wait_container(c["id"], minutes=15)
    pub = api("POST", f"{ig}/media_publish", creation_id=c["id"])
    link = api("GET", pub["id"], fields="permalink").get("permalink")
    return {"id": pub["id"], "url": link or "https://www.instagram.com/retirementplankaro/reels/"}


def post_facebook_photos(images, message):
    ids = []
    for url in images[:10]:
        p = api("POST", f"{PAGE_ID}/photos", url=url, published="false")
        ids.append(p["id"])
    params = {"message": message}
    for i, pid in enumerate(ids):
        params[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    post = api("POST", f"{PAGE_ID}/feed", **params)
    pid = post["id"]
    return {"id": pid, "url": f"https://www.facebook.com/{pid.replace('_', '/posts/')}"}


def post_facebook_video(video, description, title):
    """Publish the vertical video as a Facebook Page Reel (needs only pages_manage_posts)."""
    start = api("POST", f"{PAGE_ID}/video_reels", upload_phase="start")
    vid = start["video_id"]
    upload_url = start.get("upload_url") or f"https://rupload.facebook.com/video-upload/{GRAPH.rsplit('/', 1)[1]}/{vid}"
    r = requests.post(upload_url, headers={"Authorization": f"OAuth {TOKEN}", "file_url": video}, timeout=300)
    if not r.ok:
        raise RuntimeError(f"Facebook reel upload: {r.text[:200]}")
    api("POST", f"{PAGE_ID}/video_reels", upload_phase="finish", video_id=vid,
        video_state="PUBLISHED", description=description, title=title[:250])
    return {"id": vid, "url": f"https://www.facebook.com/reel/{vid}"}


def resolve_page_token():
    """Accept either a Page token or a User token in META_PAGE_TOKEN; always post with the Page token."""
    global TOKEN
    me = api("GET", "me", fields="id,name")
    if me.get("id") == PAGE_ID:
        log("Token type: Page")
        return
    page = api("GET", PAGE_ID, fields="access_token,name")
    if not page.get("access_token"):
        raise SystemExit("Token cannot manage the Facebook Page")
    TOKEN = page["access_token"]
    log("Token type: User -> using Page token for", page.get("name"))


def main():
    """Post every public/social/<folder>/post.json (e.g. 2026-11-27 and 2026-11-27-night).
    Already-posted platforms are skipped using social-log/<folder>.json."""
    if not TOKEN:
        log("META_PAGE_TOKEN secret is not set yet; skipping (the daily task will use its fallback).")
        return
    resolve_page_token()
    wanted = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    folders = sorted(p.parent.name for p in (ROOT / "public" / "social").glob("*/post.json"))
    if wanted:
        folders = [f for f in folders if f == wanted]
    if not folders:
        log("No post.json found; nothing to post.")
    for folder in folders:
        log(f"== {folder} ==")
        post_folder(folder)


def post_folder(date):
    spec_file = ROOT / "public" / "social" / date / "post.json"
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    log_file = ROOT / "social-log" / f"{date}.json"
    done = json.loads(log_file.read_text()) if log_file.exists() else {}
    done["date"] = date
    done["slug"] = spec.get("slug")

    images = spec.get("images", [])
    video = spec.get("video")
    if images and not wait_url(images[-1]):
        raise SystemExit("Blog files never went live; not posting.")
    if video:
        wait_url(video, minutes=3)

    ig = None
    tasks = []
    if len(images) >= 2:
        tasks.append(("instagram", lambda: post_instagram_carousel(ig, images, spec["ig_caption"])))
        tasks.append(("facebook", lambda: post_facebook_photos(images, spec["fb_message"])))
    if video and spec.get("reel_caption"):
        tasks.append(("instagram_reel", lambda: post_instagram_reel(ig, video, spec["reel_caption"])))
        if os.environ.get("FB_VIDEO") == "1":  # needs publish_video permission; off for now
          tasks.append(("facebook_video", lambda: post_facebook_video(
            video, spec.get("fb_video_description", spec["reel_caption"]), spec.get("video_title", spec.get("slug", "")))))

    for name, fn in tasks:
        if done.get(name, {}).get("ok"):
            log(f"{name}: already posted, skipping")
            continue
        try:
            if ig is None and name.startswith("instagram"):
                ig = ig_user_id()
            res = fn()
            done[name] = {"ok": True, **res}
            log(f"{name}: posted {res['url']}")
        except Exception as e:  # keep going with other platforms
            done[name] = {"ok": False, "error": str(e)[:300]}
            log(f"{name}: FAILED {e}")

    log_file.parent.mkdir(exist_ok=True)
    log_file.write_text(json.dumps(done, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
