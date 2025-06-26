from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class VoterManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Номер телефона обязателен для регистрации')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 1)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Персонал должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')

        return self.create_user(phone, password, **extra_fields)


class Voter(AbstractBaseUser):
    """
    Пользовательская модель для системы голосования:
    - first_name, last_name: имя и фамилия пользователя кастомнизированы с валидаторами
    - phone: уникальный номер телефона (используется для входа)
    - is_phone_verified: подтвержден ли номер телефона
    - is_active, is_staff, is_superuser: флаги доступа Django
    - role: роль пользователя (2 - Voter, 3 - Staff)
    - otp_code: код подтверждения номера
    - new_phone, phone_change_otp: обновление номера и код подтверждения
    """

    ROLE_CHOICES = (
        (2, 'Voter'),
        (3, 'Staff'),
    )

    first_name = models.CharField(
        max_length=50,
        validators=[
            MinLengthValidator(2, message='Имя должно содержать минимум 2 символа'),
            RegexValidator(r'^[А-Яа-яA-Za-zёЁ\-\' ]+$', message='Имя должно содержать только буквы')
        ]
    )
    last_name = models.CharField(
        max_length=50,
        validators=[
            MinLengthValidator(2, message='Фамилия должна содержать минимум 2 символа'),
            RegexValidator(r'^[А-Яа-яA-Za-zёЁ\-\' ]+$', message='Фамилия должна содержать только буквы')
        ]
    )
    phone = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=2)
    otp_code = models.CharField(max_length=10, null=True, blank=True)
    new_phone = models.CharField(max_length=15, null=True, blank=True)
    phone_change_otp = models.CharField(max_length=10, null=True, blank=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = VoterManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Poll(models.Model):
    """
    Модель опроса:
    - title: заголовок опроса
    - description: описание
    - start_date, start_time: дата и время начала
    - end_date, end_time: дата и время завершения
    """
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class Candidate(models.Model):
    """
    Модель кандидата:
    - poll: связанный опрос
    - name: имя кандидата
    - info: дополнительная информация
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=255)
    info = models.TextField(blank=True)

    class Meta:
        unique_together = ('poll', 'name')


class Vote(models.Model):
    """
    Модель голосования:
    - voter: кто проголосовал(тот кто зарегистрировани в системе(login))
    - poll: в каком опросе
    - candidate: за какого кандидата
    - voted_at: время голосования
    - уникальное голосование от одного пользователя в каждом опросе
    """
    voter = models.ForeignKey('Voter', on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'poll')
