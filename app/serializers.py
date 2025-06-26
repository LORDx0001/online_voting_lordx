from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import Poll, Candidate
import random

# Validator faqat harflar, bo‘shliq va ba'zi belgilarni ruxsat etadi
name_regex = RegexValidator(
    regex=r'^[А-Яа-яA-Za-zёЁ\-\' ]+$',
    message='Поле должно содержать только буквы, пробел, дефис или апостроф'
)

# Сериализатор для регистрации нового пользователя
class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        min_length=2,
        validators=[name_regex],
        error_messages={
            'required': 'Имя обязательно для заполнения',
            'min_length': 'Имя должно содержать минимум 2 символа'
        }
    )
    last_name = serializers.CharField(
        min_length=2,
        validators=[name_regex],
        error_messages={
            'required': 'Фамилия обязательна для заполнения',
            'min_length': 'Фамилия должна содержать минимум 2 символа'
        }
    )
    phone = serializers.CharField(
        error_messages={'required': 'Номер телефона обязателен'}
    )
    password = serializers.CharField(
        error_messages={'required': 'Пароль обязателен'}
    )
    role = serializers.ChoiceField(
        choices=[(1, 'Admin'), (2, 'Voter')],
        default=2,
        required=False
    )

# Сериализатор для подтверждения OTP
class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(
        error_messages={'required': 'Укажите номер телефона'}
    )
    otp = serializers.CharField(
        error_messages={'required': 'Укажите OTP код'}
    )

# Сериализатор для повторной отправки OTP
class ResendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(
        error_messages={'required': 'Номер телефона обязателен'}
    )

# Сериализатор для входа в систему
class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(
        error_messages={'required': 'Введите номер телефона'}
    )
    password = serializers.CharField(
        error_messages={'required': 'Введите пароль'}
    )

# Сериализатор для голосования
class VoteSerializer(serializers.Serializer):
    poll_id = serializers.IntegerField(
        error_messages={'required': 'ID опроса обязателен'}
    )
    candidate_id = serializers.IntegerField(
        error_messages={'required': 'ID кандидата обязателен'}
    )

# Сериализатор для создания опроса
class PollCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ['title', 'description', 'start_date', 'start_time', 'end_date', 'end_time']

# Сериализатор для создания кандидата
class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['poll', 'name', 'info']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Candidate.objects.all(),
                fields=['poll', 'name'],
                message='Кандидат с таким именем уже существует в этом опросе'
            )
        ]

# Сериализатор для смены пароля
class ResetPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        error_messages={'required': 'Введите старый пароль'}
    )
    new_password = serializers.CharField(
        error_messages={'required': 'Введите новый пароль'}
    )

# Сериализатор для запроса OTP при восстановлении пароля
class ForgotPasswordSendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(
        error_messages={'required': 'Номер телефона обязателен'}
    )

# Сериализатор для подтверждения восстановления пароля
class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(
        error_messages={'required': 'Номер телефона обязателен'}
    )
    otp = serializers.CharField(
        error_messages={'required': 'Введите OTP код'}
    )
    new_password = serializers.CharField(
        error_messages={'required': 'Введите новый пароль'}
    )

# Сериализатор для смены имени и фамилии
class ChangeNameSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        required=True,
        min_length=2,
        validators=[name_regex],
        error_messages={
            'required': 'Имя обязательно',
            'min_length': 'Имя должно содержать минимум 2 символа'
        }
    )
    last_name = serializers.CharField(
        required=True,
        min_length=2,
        validators=[name_regex],
        error_messages={
            'required': 'Фамилия обязательна',
            'min_length': 'Фамилия должна содержать минимум 2 символа'
        }
    )

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

# Сериализатор для смены номера телефона с отправкой OTP
class ChangePhoneNumberSerializer(serializers.Serializer):
    phone = serializers.CharField(
        required=True,
        error_messages={'required': 'Номер телефона обязателен'}
    )

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
                raise serializers.ValidationError({'otp': 'Введите OTP код для подтверждения номера'})
            if otp != otp_code:
                raise serializers.ValidationError({'otp': 'Неверный OTP код'})
            instance.is_phone_verified = True
            instance.otp_code = None
            instance.phone = validated_data['phone']
        instance.save()
        return instance

# Сериализатор для подтверждения смены номера телефона
class ChangePhoneNumberVerifySerializer(serializers.Serializer):
    phone = serializers.CharField(
        required=True,
        error_messages={'required': 'Номер телефона обязателен'}
    )
    otp = serializers.CharField(
        required=True,
        error_messages={'required': 'Введите OTP код'}
    )

    def validate(self, attrs):
        user = self.instance
        phone = attrs.get('phone')
        otp = attrs.get('otp')

        if not user.new_phone or user.new_phone != phone:
            raise serializers.ValidationError({'phone': 'Неверный или неподтверждённый номер телефона'})
        if not user.otp_code or otp != user.otp_code:
            raise serializers.ValidationError({'otp': 'Неверный OTP код'})
        return attrs

    def save(self, **kwargs):
        user = self.instance
        user.phone = user.new_phone
        user.new_phone = None
        user.otp_code = None
        user.is_phone_verified = True
        user.save()
        return user
