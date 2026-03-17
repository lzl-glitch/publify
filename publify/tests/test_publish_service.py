"""Tests for publish service."""
import pytest

from app.services.publish_service import ContentValidationError, PublishService


@pytest.fixture
def publish_service():
    """Return publish service instance."""
    return PublishService()


def test_validate_text_success(publish_service):
    """Test successful text validation."""
    # Should not raise
    publish_service.validate_text("This is a valid post")
    publish_service.validate_text("a" * 1000)  # Max length


def test_validate_text_failure(publish_service):
    """Test text validation failures."""
    with pytest.raises(ContentValidationError):
        publish_service.validate_text("")

    with pytest.raises(ContentValidationError):
        publish_service.validate_text("a" * 1001)  # Too long


def test_validate_media_urls_text(publish_service):
    """Test media URL validation for text content."""
    # Text content should not have media URLs
    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("text", ["http://example.com/image.jpg"])

    # Text content without media URLs should pass
    publish_service.validate_media_urls("text", None)
    publish_service.validate_media_urls("text", [])


def test_validate_media_urls_image(publish_service):
    """Test media URL validation for image content."""
    # Images require URLs
    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("image", None)

    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("image", [])

    # Valid image URLs
    publish_service.validate_media_urls("image", ["http://example.com/1.jpg"])
    publish_service.validate_media_urls("image", ["http://example.com/1.jpg"] * 9)

    # Too many images
    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("image", ["http://example.com/1.jpg"] * 10)

    # Invalid URL format
    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("image", ["not-a-url"])


def test_validate_media_urls_video(publish_service):
    """Test media URL validation for video content."""
    # Video requires exactly one URL
    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("video", None)

    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("video", [])

    with pytest.raises(ContentValidationError):
        publish_service.validate_media_urls("video", ["http://example.com/1.mp4", "http://example.com/2.mp4"])

    # Valid video URL
    publish_service.validate_media_urls("video", ["http://example.com/video.mp4"])


def test_validate_content_invalid_platform(publish_service):
    """Test content validation with invalid platform."""
    with pytest.raises(ContentValidationError) as exc:
        publish_service.validate_content("invalid_platform", "text", "test")

    assert exc.value.code == "PLATFORM_ERROR"


def test_validate_content_invalid_type(publish_service):
    """Test content validation with invalid content type."""
    with pytest.raises(ContentValidationError):
        publish_service.validate_content("xiaohongshu", "invalid", "test")


def test_validate_content_success(publish_service):
    """Test successful content validation."""
    # Text
    publish_service.validate_content("xiaohongshu", "text", "Valid text post")

    # Image
    publish_service.validate_content(
        "xiaohongshu",
        "image",
        "Valid image post",
        ["http://example.com/image.jpg"],
    )

    # Video
    publish_service.validate_content(
        "xiaohongshu",
        "video",
        "Valid video post",
        ["http://example.com/video.mp4"],
    )
