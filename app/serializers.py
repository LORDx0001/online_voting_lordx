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

class ResendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()

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
        fields = 'title', 'description', 'start_date', 'start_time', 'end_date', 'end_time'


# PollCreateSerializer:
# - Poll (so'rovnoma) yaratish va ko'rsatish uchun model serializer.


class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['poll', 'name', 'info']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Candidate.objects.all(),
                fields=['poll', 'name'],
                message="Bu nomdagi kandidat ushbu so‘rovda allaqachon mavjud."
            )
        ]



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

class ChangeNameSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

class ChangePhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
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
        instance.save()
        return instance
    
class ChangePhoneNumberVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.instance
        phone = attrs.get('phone')
        otp = attrs.get('otp')
        # Yangi raqam va OTP tekshiriladi
        if not user.new_phone or user.new_phone != phone:
            raise serializers.ValidationError({'phone': 'Yangi telefon raqam noto‘g‘ri yoki kiritilmagan'})
        if not user.otp_code or otp != user.otp_code:
            raise serializers.ValidationError({'otp': 'OTP noto‘g‘ri'})
        return attrs

    def save(self, **kwargs):
        user = self.instance
        user.phone = user.new_phone
        user.new_phone = None
        user.otp_code = None
        user.is_phone_verified = True
        user.save()
        return user