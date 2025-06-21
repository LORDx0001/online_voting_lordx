from rest_framework import serializers
from .models import Poll, Candidate

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    password = serializers.CharField()
    role = serializers.ChoiceField(choices=[(1, 'Admin'), (2, 'Voter')], default=2, required=False)

class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

class VoteSerializer(serializers.Serializer):
    poll_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()

class PollCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['id', 'title', 'description']

class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'poll', 'name', 'info']

class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ForgotPasswordSendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)

class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)