import logging
from core.services.wikimedia_service import search_licensed_videos
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from core.models import Topic
from core.services.licensed_media_service import download_licensed_video
from core.services.openrouter_service import generate_trending_topics

from core.services.openrouter_service import generate_ai_response
from core.services.internet_archive_service import (
    search_internet_archive_videos,
)
from .models import Topic, Video, Transcript, TranscriptSegment, GeneratedClip
from .serializers import TopicSerializer, VideoSerializer, TranscriptSerializer, TranscriptSegmentSerializer, GeneratedClipSerializer

from core.services.youtube_service import (
    search_youtube_videos,
    YouTubeAPIError,
)
from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .services.whisper_service import transcribe_audio
import tempfile
from pathlib import Path
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .services.caption_service import parse_caption_file
import os
import uuid
import yt_dlp
from core.services.pixabay_service import (
    search_pixabay_videos,
    download_pixabay_video,
    PixabayServiceError,
)
import imageio_ffmpeg
from core.models import Video, GeneratedClip
from core.services.ffmpeg_service import generate_video_clip

from core.services.tts_service import (
    generate_narration,
    TTSServiceError,
)
from core.services.narrated_clip_service import (
    create_narrated_clip,
    NarratedClipError,
)
logger = logging.getLogger(__name__)
@api_view(["GET"])
def health_check(request):
    return Response(
        {
            "status": "success",
            "message": "EduClip AI backend is running",
            "project": "EduClip AI",
        }
    )


@api_view(["GET", "POST"])
def topic_list(request):
    if request.method == "GET":
        topics = Topic.objects.all()
        serializer = TopicSerializer(topics, many=True)

        return Response(
            {
                "status": "success",
                "count": topics.count(),
                "topics": serializer.data,
            }
        )

    serializer = TopicSerializer(data=request.data)

    if serializer.is_valid():
        topic = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "Topic created successfully",
                "topic": TopicSerializer(topic).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "status": "error",
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )

@api_view(["GET", "POST", "DELETE"])
def video_list(request):
    # GET: Retrieve saved videos
    if request.method == "GET":
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)

        return Response(
            {
                "status": "success",
                "count": videos.count(),
                "videos": serializer.data,
            }
        )

    # DELETE: Remove a saved video
    if request.method == "DELETE":
        video_id = request.data.get("video_id")

        if not video_id:
            return Response(
                {"error": "video_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            video = Video.objects.get(pk=video_id)
        except (Video.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "Saved video not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        video_title = video.title
        video.delete()

        return Response(
            {
                "status": "success",
                "message": f'"{video_title}" was removed from saved videos.',
            },
            status=status.HTTP_200_OK,
        )

    # POST: Save a new video
    serializer = VideoSerializer(data=request.data)

    if serializer.is_valid():
        video = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "Video created successfully",
                "video": VideoSerializer(video).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "status": "error",
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )

@api_view(["GET", "POST"])
def transcript_list(request):
    if request.method == "GET":
        transcripts = Transcript.objects.all()
        serializer = TranscriptSerializer(transcripts, many=True)

        return Response(
            {
                "status": "success",
                "count": transcripts.count(),
                "transcripts": serializer.data,
            }
        )

    serializer = TranscriptSerializer(data=request.data)

    if serializer.is_valid():
        transcript = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "Transcript created successfully",
                "transcript": TranscriptSerializer(transcript).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "status": "error",
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )

@api_view(["GET", "POST", "DELETE"])
def transcript_segment_list(request):
    # GET: Retrieve all transcript segments
    if request.method == "GET":
        segments = TranscriptSegment.objects.all()
        serializer = TranscriptSegmentSerializer(
            segments,
            many=True,
        )

        return Response(
            {
                "status": "success",
                "count": segments.count(),
                "segments": serializer.data,
            }
        )

    # DELETE: Delete selected segments from a transcript
    if request.method == "DELETE":
        segment_ids = request.data.get("segment_ids", [])
        transcript_id = request.data.get("transcript_id")

        if not isinstance(segment_ids, list) or not segment_ids:
            return Response(
                {"error": "Select at least one segment to delete."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not transcript_id:
            return Response(
                {"error": "transcript_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        segments = TranscriptSegment.objects.filter(
            id__in=segment_ids,
            transcript_id=transcript_id,
        )

        deleted_count = segments.count()

        if deleted_count == 0:
            return Response(
                {"error": "No matching segments were found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        segments.delete()

        return Response(
            {
                "status": "success",
                "message": f"{deleted_count} segment(s) deleted successfully.",
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )

    # POST: Create a new transcript segment
    serializer = TranscriptSegmentSerializer(
        data=request.data
    )

    if serializer.is_valid():
        segment = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "Transcript segment created successfully",
                "segment": TranscriptSegmentSerializer(
                    segment
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "status": "error",
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "POST"])
def generated_clip_list(request):
    if request.method == "GET":
        clips = GeneratedClip.objects.all()
        serializer = GeneratedClipSerializer(
            clips,
            many=True,
        )

        return Response(
            {
                "status": "success",
                "count": clips.count(),
                "clips": serializer.data,
            }
        )

    serializer = GeneratedClipSerializer(
        data=request.data
    )

    if serializer.is_valid():
        clip = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "Generated clip created successfully",
                "clip": GeneratedClipSerializer(
                    clip
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {
            "status": "error",
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
def test_ai(request):
    prompt = request.data.get(
        "prompt",
        "Explain artificial intelligence in two simple sentences.",
    )

    if not isinstance(prompt, str) or not prompt.strip():
        return Response(
            {
                "status": "error",
                "message": "Prompt must be a non-empty string.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        answer = generate_ai_response(
            prompt=prompt,
            system_prompt=(
                "You are EduClip AI, an assistant that creates "
                "clear, accurate educational content."
            ),
        )

        return Response(
            {
                "status": "success",
                "message": "OpenRouter AI response generated successfully.",
                "prompt": prompt,
                "answer": answer,
            },
            status=status.HTTP_200_OK,
        )

    except (RuntimeError, ValueError) as exc:
        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

@api_view(["POST"])
def enhance_clip_text(request):
    text = request.data.get("text", "")

    if not isinstance(text, str) or not text.strip():
        return Response(
            {
                "status": "error",
                "message": "Provide non-empty text to enhance.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(text) > 20000:
        return Response(
            {
                "status": "error",
                "message": "Text must be 20,000 characters or fewer.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        enhanced_text = generate_ai_response(
            prompt=(
                "Rewrite the educational text below as a clear, engaging "
                "short-form educational video script. Preserve the original "
                "facts and meaning. Use simple language, a strong opening, "
                "short sentences, and a logical flow. Do not invent facts. "
                "Return only the improved script.\n\n"
                f"TEXT:\n{text}"
            ),
            system_prompt=(
                "You are EduClip AI, an educational script editor. "
                "Be accurate, concise, and easy to understand."
            ),
        )

        if not isinstance(enhanced_text, str) or not enhanced_text.strip():
            return Response(
                {
                    "status": "error",
                    "message": "AI returned an empty script.",
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "status": "success",
                "original_text": text,
                "enhanced_text": enhanced_text.strip(),
            },
            status=status.HTTP_200_OK,
        )

    except (RuntimeError, ValueError):
        return Response(
            {
                "status": "error",
                "message": "AI enhancement failed. Check the OpenRouter configuration and try again.",
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )



@api_view(["POST"])
def generate_topics(request):
    try:
        topics = generate_trending_topics()
        created_count = 0
        existing_count = 0

        with transaction.atomic():
            for item in topics:
                title = item["title"].strip()

                # Find an existing topic without regard to letter case.
                existing_topic = Topic.objects.filter(
                    title__iexact=title
                ).first()

                if existing_topic:
                    # Update the existing record instead of duplicating it.
                    existing_topic.category = item["category"]
                    existing_topic.keywords = item["keywords"]
                    existing_topic.difficulty = item["difficulty"]
                    existing_topic.trend_score = item["trend_score"]
                    existing_topic.save()
                    existing_count += 1
                else:
                    Topic.objects.create(
                        title=title,
                        category=item["category"],
                        keywords=item["keywords"],
                        difficulty=item["difficulty"],
                        trend_score=item["trend_score"],
                    )
                    created_count += 1

        return Response(
            {
                "status": "success",
                "message": "Topic generation and database saving completed.",
                "generated_count": len(topics),
                "created_count": created_count,
                "updated_count": existing_count,
                "total_topics_in_database": Topic.objects.count(),
            },
            status=status.HTTP_200_OK,
        )

    except (RuntimeError, ValueError) as exc:
        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["GET"])
def search_youtube(request):
    query = request.query_params.get("q", "").strip()
    max_results = request.query_params.get("max_results", "10")

    if not query:
        return Response(
            {
                "status": "error",
                "message": "Provide a search query using the q parameter.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        max_results = int(max_results)

        if not 1 <= max_results <= 50:
            raise ValueError

        videos = search_youtube_videos(
            query=query,
            max_results=max_results,
        )

        return Response(
            {
                "status": "success",
                "query": query,
                "count": len(videos),
                "videos": videos,
            },
            status=status.HTTP_200_OK,
        )

    except ValueError:
        return Response(
            {
                "status": "error",
                "message": "max_results must be an integer from 1 to 50.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except YouTubeAPIError as exc:
        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    except Exception:
        return Response(
            {
                "status": "error",
                "message": "An unexpected error occurred while searching YouTube.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class TranscribeAudioView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        video_id = request.data.get("video_id")
        audio_file = request.FILES.get("audio_file")

        if not video_id or not audio_file:
            return Response(
                {
                    "error": "Both video_id and audio_file are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            video = Video.objects.get(pk=video_id)
        except (Video.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "The selected video was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        allowed_extensions = {".mp3", ".wav", ".m4a", ".aac", ".flac"}
        extension = Path(audio_file.name).suffix.lower()

        if extension not in allowed_extensions:
            return Response(
                {
                    "error": (
                        "Unsupported audio format. "
                        "Upload MP3, WAV, M4A, AAC, or FLAC."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        audio_directory = Path(settings.MEDIA_ROOT) / "audio"
        audio_directory.mkdir(parents=True, exist_ok=True)

        audio_path = audio_directory / f"{uuid4().hex}{extension}"

        try:
            with audio_path.open("wb") as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            result = transcribe_audio(str(audio_path))

            if not result["full_text"].strip():
                audio_path.unlink(missing_ok=True)
                return Response(
                    {"error": "No speech was detected in the audio."},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            with transaction.atomic():
                transcript, _ = Transcript.objects.update_or_create(
                    video=video,
                    defaults={
                        "full_text": result["full_text"],
                        "language": result["language"],
                    },
                )

                TranscriptSegment.objects.filter(
                    transcript=transcript
                ).delete()

                segments = [
                    TranscriptSegment(
                        transcript=transcript,
                        text=segment["text"],
                        start_time=segment["start_time"],
                        end_time=segment["end_time"],
                    )
                    for segment in result["segments"]
                    if segment["text"].strip()
                ]

                TranscriptSegment.objects.bulk_create(segments)

            return Response(
                {
                    "status": "success",
                    "message": "Audio transcribed and saved successfully.",
                    "video_id": video.id,
                    "transcript_id": transcript.id,
                    "language": result["language"],
                    "full_text": result["full_text"],
                    "segment_count": len(segments),
                    "segments": [
                        {
                            "start_time": segment["start_time"],
                            "end_time": segment["end_time"],
                            "text": segment["text"],
                        }
                        for segment in result["segments"]
                    ],
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:
            audio_path.unlink(missing_ok=True)
            return Response(
                {"error": f"Transcription failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImportCaptionsView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        video_id = request.data.get("video_id")
        caption_file = request.FILES.get("caption_file")

        if not video_id or not caption_file:
            return Response(
                {"error": "video_id and caption_file are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            video = Video.objects.get(pk=video_id)
        except (Video.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "Saved video not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        extension = Path(caption_file.name).suffix.lower()

        if extension not in {".srt", ".vtt"}:
            return Response(
                {"error": "Upload an SRT or VTT caption file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=extension,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

                for chunk in caption_file.chunks():
                    temp_file.write(chunk)

            segments = parse_caption_file(temp_path)

            full_text = " ".join(
                segment["text"] for segment in segments
            )

            with transaction.atomic():
                transcript, _ = Transcript.objects.update_or_create(
                    video=video,
                    defaults={
                        "full_text": full_text,
                        "language": request.data.get("language", "unknown"),
                    },
                )

                TranscriptSegment.objects.filter(
                    transcript=transcript
                ).delete()

                TranscriptSegment.objects.bulk_create([
                    TranscriptSegment(
                        transcript=transcript,
                        start_time=segment["start_time"],
                        end_time=segment["end_time"],
                        text=segment["text"],
                    )
                    for segment in segments
                ])

            return Response(
                {
                    "status": "success",
                    "video_id": video.id,
                    "youtube_id": video.youtube_id,
                    "transcript_id": transcript.id,
                    "segment_count": len(segments),
                    "full_text": full_text,
                    "segments": segments,
                },
                status=status.HTTP_201_CREATED,
            )

        except (ValueError, UnicodeError) as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            return Response(
                {"error": "Could not import captions. Check the server logs."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


@api_view(["POST"])
def generate_clip(request):
    video_id = request.data.get("video_id")
    start_time = request.data.get("start_time")
    end_time = request.data.get("end_time")
    custom_text = request.data.get("text", "")

    if video_id is None or start_time is None or end_time is None:
        return Response(
            {
                "status": "error",
                "message": "video_id, start_time, and end_time are required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        start_time = float(start_time)
        end_time = float(end_time)
    except (TypeError, ValueError):
        return Response(
            {"status": "error", "message": "Timestamps must be numbers."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if start_time < 0 or end_time <= start_time:
        return Response(
            {
                "status": "error",
                "message": "End time must be greater than start time.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        video = Video.objects.get(pk=video_id)
    except (Video.DoesNotExist, ValueError, TypeError):
        return Response(
            {"status": "error", "message": "Video not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not video.source_file:
        return Response(
            {
                "status": "error",
                "message": (
                    "This video has no uploaded source file. "
                    "Upload an authorized local video before generating a clip."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    input_path = Path(video.source_file.path)

    if not input_path.is_file():
        return Response(
            {"status": "error", "message": "The source video file is missing."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    output_dir = Path(settings.MEDIA_ROOT) / "generated_clips"
    output_name = f"clip_{uuid.uuid4().hex}.mp4"
    output_path = output_dir / output_name

    try:
        generate_video_clip(
            input_path=input_path,
            start_time=start_time,
            end_time=end_time,
            output_path=output_path,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        if output_path.exists():
            output_path.unlink()
        return Response(
            {
                "status": "error",
                "message": "Unexpected error while generating the video clip.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    relative_output_path = output_path.relative_to(
        Path(settings.MEDIA_ROOT)
    ).as_posix()

    try:
        clip = GeneratedClip.objects.create(
            video=video,
            start_time=start_time,
            end_time=end_time,
            custom_text=custom_text,
            output_file=relative_output_path,
        )
    except Exception:
        if output_path.exists():
            output_path.unlink()
        raise

    return Response(
        {
            "status": "success",
            "message": "Video clip generated successfully.",
            "clip_id": clip.id,
            "video_id": video.id,
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "duration": round(end_time - start_time, 2),
            "output_file": clip.output_file,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def search_licensed_media(request):
    query = request.query_params.get("q", "").strip()

    if not query:
        return Response(
            {
                "status": "error",
                "message": "Enter an educational topic to search.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        results = search_licensed_videos(query, limit=10)

        return Response({
            "status": "success",
            "provider": "wikimedia_commons",
            "count": len(results),
            "videos": results,
        })

    except ValueError as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except RuntimeError as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

@api_view(["POST"])
def download_licensed_media(request):
    source_id = request.data.get("source_id", "").strip()

    if not source_id:
        return Response(
            {
                "status": "error",
                "message": "source_id is required."
            },
            status=400
        )

    if not source_id.startswith("File:") or len(source_id) > 500:
        return Response(
            {
                "status": "error",
                "message": "Invalid Wikimedia Commons source ID."
            },
            status=400
        )

    try:
        result = download_licensed_video(source_id)

        return Response(
            {
                "status": "success",
                "message": "Licensed media downloaded successfully.",
                "media": {
                    "source_id": result["source_id"],
                    "source_page": result["source_page"],
                    "relative_path": result["relative_path"],
                    "mime_type": result["mime_type"],
                    "license": result["license"],
                    "license_url": result["license_url"],
                    "creator": result["creator"],
                    "credit": result["credit"],
                }
            },
            status=200
        )

    except ValueError as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=400
        )

    except RuntimeError as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=502
        )

    except Exception:
        logger.exception("Licensed media download failed")
        return Response(
        {
            "status": "error",
            "message": "The download failed. Check the Django terminal."
        },
        status=500
    )


@api_view(["GET"])
def search_internet_archive_media(request):
    query = request.query_params.get("q", "").strip()

    if not query:
        return Response(
            {
                "status": "error",
                "message": "Enter an educational topic to search.",
            },
            status=400,
        )

    try:
        videos = search_internet_archive_videos(query, limit=10)

        return Response(
            {
                "status": "success",
                "provider": "internet_archive",
                "count": len(videos),
                "videos": videos,
            },
            status=200,
        )

    except ValueError as exc:
        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=400,
        )

    except RuntimeError as exc:
        return Response(
            {
                "status": "error",
                "message": str(exc),
            },
            status=502,
        )

# --- Pixabay endpoints: add these imports near the top of core/views.py ---
# from core.services.pixabay_service import (
#     search_pixabay_videos,
#     download_pixabay_video,
#     PixabayServiceError,
# )

@api_view(["GET"])
def pixabay_video_search(request):
    """GET /api/licensed-media/pixabay/search/?q=python&per_page=9"""
    query = request.query_params.get("q", "").strip()
    per_page = request.query_params.get("per_page", 9)
    try:
        per_page = int(per_page)
        result = search_pixabay_videos(query, per_page)
        return Response(result)
    except ValueError:
        return Response(
            {"status": "error", "message": "per_page must be a number."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except PixabayServiceError as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["POST"])
def pixabay_video_download(request):
    """POST /api/licensed-media/pixabay/download/"""
    download_url = request.data.get("download_url", "")
    title = request.data.get("title", "pixabay-video")
    try:
        result = download_pixabay_video(download_url, title)
        return Response({
            "status": "success",
            "message": "Pixabay footage downloaded successfully.",
            **result,
        }, status=status.HTTP_201_CREATED)
    except PixabayServiceError as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )



@api_view(["POST"])
def generate_narrated_video(request):
    """
    POST /api/narrated-clips/generate/

    JSON:
    {
        "video_path": "pixabay_downloads/example.mp4",
        "text": "Educational narration text",
        "voice": "en-US-AriaNeural",
        "start_time": 0,
        "end_time": 15
    }
    """
    video_path = request.data.get("video_path", "")
    text = request.data.get("text", "")
    voice = request.data.get("voice", "en-US-AriaNeural")
    start_time = request.data.get("start_time", 0)
    end_time = request.data.get("end_time")

    if not isinstance(video_path, str) or not video_path.strip():
        return Response(
            {"status": "error", "message": "Select a downloaded Pixabay video first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not isinstance(text, str) or not text.strip():
        return Response(
            {"status": "error", "message": "Narration text is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        start_time = float(start_time)
        end_time = float(end_time) if end_time is not None else None

        if start_time < 0:
            raise ValueError("start_time cannot be negative.")

        if end_time is not None and end_time <= start_time:
            raise ValueError("end_time must be greater than start_time.")

    except (TypeError, ValueError) as exc:
        return Response(
            {"status": "error", "message": str(exc) or "Invalid timestamps."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    media_root = Path(settings.MEDIA_ROOT).resolve()
    video_root = (media_root / "pixabay_downloads").resolve()

    try:
        supplied_path = Path(video_path.strip())
        candidate = (
            supplied_path.resolve()
            if supplied_path.is_absolute()
            else (media_root / supplied_path).resolve()
        )

        # Prevent access to files outside the Pixabay download folder.
        candidate.relative_to(video_root)

        if candidate.suffix.lower() not in {".mp4", ".mov", ".webm", ".mkv"}:
            raise ValueError("Unsupported video file type.")

        if not candidate.is_file():
            return Response(
                {
                    "status": "error",
                    "message": "The selected Pixabay video file does not exist.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    except (ValueError, OSError):
        return Response(
            {
                "status": "error",
                "message": (
                    "Select a valid downloaded video from "
                    "MEDIA_ROOT/pixabay_downloads."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        narration = generate_narration(text.strip(), voice)

        clip = create_narrated_clip(
            video_path=str(candidate),
            audio_path=narration["file_path"],
            output_name="educational-clip",
            start_time=start_time,
            end_time=end_time,
        )

        return Response(
            {
                "status": "success",
                "message": "Narrated educational video created successfully.",
                "clip": clip,
                "narration": {
                    "relative_path": narration["relative_path"],
                    "voice": narration["voice"],
                    "size_bytes": narration["size_bytes"],
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except (TTSServiceError, NarratedClipError) as exc:
        return Response(
            {"status": "error", "message": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )


@api_view(["GET", "DELETE"])
def narrated_clip_files(request):
    """List or delete generated narrated MP4 files."""
    clips_dir = (Path(settings.MEDIA_ROOT) / "narrated_clips").resolve()
    clips_dir.mkdir(parents=True, exist_ok=True)

    # DELETE: Remove a selected narrated video.
    if request.method == "DELETE":
        filename = request.data.get("filename", "")

        # Validate the filename.
        if (
            not isinstance(filename, str)
            or not filename.strip()
            or Path(filename).name != filename
            or not filename.lower().endswith(".mp4")
        ):
            return Response(
                {
                    "status": "error",
                    "message": "A valid MP4 filename is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_path = (clips_dir / filename).resolve()

        # Prevent deleting files outside the narrated_clips directory.
        if file_path.parent != clips_dir:
            return Response(
                {
                    "status": "error",
                    "message": "Invalid file path.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check whether the video exists.
        if not file_path.is_file():
            return Response(
                {
                    "status": "error",
                    "message": "Generated video was not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delete the selected video.
        try:
            file_path.unlink()
        except OSError:
            logger.exception(
                "Failed to delete narrated video: %s", filename
            )
            return Response(
                {
                    "status": "error",
                    "message": "Could not delete the video file.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "status": "success",
                "message": f"{filename} deleted successfully.",
                "filename": filename,
            },
            status=status.HTTP_200_OK,
        )

    # GET: List all generated narrated MP4 videos.
    clips = []

    for file_path in sorted(
        clips_dir.glob("*.mp4"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        stat_result = file_path.stat()

        clips.append(
            {
                "filename": file_path.name,
                "title": file_path.stem.replace("_", " "),
                "relative_path": (
                    f"narrated_clips/{file_path.name}"
                ),
                "url": (
                    f"{settings.MEDIA_URL.rstrip('/')}"
                    f"/narrated_clips/{file_path.name}"
                ),
                "size_bytes": stat_result.st_size,
                "created_at": stat_result.st_mtime,
            }
        )

    return Response(
        {
            "status": "success",
            "count": len(clips),
            "clips": clips,
        },
        status=status.HTTP_200_OK,
    )

class TranscribeYouTubeView(APIView):
    """
    Extract audio from an accessible YouTube video and save
    its transcript and timestamped segments.
    """

    def post(self, request):
        import tempfile
        from pathlib import Path
        from django.db import transaction

        video_id = request.data.get("video_id")

        if not video_id:
            return Response(
                {"error": "video_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            video = Video.objects.get(pk=video_id)
        except (Video.DoesNotExist, ValueError, TypeError):
            return Response(
                {"error": "Selected video was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not video.url or "youtube.com" not in video.url and "youtu.be" not in video.url:
            return Response(
                {"error": "The selected video does not have a valid YouTube URL."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_template = str(Path(temp_dir) / "audio.%(ext)s")

                options = {
                    "format": "bestaudio/best",
                    "outtmpl": output_template,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "socket_timeout": 30,
                    "max_filesize": 500 * 1024 * 1024,
                    "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128",
                    }],
                }

                with yt_dlp.YoutubeDL(options) as downloader:
                    downloader.download([video.url])

                audio_path = Path(temp_dir) / "audio.mp3"

                if not audio_path.is_file():
                    return Response(
                        {"error": "Audio extraction did not produce an audio file."},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )

                result = transcribe_audio(str(audio_path))
                full_text = result.get("full_text", "").strip()
                result_segments = result.get("segments", [])

                if not full_text or not result_segments:
                    return Response(
                        {"error": "No speech or timestamped segments were detected."},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )

                with transaction.atomic():
                    transcript, _ = Transcript.objects.update_or_create(
                        video=video,
                        defaults={
                            "full_text": full_text,
                            "language": result.get("language", "unknown"),
                        },
                    )

                    TranscriptSegment.objects.filter(
                        transcript=transcript
                    ).delete()

                    saved_segments = [
                        TranscriptSegment(
                            transcript=transcript,
                            text=item["text"].strip(),
                            start_time=item["start_time"],
                            end_time=item["end_time"],
                        )
                        for item in result_segments
                        if item.get("text", "").strip()
                    ]

                    TranscriptSegment.objects.bulk_create(saved_segments)

                return Response({
                    "status": "success",
                    "message": "YouTube audio transcribed successfully.",
                    "video_id": video.id,
                    "transcript_id": transcript.id,
                    "language": result.get("language", "unknown"),
                    "full_text": full_text,
                    "segment_count": len(saved_segments),
                    "segments": [
                        {
                            "id": segment.id,
                            "text": segment.text,
                            "start_time": segment.start_time,
                            "end_time": segment.end_time,
                        }
                        for segment in saved_segments
                    ],
                }, status=status.HTTP_201_CREATED)

        except Exception as exc:
            logger.exception("YouTube transcription failed")
            return Response(
                {
                    "error": (
                        "Could not extract or transcribe this video. "
                        "It may be unavailable, restricted, or incompatible. "
                        f"Details: {str(exc)[:300]}"
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
