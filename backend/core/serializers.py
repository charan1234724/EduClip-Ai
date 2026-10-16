from rest_framework import serializers

from .models import (
    GeneratedClip,
    Topic,
    Transcript,
    TranscriptSegment,
    Video,
)


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = [
            "id",
            "title",
            "category",
            "keywords",
            "difficulty",
            "trend_score",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]




class VideoSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(
        source="topic.title",
        read_only=True,
    )

    class Meta:
        model = Video
        fields = [
            "id",
            "topic",
            "topic_title",
            "source_file",
            "youtube_id",
            "title",
            "channel",
            "url",
            "thumbnail",
            "view_count",
            "duration",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_youtube_id(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "YouTube video ID cannot be empty."
            )

        existing_video = Video.objects.filter(
            youtube_id=value
        )

        # Exclude the current record when updating an existing video.
        if self.instance:
            existing_video = existing_video.exclude(
                pk=self.instance.pk
            )

        if existing_video.exists():
            raise serializers.ValidationError(
                "This YouTube video has already been saved. "
                "Please select a different video."
            )

        return value



class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = [
            "id",
            "video",
            "full_text",
            "language",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = [
            "id",
            "transcript",
            "text",
            "start_time",
            "end_time",
        ]
        read_only_fields = ["id"]

class GeneratedClipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedClip
        fields = [
            "id",
            "video",
            "start_time",
            "end_time",
            "custom_text",
            "output_file",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]