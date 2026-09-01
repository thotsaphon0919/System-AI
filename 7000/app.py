from flask import Flask, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INFINI PRO V1</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
        body { background: #1e1e1e; color: #fff; min-height: 100vh; }
        .container { width: 100%; max-width: 480px; margin: 0 auto; min-height: 100vh; display: flex; flex-direction: column; }

        .header { display: flex; align-items: center; gap: 12px; padding: 18px; border-bottom: 1px solid #ff6b0040; background: #252526; }
        .lbl-m { font-size: 32px; font-weight: 900; color: #ff6b00; }
        .btn-gear { 
            width: 52px; height: 52px; border-radius: 50%; 
            background: rgba(0,0,0,0.4); border: 2px solid #ffb700;
            color: #ffc107; font-size: 28px; font-weight: bold;
            display: grid; place-items: center; cursor: pointer;
            box-shadow: 0 0 15px rgba(255,183,0,0.7);
            position: relative; z-index: 9999 !important;
        }

        .world { flex: 1; margin: 18px; border-radius: 20px; border: 1px solid #ff6b0060; background: #2a2a2a; display: flex; align-items: center; justify-content: center; position: relative; }
        .world-txt { color: #888; font-size: 16px; }
        .lbl-no { position: absolute; left: 12px; bottom: 12px; font-size: 11px; color: #666; background: rgba(0,0,0,0.2); padding: 3px 8px; border-radius: 99px; }

        .bottom-bar { height: 15px; background: #ff6b00; margin-top: auto; }

        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 99999; padding: 20px; overflow-y: auto; }
        .modal.show { display: block; }
        .m-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        .m-close { font-size: 32px; color: #ff6b00; cursor: pointer; }
        .box { background: #252526; border-radius: 12px; padding: 14px; margin-bottom: 16px; border: 1px solid #ff6b0030; }
        .box legend { font-weight: bold; color: #ff6b00; padding: 0 8px; font-size: 14px; }
        .opts { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
        .opts label { font-size: 14px; cursor: pointer; }
        input, select { width: 100%; padding: 12px; border-radius: 10px; border: none; background: #1e1e1e; color: #fff; border: 1px solid #ff6b0050; margin-top: 6px; font-size: 15px; }
        .btn-orange { background: #ff6b00; color: #000; font-weight: bold; border: none; padding: 12px; border-radius: 10px; width: 100%; margin-top: 8px; cursor: pointer; font-size: 15px; }
        .btn-green { background: #28a745; color: #fff; font-weight: bold; border: none; padding: 14px; border-radius: 10px; width: 100%; margin-top: 20px; cursor: pointer; font-size: 16px; }
        .status { font-size: 13px; color: #aaa; margin-top: 6px; display: block; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="lbl-m">M</div>
        <button class="btn-gear" onclick="openGear()">⚙</button>
    </div>

    <div class="world">
        <div class="world-txt">พื้นที่แสดงผลหลัก / ช่องโลก</div>
        <div class="lbl-no" id="showNo">no. 001</div>
    </div>

    <div class="bottom-bar"></div>

    <div class="modal" id="gearWin">
        <div class="m-head"><h2>⚙ ตั้งค่าระบบ</h2><span class="m-close" onclick="closeGear()">×</span></div>

        <fieldset class="box">
            <legend>เลือกโซน</legend>
            <div class="opts">
                <label><input type="radio" name="z" value="ส่วนตัว" checked> ส่วนตัว</label>
                <label><input type="radio" name="z" value="ครีเอทีฟ"> ครีเอทีฟ</label>
                <label><input type="radio" name="z" value="ออฟฟิต"> ออฟฟิต</label>
                <label><input type="radio" name="z" value="ร้านค้า"> ร้านค้า</label>
            </div>
        </fieldset>

        <fieldset class="box">
            <legend>อัปโหลด & AI</legend>
            <label style="display:flex;align-items:center;gap:8px;margin-top:8px;"><input type="checkbox" id="aiOk"> ให้ AI จัดร้านให้</label>
            <button class="btn-orange" onclick="document.getElementById('upFile').click()">📁 อัปโหลดรูป/วิดีโอ</button>
            <input type="file" id="upFile" multiple accept="image/*,video/*" hidden onchange="countUp(this)">
            <span class="status" id="upStatus">ยังไม่มีไฟล์</span>
        </fieldset>

        <fieldset class="box">
            <legend>เชื่อมแผ่น</legend>
            <input type="text" id="syncVal" placeholder="กรอกเลข/รหัสให้ตรงกัน">
        </fieldset>

        <button class="btn-green" onclick="saveAll()">บันทึกและปิด</button>
    </div>
</div>

<script>
function openGear(){document.getElementById('gearWin').classList.add('show')}
function closeGear(){document.getElementById('gearWin').classList.remove('show')}
function countUp(f){if(f.files.length){document.getElementById('upStatus').textContent=`อัปโหลดแล้ว ${f.files.length} ไฟล์`;document.getElementById('upStatus').style.color='#28a745'}}
function saveAll(){let v=document.getElementById('syncVal').value.trim();if(v)document.getElementById('showNo').textContent=`no. ${v}`;closeGear()}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)
