from fastapi import UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import json
import mimetypes
import re
import shutil
import time
import uuid

from user_scope_7000 import current_user_key, scoped_data_file, scoped_upload_dir, scoped_upload_url


def install_subpage_7000(app):
    base = Path(__file__).resolve().parent
    legacy_state_file = base / "data" / "remote_show_state.json"
    legacy_detail_state_file = base / "data" / "detail_swipe_7000.json"

    def state_file():
        return scoped_data_file(base, "remote_show_state.json", legacy_state_file)

    def detail_state_file():
        return scoped_data_file(base, "detail_swipe_7000.json", legacy_detail_state_file)
    uploads = base / "uploads"

    uploads.mkdir(parents=True, exist_ok=True)

    def now():
        return int(time.time())

    def new_item():
        return {
            "id": f"item_{uuid.uuid4().hex[:10]}",
            "title": "",
            "subtitle": "",
            "detail": "",
            "media_url": "",
            "media_type": "",
            "link_url": "",
            "enabled": True,
            "created_at": now(),
            "updated_at": now(),
        }

    def load_state():
        if not state_file().exists():
            raise HTTPException(
                404,
                "ยังไม่พบข้อมูล Remote กรุณาเปิดหน้า 7000 ก่อนหนึ่งครั้ง",
            )

        try:
            data = json.loads(
                state_file().read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise HTTPException(
                500,
                f"อ่านข้อมูล Remote ไม่สำเร็จ: {exc}",
            )

        if not isinstance(data.get("pages"), list):
            data["pages"] = []

        return data

    def save_state(data):
        tmp = state_file().with_suffix(".subpage.tmp")

        tmp.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        tmp.replace(state_file())


    def delete_upload_url(url):
        value = str(url or "").strip()
        if not value.startswith("/uploads/"):
            return
        relative = value.split("?", 1)[0].removeprefix("/uploads/").lstrip("/")
        if not relative:
            return
        target = (uploads / relative).resolve()
        try:
            target.relative_to(uploads.resolve())
        except ValueError:
            return
        try:
            if target.is_file():
                target.unlink()
        except OSError:
            pass

    def remove_detail_group(group_no):
        if not detail_state_file().exists():
            return
        try:
            detail_data = json.loads(
                detail_state_file().read_text(encoding="utf-8")
            )
        except Exception:
            return

        groups = detail_data.get("groups")
        if not isinstance(groups, dict):
            return

        group = groups.pop(str(group_no), None)
        if not isinstance(group, dict):
            return

        for detail_page in group.get("pages", []):
            if isinstance(detail_page, dict):
                delete_upload_url(detail_page.get("media_url", ""))

        tmp = detail_state_file().with_suffix(".clear-subpage.tmp")
        tmp.write_text(
            json.dumps(detail_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(detail_state_file())

    def get_room(page_id):
        data = load_state()

        for room_no, page in enumerate(
            data["pages"],
            start=1,
        ):
            if str(page.get("id")) != str(page_id):
                continue

            items = page.get("items")

            if not isinstance(items, list):
                items = []

            while len(items) < 6:
                items.append(new_item())

            for sub_index, item in enumerate(
                items,
                start=1,
            ):
                item.setdefault(
                    "id",
                    f"item_{uuid.uuid4().hex[:10]}",
                )
                item.setdefault("title", "")
                item.setdefault("subtitle", "")
                item.setdefault("detail", "")
                item.setdefault("media_url", "")
                item.setdefault("media_type", "")
                item.setdefault("link_url", "")
                item.setdefault("enabled", True)
                item.setdefault("created_at", now())
                item.setdefault("updated_at", now())

                item["sub_no"] = (
                    f"{room_no}.{sub_index}"
                )

            page["items"] = items
            save_state(data)

            return data, page, room_no

        raise HTTPException(
            404,
            "ไม่พบ Room นี้",
        )

    def load_detail_thumbnails():
        """ดึงรูปหน้าแรกของแต่ละชุด เช่น 7.1.1 มาใช้เป็นปก no.7.1"""
        if not detail_state_file().exists():
            return {}
        try:
            detail_data = json.loads(
                detail_state_file().read_text(encoding="utf-8")
            )
        except Exception:
            return {}

        result = {}
        groups = detail_data.get("groups", {})
        if not isinstance(groups, dict):
            return result

        for group_no, group in groups.items():
            pages = group.get("pages", []) if isinstance(group, dict) else []
            if not isinstance(pages, list) or not pages:
                continue
            first = pages[0] if isinstance(pages[0], dict) else {}
            if first.get("media_url"):
                result[str(group_no)] = {
                    "media_url": first.get("media_url", ""),
                    "media_type": first.get("media_type", ""),
                }
        return result

    def payload(page_id):
        _, page, room_no = get_room(page_id)
        detail_thumbnails = load_detail_thumbnails()
        public_items = []

        for index, item in enumerate(page.get("items", [])[:6], start=1):
            fallback = detail_thumbnails.get(f"{room_no}.{index}", {})
            public_items.append(
                {
                    "id": item.get("id"),
                    "sub_no": f"{room_no}.{index}",
                    "media_url": (
                        item.get("media_url", "")
                        or fallback.get("media_url", "")
                    ),
                    "media_type": (
                        item.get("media_type", "")
                        or fallback.get("media_type", "")
                    ),
                    "link_url": item.get("link_url", ""),
                    "enabled": item.get("enabled", True),
                }
            )

        return {
            "page_id": page.get("id"),
            "room_no": room_no,
            "items": public_items,
        }

    html = r'''
<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">

<meta
  name="viewport"
  content="width=device-width,
  initial-scale=1,
  maximum-scale=1,
  user-scalable=no"
>

<title>INFINI SUBPAGE</title>

<style>
*{
  box-sizing:border-box;
  -webkit-tap-highlight-color:transparent;
}

body{
  margin:0;
  min-height:100vh;
  padding:14px 14px 40px;

  background:
    radial-gradient(
      circle at top,
      #241104,
      #050302 48%,
      #000
    );

  color:#fff;

  font-family:
    system-ui,
    -apple-system,
    "Segoe UI",
    sans-serif;
}

.wrap{
  width:100%;
  max-width:760px;
  margin:auto;
}

.top{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom:14px;
}

.title{
  font-size:20px;
  font-weight:950;
}

.roomno{
  margin-top:3px;
  color:#ffad3d;
  font-size:14px;
  font-weight:900;
}

.back{
  padding:10px 14px;

  border:
    1px solid
    rgba(255,154,20,.5);

  border-radius:14px;

  background:
    rgba(0,0,0,.55);

  color:#ffd398;
  font-weight:900;
}

.grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
}

.card{
  position:relative;

  min-height:175px;
  aspect-ratio:4 / 5;

  overflow:hidden;

  border:
    1px solid
    rgba(255,145,0,.42);

  border-radius:24px;

  background:
    linear-gradient(
      155deg,
      rgba(255,145,0,.14),
      rgba(0,0,0,.96)
    );

  box-shadow:
    0 16px 38px
    rgba(0,0,0,.42);

  touch-action:manipulation;

  user-select:none;
  -webkit-user-select:none;
  -webkit-touch-callout:none;
}

.card:active{
  transform:scale(.985);
}

.card img,
.card video{
  width:100%;
  height:100%;
  object-fit:cover;
  display:block;

  pointer-events:none;

  -webkit-user-drag:none;
  user-select:none;
}

.empty{
  position:absolute;
  inset:0;

  display:grid;
  place-items:center;

  color:
    rgba(255,164,35,.28);

  font-size:60px;
}

.number{
  position:absolute;
  left:9px;
  bottom:9px;
  z-index:3;

  padding:7px 10px;

  border:
    1px solid
    rgba(255,181,69,.55);

  border-radius:999px;

  background:
    rgba(0,0,0,.76);

  color:#ffd18a;

  font-size:13px;
  font-weight:950;
}

.toast{
  position:fixed;
  top:12px;
  left:50%;
  z-index:110;

  transform:
    translateX(-50%);

  display:none;

  max-width:
    calc(100% - 28px);

  padding:10px 14px;

  border:
    1px solid
    rgba(255,145,0,.45);

  border-radius:999px;

  background:#170a03;
  color:#ffd398;

  text-align:center;
  font-weight:800;
}

.toast.show{
  display:block;
}

.viewer{
  position:fixed;
  inset:0;
  z-index:100;

  display:none;
  place-items:center;

  padding:16px;

  background:
    rgba(0,0,0,.96);
}

.viewer.show{
  display:grid;
}

.viewer img,
.viewer video{
  max-width:100%;
  max-height:88vh;
  border-radius:18px;
}

.close{
  position:absolute;
  top:12px;
  right:12px;

  padding:10px 14px;

  border:
    1px solid
    rgba(255,154,20,.5);

  border-radius:14px;

  background:#080402;
  color:#ffd398;
  font-weight:900;
}

.actionSheet[hidden]{display:none!important}
.actionSheet{
  position:fixed;inset:0;z-index:150;
  display:flex;align-items:flex-end;justify-content:center;
  padding:16px;background:rgba(0,0,0,.76);backdrop-filter:blur(5px)
}
.actionBox{
  width:min(560px,100%);padding:14px;border:1px solid rgba(255,145,0,.5);
  border-radius:24px;background:#0b0502;box-shadow:0 22px 70px rgba(0,0,0,.68)
}
.actionTitle{padding:4px 4px 11px;text-align:center;color:#ffd398;font-size:18px;font-weight:1000}
.actionBtn{
  width:100%;min-height:58px;margin:6px 0;border:1px solid rgba(255,145,0,.45);
  border-radius:18px;background:#180903;color:#fff;font-size:18px;font-weight:1000
}
.actionBtn.upload{background:linear-gradient(180deg,#ffc247,#ff9200);color:#1a0800}
.actionBtn.delete{border-color:#b7463c;background:#2b0805;color:#ffb7ae}

/* === INFINI_SUBPAGE_RESPONSIVE_MENU_FIX_V2 === */
html,body{max-width:100%;overflow-x:hidden}
.actionSheet{
  padding:max(10px,env(safe-area-inset-top)) max(10px,env(safe-area-inset-right))
          max(10px,env(safe-area-inset-bottom)) max(10px,env(safe-area-inset-left));
  overflow-y:auto;overflow-x:hidden;
}
.actionBox{
  width:min(560px,calc(100vw - 20px));
  max-width:calc(100vw - 20px);min-width:0;
  margin:0 auto;box-sizing:border-box;overflow:hidden;
}
.actionTitle,.actionBtn{overflow-wrap:anywhere;word-break:break-word;white-space:normal}
@media(max-width:420px){
  .actionBox{width:100%;max-width:100%;padding:10px;border-radius:18px}
  .actionBtn{min-height:52px;margin:5px 0;font-size:16px;border-radius:15px}
  .actionTitle{font-size:17px}
}
/* === END INFINI_SUBPAGE_RESPONSIVE_MENU_FIX_V2 === */

@media(min-width:700px){
  .grid{
    grid-template-columns:
      repeat(3,1fr);
  }
}
</style>
</head>

<body>

<div
  class="toast"
  id="toast"
></div>

<div class="wrap">

  <div class="top">

    <div>
      <div class="title">
        ห้องแสดงผลงาน
      </div>

      <div
        class="roomno"
        id="roomNo"
      ></div>
    </div>

    <button
      class="back"
      id="backBtn"
    >
      กลับ
    </button>

  </div>

  <div
    class="grid"
    id="grid"
  ></div>

</div>

<div class="actionSheet" id="itemActionSheet" hidden>
  <div class="actionBox" role="dialog" aria-modal="true" aria-label="จัดการหน้านี้">
    <div class="actionTitle">จัดการหน้านี้</div>
    <button class="actionBtn upload" id="itemActionUpload">อัปโหลดรูป</button>
    <button class="actionBtn delete" id="itemActionDelete">ลบหน้า</button>
  </div>
</div>

<div
  class="viewer"
  id="viewer"
>

  <button
    class="close"
    id="closeViewer"
  >
    ปิด
  </button>

  <div id="viewerBody"></div>

</div>

<script>
const pageId =
  decodeURIComponent(
    location.pathname
      .split("/")
      .filter(Boolean)[1] || ""
  );

const grid =
  document.getElementById("grid");

const toastBox =
  document.getElementById("toast");

const viewer =
  document.getElementById("viewer");

const viewerBody =
  document.getElementById("viewerBody");

let selectedItemForAction = null;


function toast(message){
  toastBox.textContent =
    message;

  toastBox.classList.add(
    "show"
  );

  setTimeout(()=>{
    toastBox.classList.remove(
      "show"
    );
  },1500);
}


function closeViewer(){
  viewer.classList.remove(
    "show"
  );

  viewerBody.innerHTML = "";
}


function openItem(item){

  if(item.link_url){
    location.href =
      item.link_url;

    return;
  }

  if(!item.media_url){
    toast(
      "no." +
      item.sub_no +
      " ยังไม่มีข้อมูล"
    );

    return;
  }

  if(
    item.media_type ===
    "video"
  ){
    viewerBody.innerHTML =
      '<video src="' +
      item.media_url +
      '" controls autoplay playsinline></video>';
  }else{
    viewerBody.innerHTML =
      '<img src="' +
      item.media_url +
      '">';
  }

  viewer.classList.add(
    "show"
  );
}


function closeItemActionSheet(){
  selectedItemForAction = null;
  window.__infiniActionMenuOpen = false;
  document.getElementById("itemActionSheet").hidden = true;
}

function openItemActionSheet(item){
  selectedItemForAction = item;
  window.__infiniActionMenuOpen = true;
  document.getElementById("itemActionSheet").hidden = false;
}

async function deleteItemPage(){
  const item = selectedItemForAction;
  if(!item) return;

  if(!confirm("ลบหน้านี้และข้อมูลด้านในทั้งหมดใช่ไหม?")) return;

  toast("กำลังลบ no." + item.sub_no);
  const response = await fetch(
    "/api/subpages/" + encodeURIComponent(pageId) +
    "/items/" + encodeURIComponent(item.id),
    {method:"DELETE"}
  );

  if(!response.ok){
    toast("ลบหน้าไม่สำเร็จ");
    return;
  }

  closeItemActionSheet();
  toast("ลบหน้าแล้ว");
  setTimeout(()=>location.reload(),450);
}

function uploadItem(item){

  const input =
    document.createElement(
      "input"
    );

  input.type = "file";

  input.accept =
    "image/*,video/*";

  input.onchange =
    async()=>{

      const file =
        input.files &&
        input.files[0];

      if(!file){
        return;
      }

      const form =
        new FormData();

      form.append(
        "file",
        file
      );

      toast(
        "กำลังอัปโหลด no." +
        item.sub_no
      );

      const response =
        await fetch(
          "/api/subpages/" +
          encodeURIComponent(
            pageId
          ) +
          "/items/" +
          encodeURIComponent(
            item.id
          ) +
          "/upload",
          {
            method:"POST",
            body:form
          }
        );

      if(!response.ok){
        toast(
          "อัปโหลดไม่สำเร็จ"
        );

        return;
      }

      location.reload();
    };

  input.click();
}


function bindPress(
  card,
  item
){
  let timer = null;
  let longPressed = false;

  let startX = 0;
  let startY = 0;

  card.addEventListener(
    "contextmenu",
    event=>{
      event.preventDefault();
    }
  );

  card.addEventListener(
    "pointerdown",
    event=>{
      longPressed = false;

      startX = event.clientX;
      startY = event.clientY;

      timer =
        setTimeout(()=>{
          longPressed = true;
          openItemActionSheet(item);
        },280);
    }
  );

  card.addEventListener(
    "pointermove",
    event=>{
      const moveX =
        Math.abs(
          event.clientX -
          startX
        );

      const moveY =
        Math.abs(
          event.clientY -
          startY
        );

      if(
        moveX > 12 ||
        moveY > 12
      ){
        clearTimeout(timer);
      }
    }
  );

  card.addEventListener(
    "pointerup",
    ()=>{
      clearTimeout(timer);

      if(!longPressed){
        openItem(item);
      }
    }
  );

  card.addEventListener(
    "pointercancel",
    ()=>{
      clearTimeout(timer);
    }
  );

  card.addEventListener(
    "pointerleave",
    ()=>{
      clearTimeout(timer);
    }
  );
}


async function load(){

  const response =
    await fetch(
      "/api/subpages/" +
      encodeURIComponent(
        pageId
      )
    );

  if(!response.ok){
    throw new Error(
      await response.text()
    );
  }

  const data =
    await response.json();

  document
    .getElementById(
      "roomNo"
    )
    .textContent =
      "Subpage ของ no." +
      data.room_no;

  grid.innerHTML = "";

  data.items.forEach(
    item=>{

      const card =
        document.createElement(
          "div"
        );

      card.className =
        "card";

      let media =
        '<div class="empty">+</div>';

      if(
        item.media_url &&
        item.media_type ===
        "video"
      ){
        media =
          '<video src="' +
          item.media_url +
          '" muted autoplay loop playsinline></video>';
      }else if(
        item.media_url
      ){
        media =
          '<img src="' +
          item.media_url +
          '">';
      }

      card.innerHTML =
        media +
        '<div class="number">' +
        "no." +
        item.sub_no +
        "</div>";

      bindPress(
        card,
        item
      );

      grid.appendChild(
        card
      );
    }
  );
}


document
  .getElementById(
    "backBtn"
  )
  .onclick = ()=>{

    if(history.length > 1){
      history.back();
    }else{
      location.href = "/";
    }
  };


document
  .getElementById(
    "closeViewer"
  )
  .onclick =
    closeViewer;


viewer.addEventListener(
  "click",
  event=>{
    if(
      event.target ===
      viewer
    ){
      closeViewer();
    }
  }
);


document.getElementById("itemActionUpload").onclick = ()=>{
  const item = selectedItemForAction;
  closeItemActionSheet();
  if(item) uploadItem(item);
};

document.getElementById("itemActionDelete").onclick = deleteItemPage;

document.getElementById("itemActionSheet").addEventListener("click", event=>{
  if(event.target === document.getElementById("itemActionSheet")){
    closeItemActionSheet();
  }
});

function refreshSubpage(){
  load().catch(
    error=>{
      console.error(error);

      toast(
        "โหลด Subpage ไม่สำเร็จ"
      );
    }
  );
}

// โหลดใหม่ทุกครั้งที่เปิดหน้า รวมถึงตอนกดย้อนกลับจากหน้ารายละเอียด
// เพื่อไม่ให้ Chrome แสดงรูปเก่าจาก back-forward cache
window.addEventListener(
  "pageshow",
  refreshSubpage
);
</script>

</body>
</html>
'''

    @app.get(
        "/subpages/{page_id}",
        response_class=HTMLResponse,
    )
    def subpage_page(page_id: str):
        get_room(page_id)

        return HTMLResponse(html)

    @app.get(
        "/api/subpages/{page_id}"
    )
    def subpage_data(page_id: str):
        return JSONResponse(
            payload(page_id)
        )

    @app.post(
        "/api/subpages/{page_id}"
        "/items/{item_id}/upload"
    )
    def subpage_upload(
        page_id: str,
        item_id: str,
        file: UploadFile = File(...),
    ):
        data, page, _ = get_room(
            page_id
        )

        target = next(
            (
                item
                for item in page["items"]
                if str(
                    item.get("id")
                ) == str(item_id)
            ),
            None,
        )

        if target is None:
            raise HTTPException(
                404,
                "ไม่พบ Subpage นี้",
            )

        original = re.sub(
            r"[^a-zA-Z0-9._-]+",
            "-",
            file.filename or
            "upload.bin",
        )

        extension = (
            Path(original).suffix
            or ".bin"
        )

        filename = (
            f"{now()}_"
            f"{uuid.uuid4().hex[:8]}"
            f"{extension}"
        )

        destination = (
            scoped_upload_dir(base) / filename
        )

        with destination.open(
            "wb"
        ) as output:
            shutil.copyfileobj(
                file.file,
                output,
            )

        content_type = (
            file.content_type
            or mimetypes.guess_type(
                filename
            )[0]
            or ""
        ).lower()

        target["media_url"] = (
            scoped_upload_url(filename)
        )

        target["media_type"] = (
            "video"
            if content_type.startswith(
                "video/"
            )
            else "image"
        )

        target["updated_at"] = now()

        save_state(data)

        return JSONResponse(
            payload(page_id)
        )


    @app.delete(
        "/api/subpages/{page_id}"
        "/items/{item_id}"
    )
    def subpage_delete(
        page_id: str,
        item_id: str,
    ):
        data, page, room_no = get_room(page_id)

        target_index = next(
            (
                index
                for index, item in enumerate(page.get("items", []), start=1)
                if str(item.get("id")) == str(item_id)
            ),
            None,
        )
        if target_index is None:
            raise HTTPException(404, "ไม่พบ Subpage นี้")

        target = page["items"][target_index - 1]
        delete_upload_url(target.get("media_url", ""))
        remove_detail_group(f"{room_no}.{target_index}")

        target_id = target.get("id") or f"item_{uuid.uuid4().hex[:10]}"
        created_at = target.get("created_at", now())
        target.clear()
        target.update({
            "id": target_id,
            "title": "",
            "subtitle": "",
            "detail": "",
            "media_url": "",
            "media_type": "",
            "link_url": "",
            "enabled": True,
            "created_at": created_at,
            "updated_at": now(),
            "sub_no": f"{room_no}.{target_index}",
        })

        page["updated_at"] = now()
        save_state(data)
        return JSONResponse(payload(page_id))
