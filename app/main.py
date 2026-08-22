import io
import os
import time
from datetime import datetime
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from .rag import chunks, cosine, embed, generate

URL=os.getenv("DATABASE_URL","sqlite:///./logiai.db")
engine=create_engine(URL,connect_args={"check_same_thread":False} if URL.startswith("sqlite") else {})
SessionLocal=sessionmaker(bind=engine,expire_on_commit=False)
class Base(DeclarativeBase): pass
class Document(Base):
    __tablename__="documents"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(200)); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Chunk(Base):
    __tablename__="chunks"; id:Mapped[int]=mapped_column(primary_key=True); document_id:Mapped[int]=mapped_column(ForeignKey("documents.id")); content:Mapped[str]=mapped_column(Text); embedding:Mapped[str]=mapped_column(Text)
class Query(Base):
    __tablename__="queries"; id:Mapped[int]=mapped_column(primary_key=True); question:Mapped[str]=mapped_column(Text); answer:Mapped[str]=mapped_column(Text); grounded:Mapped[int]=mapped_column(Integer); latency_ms:Mapped[float]=mapped_column(Float); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Feedback(Base):
    __tablename__="feedback"; id:Mapped[int]=mapped_column(primary_key=True); query_id:Mapped[int]=mapped_column(ForeignKey("queries.id"),unique=True); helpful:Mapped[int]=mapped_column(Integer); comment:Mapped[str|None]=mapped_column(Text,nullable=True)
Base.metadata.create_all(engine)
app=FastAPI(title="LogiAI",description="Grounded logistics document assistant")
def db():
    s=SessionLocal()
    try: yield s
    finally:s.close()
class Ask(BaseModel): question:str=Field(min_length=3)
class FeedbackIn(BaseModel): query_id:int; helpful:bool; comment:str|None=None

@app.get("/health")
def health():return {"status":"ok","llm_provider":os.getenv("LLM_PROVIDER","stub")}
@app.post("/documents",status_code=201)
async def upload(file:UploadFile=File(...),s:Session=Depends(db)):
    raw=await file.read()
    if len(raw)>10_000_000:raise HTTPException(413,"Maximum file size is 10 MB")
    try:
        if file.filename and file.filename.lower().endswith(".pdf"): text="\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
        else:text=raw.decode("utf-8")
    except Exception as exc:raise HTTPException(422,"Could not extract text") from exc
    if not text.strip():raise HTTPException(422,"Document contains no extractable text")
    doc=Document(name=file.filename or "document");s.add(doc);s.flush()
    for part in chunks(text):s.add(Chunk(document_id=doc.id,content=part,embedding=",".join(map(str,embed(part)))))
    s.commit();return {"id":doc.id,"name":doc.name}
@app.post("/ask")
def ask(data:Ask,s:Session=Depends(db)):
    started=time.perf_counter();qv=embed(data.question);all_chunks=s.scalars(select(Chunk)).all()
    ranked=sorted(((cosine(qv,[float(x) for x in c.embedding.split(",")]),c) for c in all_chunks),key=lambda x:x[0],reverse=True)
    selected=[c for score,c in ranked[:3] if score>=0.05];result=generate(data.question,[c.content for c in selected]);latency=(time.perf_counter()-started)*1000
    record=Query(question=data.question,answer=result.answer,grounded=int(result.grounded),latency_ms=latency);s.add(record);s.commit();s.refresh(record)
    sources=[{"document_id":c.document_id,"chunk_id":c.id,"excerpt":c.content[:160]} for c in selected]
    return {"query_id":record.id,"answer":result.answer,"grounded":result.grounded,"sources":sources,"latency_ms":round(latency,2)}
@app.post("/feedback",status_code=201)
def feedback(data:FeedbackIn,s:Session=Depends(db)):
    if not s.get(Query,data.query_id):raise HTTPException(404,"Query not found")
    item=Feedback(query_id=data.query_id,helpful=int(data.helpful),comment=data.comment);s.add(item);s.commit();return {"status":"recorded"}
@app.get("/evaluations")
def evaluations(s:Session=Depends(db)):
    queries=s.scalars(select(Query)).all();feedbacks=s.scalars(select(Feedback)).all();total=len(queries)
    return {"questions":total,"grounded_rate":round(sum(q.grounded for q in queries)/total,3) if total else 0,"average_latency_ms":round(sum(q.latency_ms for q in queries)/total,2) if total else 0,"feedback_count":len(feedbacks),"helpful_rate":round(sum(f.helpful for f in feedbacks)/len(feedbacks),3) if feedbacks else 0}


