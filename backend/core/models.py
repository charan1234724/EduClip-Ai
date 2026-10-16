from django.db import models


class Topic(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    keywords = models.JSONField(default=list, blank=True)
    difficulty = models.CharField(max_length=50, default="Beginner")
    trend_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-trend_score", "-created_at"]

    def __str__(self):
        return self.title


class Video(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="videos",
    )
    source_file = models.FileField(
    upload_to="uploads/",
    blank=True,
    null=True,
    )
    youtube_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=500)
    channel = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=500)
    thumbnail = models.URLField(max_length=500, blank=True)
    view_count = models.BigIntegerField(default=0)
    duration = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        ordering = ["-view_count", "-created_at"]

    def __str__(self):
        return self.title

class Transcript(models.Model):
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name="transcript",
    )
    full_text = models.TextField(blank=True)
    language = models.CharField(max_length=50, default="en")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcript - {self.video.title}"


class TranscriptSegment(models.Model):
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    text = models.TextField()
    start_time = models.FloatField()
    end_time = models.FloatField()

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.start_time:.2f}s - {self.end_time:.2f}s"


class GeneratedClip(models.Model):
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="generated_clips",
    )
    start_time = models.FloatField()
    end_time = models.FloatField()
    custom_text = models.TextField(blank=True)
    output_file = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Clip - {self.video.title}"