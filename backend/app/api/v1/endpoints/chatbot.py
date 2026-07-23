import uuid
import json
import logging
import asyncio
import numpy as np
from typing import List, Any, Optional, Dict
from fastapi import APIRouter, Depends, UploadFile, File, status, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pathlib import Path

from app.core.db import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.core.dependencies import get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.models.chatbot import ChatbotDocument, ChatbotDocumentChunk, ChatSession, ChatMessage
from app.services.storage import StorageService
from app.services.parser import ParserService
from app.services.embeddings import EmbeddingService

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_document_embeddings_bg(document_id: uuid.UUID, file_name: str, file_url: str, raw_text: str, db_session_factory):
    """Background task to chunk document text, generate vector embeddings, and save to database."""
    logger.info(f"Background embedding generation started for doc: {file_name} ({document_id})")
    try:
        embedding_service = EmbeddingService()
        chunks = embedding_service.chunk_text(raw_text)
        
        if not chunks:
            logger.warning(f"No text chunks extracted for document {file_name}.")
            return
            
        logger.info(f"Splitted document {file_name} into {len(chunks)} chunks. Generating embeddings...")
        
        # We need a new session in background thread
        async with db_session_factory() as db:
            for chunk in chunks:
                vector = embedding_service.generate_embedding(chunk)
                db_chunk = ChatbotDocumentChunk(
                    document_id=document_id,
                    content=chunk,
                    embedding=vector
                )
                db.add(db_chunk)
            await db.commit()
            logger.info(f"Successfully saved {len(chunks)} embeddings chunks for doc {file_name}.")
    except Exception as e:
        logger.error(f"Failed to generate background embeddings for document {document_id}: {str(e)}")


@router.get("/upload")
async def get_upload_info():
    """Information endpoint for chatbot document upload."""
    return {
        "message": "Chatbot document upload endpoint requires an HTTP POST request with multipart/form-data containing the PDF, DOCX, or TXT file."
    }


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_chatbot_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Upload reference file (PDF or DOCX), parse text, and enqueue background vector embedding generation."""
    filename = file.filename or "document.pdf"
    ext = Path(filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".doc", ".txt"]:
        raise BadRequestException(message="Unsupported file format. Please upload PDF, DOCX, or TXT.")
        
    try:
        content = await file.read()
    except Exception:
        raise BadRequestException(message="Failed to read uploaded file.")
        
    storage_service = StorageService()
    file_url, _ = await storage_service.save_file(content, filename)
    
    try:
        parser_service = ParserService()
        parsed_data = await parser_service.parse_resume(content, filename)
        raw_text = parsed_data.get("raw_text") or ""
        
        if not raw_text.strip():
            raise BadRequestException(message="No readable text found in document.")
            
        # Create Document record
        doc = ChatbotDocument(
            user_id=current_user.id,
            file_name=filename,
            file_url=file_url,
            raw_text=raw_text
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        
        # Dispatch background embedding generator
        from app.core.db import SessionLocal
        background_tasks.add_task(
            process_document_embeddings_bg,
            doc.id,
            filename,
            file_url,
            raw_text,
            SessionLocal
        )
        
        return {
            "document_id": doc.id,
            "file_name": filename,
            "status": "processing",
            "message": "File uploaded successfully. Text parsing and embedding calculations are running in the background."
        }
        
    except Exception as e:
        await storage_service.delete_file(file_url)
        raise BadRequestException(message=f"Failed to process document: {str(e)}")


@router.get("/documents")
async def get_chatbot_documents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all active context documents uploaded by current user."""
    stmt = (
        select(ChatbotDocument)
        .where(
            (ChatbotDocument.user_id == current_user.id) | (ChatbotDocument.user_id == None),
            ChatbotDocument.deleted_at == None
        )
        .order_by(ChatbotDocument.created_at.desc())
    )
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return [{"id": str(d.id), "file_name": d.file_name, "created_at": d.created_at.isoformat() if d.created_at else ""} for d in docs]


@router.delete("/documents/{document_id}")
async def delete_chatbot_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a chatbot document so its chunks are excluded from RAG search."""
    stmt = select(ChatbotDocument).where(ChatbotDocument.id == document_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise NotFoundException(message="Document not found.")
        
    from datetime import datetime, timezone
    doc.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"success": True, "message": "Document removed from context."}


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    title: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new chatbot session."""
    session = ChatSession(
        user_id=current_user.id,
        title=title
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at
    }


@router.get("/sessions", response_model=List[Dict[str, Any]])
async def list_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve chat history sessions for the current user."""
    stmt = select(ChatSession).where(
        ChatSession.user_id == current_user.id,
        ChatSession.deleted_at.is_(None)
    ).order_by(ChatSession.created_at.desc())
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    return [
        {"id": s.id, "title": s.title, "created_at": s.created_at}
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Delete a chat session."""
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundException(message="Session not found.")
    if session.user_id != current_user.id:
        raise ForbiddenException(message="Forbidden session access.")
        
    await db.delete(session)
    await db.commit()
    return {"success": True, "message": "Chat session deleted successfully."}


@router.get("/sessions/{session_id}/messages", response_model=List[Dict[str, Any]])
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve all historical messages for a chat session."""
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundException(message="Session not found.")
    if session.user_id != current_user.id:
        raise ForbiddenException(message="Forbidden session access.")
        
    stmt_msg = select(ChatMessage).where(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc())
    
    result_msg = await db.execute(stmt_msg)
    messages = result_msg.scalars().all()
    
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "confidence_score": m.confidence_score,
            "created_at": m.created_at
        }
        for m in messages
    ]


@router.post("/sessions/{session_id}/stream")
async def stream_chatbot_response(
    session_id: uuid.UUID,
    content: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Perform RAG search on uploaded context files, formulate prompt, and stream Gemini tokens via SSE."""
    # Verify session ownership
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise NotFoundException(message="Session not found.")
    if session.user_id != current_user.id:
        raise ForbiddenException(message="Forbidden session access.")
        
    # Save User message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=content
    )
    db.add(user_msg)
    await db.commit()

    async def sse_event_generator():
        embedding_service = EmbeddingService()
        query_vector = embedding_service.generate_embedding(content)
        
        # 1. Cosine similarity query on pgvector
        # Cosine distance operator <=> translates to cosine_distance
        distance = ChatbotDocumentChunk.embedding.cosine_distance(query_vector)
        stmt_chunks = (
            select(ChatbotDocumentChunk, ChatbotDocument.file_name)
            .join(ChatbotDocument, ChatbotDocument.id == ChatbotDocumentChunk.document_id)
            .where(
                ChatbotDocument.deleted_at == None,
                (ChatbotDocument.user_id == current_user.id) | (ChatbotDocument.user_id == None)
            )
            .order_by(distance)
            .limit(4)
        )
        
        chunks_res = await db.execute(stmt_chunks)
        results = chunks_res.all()
        
        # Gather context text and citation names
        context_blocks = []
        citations_list = []
        
        for chunk, doc_name in results:
            context_blocks.append(chunk.content)
            if doc_name not in citations_list:
                citations_list.append(doc_name)
                
        context_str = "\n---\n".join(context_blocks)
        
        # Calculate confidence score based on similarity distance
        # Lower distance = higher similarity
        avg_distance = 1.0
        if results:
            # SQLAlchemy retrieves (model_instance, string)
            distances = []
            for chunk, _ in results:
                # Calculate vector distance manually for confidence calculations
                v1 = np.array(chunk.embedding)
                v2 = np.array(query_vector)
                dot_product = np.dot(v1, v2)
                norm_v1 = np.linalg.norm(v1)
                norm_v2 = np.linalg.norm(v2)
                sim = dot_product / (norm_v1 * norm_v2) if norm_v1 > 0 and norm_v2 > 0 else 0.0
                distances.append(1.0 - sim)
            avg_distance = sum(distances) / len(distances)
            
        confidence = max(0.0, min(1.0, 1.0 - avg_distance))
        
        # 2. Build system RAG prompt
        system_prompt = f"""
        You are NaziranGPT's expert Career chatbot. Answer the User Query based ONLY on the provided context documents.
        If the information is not contained in the context documents, reply saying you cannot find the answer in the provided documents and keep confidence indicators low.
        
        [CONTEXT DOCUMENTS]
        {context_str if context_str else "No context documents uploaded yet."}
        
        [USER QUERY]
        {content}
        
        Answer professionally and clearly.
        """

        full_response_text = ""
        
        # Check Gemini API Key
        gemini_success = False
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # Streaming call
                response = await asyncio.to_thread(
                    model.generate_content,
                    system_prompt,
                    stream=True
                )
                
                for chunk in response:
                    token = chunk.text
                    full_response_text += token
                    yield f"data: {json.dumps({'token': token})}\n\n"
                    await asyncio.sleep(0.01) # Yield to event loop
                
                gemini_success = True
                    
            except Exception as e:
                logger.error(f"Gemini streaming failed: {str(e)}")

        if not gemini_success:
            # Fallback local RAG response generator
            fallback_text = (
                f"Note: Running in local database RAG preview mode (Gemini Key not configured or invalid).\n"
                f"Retrieved Context Chunks:\n\n"
            )
            for chunk in context_blocks:
                fallback_text += f"- {chunk[:150]}...\n"
                
            for char in fallback_text:
                full_response_text += char
                yield f"data: {json.dumps({'token': char})}\n\n"
                await asyncio.sleep(0.002)

        # 3. Save generated response to db
        db_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=full_response_text,
            citations={"files": citations_list} if citations_list else None,
            confidence_score=float(confidence)
        )
        db.add(db_msg)
        await db.commit()
        await db.refresh(db_msg)
        
        # Yield termination payload with citations and confidence score
        yield f"data: {json.dumps({'done': True, 'message_id': str(db_msg.id), 'citations': citations_list, 'confidence_score': float(confidence)})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
