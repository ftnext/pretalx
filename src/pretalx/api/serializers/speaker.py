from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    SerializerMethodField,
)

from pretalx.api.serializers.question import AnswerSerializer
from pretalx.api.serializers.room import AvailabilitySerializer
from pretalx.common.urls import build_absolute_uri
from pretalx.person.models import SpeakerProfile, User
from pretalx.schedule.models import Availability
from pretalx.submission.models import Answer


class SubmitterSerializer(ModelSerializer):
    biography = SerializerMethodField()

    def get_biography(self, obj):
        if self.context.get("request") and self.context["request"].event:
            return getattr(
                obj.profiles.filter(event=self.context["request"].event).first(),
                "biography",
                "",
            )
        return ""

    class Meta:
        model = User
        fields = ("code", "name", "biography", "avatar")


class SpeakerSerializer(ModelSerializer):
    code = CharField(source="user.code")
    name = CharField(source="user.name")
    avatar = SerializerMethodField()
    submissions = SerializerMethodField()

    @staticmethod
    def get_avatar(obj):
        if obj.user.get_gravatar:
            return "https://www.gravatar.com/avatar/" + obj.user.gravatar_parameter
        if obj.user.has_local_avatar:
            return build_absolute_uri(obj.user.avatar.url, obj.event)

    @staticmethod
    def get_submissions(obj):
        talks = (
            obj.event.current_schedule.talks.all() if obj.event.current_schedule else []
        )
        return obj.user.submissions.filter(
            event=obj.event, slots__in=talks
        ).values_list("code", flat=True)

    class Meta:
        model = SpeakerProfile
        fields = ("code", "name", "biography", "submissions", "avatar")


class SpeakerOrgaSerializer(SpeakerSerializer):
    email = CharField(source="user.email")
    answers = AnswerSerializer(Answer.objects.none(), many=True, read_only=True)
    availabilities = AvailabilitySerializer(
        Availability.objects.none(), many=True, read_only=True
    )

    def get_submissions(self, obj):
        return obj.user.submissions.filter(event=obj.event).values_list(
            "code", flat=True
        )

    class Meta(SpeakerSerializer.Meta):
        fields = SpeakerSerializer.Meta.fields + ("answers", "email", "availabilities")


class SpeakerReviewerSerializer(SpeakerOrgaSerializer):
    answers = AnswerSerializer(many=True, source="reviewer_answers")

    class Meta(SpeakerOrgaSerializer.Meta):
        pass
