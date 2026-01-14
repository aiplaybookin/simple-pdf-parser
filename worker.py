import os
import io
import json
import base64
import asyncio
import tempfile
import logging
from typing import Literal, List, Dict, Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from pypdf import PdfReader
from pdf2image import convert_from_path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STREAM_NAME = "pdf_processing_tasks"
CONSUMER_GROUP = "pdf_workers"
CONSUMER_NAME = "worker_1"
CHUNK_SIZE = 5000  # words per chunk for summarization


def parse_pdf_with_gemini(pdf_file: bytes, filename: str) -> str:
    """Parse PDF using Gemini 2.0 Flash by converting pages to images."""
    markdown_content = f"# {filename}\n\n"

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_file.write(pdf_file)
        tmp_path = tmp_file.name

    try:
        images = convert_from_path(tmp_path)
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        for page_num, image in enumerate(images, start=1):
            markdown_content += f"## Page {page_num}\n\n"

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            prompt = """Analyze this PDF page image and extract all contents in markdown format.

For text content:
- Extract all text preserving structure and formatting
- Use appropriate markdown headers, lists, tables, superscript, subscripts, chemical formulas, etc.

For figures, charts, or graphs:
- Provide a detailed summary describing what the visual represents
- Include key data points, trends, or insights visible in the visual
- Format as: **[Figure/Chart/Graph Summary]:** [your description]

Please be thorough and accurate in your extraction."""

            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt, types.Part.from_bytes(
                    data=img_byte_arr.getvalue(),
                    mime_type="image/png"
                )]
            )
            markdown_content += response.text + "\n\n"

        return markdown_content

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def parse_pdf_with_pypdf(pdf_file: bytes, filename: str) -> str:
    """Parse PDF using PyPDF and convert to markdown."""
    try:
        logger.info(f"Starting PyPDF parsing for {filename}")
        markdown_content = f"# {filename}\n\n"

        pdf_reader = PdfReader(io.BytesIO(pdf_file), strict=False)
        logger.info(f"PDF has {len(pdf_reader.pages)} pages")

        for page_num, page in enumerate(pdf_reader.pages, start=1):
            logger.info(f"Extracting text from page {page_num}")

            text = ""
            extraction_methods = [
                ("default", lambda: page.extract_text()),
                ("layout", lambda: page.extract_text(extraction_mode="layout")),
                ("plain", lambda: page.extract_text(extraction_mode="plain")),
            ]

            for method_name, extract_func in extraction_methods:
                try:
                    text = extract_func()
                    if text.strip():
                        logger.info(f"Successfully extracted text using {method_name} method")
                        break
                except Exception as e:
                    logger.warning(f"Extraction method {method_name} failed: {str(e)}")
                    continue

            if not text.strip():
                text = f"[Could not extract text from this page due to PDF formatting issues]"
                logger.warning(f"All extraction methods failed for page {page_num}")

            markdown_content += f"## Page {page_num}\n\n{text}\n\n"

        logger.info(f"PyPDF parsing complete for {filename}")
        return markdown_content
    except Exception as e:
        logger.error(f"Error in parse_pdf_with_pypdf: {str(e)}", exc_info=True)
        raise


def chunk_text_by_words(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split text into chunks by word count."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def summarize_with_gemini(text: str, filename: str) -> str:
    """
    Summarize markdown content using Gemini with chunked processing.

    Process:
    1. Split text into chunks of 5000 words
    2. Summarize each chunk
    3. Combine intermediate summaries
    4. Create final summary
    """
    try:
        logger.info(f"Starting summarization for {filename}")
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Count total words
        word_count = len(text.split())
        logger.info(f"Total words in {filename}: {word_count}")

        # If text is small enough, summarize directly
        if word_count <= CHUNK_SIZE:
            logger.info(f"Text is small ({word_count} words), summarizing directly")
            prompt = f"""Please provide a comprehensive summary of the following document.

Document content:
{text}

Provide a clear, concise summary that captures the main points, key findings, and important details."""

            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            return response.text.strip()

        # For large documents, use chunked processing
        logger.info(f"Text is large ({word_count} words), using chunked processing")
        chunks = chunk_text_by_words(text, CHUNK_SIZE)
        logger.info(f"Split into {len(chunks)} chunks")

        # Step 1: Summarize each chunk
        intermediate_summaries = []
        for idx, chunk in enumerate(chunks, start=1):
            logger.info(f"Summarizing chunk {idx}/{len(chunks)}")

            prompt = f"""Please provide a concise summary of this section of a document (part {idx} of {len(chunks)}).
Focus on key points and important information.

Content:
{chunk}

Summary:"""

            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=[prompt]
            )
            intermediate_summaries.append(response.text.strip())

        # Step 2: Combine intermediate summaries
        logger.info(f"Combining {len(intermediate_summaries)} intermediate summaries")
        combined_summary = "\n\n".join([
            f"Section {i+1}: {summary}"
            for i, summary in enumerate(intermediate_summaries)
        ])

        # Step 3: Create final summary
        logger.info("Creating final summary")
        final_prompt = f"""Based on the following section summaries from a document, create a comprehensive final summary.
Synthesize the information into a cohesive summary that captures the overall content, main themes, and key points.

Section Summaries:
{combined_summary}

Final Comprehensive Summary:"""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[final_prompt]
        )

        final_summary = response.text.strip()
        logger.info(f"Summarization complete for {filename}")
        return final_summary

    except Exception as e:
        logger.error(f"Error summarizing {filename}: {str(e)}", exc_info=True)
        return f"Error generating summary: {str(e)}"


async def update_task_status(
    redis_client: Redis,
    task_id: str,
    status: str,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Update task status in Redis."""
    status_data = {
        "status": status,
        **(data or {})
    }
    await redis_client.set(
        f"task:{task_id}:status",
        json.dumps(status_data),
        ex=3600  # Expire after 1 hour
    )


async def process_task(
    redis_client: Redis,
    task_id: str,
    task_data: Dict[str, Any]
) -> None:
    """Process a single task."""
    try:
        files_data = json.loads(task_data['files_data'])
        mode = task_data['mode']
        total_files = len(files_data)

        logger.info(f"Processing task {task_id} with {total_files} files in {mode} mode")

        await update_task_status(redis_client, task_id, "PROCESSING", {
            "current": 0,
            "total": total_files,
            "message": "Starting processing..."
        })

        processed_files = []
        failed_files = []

        for idx, file_data in enumerate(files_data, start=1):
            filename = file_data['filename']

            await update_task_status(redis_client, task_id, "PROCESSING", {
                "current": idx,
                "total": total_files,
                "message": f"Processing {filename}...",
                "processed": processed_files,
                "failed": failed_files
            })

            try:
                logger.info(f"Processing file {idx}/{total_files}: {filename}")

                # Decode base64 content
                content = base64.b64decode(file_data['content'])

                # Parse based on mode
                if mode == "gemini":
                    logger.info(f"Using Gemini mode for {filename}")
                    markdown = parse_pdf_with_gemini(content, filename)
                else:
                    logger.info(f"Using PyPDF mode for {filename}")
                    markdown = parse_pdf_with_pypdf(content, filename)

                # Store markdown in Redis
                md_filename = filename.rsplit('.', 1)[0] + '.md'
                redis_key = f"task:{task_id}:file:{md_filename}"
                await redis_client.set(redis_key, markdown, ex=3600)

                # Update status for summarization
                await update_task_status(redis_client, task_id, "PROCESSING", {
                    "current": idx,
                    "total": total_files,
                    "message": f"Summarizing {filename}...",
                    "processed": processed_files,
                    "failed": failed_files
                })

                # Generate summary
                logger.info(f"Generating summary for {filename}")
                summary = summarize_with_gemini(markdown, filename)

                # Store summary in Redis
                summary_key = f"task:{task_id}:summary:{filename}"
                await redis_client.set(summary_key, summary, ex=3600)

                processed_files.append({
                    'filename': filename,
                    'md_filename': md_filename,
                    'status': 'success',
                    'size': len(markdown)
                })

                logger.info(f"Successfully processed and summarized {filename}")

            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}", exc_info=True)
                failed_files.append({
                    'filename': filename,
                    'status': 'failed',
                    'error': str(e)
                })

        # Final status update
        await update_task_status(redis_client, task_id, "SUCCESS", {
            "total": total_files,
            "processed": len(processed_files),
            "failed": len(failed_files),
            "files": processed_files,
            "errors": failed_files,
            "mode": mode,
            "message": "Processing complete"
        })

        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        await update_task_status(redis_client, task_id, "FAILURE", {
            "error": str(e),
            "message": f"Task failed: {str(e)}"
        })


async def create_consumer_group(redis_client: Redis) -> None:
    """Create consumer group if it doesn't exist."""
    try:
        await redis_client.xgroup_create(
            STREAM_NAME,
            CONSUMER_GROUP,
            id='0',
            mkstream=True
        )
        logger.info(f"Created consumer group: {CONSUMER_GROUP}")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"Consumer group {CONSUMER_GROUP} already exists")
        else:
            logger.error(f"Error creating consumer group: {e}")
            raise


async def process_pending_messages(redis_client: Redis) -> None:
    """Process any pending messages that weren't acknowledged."""
    try:
        pending = await redis_client.xpending_range(
            STREAM_NAME,
            CONSUMER_GROUP,
            min='-',
            max='+',
            count=10,
            consumername=CONSUMER_NAME
        )

        for message in pending:
            message_id = message['message_id']
            logger.info(f"Reclaiming pending message: {message_id}")

            # Claim the message
            claimed = await redis_client.xclaim(
                STREAM_NAME,
                CONSUMER_GROUP,
                CONSUMER_NAME,
                min_idle_time=60000,  # 1 minute
                message_ids=[message_id]
            )

            if claimed:
                for msg_id, msg_data in claimed:
                    task_id = msg_data[b'task_id'].decode('utf-8')
                    task_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in msg_data.items()}

                    logger.info(f"Processing reclaimed message: {task_id}")
                    await process_task(redis_client, task_id, task_data)
                    await redis_client.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)

    except Exception as e:
        logger.error(f"Error processing pending messages: {e}")


async def worker_loop() -> None:
    """Main worker loop to process tasks from Redis Stream."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Connecting to Redis at: {redis_url}")

    redis_client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=False  # Keep bytes for stream operations
    )

    try:
        # Create consumer group
        await create_consumer_group(redis_client)

        logger.info(f"Worker {CONSUMER_NAME} started, waiting for tasks...")

        while True:
            try:
                # Process any pending messages first
                await process_pending_messages(redis_client)

                # Read new messages from the stream
                messages = await redis_client.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={STREAM_NAME: '>'},
                    count=1,
                    block=5000  # Block for 5 seconds
                )

                if messages:
                    for _stream_name, stream_messages in messages:
                        for message_id, message_data in stream_messages:
                            task_id = message_data[b'task_id'].decode('utf-8')
                            task_data = {
                                k.decode('utf-8'): v.decode('utf-8')
                                for k, v in message_data.items()
                            }

                            logger.info(f"Processing task: {task_id}")

                            # Process the task
                            await process_task(redis_client, task_id, task_data)

                            # Acknowledge the message
                            await redis_client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)
                            logger.info(f"Task {task_id} acknowledged")

            except asyncio.CancelledError:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

    finally:
        await redis_client.aclose()
        logger.info("Worker stopped")


async def main() -> None:
    """Main entry point."""
    try:
        await worker_loop()
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")


if __name__ == "__main__":
    asyncio.run(main())
