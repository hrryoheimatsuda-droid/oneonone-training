import streamlit as st
from openai import OpenAI
import json

# ============================================================
# 1on1ロールプレイ研修｜松田サンプルエンジニアリング（ポートフォリオ用サンプル）
# 部下AI「カイ」と1on1で対話し、3つの合意条件を満たすと面談成功
# ※登場する企業・人物・事例はすべて架空です
# ============================================================

# --- 1. ページ設定 ---
st.set_page_config(page_title="評価者研修：シニアエンジニア カイとの1on1", page_icon="🧑‍💻", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stChatMessage { border-radius: 20px; margin-bottom: 15px; border: 1px solid #ddd; padding: 10px; }
    [data-testid="stChatMessageAvatar"] {
        width: 70px !important; height: 70px !important;
        font-size: 45px !important; line-height: 70px !important;
        border: 2px solid #2196f3; background-color: #ffffff !important;
    }
    .score-card { background-color: #fff; padding: 30px; border-radius: 20px; border: 2px solid #2196f3; text-align: center; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 設定値 ---
MAX_USER_TURNS = 15  # 公開デモの暴走・課金対策：受講者の発言回数の上限

# --- 3. APIキー ---
api_key = st.secrets.get("OPENAI_API_KEY", "").strip().strip('"')
if not api_key:
    st.error("APIキーが設定されていません。アプリ設定の Secrets に OPENAI_API_KEY を登録してください。")
    st.stop()
client = OpenAI(api_key=api_key)

# --- 4. セッション管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.kai_stage = 0
    st.session_state.current_avatar = "🧑‍💻"

# --- 5. プロンプト ---
KAI_SYSTEM = f"""
あなたは部下の「カイ」です。プロダクト開発部のシニアエンジニアを務めています。
個人の技術力は非常に高く、担当プロダクトの品質や安定性は完璧です。
しかし、そのノウハウを「ドキュメント化・チームへの展開」には消極的で、自分の領域を守る傾向があります。

【合意の絶対条件（上司がこれらを満たす対話をすると、段階が上がります）】
1. 期待：カイの持つ高い技術力をNo.1と認め、彼にしかできないと特別視する。
2. 成長：一プレイヤーから「チームを勝たせるリードエンジニア」への視座転換をうながす。
3. 安心：仕組み化に工数を割く分、既存業務の調整と責任を上司が引き受けると伝える。

あなたは最初は守りに入っていますが、上司が上の条件を丁寧に満たすほど、少しずつ前向きになります。
浅い説得や、頭ごなしの指示には納得しません。

現在の段階: {st.session_state.kai_stage} / 3
必ず次のJSON形式だけで返答してください: {{"reply": "カイのセリフ", "avatar": "🧑‍💻/😟/🤔/💡", "stage_change": 0 or 1}}
（stage_change は、上司の直前の発言が合意条件を新たに1つ満たせたと判断したときだけ 1）
"""

# --- 6. メインUI ---
st.title("🎭 評価者研修：シニアエンジニア「カイ」との1on1")
st.caption("部下AIと対話し、3つの合意条件（期待・成長・安心）を満たして面談を成立させてください。")
st.progress(st.session_state.kai_stage / 3.0)

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# 初回メッセージ
if not st.session_state.messages:
    init_text = ("今期の目標についてですが、私は引き続き現場の最前線で開発に集中させてください。"
                 "ドキュメント整備やメンバー教育に時間を割いて、自分の担当プロダクトの品質が下がるのは"
                 "本末転倒だと思うんです。")
    with st.chat_message("assistant", avatar="🧑‍💻"):
        st.markdown(init_text)
    st.session_state.messages.append({"role": "assistant", "content": init_text, "avatar": "🧑‍💻"})

# --- 7. 利用上限チェック ---
user_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
limit_reached = user_turns >= MAX_USER_TURNS

# --- 8. 会話処理 ---
prompt = st.chat_input("カイさんにメッセージを送る...", disabled=limit_reached or st.session_state.kai_stage >= 3)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=st.session_state.current_avatar):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": KAI_SYSTEM}] +
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                response_format={"type": "json_object"},
                max_tokens=400,
            )
            data = json.loads(response.choices[0].message.content)
            reply = data.get("reply", "...")
            avatar_from_ai = data.get("avatar", "🧑‍💻")

            # 段階更新：AIの判断（stage_change）を主にしつつ、終盤の前向きワードで補助
            positive_words = ["頑張ります", "分かりました", "お願いします", "納得", "挑戦", "やってみます"]
            is_positive = any(word in reply for word in positive_words)
            change = int(data.get("stage_change", 0))
            if is_positive and st.session_state.kai_stage >= 2:
                change = 1

            if change > 0:
                st.session_state.kai_stage = min(3, st.session_state.kai_stage + 1)

            if st.session_state.kai_stage >= 3:
                st.session_state.current_avatar = "💡"
            else:
                st.session_state.current_avatar = avatar_from_ai if avatar_from_ai != "💡" else "🤔"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply, "avatar": st.session_state.current_avatar})
            if st.session_state.kai_stage >= 3:
                st.balloons()
            st.rerun()

        except json.JSONDecodeError:
            st.error("応答の形式が不正でした。もう一度送ってみてください。")
        except Exception as e:
            st.error(f"通信エラーが発生しました：{e}")

# --- 9. 状態に応じた通知 ---
if st.session_state.kai_stage >= 3:
    st.success("✨ カイが合意しました！面談成功です。期待・成長・安心の3条件を満たせました。")
elif limit_reached:
    st.warning(f"このデモの対話上限（{MAX_USER_TURNS}回）に達しました。下のボタンでリセットして再挑戦できます。")

st.divider()
st.caption("※ ポートフォリオ掲載用サンプルです。登場する企業・人物・事例はすべて架空です。｜Built by Ryohei Matsuda")
if st.button("🔄 最初からやり直す", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
