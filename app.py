import streamlit as st
from openai import OpenAI
import json

# ============================================================
# 評価フィードバック面談ロールプレイ｜松田サンプルエンジニアリング（ポートフォリオ用サンプル）
# 部下AI「リク」と評価面談で対話し、3つの本音を解消して納得を引き出す
# ※登場する企業・人物・事例はすべて架空です
# ============================================================

# --- 1. ページ設定 ---
st.set_page_config(page_title="評価面談ロールプレイ：部下のリク", page_icon="🗣️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stChatMessage { border-radius: 20px; margin-bottom: 15px; border: 1px solid #ddd; padding: 10px; }
    [data-testid="stChatMessageAvatar"] {
        width: 70px !important; height: 70px !important;
        font-size: 45px !important; line-height: 70px !important;
        border: 2px solid #2196f3; background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 設定値 ---
MAX_USER_TURNS = 15  # 公開デモの暴走・課金対策

HONNE = {
    1: "成果は出しているのに、評価に反映されていないと感じている",
    2: "評価基準が不透明で、何を期待されているか分からない",
    3: "このまま報われないなら、ここにいる意味があるのか（将来への不安）",
}

# --- 3. APIキー ---
api_key = st.secrets.get("OPENAI_API_KEY", "").strip().strip('"')
if not api_key:
    st.error("APIキーが設定されていません。アプリ設定の Secrets に OPENAI_API_KEY を登録してください。")
    st.stop()
client = OpenAI(api_key=api_key)

# --- 4. セッション管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.resolved = {1: False, 2: False, 3: False}
    st.session_state.current_avatar = "😟"

def resolved_count():
    return sum(st.session_state.resolved.values())

# --- 5. プロンプト ---
resolved_status = "、".join(
    [f"本音{k}={'解消済' if v else '未解消'}" for k, v in st.session_state.resolved.items()]
)

RIKU_SYSTEM = f"""
あなたは部下の「リク」です。松田サンプルエンジニアリングの入社4年目・中堅社員。
担当業務の成果はしっかり出していますが、今回の評価が自己評価より低く、納得できていません。
評価面談の場で、上司（ユーザー）と1対1で話しています。

あなたは次の3つの本音を抱えています。
【本音1】{HONNE[1]}。
　→ 上司が、あなたの具体的な成果をきちんと把握・承認したうえで、評価は成果の大きさだけで決まらないことを誠実に説明したら、解消する。
【本音2】{HONNE[2]}。
　→ 上司が、評価の観点や、次にあなたに期待する具体的な行動・基準を明確に示したら、解消する。
【本音3】{HONNE[3]}。
　→ 上司が、あなたの成長機会やキャリアの道筋を具体的に示し、あなたを必要としていると伝えたら、解消する。

【厳守ルール】
- 上司の発言が、まだ解消されていない本音のどれかに「的確に」応えたときだけ、その本音は解消される。
- 表面的な褒め、頭ごなしの説得、評価の一方的な正当化、ただの励まし、感情論では解消されない（その場合の resolved_id は 0）。
- 解消された本音については、少し前向きに、感情を動かして反応する。
- まだ解消されていない本音が残っているなら、そのうち1つを、セリフの中でさりげなくヒントとして匂わせる。ただし毎回同じ言い回しを避け、対話が進むごとに少しずつ歩み寄り、態度を軟化させること（同じ場所を堂々巡りしない）。
- 3つすべて解消されたら、心から納得して前を向く。
- 1回の発言は2〜4文程度で、自然な口語にする。

現在の解消状況: {resolved_status}

必ず次のJSON形式だけで返答してください:
{{"reply": "リクのセリフ", "avatar": "😟/🤔/💡", "resolved_id": 今回新たに解消した本音の番号(1か2か3)。解消なしなら0}}
"""

# --- 6. メインUI ---
st.title("🎭 評価面談ロールプレイ：部下「リク」")
st.caption("評価に納得していない部下と1on1。3つの本音に向き合い、納得を引き出してください。")
st.progress(resolved_count() / 3.0, text=f"納得度：{resolved_count()} / 3")

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# 初回メッセージ
if not st.session_state.messages:
    init_text = ("お時間ありがとうございます。……正直に言うと、今回の評価、僕は納得できていないんです。"
                 "成果はちゃんと出してきたつもりなので。何がいけなかったのか、教えてもらえますか。")
    with st.chat_message("assistant", avatar="😟"):
        st.markdown(init_text)
    st.session_state.messages.append({"role": "assistant", "content": init_text, "avatar": "😟"})

# --- 7. 利用上限チェック ---
user_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
limit_reached = user_turns >= MAX_USER_TURNS
done = resolved_count() >= 3

# --- 8. 会話処理 ---
prompt = st.chat_input("リクさんにメッセージを送る...", disabled=limit_reached or done)
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=st.session_state.current_avatar):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": RIKU_SYSTEM}] +
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                response_format={"type": "json_object"},
                max_tokens=400,
            )
            data = json.loads(response.choices[0].message.content)
            reply = data.get("reply", "...")
            avatar_from_ai = data.get("avatar", "🤔")

            # 本音の解消を反映（未解消のものだけ／二重カウント防止）
            rid = int(data.get("resolved_id", 0) or 0)
            if rid in (1, 2, 3) and not st.session_state.resolved[rid]:
                st.session_state.resolved[rid] = True

            if resolved_count() >= 3:
                st.session_state.current_avatar = "💡"
            else:
                st.session_state.current_avatar = avatar_from_ai if avatar_from_ai != "💡" else "🤔"

            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply, "avatar": st.session_state.current_avatar})
            if resolved_count() >= 3:
                st.balloons()
            st.rerun()

        except json.JSONDecodeError:
            st.error("応答の形式が不正でした。もう一度送ってみてください。")
        except Exception as e:
            st.error(f"通信エラーが発生しました：{e}")

# --- 9. 状態に応じた通知 ---
if done:
    st.success("✨ リクが納得しました！面談成功です。3つの本音（成果の承認・期待の明確化・将来への道筋）に向き合えました。")
elif limit_reached:
    st.warning(f"このデモの対話上限（{MAX_USER_TURNS}回）に達しました。下のボタンでリセットして再挑戦できます。")

# 進行中ヒント（受講者向けの薄いガイド）
if not done and st.session_state.messages:
    with st.expander("💭 ヒント：リクは何を求めている？"):
        st.markdown(
            "- 成果を**具体的に**認めたうえで、評価が成果だけで決まらない理由を誠実に\n"
            "- 次に何を期待しているか、**評価の観点を具体的に**\n"
            "- この先の**成長機会・キャリアの道筋**と、必要としている気持ちを"
        )

st.divider()
st.caption("※ ポートフォリオ掲載用サンプルです。登場する企業・人物・事例はすべて架空です。｜Built by Ryohei Matsuda")
if st.button("🔄 最初からやり直す", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
