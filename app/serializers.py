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
import random

class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    otp = serializers.CharField(required=False)

    def validate(self, attrs):
        phone = attrs.get('phone')
        otp = attrs.get('otp')
        user = self.instance

        if phone and phone != user.phone:
            otp_code = str(random.randint(1000, 9999))
            attrs['otp_code'] = otp_code
            attrs['is_phone_verified'] = False
            from .views import send_otp_to_telegram
            send_otp_to_telegram(phone, otp_code)
        return attrs

    def update(self, instance, validated_data):
        if 'phone' in validated_data and validated_data['phone'] != instance.phone:
            otp = validated_data.get('otp')
            otp_code = validated_data.get('otp_code') or instance.otp_code
            if not otp:
                raise serializers.ValidationError({'otp': 'Telefon raqamni tasdiqlash uchun OTP kiriting'})
            if otp != otp_code:
                raise serializers.ValidationError({'otp': 'OTP noto‘g‘ri'})
            instance.is_phone_verified = True
            instance.otp_code = None
            instance.phone = validated_data['phone']
        for attr, value in validated_data.items():
            if attr in ['otp', 'otp_code', 'phone']:
                continue  # yuqorida ishladik yoki texnik maydon
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance