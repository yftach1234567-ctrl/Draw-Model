import math, random
import streamlit as st

st.set_page_config(page_title="Draw Value Model", page_icon="⚽", layout="wide")
st.title("⚽ Draw Value Model")
st.caption("V1 — כושר + בית/חוץ + H2H + HT X + מודל שערים + Value")

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def poisson(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def poisson_probs(lh, la, max_goals=8):
    hp = [poisson(i, lh) for i in range(max_goals + 1)]
    ap = [poisson(i, la) for i in range(max_goals + 1)]
    z = sum(a*b for a in hp for b in ap)
    p1 = sum(hp[i]*ap[j] for i in range(max_goals+1) for j in range(max_goals+1) if i > j) / z
    px = sum(hp[i]*ap[j] for i in range(max_goals+1) for j in range(max_goals+1) if i == j) / z
    p2 = sum(hp[i]*ap[j] for i in range(max_goals+1) for j in range(max_goals+1) if i < j) / z
    return p1, px, p2

def sample_poisson(lam, rng):
    L, k, p = math.exp(-lam), 0, 1.0
    while p > L:
        k += 1
        p *= rng.random()
    return k - 1

def simulate(lh, la, n, seed):
    rng = random.Random(seed)
    counts = {1: 0, 0: 0, 2: 0}
    scores = {}
    for _ in range(n):
        h, a = sample_poisson(lh, rng), sample_poisson(la, rng)
        result = 1 if h > a else 2 if h < a else 0
        counts[result] += 1
        scores[(h, a)] = scores.get((h, a), 0) + 1
    return counts, scores

def verdict(edge):
    if edge >= .05: return "🟢🟢 VALUE חזק"
    if edge >= .03: return "🟢 VALUE"
    if edge >= .01: return "🟡 גבולי"
    return "🔴 NO BET"

st.sidebar.header("משחק")
home = st.sidebar.text_input("קבוצה ביתית", "מכבי נתניה")
away = st.sidebar.text_input("קבוצה אורחת", "בני סכנין")
league = st.sidebar.text_input("ליגה", "ליגת העל")

st.sidebar.header("נתוני שערים")
hs = st.sidebar.number_input("בית: שערי זכות", .2, 4.5, 1.35, .01)
hc = st.sidebar.number_input("בית: שערי חובה", .2, 4.5, 1.20, .01)
aws = st.sidebar.number_input("חוץ: שערי זכות", .2, 4.5, 1.20, .01)
awc = st.sidebar.number_input("חוץ: שערי חובה", .2, 4.5, 1.30, .01)

st.sidebar.header("היסטוריית תיקו")
hd = st.sidebar.slider("X של הבית (%)", 0, 60, 30)
ad = st.sidebar.slider("X של החוץ (%)", 0, 60, 30)
ld = st.sidebar.slider("X בליגה (%)", 0, 60, 27)
h2h = st.sidebar.slider("X ב-H2H (%)", 0, 60, 30)

st.sidebar.header("מחצית")
hht = st.sidebar.slider("HT X של הבית (%)", 0, 60, 35)
aht = st.sidebar.slider("HT X של החוץ (%)", 0, 60, 34)
lht = st.sidebar.slider("HT X בליגה (%)", 0, 60, 31)
htft = st.sidebar.slider("HT X → FT X (%)", 0, 80, 50)

st.sidebar.header("Winner")
oddx = st.sidebar.number_input("יחס Winner X", 1.01, 20.0, 3.60, .01)
oddxx = st.sidebar.number_input("יחס Winner X/X", 1.01, 30.0, 4.20, .01)

st.sidebar.header("סימולציה")
n = st.sidebar.selectbox("מספר סימולציות", [1000, 5000, 10000], 0)
seed = st.sidebar.number_input("Seed", 0, 999999, 42)

lh = .75*((hs + awc)/2) + .25*1.25
la = .75*((aws + hc)/2) + .25*1.10
p1p, pxp, p2p = poisson_probs(lh, la)

hist = .30*hd/100 + .25*ad/100 + .20*ld/100 + .25*h2h/100
px = clamp(.65*pxp + .35*hist, .01, .80)
non = 1 - pxp
p1 = (1-px) * p1p / non
p2 = (1-px) * p2p / non

pht = clamp(.45*hht/100 + .35*aht/100 + .20*lht/100, .01, .80)
pxx = clamp(pht * (htft/100) * 1.05, .005, .70)

counts, scores = simulate(lh, la, n, seed)
sim1, simx, sim2 = counts[1]/n, counts[0]/n, counts[2]/n

bex, edge, ev = 1/oddx, px - 1/oddx, px*oddx - 1
bexx, edgexx, evxx = 1/oddxx, pxx - 1/oddxx, pxx*oddxx - 1

st.subheader(f"{home} — {away}")
a,b,c = st.columns(3)
a.metric("1", f"{p1*100:.1f}%")
b.metric("X", f"{px*100:.1f}%")
c.metric("2", f"{p2*100:.1f}%")

st.markdown("### 🎲 סימולציה")
a,b,c = st.columns(3)
a.metric("1", f"{sim1*100:.1f}%")
b.metric("X", f"{simx*100:.1f}%")
c.metric("2", f"{sim2*100:.1f}%")

st.markdown("### 💰 Value על X")
a,b,c,d = st.columns(4)
a.metric("P(X)", f"{px*100:.1f}%")
b.metric("Break-even", f"{bex*100:.2f}%")
c.metric("Edge", f"{edge*100:+.2f}%")
d.metric("EV", f"{ev*100:+.1f}%")
if edge >= .03:
    st.success(verdict(edge))
elif edge >= .01:
    st.warning(verdict(edge))
else:
    st.error(verdict(edge))

st.markdown("### ⏱️ HT X → FT X")
a,b,c,d = st.columns(4)
a.metric("P(HT X)", f"{pht*100:.1f}%")
b.metric("P(X/X)", f"{pxx*100:.1f}%")
c.metric("BE X/X", f"{bexx*100:.2f}%")
d.metric("Edge X/X", f"{edgexx*100:+.2f}%")
st.write(f"EV X/X: {evxx*100:+.1f}% — {verdict(edgexx)}")

st.markdown("### 🔢 תוצאות מדויקות בולטות")
for (h, a_), cnt in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]:
    st.write(f"**{h}-{a_}** — {cnt/n*100:.1f}%")

st.markdown("---")
st.caption(f"Poisson X: {pxp*100:.1f}% | Historical X blend: {hist*100:.1f}% | ליגה: {league}")
st.info("V1 היא אבטיפוס. הנתונים מוזנים ידנית; אין עדיין חיבור אוטומטי ל-Winner או למאגרי תוצאות. לפני שימוש בכסף אמיתי יש לבצע backtesting.")

