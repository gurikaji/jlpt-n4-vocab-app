from flask import Flask, render_template_string, session, redirect, url_for
import csv
import random
import os

app = Flask(__name__)
app.secret_key = "secret_key_for_session"

# CSVファイルからデータを読み込む関数
def load_vocabulary():
    rows = []
    file_path = "JLPT N4 語彙.csv"
    if os.path.exists(file_path):
        with open(file_path, mode="r", encoding="cp932") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    rows.append(row)
    return rows

@app.route("/")
def index():
    rows = load_vocabulary()
    if not rows:
        return "<h1>エラー: 語彙データが見つかりません。「JLPT N4 語彙.csv」と同じフォルダにあるか確認してください。</h1>"
    
    # セッション履歴の初期化
    if "history" not in session:
        session["history"] = []
    
    # ランダムに問題を選ぶ
    item = random.choice(rows)
    
    # 履歴に追加（最大20件まで保持）
    history = session["history"]
    history.append(item)
    if len(history) > 20:
        history.pop(0)
    session["history"] = history
    session.modified = True

    return render_card(item, len(history) > 1)

@app.route("/prev")
def prev():
    history = session.get("history", [])
    if len(history) > 1:
        # 現在の問題を捨てて、1つ前の問題に戻る
        history.pop()
        prev_item = history.pop()
        session["history"] = history
        session.modified = True
        return render_card(prev_item, len(history) > 0)
    return redirect(url_for("index"))

def render_card(item, has_prev):
    # 安全に列データを取得
    word = item[2] if len(item) > 2 else (item[0] if len(item) > 0 else "")    # 3列目：漢字
    reading = item[1] if len(item) > 1 else ""                                # 2列目：よみ
    example = item[3] if len(item) > 3 else ""                                # 4列目：例文

    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JLPT N4 語彙学習</title>
        <style>
            body {{ font-family: sans-serif; text-align: center; margin-top: 40px; background-color: #f4f4f9; }}
            .card {{ background: white; padding: 30px; border-radius: 12px; display: inline-block; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 500px; width: 90%; text-align: left; }}
            h2 {{ text-align: center; color: #555; margin-top: 0; }}
            
            /* タップで開閉するエリアのスタイル */
            .step-box {{
                background: #eef5ff;
                border: 1px solid #cce0ff;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: background 0.2s;
            }}
            .step-box:hover {{ background: #ddebff; }}
            .step-title {{ font-weight: bold; color: #0056b3; font-size: 16px; margin: 0; }}
            .step-content {{ font-size: 22px; color: #222; margin-top: 8px; display: none; word-break: break-all; }}
            
            /* 最初から表示する漢字（3列目） */
            .kanji-box {{ background: #fff8e6; border-color: #ffe0b2; cursor: default; }}
            .kanji-box .step-title {{ color: #d97706; }}
            .kanji-box .step-content {{ display: block; font-weight: bold; font-size: 28px; }}

            .btn-group {{ display: flex; justify-content: space-between; margin-top: 25px; gap: 10px; }}
            button {{ padding: 12px 20px; font-size: 16px; cursor: pointer; border: none; border-radius: 6px; font-weight: bold; }}
            
            .btn-next {{ background: #007BFF; color: white; display: none; flex: 1; }}
            .btn-next:hover {{ background: #0056b3; }}
            
            .btn-prev {{ background: #6c757d; color: white; flex: 1; }}
            .btn-prev:hover {{ background: #5a6268; }}
            .btn-disabled {{ background: #ccc; cursor: not-allowed; flex: 1; }}
        </style>
        <script>
            let openedCount = 0;
            function showNext(contentId, hintId) {{
                var el = document.getElementById(contentId);
                if (el.style.display !== "block") {{
                    el.style.display = "block";
                    var hint = document.getElementById(hintId);
                    if (hint) hint.style.display = "none";
                    
                    openedCount++;
                    // 「よみ」と「例文」の2つを開き終わったら「次の問題へ」ボタンを表示する
                    if (openedCount === 2) {{
                        document.getElementById('next-btn').style.display = "block";
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <div class="card">
            <h2>JLPT N4 語彙問題</h2>
            
            <!-- 1. 3列目：漢字（最初から表示） -->
            <div class="step-box kanji-box">
                <p class="step-title">【漢字】</p>
                <div class="step-content">{word}</div>
            </div>

            <!-- 2. 2列目：よみ（タップで表示） -->
            <div class="step-box" onclick="showNext('reading-content', 'hint2')">
                <p class="step-title">【よみ】 <span id="hint2" style="font-size:14px; color:#0056b3;">👈 タップして表示</span></p>
                <div id="reading-content" class="step-content">{reading}</div>
            </div>

            <!-- 3. 4列目：例文（タップで表示） -->
            <div class="step-box" onclick="showNext('example-content', 'hint3')">
                <p class="step-title">【例文】 <span id="hint3" style="font-size:14px; color:#0056b3;">👈 タップして表示</span></p>
                <div id="example-content" class="step-content">{example}</div>
            </div>

            <!-- ボタンエリア -->
            <div class="btn-group">
                {'<button class="btn-prev" onclick="location.href=\'/prev\'">◀ 前の問題へ</button>' if has_prev else '<button class="btn-prev btn-disabled" disabled>◀ 前の問題へ</button>'}
                <button id="next-btn" class="btn-next" onclick="location.href='/'">次の問題へ ▶</button>
            </div>
        </div>
    </body>
    </html>
    """
    return html  # ここを正しく修正しました

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)