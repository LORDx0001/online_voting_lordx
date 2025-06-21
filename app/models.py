from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class VoterManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Telefon raqam kiritilishi shart')
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
            raise ValueError('Superuser uchun is_staff=True bo‘lishi kerak')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser uchun is_superuser=True bo‘lishi kerak')
        return self.create_user(phone, password, **extra_fields)

class Voter(AbstractBaseUser):
    ROLE_CHOICES = (
        (2, 'Voter'),
        (3, 'Staff'),
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=2)
    otp_code = models.CharField(max_length=10, null=True, blank=True)

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
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField(null=True, blank=True)   
    end_time = models.DateTimeField(null=True, blank=True)    

    def __str__(self):
        return self.title

class Candidate(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=100)
    info = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.poll.title})"

class Vote(models.Model):
    voter = models.ForeignKey('Voter', on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'poll')