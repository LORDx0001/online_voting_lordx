from rest_framework import serializers
from .models import Poll, Candidate

# Bu faylda barcha API uchun serializerlar joylashgan.
# Serializerlar ma'lumotlarni tekshiradi va validatsiya qiladi.
# Har bir serializer API endpoint uchun kiruvchi (input) va chiquvchi (output) ma'lumotlarni aniqlaydi.

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField()
    password = serializers.CharField()
    role = serializers.ChoiceField(choices=[(1, 'Admin'), (2, 'Voter')], default=2, required=False)

# RegisterSerializer:
# - Ro'yxatdan o'tish uchun: ism, familiya, telefon, parol va rol maydonlarini tekshiradi.

class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()

# VerifyOtpSerializer:
# - Telefon raqami va OTP kodini tekshiradi (OTP tasdiqlash uchun).

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()


# LoginSerializer:
# - Login uchun telefon va parol maydonlarini tekshiradi.

class VoteSerializer(serializers.Serializer):
    poll_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()

# VoteSerializer:
# - Ovoz berish uchun poll_id va candidate_id maydonlarini tekshiradi.

class PollCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['id', 'title', 'description']

# PollCreateSerializer:
# - Poll (so'rovnoma) yaratish va ko'rsatish uchun model serializer.

class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'poll', 'name', 'info']

# CandidateCreateSerializer:
# - Kandidat (nomzod) yaratish va ko'rsatish uchun model serializer.

class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

# ResetPasswordSerializer:
# - Parolni o'zgartirish uchun eski va yangi parol maydonlarini tekshiradi.

class ForgotPasswordSendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)

# ForgotPasswordSendOtpSerializer:
# - Parolni unutgan foydalanuvchi uchun telefon raqamini tekshiradi (OTP yuborish uchun).

class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

# ForgotPasswordConfirmSerializer:
# - Parolni tiklash uchun telefon, OTP va yangi parol maydonlarini tekshiradi.