import os,io,json
from pathlib import Path
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="QuoteLens — Aerchain",page_icon="🔎",layout="wide")
EXTRACT="""You are a procurement quote extraction agent. Extract only what is supported by the vendor response.
Return JSON: vendor_name,currency,validity_days,freight_terms,tax_terms,quality_status,
line_items:[{line_id,description,quoted_quantity,unit,unit_price,currency,confidence,evidence}],
exceptions:[{type,line_id,message,evidence}].
Never invent missing prices. If ambiguous, mark confidence low and explain why. Preserve vendor currency and unit."""
ANALYST="""You are a procurement analyst. Answer only from the supplied normalized RFx dataset.
Show calculations when useful. Flag assumptions and uncertainty. Never invent a quote. For award questions,
apply eligibility filters before comparing prices. Use concise business language and a markdown table when useful."""

def get_client():
    # Prefer Streamlit Secrets in deployed apps; fall back to environment locally.
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    key = key or os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=key) if key else None

def file_text(u):
    name=u.name.lower(); data=u.getvalue()
    if name.endswith((".txt",".md",".csv")): return data.decode("utf-8",errors="ignore")
    if name.endswith((".xlsx",".xls")):
        xl=pd.ExcelFile(io.BytesIO(data)); out=[]
        for s in xl.sheet_names:
            out.append(f"SHEET {s}\n{pd.read_excel(io.BytesIO(data),sheet_name=s).to_csv(index=False)}")
        return "\n\n".join(out)
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    return None

def extract(u,rfq):
    c=get_client()
    if not c:
        raise RuntimeError("GEMINI_API_KEY is not configured in Streamlit Secrets.")
    data=u.getvalue(); name=u.name.lower()
    prompt=EXTRACT+"\nRFQ:\n"+rfq
    txt=file_text(u)
    contents=[prompt]
    if txt is not None:
        contents.append("VENDOR RESPONSE:\n"+txt)
    elif name.endswith(".pdf"):
        contents.append(types.Part.from_bytes(data=data,mime_type="application/pdf"))
    elif name.endswith((".jpg",".jpeg",".png",".webp")):
        mime="image/png" if name.endswith(".png") else "image/webp" if name.endswith(".webp") else "image/jpeg"
        contents.append(types.Part.from_bytes(data=data,mime_type=mime))
    else:
        raise ValueError("Unsupported file.")
    r=c.models.generate_content(
        model=st.session_state.get("model","gemini-2.5-flash"),
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json",temperature=0.1),
    )
    return json.loads(r.text)

rfq_rows=[
("BX-001","5-ply corrugated box, 400x300x250 mm","pcs","10,000"),("BX-002","5-ply corrugated box, 500x400x300 mm","pcs","8,000"),
("BX-003","3-ply corrugated box, 300x200x150 mm","pcs","12,000"),("BX-004","3-ply corrugated box, 450x300x200 mm","pcs","9,000"),
("BX-005","5-ply heavy-duty box, 600x400x400 mm","pcs","5,000"),("BX-006","Die-cut mailer, 320x240x80 mm","pcs","7,500"),
("BX-007","Die-cut mailer, 400x300x100 mm","pcs","6,000"),("BX-008","Single-wall carton, 250x200x150 mm","pcs","15,000"),
("BX-009","Double-wall carton, 700x500x500 mm","pcs","3,000"),("BX-010","Archive box with lid, 450x350x300 mm","pcs","4,000"),
("BX-011","Partition set, 12-cell","sets","2,500"),("BX-012","Edge protector, 50x50x1000 mm","pcs","18,000"),
("BX-013","Corrugated sheet, 1200x800 mm","sheets","10,000"),("BX-014","Corrugated roll, 1.2 m x 50 m","rolls","800"),
("BX-015","5-ply box, 800x600x500 mm","pcs","2,500"),("BX-016","Printed shipper, 5-ply","pcs","6,000"),
("BX-017","Printed shipper, 3-ply","pcs","8,000"),("BX-018","Recycled-content carton, 5-ply","pcs","5,000"),
("BX-019","Moisture-resistant carton, 5-ply","pcs","3,500"),("BX-020","Automotive parts carton, 600x400x300 mm","pcs","4,500"),
("BX-021","E-commerce return box, medium","pcs","7,000"),("BX-022","E-commerce return box, large","pcs","5,000"),
("BX-023","Bottle divider, 6-cell","sets","3,000"),("BX-024","Pallet top sheet, 1200x1000 mm","sheets","4,000"),
("BX-025","Pallet collar, 1200x1000 mm","pcs","1,500"),("BX-026","Corner guard, 75x75x1200 mm","pcs","9,000"),
("BX-027","Floor protection sheet, 1000x2000 mm","sheets","2,000"),("BX-028","Small parts carton, 200x150x100 mm","pcs","20,000"),
("BX-029","Large appliance carton, 1000x700x700 mm","pcs","1,200"),("BX-030","Export-grade carton, 5-ply","pcs","2,000")]
rfq="\n".join(f"{a}|{b}|{c}|qty {d}" for a,b,c,d in rfq_rows)

st.title("QuoteLens")
st.caption("Aerchain take-home • RFx → heterogeneous vendor responses → normalized comparison → analyst copilot")
with st.sidebar:
    st.session_state.model=st.selectbox("Gemini model",["gemini-2.5-flash","gemini-2.5-flash-lite"],index=0)
    if get_client():
        st.success("Gemini connected")
    else:
        st.warning("Add GEMINI_API_KEY in Streamlit Secrets before running AI actions.")
    st.info("Extraction and analyst reasoning are live Gemini calls; answers are not hardcoded.")

tabs=st.tabs(["1 · RFx Copilot","2 · Vendor Intake","3 · Comparison","4 · Analyst"])
with tabs[0]:
    st.subheader("Draft the RFx")
    scope=st.text_area("Scope","Source 30 corrugated packaging SKUs for Bangalore operations; compare commercials and quality eligibility.")
    if st.button("Generate RFx draft"):
        c=get_client()
        if not c: st.error("Configure GEMINI_API_KEY in Streamlit Secrets.")
        else:
            r=c.models.generate_content(model=st.session_state.model,contents=f"Draft a buyer-ready RFx for corrugated packaging.\nScope: {scope}\nUse this 30-line structure:\n{rfq}")
            st.markdown(r.text)
with tabs[1]:
    st.subheader("Vendor responses — any shape")
    uploads=st.file_uploader("Upload responses",type=["xlsx","csv","docx","pdf","jpg","jpeg","png","txt"],accept_multiple_files=True)
    if st.button("Extract & normalize") and uploads:
        if not get_client(): st.error("Configure GEMINI_API_KEY in Streamlit Secrets.")
        else:
            out=[]; bar=st.progress(0)
            for i,u in enumerate(uploads):
                try: out.append({"file":u.name,"data":extract(u,rfq)})
                except Exception as e: out.append({"file":u.name,"error":str(e)})
                bar.progress((i+1)/len(uploads))
            st.session_state.extractions=out
    for x in st.session_state.get("extractions",[]):
        with st.expander(x["file"]):
            st.json(x.get("data",x.get("error")))
with tabs[2]:
    st.subheader("Normalized comparison")
    rows=[]
    for x in st.session_state.get("extractions",[]):
        d=x.get("data",{}); vendor=d.get("vendor_name",x["file"])
        for li in d.get("line_items",[]):
            rows.append({"Vendor":vendor,"Line":li.get("line_id"),"Unit":li.get("unit"),
                         "Price":li.get("unit_price"),"Currency":li.get("currency") or d.get("currency"),
                         "Confidence":li.get("confidence"),"Evidence":li.get("evidence")})
    if rows:
        df=pd.DataFrame(rows); st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Export CSV",df.to_csv(index=False),"normalized_quotes.csv","text/csv")
    else: st.info("Run extraction first.")
with tabs[3]:
    st.subheader("Ask the comparison")
    q=st.text_area("Question","Among vendors that passed the quality questionnaire, who is cheapest per line? Show where currency conversion or missing quotes prevent a definitive answer.")
    if st.button("Ask analyst"):
        c=get_client()
        if not c: st.error("Configure GEMINI_API_KEY in Streamlit Secrets.")
        else:
            context=json.dumps(st.session_state.get("extractions",[]),ensure_ascii=False)[:120000]
            prompt=ANALYST+"\n\nRFQ:\n"+rfq+"\n\nEXTRACTED DATA:\n"+context+"\n\nQUESTION:\n"+q
            r=c.models.generate_content(model=st.session_state.model,contents=prompt,config=types.GenerateContentConfig(temperature=0.1))
            st.markdown(r.text)
            st.caption("Trust guardrail: missing, ambiguous and ineligible data should be surfaced, not silently filled.")
